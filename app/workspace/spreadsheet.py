"""Pure helpers shared by the spreadsheet UI and its tests."""


def parse_cell_value(raw, data_type):
    """Convert an edited cell string into the value expected by WorkspaceStore."""
    import json

    if raw == "":
        return None
    if data_type == "text":
        return raw
    if data_type == "integer":
        return int(raw)
    if data_type == "decimal":
        return float(raw.replace(",", "."))
    if data_type == "boolean":
        normalized = raw.strip().casefold()
        if normalized in {"true", "1", "sim", "yes"}:
            return True
        if normalized in {"false", "0", "não", "nao", "no"}:
            return False
        raise ValueError("Use sim/não ou verdadeiro/falso.")
    if data_type == "json":
        return json.loads(raw)
    return raw


def matches_condition(value, operator, target):
    """Evaluate a typed column filter condition."""
    if value is None:
        return operator == "está vazio"
    if operator == "não está vazio":
        return True
    if operator == "contém":
        return str(target).casefold() in str(value).casefold()
    if operator == "começa com":
        return str(value).casefold().startswith(str(target).casefold())
    if operator == "igual a":
        return value == target
    if operator == "diferente de":
        return value != target
    if operator == "maior que":
        return value > target
    if operator == "maior ou igual a":
        return value >= target
    if operator == "menor que":
        return value < target
    if operator == "menor ou igual a":
        return value <= target
    return False
