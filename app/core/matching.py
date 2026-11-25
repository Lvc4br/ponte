from app.core.models import BridgeRecord, SearchCriteria
from app.core.validation import parse_range
from app.core.terminology import type_matches

FIELDS = {
    "width": "largura_m",
    "total_length": "compr_obra_m",
}


def _stored_span(record, criteria_span):
    low = parse_range(record.get("vao_min_m"))
    high = parse_range(record.get("vao_max_m"))
    if low is not None or high is not None:
        return type(criteria_span)(
            low.minimum if low is not None else float("-inf"),
            high.maximum if high is not None else float("inf"),
        )
    return parse_range(record.get("vao_m"))


def missing_criteria_fields(record: BridgeRecord, criteria: SearchCriteria):
    """Return the active filters that cannot be checked due to missing source data."""
    missing = []
    if criteria.type_obra and not str(record.get("tipo_obra") or "").strip():
        missing.append("tipo_obra")

    for attr, column in FIELDS.items():
        if getattr(criteria, attr) is not None and parse_range(record.get(column)) is None:
            missing.append(column)

    if criteria.span is not None:
        low = parse_range(record.get("vao_min_m"))
        high = parse_range(record.get("vao_max_m"))
        scalar_span = parse_range(record.get("vao_m"))
        if low is None and high is None and scalar_span is None:
            missing.append("vao_m")
        elif (low is None) != (high is None):
            missing.append("intervalo_vão_parcial")

    return missing


def match_record(record: BridgeRecord, criteria: SearchCriteria) -> bool:
    if criteria.type_obra:
        stored_type = record.get("tipo_obra")
        if stored_type is None or not str(stored_type).strip():
            return False
        if not type_matches(stored_type, criteria.type_obra):
            return False

    for attr, column in FIELDS.items():
        wanted = getattr(criteria, attr)
        if wanted is None:
            continue
        stored = parse_range(record.get(column))
        # Keep incomplete historical records, but identify them in the UI.
        if stored is None or not stored.overlaps(wanted):
            return False

    if criteria.span is not None:
        stored = _stored_span(record, criteria.span)
        if stored is None or not stored.overlaps(criteria.span):
            return False

    return True


def filter_records(records, criteria):
    return [record for record in records if match_record(record, criteria)]
