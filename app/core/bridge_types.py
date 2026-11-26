"""Engineering terminology for bridge structural systems and construction methods.

The original spreadsheet text is never modified. This catalog only provides
conservative, traceable recognition of known engineering expressions.
"""
from __future__ import annotations

import re
import unicodedata


# Keys are stable identifiers; canonical labels are presentation values.
# Do not merge section configuration with construction methods.
ENGINEERING_CLASSIFICATIONS = {
    "structural_system": {
        "grelha": {
            "canonical": "Grelha",
            "aliases": (
                "grelha",
                "sistema em grelha",
                "sistema estrutural em grelha",
                "estrutura em grelha",
                "grelha de vigas",
            ),
        },
        "viga_biapoiada": {
            "canonical": "Viga biapoiada",
            "aliases": (
                "viga biapoiada",
                "vigas biapoiadas",
                "viga simplesmente apoiada",
                "vigas simplesmente apoiadas",
                "simplesmente apoiada",
                "simply supported beam",
            ),
        },
        "viga_continua": {
            "canonical": "Viga contínua",
            "aliases": (
                "viga contínua",
                "vigas contínuas",
                "sistema de vigas contínuas",
                "continuous beam",
            ),
        },
        "laje": {
            "canonical": "Laje",
            "aliases": (
                "laje",
                "ponte em laje",
                "tabuleiro em laje",
                "laje maciça",
                "laje nervurada",
                "slab bridge",
            ),
        },
        "estaiada": {
            "canonical": "Estaiada",
            "aliases": (
                "estaiada",
                "estaiado",
                "ponte estaiada",
                "pontes estaiadas",
                "ponte atirantada",
                "pontes atirantadas",
                "estrutura estaiada",
                "ponte com estais",
                "ponte de estais",
                "cable stayed",
                "cable-stayed bridge",
            ),
        },
    },
    "section_configuration": {
        "secao_caixao": {
            "canonical": "Seção caixão",
            "aliases": (
                "caixão",
                "caixao",
                "seção caixão",
                "seção em caixão",
                "viga caixão",
                "viga-caixão",
                "seção tipo caixão",
                "box girder",
                "box-girder",
            ),
        },
        "secao_celular": {
            "canonical": "Seção celular",
            "aliases": (
                "seção celular",
                "seção em células",
                "seção unicelular",
                "seção multicelular",
                "seção monocelular",
                "cellular section",
            ),
        },
    },
    "construction_method": {
        "consolos_sucessivos": {
            "canonical": "Consolos sucessivos",
            "aliases": (
                "consolos sucessivos",
                "construção por consolos sucessivos",
                "construída por consolos sucessivos",
                "balanços sucessivos",
                "construção por balanços sucessivos",
                "construída por balanços sucessivos",
                "método dos balanços sucessivos",
                "avanço por aduelas",
                "cantilever construction",
            ),
        },
    },
}


def normalize_classification_text(value: object) -> str:
    """Normalize text for comparison without changing the imported source."""
    text = unicodedata.normalize("NFKD", str(value or "").casefold())
    text = "".join(char for char in text if not unicodedata.combining(char))
    return " ".join(re.findall(r"[a-z0-9]+", text))


def _contains_phrase(text: str, phrase: str) -> bool:
    """Match complete normalized tokens, never arbitrary substrings."""
    return bool(text and phrase and f" {phrase} " in f" {text} ")


def identify_classifications(value: object) -> list[dict[str, str]]:
    """Return every recognized classification with its dimension and alias."""
    normalized = normalize_classification_text(value)
    if not normalized:
        return []

    found = []
    for dimension, entries in ENGINEERING_CLASSIFICATIONS.items():
        for key, definition in entries.items():
            for alias in definition["aliases"]:
                normalized_alias = normalize_classification_text(alias)
                if _contains_phrase(normalized, normalized_alias):
                    found.append({
                        "dimension": dimension,
                        "key": key,
                        "canonical": definition["canonical"],
                        "matched_alias": alias,
                    })
                    break
    return found


def classification_matches(actual: object, requested: object) -> bool:
    """Compare a requested type with source text using known aliases safely.

    If both sides resolve to catalog entries, their stable keys must intersect.
    Otherwise, use complete-token phrase matching for generic/legacy values
    such as 'Ponte' and 'Ponte rodoviária'.
    """
    actual_text = normalize_classification_text(actual)
    requested_text = normalize_classification_text(requested)
    if not actual_text or not requested_text:
        return False

    actual_matches = identify_classifications(actual)
    requested_matches = identify_classifications(requested)

    actual_keys = {item["key"] for item in actual_matches}
    requested_keys = {item["key"] for item in requested_matches}
    if actual_keys and requested_keys:
        return bool(actual_keys & requested_keys)

    return _contains_phrase(actual_text, requested_text)
