"""Technical filters for engineering records stored in the workspace.

Column names are matched by normalized aliases so imported spreadsheets keep
their original headers without losing filter compatibility.
"""
from __future__ import annotations

import math
import re
import unicodedata

from app.core.bridge_types import classification_matches


ALIASES = {
    "type_obra": ("tipo_obra", "tipo de obra", "tipo obra", "obra tipo"),
    "width": ("largura_m", "largura", "largura (m)", "width", "width_m"),
    "length": (
        "compr_obra_m", "compr_obra", "comprimento_obra_m", "comprimento total",
        "comprimento total (m)", "comprimento", "comprimento da obra m",
        "total_length", "total length",
    ),
    "span_min": ("vao_min_m", "vao minimo m", "vao minimo (m)", "span_min"),
    "span_max": ("vao_max_m", "vao maximo m", "vao maximo (m)", "span_max"),
    "span": ("vao_m", "vao", "vao (m)", "span", "span_m"),
}


def normalize_name(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value).strip().casefold())
    text = "".join(char for char in text if not unicodedata.combining(char))
    return "".join(char for char in text if char.isalnum())


def parse_filter_number(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        number = float(value)
        return number if math.isfinite(number) else None
    raw = str(value).strip().replace(" ", "")
    if not raw:
        return None
    # Accept both Brazilian (1.234,56) and international (1,234.56) notation.
    if "," in raw and "." in raw:
        if raw.rfind(",") > raw.rfind("."):
            raw = raw.replace(".", "").replace(",", ".")
        else:
            raw = raw.replace(",", "")
    elif "," in raw:
        raw = raw.replace(",", ".")
    try:
        number = float(raw)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _value(values: dict, aliases: tuple[str, ...]):
    normalized = {normalize_name(key): value for key, value in values.items()}
    for alias in aliases:
        key = normalize_name(alias)
        if key in normalized and normalized[key] not in (None, ""):
            return normalized[key]
    return None


def _within(value, minimum, maximum) -> bool:
    number = parse_filter_number(value)
    if number is not None:
        return (minimum is None or number >= minimum) and (maximum is None or number <= maximum)
    # Aceita vãos armazenados como intervalo, por exemplo: 41,25 - 41,80.
    if value is None:
        return False
    raw_numbers = re.findall(r'\d+(?:[.,]\d+)?', str(value))
    numbers = [parse_filter_number(item) for item in raw_numbers]
    numbers = [item for item in numbers if item is not None]
    if not numbers:
        return False
    low, high = min(numbers), max(numbers)
    return (maximum is None or low <= maximum) and (minimum is None or high >= minimum)


def matches_technical_filters(values: dict, criteria: dict) -> bool:
    """Return whether one row satisfies the active technical criteria."""
    requested_type = criteria.get("type_obra")
    if requested_type:
        stored_type = _value(values, ALIASES["type_obra"])
        if stored_type is None or not classification_matches(stored_type, requested_type):
            return False

    for key, aliases in (("width", ALIASES["width"]), ("length", ALIASES["length"])):
        minimum = criteria.get(f"{key}_min")
        maximum = criteria.get(f"{key}_max")
        if minimum is not None or maximum is not None:
            if not _within(_value(values, aliases), minimum, maximum):
                return False

    span_min = criteria.get("span_min")
    span_max = criteria.get("span_max")
    if span_min is not None or span_max is not None:
        stored_min = parse_filter_number(_value(values, ALIASES["span_min"]))
        stored_max = parse_filter_number(_value(values, ALIASES["span_max"]))
        if stored_min is None and stored_max is None:
            scalar = _value(values, ALIASES["span"])
            if not _within(scalar, span_min, span_max):
                return False
        else:
            if stored_min is None:
                stored_min = stored_max
            if stored_max is None:
                stored_max = stored_min
            if span_min is not None and stored_max < span_min:
                return False
            if span_max is not None and stored_min > span_max:
                return False
    return True
