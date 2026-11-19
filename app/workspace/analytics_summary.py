"""Pure statistical summaries for numeric workspace columns."""
from __future__ import annotations

from statistics import mean, median
from collections.abc import Iterable, Mapping

from app.workspace.technical_filters import parse_filter_number


def summarize_numeric_columns(columns: Iterable[Mapping], records: Iterable[Mapping]) -> dict:
    """Summarize numeric columns using only the supplied (already filtered) rows."""
    rows = list(records)
    result = {}
    for column in columns:
        name = str(column["name"])
        values = [
            parse_filter_number(row.get("values", {}).get(name))
            for row in rows
        ]
        values = [value for value in values if value is not None]
        result[name] = {
            "count": len(values),
            "mean": mean(values) if values else None,
            "median": median(values) if values else None,
            "minimum": min(values) if values else None,
            "maximum": max(values) if values else None,
        }
    return result
