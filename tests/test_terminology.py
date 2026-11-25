from app.core.terminology import (
    canonical_type,
    terminology_report,
    type_matches,
)


def test_explicit_bridge_aliases_share_canonical_type():
    assert canonical_type("Ponte Estaiada") == "ponte estaiada"
    assert canonical_type("PONTE ATIRANTADA") == "ponte estaiada"
    assert canonical_type("Cable-stayed bridge") == "ponte estaiada"


def test_accents_spacing_and_punctuation_are_normalized():
    assert type_matches("  PONTE   ESTAIADA ", "ponte-estaiada")


def test_different_structural_systems_are_not_merged():
    assert not type_matches("Ponte estaiada", "Ponte pênsil")


def test_broad_or_ambiguous_labels_are_not_auto_classified():
    assert canonical_type("Estrutura estaiada") == "estrutura estaiada"
    assert not type_matches("Estrutura estaiada", "Ponte estaiada")


def test_partial_search_remains_available_for_unmapped_terms():
    assert type_matches("Ponte estaiada", "estaiada")


def test_terminology_report_preserves_unknown_labels():
    report = terminology_report([
        "Ponte estaiada", "Ponte atirantada", "Estrutura estaiada"
    ])
    assert report["recognized"] == [{
        "canonical": "ponte estaiada",
        "variants": ["Ponte estaiada", "Ponte atirantada"],
    }]
    assert report["unrecognized"] == ["Estrutura estaiada"]


def test_legacy_search_uses_the_alias_vector():
    from app.core.matching import filter_records
    from app.core.models import BridgeRecord, SearchCriteria

    rows = [
        BridgeRecord({"tipo_obra": "Ponte estaiada"}, 1),
        BridgeRecord({"tipo_obra": "Ponte pênsil"}, 2),
    ]
    found = filter_records(rows, SearchCriteria(type_obra="Ponte atirantada"))
    assert [record.source_row for record in found] == [1]


def test_workspace_filter_uses_the_same_alias_vector():
    from app.workspace.technical_filters import matches_technical_filters

    assert matches_technical_filters(
        {"Tipo de Obra": "Ponte estaiada"},
        {"type_obra": "Ponte atirantada"},
    )
    assert not matches_technical_filters(
        {"Tipo de Obra": "Ponte pênsil"},
        {"type_obra": "Ponte estaiada"},
    )
