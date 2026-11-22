"""Versioned indicator metadata and result-state models.

No legacy engineering formula is inferred here. Definitions can only be marked
approved when the complete calculation contract has been supplied.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4


class IndicatorStatus(str, Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    RETIRED = "retired"


class IndicatorValueStatus(str, Enum):
    CALCULATED = "calculated"
    UNAVAILABLE = "unavailable"
    PENDING_VALIDATION = "pending_validation"
    APPROVED = "approved"


@dataclass(frozen=True)
class IndicatorDefinition:
    code: str
    name: str
    unit: str
    version: int = 1
    id: UUID = field(default_factory=uuid4)
    description: str = ""
    numerator_definition: str | None = None
    denominator_definition: str | None = None
    formula: str | None = None
    aggregation_rule: str | None = None
    rounding_rule: str | None = None
    source_reference: str | None = None
    status: IndicatorStatus = IndicatorStatus.DRAFT
    approved_by: str | None = None
    approved_at: datetime | None = None

    def __post_init__(self):
        for value, label in ((self.code, "Código"), (self.name, "Nome"), (self.unit, "Unidade")):
            if not value.strip():
                raise ValueError(f"{label} do indicador é obrigatório.")
        if isinstance(self.version, bool) or not isinstance(self.version, int) or self.version < 1:
            raise ValueError("A versão do indicador deve ser um inteiro positivo.")
        if self.status == IndicatorStatus.APPROVED:
            required = {
                "numerador": self.numerator_definition,
                "denominador": self.denominator_definition,
                "fórmula": self.formula,
                "regra de agregação": self.aggregation_rule,
                "arredondamento": self.rounding_rule,
                "fonte": self.source_reference,
                "responsável pela aprovação": self.approved_by,
            }
            missing = [label for label, value in required.items() if not value or not value.strip()]
            if missing or self.approved_at is None:
                raise ValueError(
                    "Indicador não pode ser aprovado; faltam: "
                    + ", ".join(missing + (["data da aprovação"] if self.approved_at is None else []))
                )


@dataclass(frozen=True)
class IndicatorResult:
    definition_id: UUID
    definition_version: int
    bridge_id: UUID
    unit: str
    status: IndicatorValueStatus
    value: Decimal | None = None
    numerator_value: Decimal | None = None
    denominator_value: Decimal | None = None
    source_references: tuple[str, ...] = ()
    calculated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: UUID = field(default_factory=uuid4)
    note: str = ""

    def __post_init__(self):
        if isinstance(self.definition_version, bool) or not isinstance(self.definition_version, int) or self.definition_version < 1:
            raise ValueError("A versão da definição é obrigatória.")
        if not self.unit.strip():
            raise ValueError("A unidade do resultado é obrigatória.")
        for field_name in ("value", "numerator_value", "denominator_value"):
            raw = getattr(self, field_name)
            if raw is not None:
                try:
                    number = Decimal(str(raw))
                except Exception:
                    raise ValueError(f"{field_name}: valor numérico inválido.") from None
                if not number.is_finite():
                    raise ValueError(f"{field_name}: o valor precisa ser finito.")
                object.__setattr__(self, field_name, number)
        if self.denominator_value == Decimal("0"):
            raise ValueError("O denominador do indicador não pode ser zero.")
        if self.status == IndicatorValueStatus.UNAVAILABLE and self.value is not None:
            raise ValueError("Resultado indisponível não pode possuir valor numérico.")
        if self.status in {IndicatorValueStatus.CALCULATED, IndicatorValueStatus.APPROVED} and self.value is None:
            raise ValueError("Resultado calculado precisa possuir valor.")
