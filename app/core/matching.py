from app.core.models import BridgeRecord, SearchCriteria
from app.core.validation import parse_range

FIELDS = {'width':'largura_m', 'span':'vao_m', 'total_length':'compr_obra_m'}

def match_record(record: BridgeRecord, criteria: SearchCriteria) -> bool:
    for attr, column in FIELDS.items():
        wanted = getattr(criteria, attr)
        if wanted is None: continue
        stored = parse_range(record.get(column))
        # Mantém registros históricos com dimensão não informada.
        if stored is not None and not stored.overlaps(wanted): return False
    return True

def filter_records(records, criteria):
    return [r for r in records if match_record(r, criteria)]
