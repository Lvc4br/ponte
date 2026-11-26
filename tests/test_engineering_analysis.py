import pytest

from app.workspace.analysis import (
    calculate_indicator_metrics,
    filter_analysis_records,
    parse_analysis_number,
)


@pytest.fixture
def records():
    return [
        {"id": 1, "values": {"obra": "OAE-01", "Paf_kg_m2": "10,0", "comprimento_m": 100}},
        {"id": 2, "values": {"obra": "OAE-02", "Paf_kg_m2": 20, "comprimento_m": 200}},
        {"id": 3, "values": {"obra": "OAE-03", "Paf_kg_m2": None, "comprimento_m": 300}},
        {"id": 4, "values": {"obra": "OAE-04", "Paf_kg_m2": 40, "comprimento_m": None}},
    ]


def test_parse_analysis_number_accepts_brazilian_and_international_formats():
    assert parse_analysis_number("1.234,56") == pytest.approx(1234.56)
    assert parse_analysis_number("12,5") == pytest.approx(12.5)
    assert parse_analysis_number("12.5") == pytest.approx(12.5)
    assert parse_analysis_number(None) is None
    assert parse_analysis_number("—") is None
    assert parse_analysis_number(True) is None


def test_average_ignores_missing_values_instead_of_counting_them_as_zero(records):
    result = calculate_indicator_metrics(records, [("Paf", "Paf_kg_m2", 2)])
    metric = result["Paf_kg_m2"]
    assert metric["mean"] == pytest.approx((10 + 20 + 40) / 3)
    assert metric["valid"] == 3
    assert metric["missing"] == 1


def test_filter_by_only_maximum_value(records):
    selected = filter_analysis_records(records, ranges=[("comprimento_m", None, 200)])
    assert [record["id"] for record in selected] == [1, 2]


def test_filter_by_only_minimum_value(records):
    selected = filter_analysis_records(records, ranges=[("comprimento_m", 200, None)])
    assert [record["id"] for record in selected] == [2, 3]


def test_filter_by_one_numeric_field_and_keep_average_eligible(records):
    selected = filter_analysis_records(records, ranges=[("comprimento_m", 100, None)])
    metrics = calculate_indicator_metrics(selected, [("Paf", "Paf_kg_m2", 2)])
    assert [record["id"] for record in selected] == [1, 2, 3]
    assert metrics["Paf_kg_m2"]["mean"] == pytest.approx(15)
    assert metrics["Paf_kg_m2"]["valid"] == 2
    assert metrics["Paf_kg_m2"]["missing"] == 1


def test_combines_multiple_numeric_ranges(records):
    selected = filter_analysis_records(
        records,
        ranges=[("comprimento_m", 100, 300), ("Paf_kg_m2", 15, 40)],
    )
    assert [record["id"] for record in selected] == [2]


def test_missing_numeric_value_does_not_pass_active_range(records):
    selected = filter_analysis_records(records, ranges=[("comprimento_m", 100, 300)])
    assert [record["id"] for record in selected] == [1, 2, 3]


def test_filter_by_text_and_classification(records):
    work_types = {1: "Viga biapoiada", 2: "Laje", 3: "Viga biapoiada"}
    selected = filter_analysis_records(
        records, search="oae-0", work_types=work_types, selected_type="Viga biapoiada"
    )
    assert [record["id"] for record in selected] == [1, 3]


def test_no_active_filter_returns_all_records(records):
    assert filter_analysis_records(records) == records


def test_empty_selection_has_no_average_and_zero_counts():
    result = calculate_indicator_metrics([], [("Paf", "Paf_kg_m2", 2)])
    assert result["Paf_kg_m2"] == {
        "mean": None, "valid": 0, "missing": 0, "decimals": 2
    }
