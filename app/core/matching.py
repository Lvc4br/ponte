from app.core.models import BridgeRecord, SearchCriteria
from app.core.validation import parse_range

FIELDS = {
    "width": "largura_m",
    "total_length": "compr_obra_m",
}


def match_record(record: BridgeRecord, criteria: SearchCriteria) -> bool:
    if criteria.type_obra:
        stored_type = record.get("tipo_obra")
        if stored_type is not None and str(stored_type).strip():
            if str(stored_type).strip().casefold() != criteria.type_obra.strip().casefold():
                return False

    for attr, column in FIELDS.items():
        wanted = getattr(criteria, attr)
        if wanted is None:
            continue
        stored = parse_range(record.get(column))
        # Missing historical dimensions do not silently remove a record.
        if stored is not None and not stored.overlaps(wanted):
            return False

    if criteria.span is not None:
        low = parse_range(record.get("vao_min_m"))
        high = parse_range(record.get("vao_max_m"))
        if low is not None or high is not None:
            stored = type(criteria.span)(
                low.minimum if low is not None else float("-inf"),
                high.maximum if high is not None else float("inf"),
            )
        else:
            stored = parse_range(record.get("vao_m"))
        if stored is not None and not stored.overlaps(criteria.span):
            return False

    return True


def filter_records(records, criteria):
    return [record for record in records if match_record(record, criteria)]
