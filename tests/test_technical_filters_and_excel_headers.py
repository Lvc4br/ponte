from app.workspace.exchange import SpreadsheetExchange
from app.workspace.technical_filters import matches_technical_filters


def test_detect_header_row_below_grouped_titles():
    rows = [
        [None, None, "Dados Geométricos", None, "Taxas", None],
        ["obra", "data", "largura_m", "vão_m", "compr_obra_m", "em_m3_m2"],
        [1, None, 12.4, 20, 20, 0.544],
    ]
    assert SpreadsheetExchange._detect_header_row(rows) == 1


def test_detect_header_row_keeps_first_row_when_already_complete():
    rows = [
        ["obra", "largura_m", "vão_m", "compr_obra_m"],
        [1, 12.4, 20, 20],
        [2, 10.56, 24.8, 32.3],
    ]
    assert SpreadsheetExchange._detect_header_row(rows) == 0


def test_width_filter_matches_imported_alias():
    assert matches_technical_filters(
        {"largura_m": 12.4}, {"width_min": 12, "width_max": 13}
    )


def test_length_filter_matches_compr_obra_m():
    assert matches_technical_filters(
        {"compr_obra_m": 32.3}, {"length_min": 30, "length_max": 33}
    )


def test_span_filter_matches_decimal_comma_interval():
    assert matches_technical_filters(
        {"vão_m": "41,25 - 41,80"}, {"span_min": 41.5, "span_max": 42}
    )


def test_span_filter_rejects_non_overlapping_interval():
    assert not matches_technical_filters(
        {"vão_m": "41,25 - 41,80"}, {"span_min": 42, "span_max": 43}
    )


def test_type_filter_accepts_obra_column_as_fallback():
    assert matches_technical_filters({"obra": "Ponte estaiada"}, {"type_obra": "estaiada"})
