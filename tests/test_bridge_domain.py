from decimal import Decimal
from uuid import uuid4

import pytest

from app.domain.bridges import Bridge, BridgeSpan, IssueSeverity, MaterialQuantity, validate_bridge
from app.domain.indicators import (
    IndicatorDefinition, IndicatorStatus, IndicatorValueStatus, IndicatorResult,
)


def test_bridge_accepts_multiple_spans_and_orders_them():
    bridge = Bridge(
        project_id=uuid4(), code="OAE-001", name="Ponte de demonstração",
        length_m="60", width_m="12",
        spans=(BridgeSpan(3, "20"), BridgeSpan(1, "20"), BridgeSpan(2, "20")),
    )
    assert [span.sequence for span in bridge.spans] == [1, 2, 3]
    assert sum((span.length_m for span in bridge.spans), Decimal("0")) == Decimal("60")


def test_bridge_rejects_non_positive_dimensions():
    with pytest.raises(ValueError, match="maior que zero"):
        Bridge(project_id=uuid4(), code="OAE-002", name="Ponte", width_m=0)


def test_duplicate_span_sequence_is_rejected():
    with pytest.raises(ValueError, match="não pode se repetir"):
        Bridge(
            project_id=uuid4(), code="OAE-003", name="Ponte",
            spans=(BridgeSpan(1, 10), BridgeSpan(1, 12)),
        )


def test_geometry_difference_is_a_warning_not_an_automatic_correction():
    bridge = Bridge(
        project_id=uuid4(), code="OAE-004", name="Ponte",
        length_m=60,
        spans=(BridgeSpan(1, 18), BridgeSpan(2, 18), BridgeSpan(3, 18)),
    )
    issues = validate_bridge(bridge)
    assert len(issues) == 1
    assert issues[0].severity == IssueSeverity.WARNING
    assert bridge.length_m == Decimal("60")


def test_material_quantity_requires_unit_and_scope():
    with pytest.raises(ValueError, match="escopo"):
        MaterialQuantity(
            bridge_id=uuid4(), material_code="CONCRETO", quantity=10,
            unit="m3", scope=" ",
        )


def test_legacy_indicator_can_be_registered_without_invented_formula():
    definition = IndicatorDefinition(code="Paf", name="Paf (legado)", unit="kg/m²")
    assert definition.status == IndicatorStatus.DRAFT
    assert definition.formula is None


def test_indicator_cannot_be_approved_without_complete_definition():
    with pytest.raises(ValueError, match="não pode ser aprovado"):
        IndicatorDefinition(code="Ecm", name="Ecm", unit="m³/m²", status=IndicatorStatus.APPROVED)


def test_unavailable_indicator_result_must_not_be_zero():
    with pytest.raises(ValueError, match="não pode possuir valor"):
        IndicatorResult(
            definition_id=uuid4(), definition_version=1, bridge_id=uuid4(),
            unit="kg/m²", status=IndicatorValueStatus.UNAVAILABLE, value=Decimal("0"),
        )


def test_unavailable_indicator_result_can_have_no_value():
    result = IndicatorResult(
        definition_id=uuid4(), definition_version=1, bridge_id=uuid4(),
        unit="kg/m²", status=IndicatorValueStatus.UNAVAILABLE,
    )
    assert result.value is None
