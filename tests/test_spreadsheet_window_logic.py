from app.ui.spreadsheet_window import SpreadsheetWindow


def test_spreadsheet_condition_filters_text_and_numbers():
    matches = SpreadsheetWindow._matches_condition
    assert matches("Concreto", "contém", "cret")
    assert matches("Concreto", "começa com", "con")
    assert matches(12.5, "maior que", 10.0)
    assert matches(10, "menor ou igual a", 10)
    assert not matches(5, "maior que", 10)


def test_spreadsheet_condition_handles_empty_values():
    matches = SpreadsheetWindow._matches_condition
    assert matches(None, "está vazio", None)
    assert matches("preenchido", "não está vazio", None)
    assert not matches(None, "não está vazio", None)


def test_spreadsheet_value_parser_validates_column_types():
    parse = SpreadsheetWindow._parse_value
    assert parse("42", "integer") == 42
    assert parse("12,75", "decimal") == 12.75
    assert parse("SIM", "boolean") is True
    assert parse("não", "boolean") is False
    assert parse("", "text") is None
