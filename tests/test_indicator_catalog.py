from app.domain.indicator_catalog import legacy_indicator_catalog
from app.domain.indicators import IndicatorStatus


def test_legacy_catalog_preserves_codes_units_and_pending_status():
    definitions = {item.code: item for item in legacy_indicator_catalog()}
    assert set(definitions) == {"Paf", "Pap", "Ecm", "Af", "ACO_TOTAL_KG_M2", "ACO_TOTAL_KG_M3"}
    assert definitions["Paf"].unit == "kg/m²"
    assert definitions["Pap"].unit == "kg/m²"
    assert definitions["Ecm"].unit == "m³/m²"
    assert definitions["Af"].unit == "m²/m²"
    assert all(item.status == IndicatorStatus.DRAFT for item in definitions.values())
    assert all(item.formula is None for item in definitions.values())
