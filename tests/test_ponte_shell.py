from app.ui.ponte_shell import PonteMainWindow


def test_bridge_span_text_missing_values():
    assert PonteMainWindow._bridge_span_text({}) == "Não informado"


def test_bridge_span_text_single_span_value():
    assert PonteMainWindow._bridge_span_text({"vao_min_m": 24.0}) == "24.0"


def test_bridge_span_text_range():
    assert PonteMainWindow._bridge_span_text(
        {"vao_min_m": 24.0, "vao_max_m": 36.0}
    ) == "24.0 – 36.0"


def test_bridge_span_text_accepts_legacy_accented_columns():
    assert PonteMainWindow._bridge_span_text(
        {"vão_min_m": 24.0, "vão_max_m": 36.0}
    ) == "24.0 – 36.0"
