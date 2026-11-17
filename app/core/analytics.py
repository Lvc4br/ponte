from statistics import mean, median

from app.core.validation import parse_number


# Keep source column names visible. Do not infer meanings that are not documented.
RATE_FIELDS = (
    "em_m3_m2",
    "Paf_kg_m2",
    "Pap_kg_m2",
    "Af_m2_m2",
)


def summarize_rates(records):
    """Summarize available scalar values per source column, without imputing data."""
    summaries = {}
    for field in RATE_FIELDS:
        values = []
        for record in records:
            value = parse_number(record.get(field))
            if value is not None:
                values.append(value)
        if values:
            summaries[field] = {
                "count": len(values),
                "mean": mean(values),
                "median": median(values),
                "minimum": min(values),
                "maximum": max(values),
            }
        else:
            summaries[field] = {
                "count": 0,
                "mean": None,
                "median": None,
                "minimum": None,
                "maximum": None,
            }
    return summaries
