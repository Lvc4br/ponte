from app.core.models import BridgeRecord, NumericRange, SearchCriteria
from app.core.matching import filter_records


def test_overlap_range():
    rows = [
        BridgeRecord(
            {"largura_m": "12,0", "vao_m": "41,25 - 41,80", "compr_obra_m": 80},
            1,
        ),
        BridgeRecord(
            {"largura_m": "8,0", "vao_m": 20, "compr_obra_m": 30},
            2,
        ),
    ]
    result = filter_records(
        rows,
        SearchCriteria(width=NumericRange(10, 14), span=NumericRange(41, 42)),
    )
    assert len(result) == 1
    assert result[0].source_row == 1


def test_missing_value_kept():
    row = BridgeRecord({"largura_m": None}, 1)
    assert filter_records([row], SearchCriteria(width=NumericRange(5, 10))) == [row]


def test_type_filter_is_case_insensitive():
    rows = [
        BridgeRecord({"tipo_obra": "Ponte"}, 1),
        BridgeRecord({"tipo_obra": "Viaduto"}, 2),
    ]
    result = filter_records(rows, SearchCriteria(type_obra="ponte"))
    assert [record.source_row for record in result] == [1]


def test_missing_type_is_preserved_when_filtering():
    rows = [
        BridgeRecord({"tipo_obra": None}, 1),
        BridgeRecord({"tipo_obra": "Ponte"}, 2),
    ]
    result = filter_records(rows, SearchCriteria(type_obra="Ponte"))
    assert [record.source_row for record in result] == [1, 2]

def test_search_by_total_length_only():
    rows = [
        BridgeRecord(
            {"largura_m": 10, "vao_m": 20, "compr_obra_m": 100},
            1,
        ),
        BridgeRecord(
            {"largura_m": 30, "vao_m": 50, "compr_obra_m": 150},
            2,
        ),
        BridgeRecord(
            {"largura_m": None, "vao_m": None, "compr_obra_m": 120},
            3,
        ),
        BridgeRecord(
            {"largura_m": 10, "vao_m": 20, "compr_obra_m": 200},
            4,
        ),
    ]
    result = filter_records(
        rows,
        SearchCriteria(total_length=NumericRange(90, 160)),
    )
    assert [record.source_row for record in result] == [1, 2, 3]


def test_search_by_total_length_minimum_only():
    rows = [
        BridgeRecord({"compr_obra_m": 79}, 1),
        BridgeRecord({"compr_obra_m": 80}, 2),
        BridgeRecord({"compr_obra_m": 120}, 3),
        BridgeRecord({"compr_obra_m": None}, 4),
    ]
    result = filter_records(
        rows,
        SearchCriteria(total_length=NumericRange(80, float("inf"))),
    )
    assert [record.source_row for record in result] == [2, 3, 4]


def test_search_by_total_length_maximum_only():
    rows = [
        BridgeRecord({"compr_obra_m": 79}, 1),
        BridgeRecord({"compr_obra_m": 80}, 2),
        BridgeRecord({"compr_obra_m": 120}, 3),
        BridgeRecord({"compr_obra_m": None}, 4),
    ]
    result = filter_records(
        rows,
        SearchCriteria(total_length=NumericRange(float("-inf"), 80)),
    )
    assert [record.source_row for record in result] == [1, 2, 4]

