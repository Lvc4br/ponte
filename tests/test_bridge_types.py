import pytest

from app.core.bridge_types import (
    classification_matches,
    identify_classifications,
    normalize_classification_text,
)


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
