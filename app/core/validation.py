from math import isfinite

from app.core.models import NumericRange


def parse_number(value):
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(" ", "")
    if not text or text.lower() in {"nan", "none", "n/a", "-"}:
        return None
    if "," in text and "." not in text:
        text = text.replace(",", ".")
    elif "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return None


def parse_input_number(value, field_name):
    """Parse a user-entered measurement, distinguishing blank from invalid."""
    if value is None or not str(value).strip():
        return None
    number = parse_number(value)
    if number is None or not isfinite(number):
        raise ValueError(
            f"{field_name}: informe um número válido (ex.: 12,5) ou deixe o campo vazio."
        )
    return number


def parse_range(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return NumericRange(float(value), float(value))
    text = str(value).strip().replace("–", "-").replace("—", "-")
    parts = [part.strip() for part in text.split("-")]
    if len(parts) == 2:
        first, second = parse_number(parts[0]), parse_number(parts[1])
        if first is not None and second is not None:
            return NumericRange(min(first, second), max(first, second))
    number = parse_number(text)
    return NumericRange(number, number) if number is not None else None
