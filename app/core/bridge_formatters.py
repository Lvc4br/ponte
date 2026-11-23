"""Pure formatting helpers for legacy bridge records."""


def bridge_span_text(values: dict) -> str:
    """Format legacy minimum/maximum span fields without changing source values."""
    minimum = values.get("vao_min_m", values.get("vão_min_m"))
    maximum = values.get("vao_max_m", values.get("vão_max_m"))
    if minimum is None and maximum is None:
        return "Não informado"
    if minimum is None:
        return str(maximum)
    if maximum is None or maximum == minimum:
        return str(minimum)
    return f"{minimum} – {maximum}"
