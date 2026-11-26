import pytest

from app.core.bridge_types import (
    classification_matches,
    identify_classifications,
    normalize_classification_text,
)
from app.core.matching import filter_records
from app.core.models import BridgeRecord, SearchCriteria
from app.workspace.technical_filters import matches_technical_filters


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("GRELHA", "Grelha"),
        ("VIGA BIAPOIADA", "Viga biapoiada"),
        ("viga simplesmente apoiada", "Viga biapoiada"),
        ("Vigas contínuas", "Viga contínua"),
        ("PONTE EM LAJE MACIÇA", "Laje"),
        ("viga-caixão", "Seção caixão"),
        ("seção multicelular", "Seção celular"),
        ("Ponte atirantada", "Estaiada"),
        ("construção por balanços sucessivos", "Consolos sucessivos"),
    ],
)
def test_identifies_engineering_variations(raw, expected):
    matches = identify_classifications(raw)
    assert expected in {item["canonical"] for item in matches}


def test_normalization_ignores_accents_case_and_punctuation():
    assert normalize_classification_text("  SEÇÃO-CELULAR ") == "secao celular"


@pytest.mark.parametrize(
    ("actual", "requested"),
    [
        ("Ponte em concreto protendido, seção celular", "seção celular"),
        ("Viga-caixão de concreto", "caixão"),
        ("Ponte atirantada", "Estaiada"),
        ("Ponte rodoviária", "ponte"),
        ("Ponte em arco", "Ponte"),
        ("Viga simplesmente apoiada", "Viga biapoiada"),
    ],
)
def test_classification_match_accepts_known_aliases(actual, requested):
    assert classification_matches(actual, requested)


@pytest.mark.parametrize(
    ("actual", "requested"),
    [
        ("Viga biapoiada", "Viga contínua"),
        ("Ponte estaiada", "Ponte pênsil"),
        ("Viga biapoiada", "biapoiadismo"),
        ("Seção celular", "Seção caixão"),
    ],
)
def test_classification_match_rejects_false_or_unverified_equivalence(actual, requested):
    assert not classification_matches(actual, requested)


def test_identifies_multiple_independent_dimensions_in_one_cell():
    matches = identify_classifications(
        "Ponte estaiada com seção celular, executada por balanços sucessivos"
    )
    found = {(item["dimension"], item["canonical"]) for item in matches}
    assert ("structural_system", "Estaiada") in found
    assert ("section_configuration", "Seção celular") in found
    assert ("construction_method", "Consolos sucessivos") in found


def test_core_record_filter_uses_engineering_aliases():
    rows = [
        BridgeRecord({"tipo_obra": "Ponte atirantada"}, 1),
        BridgeRecord({"tipo_obra": "Viga biapoiada"}, 2),
    ]
    result = filter_records(rows, SearchCriteria(type_obra="Estaiada"))
    assert [record.source_row for record in result] == [1]


def test_workspace_filter_uses_engineering_aliases():
    assert matches_technical_filters(
        {"Tipo de obra": "Ponte construída por balanços sucessivos"},
        {"type_obra": "Consolos sucessivos"},
    )
