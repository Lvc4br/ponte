"""Pure helpers for engineering analysis filters and descriptive indicators.

These functions intentionally do not depend on Qt so the calculation rules can be
verified independently from the desktop interface.
"""
from __future__ import annotations


def parse_analysis_number(value):
    """Parse stored numeric values, accepting Brazilian decimal notation."""
    if value is None or isinstance(value, bool) or str(value).strip() in ("", "—", "-"):
        return None
    raw = str(value).strip().replace(" ", "")
    try:
        if "," in raw and "." in raw:
            raw = raw.replace(".", "").replace(",", ".")
        else:
            raw = raw.replace(",", ".")
        return float(raw)
    except (TypeError, ValueError):
        return None


def filter_analysis_records(records, ranges=(), search="", work_types=None, selected_type=None):
    """Apply all active numeric ranges, text search and optional OAE classification.

    Each range is (field_name, minimum, maximum); either bound may be None.
    Missing/non-numeric values do not match an active range.
    """
    work_types = work_types or {}
    needle = str(search or "").strip().casefold()
    selected = []
    for record in records:
        values = record.get("values") or {}
        keep = True
        for field_name, minimum, maximum in ranges:
            number = parse_analysis_number(values.get(field_name))
            if number is None:
                keep = False
                break
            if minimum is not None and number < minimum:
                keep = False
                break
            if maximum is not None and number > maximum:
                keep = False
                break
        if keep and needle:
            haystack = " ".join(str(value) for value in values.values() if value is not None)
            keep = needle in haystack.casefold()
        if keep and selected_type:
            keep = work_types.get(record.get("id")) == selected_type
        if keep:
            selected.append(record)
    return selected


def calculate_indicator_metrics(records, definitions):
    """Return mean, valid count and missing count for each (label, field, decimals)."""
    results = {}
    total = len(records)
    for label, field_name, decimals in definitions:
        valid = [
            number for record in records
            if (number := parse_analysis_number((record.get("values") or {}).get(field_name))) is not None
        ]
        results[field_name] = {
            "mean": sum(valid) / len(valid) if valid else None,
            "valid": len(valid),
            "missing": total - len(valid),
            "decimals": decimals,
        }
    return results
