from app.core.analytics import summarize_rates
from app.core.models import BridgeRecord


def test_rate_summary_uses_available_values_and_preserves_missing():
    records = [
        BridgeRecord({"em_m3_m2": "0,40", "Paf_kg_m2": "100"}, 1),
        BridgeRecord({"em_m3_m2": "0.60", "Paf_kg_m2": None}, 2),
        BridgeRecord({"em_m3_m2": None, "Paf_kg_m2": "200"}, 3),
        BridgeRecord({"em_m3_m2": "texto", "Paf_kg_m2": "intervalo"}, 4),
    ]
    result = summarize_rates(records)
    assert result["em_m3_m2"]["count"] == 2
    assert result["em_m3_m2"]["mean"] == 0.5
    assert result["em_m3_m2"]["median"] == 0.5
    assert result["Paf_kg_m2"]["count"] == 2
    assert result["Paf_kg_m2"]["mean"] == 150
    assert result["Pap_kg_m2"]["count"] == 0
    assert result["Pap_kg_m2"]["mean"] is None


def test_rate_summary_does_not_mutate_source_records():
    row = BridgeRecord({"em_m3_m2": "0.45"}, 1)
    summarize_rates([row])
    assert row.get("em_m3_m2") == "0.45"
