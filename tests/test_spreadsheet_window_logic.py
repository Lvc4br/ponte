from app.workspace.spreadsheet import matches_condition, parse_cell_value


def test_spreadsheet_condition_filters_text_and_numbers():
    assert matches_condition("Concreto", "contém", "cret")
    assert matches_condition("Concreto", "começa com", "con")
    assert matches_condition(12.5, "maior que", 10.0)
    assert matches_condition(10, "menor ou igual a", 10)
    assert not matches_condition(5, "maior que", 10)


def test_spreadsheet_condition_handles_empty_values():
    assert matches_condition(None, "está vazio", None)
    assert matches_condition("preenchido", "não está vazio", None)
    assert not matches_condition(None, "não está vazio", None)


def test_spreadsheet_value_parser_validates_column_types():
    assert parse_cell_value("42", "integer") == 42
    assert parse_cell_value("12,75", "decimal") == 12.75
    assert parse_cell_value("SIM", "boolean") is True
    assert parse_cell_value("não", "boolean") is False
    assert parse_cell_value("", "text") is None
