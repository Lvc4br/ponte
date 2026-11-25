"""Canonical technical terminology and explicit aliases for structure types.

Original spreadsheet values are never modified. Canonical names are used only
for comparisons and grouping; uncertain labels remain distinct.
"""
from __future__ import annotations

import re
import unicodedata


def normalize_term(value: object) -> str:
    """Normalize accents, case, punctuation and whitespace for comparison."""
    text = unicodedata.normalize("NFKD", str(value or "").strip().casefold())
    text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


# Each vector contains only terms explicitly approved as equivalent.
# Do not add broad labels such as "estrutura estaiada": they may describe
# components or systems other than a complete cable-stayed bridge.
TYPE_TERMINOLOGY = {
    "ponte estaiada": (
        "ponte estaiada",
        "pontes estaiadas",
        "ponte atirantada",
        "pontes atirantadas",
        "ponte com estais",
        "ponte de estais",
        "cable stayed bridge",
        "cable stayed bridges",
    ),
}


def _alias_index() -> dict[str, str]:
    return {
        normalize_term(alias): canonical
        for canonical, aliases in TYPE_TERMINOLOGY.items()
        for alias in aliases
    }


_TYPE_ALIAS_INDEX = _alias_index()


def canonical_type(value: object) -> str:
    """Return the canonical category for known aliases; keep unknowns distinct."""
    normalized = normalize_term(value)
    return _TYPE_ALIAS_INDEX.get(normalized, normalized)


def type_matches(stored_value: object, requested_value: object) -> bool:
    """Compare known synonyms safely, with normalized partial search fallback."""
    stored = normalize_term(stored_value)
    requested = normalize_term(requested_value)
    if not stored or not requested:
        return False

    stored_canonical = _TYPE_ALIAS_INDEX.get(stored)
    requested_canonical = _TYPE_ALIAS_INDEX.get(requested)
    if stored_canonical and requested_canonical:
        return stored_canonical == requested_canonical

    # Keep the existing useful search behavior for partial labels, but do not
    # infer equivalence between two different, fully specified known classes.
    if stored_canonical and requested == stored_canonical:
        return True
    if requested_canonical and stored == requested_canonical:
        return True
    return requested in stored or stored in requested


def terminology_report(values) -> dict:
    """Group known aliases and list unknown labels without guessing their class."""
    groups: dict[str, dict] = {}
    unknown: set[str] = set()
    for value in values:
        if value is None or not str(value).strip():
            continue
        original = str(value).strip()
        normalized = normalize_term(original)
        canonical = _TYPE_ALIAS_INDEX.get(normalized)
        if canonical is None:
            unknown.add(original)
            continue
        group = groups.setdefault(canonical, {"canonical": canonical, "variants": []})
        if original not in group["variants"]:
            group["variants"].append(original)
    return {
        "recognized": list(groups.values()),
        "unrecognized": sorted(unknown, key=str.casefold),
    }
