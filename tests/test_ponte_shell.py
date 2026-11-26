from app.core.bridge_formatters import bridge_span_text


def test_bridge_span_text_missing_values():
    assert bridge_span_text({}) == "Não informado"


def test_bridge_span_text_single_span_value():
    assert bridge_span_text({"vao_min_m": 24.0}) == "24.0"


def test_bridge_span_text_range():
    assert bridge_span_text(
        {"vao_min_m": 24.0, "vao_max_m": 36.0}
    ) == "24.0 – 36.0"


def test_bridge_span_text_accepts_legacy_accented_columns():
    assert bridge_span_text(
        {"vão_min_m": 24.0, "vão_max_m": 36.0}
    ) == "24.0 – 36.0"



def test_invalid_analysis_filter_clears_exportable_records():
    from types import SimpleNamespace

    from app.ui.ponte_shell import PonteMainWindow

    calls = []
    table = SimpleNamespace(setRowCount=lambda count: calls.append(("rows", count)))
    label = SimpleNamespace(setText=lambda value: calls.append(("count", value)))
    window = SimpleNamespace(
        analysis_filtered_records=[{"id": 1}],
        analysis_table=table,
        analysis_count=label,
        analysis_results_count=label,
        analysis_total_label=label,
        _update_analysis_indicators=lambda records: calls.append(("indicators", records)),
        _refresh_report_fields=lambda: calls.append(("report", None)),
    )

    PonteMainWindow._invalidate_analysis_filter(window, "Limite inválido")

    assert window.analysis_filtered_records == []
    assert ("rows", 0) in calls
    assert ("indicators", []) in calls
    assert ("report", None) in calls
    assert ("count", "OBRAS NO RECORTE: 0") in calls
    assert ("count", "Limite inválido") in calls
