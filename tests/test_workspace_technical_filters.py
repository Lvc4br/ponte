import pytest

from app.workspace.technical_filters import (
    matches_technical_filters,
    parse_filter_number,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("12,5", 12.5), ("1.234,56", 1234.56), ("1,234.56", 1234.56), (12, 12.0)],
)
def test_parse_filter_number_accepts_common_formats(raw, expected):
    assert parse_filter_number(raw) == expected


def test_filters_match_headers_with_accents_and_units():
    row = {"Tipo de Obra": "Ponte rodoviária", "Largura (m)": "12,5",
           "Vão mínimo (m)": 20, "Vão máximo (m)": 35,
           "Comprimento total (m)": "120,0"}
    criteria = {"type_obra": "ponte", "width_min": 12, "width_max": 13,
                "span_min": 30, "span_max": 40, "length_min": 100}
    assert matches_technical_filters(row, criteria)


def test_span_filter_uses_overlap_for_stored_interval():
    row = {"vao_min_m": 20, "vao_max_m": 35}
    assert matches_technical_filters(row, {"span_min": 30, "span_max": 40})
    assert not matches_technical_filters(row, {"span_min": 36})


def test_scalar_span_filter_works_without_interval_columns():
    assert matches_technical_filters({"Vão (m)": "32,5"}, {"span_min": 30, "span_max": 35})
    assert not matches_technical_filters({"Vão (m)": "32,5"}, {"span_min": 33})


def test_missing_values_do_not_match_active_numeric_filter():
    assert not matches_technical_filters({"largura": None}, {"width_min": 1})
    assert matches_technical_filters({"largura": None}, {})
