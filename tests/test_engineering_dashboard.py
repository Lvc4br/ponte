from app.workspace.analytics_summary import summarize_numeric_columns


def test_numeric_summary_uses_only_supplied_filtered_records():
    columns = [{"name": "largura", "data_type": "decimal"}]
    records = [
        {"values": {"largura": "10"}},
        {"values": {"largura": "12,5"}},
        {"values": {"largura": None}},
        {"values": {"largura": "texto"}},
    ]

    result = summarize_numeric_columns(columns, records)["largura"]

    assert result == {
        "count": 2,
        "mean": 11.25,
        "median": 11.25,
        "minimum": 10.0,
        "maximum": 12.5,
    }


def test_numeric_summary_returns_empty_statistics_when_no_valid_values():
    result = summarize_numeric_columns(
        [{"name": "vão", "data_type": "decimal"}],
        [{"values": {"vão": "41,25 - 41,80"}}],
    )["vão"]

    assert result == {
        "count": 0,
        "mean": None,
        "median": None,
        "minimum": None,
        "maximum": None,
    }
