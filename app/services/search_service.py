from app.core.matching import filter_records
class SearchService:
    def search(self, records, criteria): return filter_records(records, criteria)
