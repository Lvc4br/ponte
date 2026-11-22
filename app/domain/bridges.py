"""Core structural-domain entities for bridges and OAE.

Independent from the desktop UI and persistence layer. Unknown values remain
None; validation distinguishes blocking errors from review warnings.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from enum import Enum
from uuid import UUID, uuid4


def _decimal(value, label: str) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError(f"{label}: valor booleano não é uma medida válida.")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError(f"{label}: informe um número válido.") from None
    if not result.is_finite():
        raise ValueError(f"{label}: o valor precisa ser finito.")
    return result


def _positive_measure(value, label: str):
    result = _decimal(value, label)
    if result is not None and result <= 0:
        raise ValueError(f"{label}: o valor precisa ser maior que zero.")
    return result


@dataclass(frozen=True)
class Project:
    name: str
    code: str | None = None
    description: str = ""
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        if not self.name.strip():
            raise ValueError("O nome do empreendimento é obrigatório.")
        if self.code is not None and not self.code.strip():
            raise ValueError("O código do empreendimento não pode ser vazio.")


@dataclass(frozen=True)
class BridgeSpan:
    sequence: int
    length_m: Decimal
    id: UUID = field(default_factory=uuid4)
    label: str | None = None

    def __post_init__(self):
        if isinstance(self.sequence, bool) or not isinstance(self.sequence, int) or self.sequence < 1:
            raise ValueError("A sequência do vão deve ser um inteiro positivo.")
        object.__setattr__(self, "length_m", _positive_measure(self.length_m, "Comprimento do vão"))


@dataclass(frozen=True)
class Bridge:
    project_id: UUID
    code: str
    name: str
    id: UUID = field(default_factory=uuid4)
    bridge_type: str | None = None
    purpose: str | None = None
    status: str = "draft"
    length_m: Decimal | None = None
    width_m: Decimal | None = None
    municipality: str | None = None
    state: str | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    spans: tuple[BridgeSpan, ...] = ()
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        if not self.code.strip():
            raise ValueError("O código da ponte/OAE é obrigatório.")
        if not self.name.strip():
            raise ValueError("O nome da ponte/OAE é obrigatório.")
        object.__setattr__(self, "length_m", _positive_measure(self.length_m, "Comprimento total"))
        object.__setattr__(self, "width_m", _positive_measure(self.width_m, "Largura"))
        object.__setattr__(self, "latitude", _decimal(self.latitude, "Latitude"))
        object.__setattr__(self, "longitude", _decimal(self.longitude, "Longitude"))
        normalized_spans = tuple(self.spans)
        if any(not isinstance(span, BridgeSpan) for span in normalized_spans):
            raise ValueError("Todos os vãos devem ser instâncias de BridgeSpan.")
        if len({span.sequence for span in normalized_spans}) != len(normalized_spans):
            raise ValueError("A sequência dos vãos não pode se repetir.")
        object.__setattr__(self, "spans", tuple(sorted(normalized_spans, key=lambda span: span.sequence)))
        if self.latitude is not None and not Decimal("-90") <= self.latitude <= Decimal("90"):
            raise ValueError("Latitude deve estar entre -90 e 90 graus.")
        if self.longitude is not None and not Decimal("-180") <= self.longitude <= Decimal("180"):
            raise ValueError("Longitude deve estar entre -180 e 180 graus.")


@dataclass(frozen=True)
class MaterialQuantity:
    bridge_id: UUID
    material_code: str
    quantity: Decimal
    unit: str
    scope: str
    id: UUID = field(default_factory=uuid4)
    element_reference: str | None = None
    source_reference: str | None = None
    validation_status: str = "pending"

    def __post_init__(self):
        if not self.material_code.strip():
            raise ValueError("O material precisa possuir um código ou identificação.")
        quantity = _decimal(self.quantity, "Quantidade")
        if quantity is None or quantity < 0:
            raise ValueError("A quantidade deve ser informada e não pode ser negativa.")
        if not self.unit.strip():
            raise ValueError("A unidade do quantitativo é obrigatória.")
        if not self.scope.strip():
            raise ValueError("O escopo do quantitativo é obrigatório.")
        object.__setattr__(self, "quantity", quantity)


class IssueSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True)
class DomainIssue:
    code: str
    severity: IssueSeverity
    message: str
    field: str | None = None


def validate_bridge(
    bridge: Bridge,
    *,
    span_sum_tolerance_m: Decimal = Decimal("0.50"),
    span_sum_tolerance_ratio: Decimal = Decimal("0.02"),
) -> list[DomainIssue]:
    """Return review findings without silently changing engineering data.

    The sum of span lengths is only compared with total bridge length as a
    warning: definitions may differ because of approaches, joints or scope.
    """
    issues: list[DomainIssue] = []
    if bridge.length_m is not None and bridge.spans:
        span_sum = sum((span.length_m for span in bridge.spans), Decimal("0"))
        tolerance = max(span_sum_tolerance_m, bridge.length_m * span_sum_tolerance_ratio)
        difference = abs(bridge.length_m - span_sum)
        if difference > tolerance:
            issues.append(DomainIssue(
                code="BRIDGE_SPAN_LENGTH_MISMATCH",
                severity=IssueSeverity.WARNING,
                field="spans",
                message=(
                    f"A soma dos vãos ({span_sum} m) difere do comprimento total "
                    f"({bridge.length_m} m) em {difference} m. Verifique se os "
                    "escopos geométricos são equivalentes."
                ),
            ))
    if not bridge.spans:
        issues.append(DomainIssue(
            code="BRIDGE_SPANS_NOT_REGISTERED",
            severity=IssueSeverity.INFO,
            field="spans",
            message="Nenhum vão foi cadastrado; a informação permanece não informada.",
        ))
    return issues
