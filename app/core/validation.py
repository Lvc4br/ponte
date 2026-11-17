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
    # Brazilian notation (1.234,56) and decimal point (1234.56).
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    elif "," in text:
        text = text.replace(",", ".")
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


def format_display_value(value):
    """Display scalar decimal values with a comma without changing stored data."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return format(value, ".15g").replace(".", ",")

    original = str(value)
    text = original.strip()
    if not text or ("," not in text and "." not in text):
        return original
    # Preserve source intervals and formulas exactly as supplied.
    if "-" in text or "+" in text:
        return original
    number = parse_number(text)
    if number is None or not isfinite(number):
        return original
    separator = "," if "," in text else "."
    decimals = len(text.rsplit(separator, 1)[-1])
    if decimals == 0:
        return original
    return f"{number:.{decimals}f}".replace(".", ",")


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
