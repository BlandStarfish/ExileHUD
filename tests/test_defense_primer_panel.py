"""Tests for Defence & Resistance Primer data and panel logic."""

import json
import os
import pytest

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "defense_primer.json")


@pytest.fixture(scope="module")
def data():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def concepts(data):
    return data["concepts"]


# ── Data integrity ─────────────────────────────────────────────────────────────

def test_data_file_exists():
    assert os.path.exists(DATA_PATH)


def test_has_required_top_level_keys(data):
    for key in ("concepts", "categories", "tips"):
        assert key in data, f"Missing top-level key: {key}"


def test_concepts_non_empty(concepts):
    assert len(concepts) >= 8, f"Expected at least 8 concepts, got {len(concepts)}"


def test_all_concepts_have_required_fields(concepts):
    required = ("name", "category", "key_facts", "notes")
    for concept in concepts:
        for field in required:
            assert field in concept, f"Concept '{concept.get('name')}' missing field: {field}"


def test_concept_names_unique(concepts):
    names = [c["name"] for c in concepts]
    assert len(names) == len(set(names)), "Duplicate concept names found"


def test_valid_categories(concepts, data):
    valid = set(data.get("categories", []))
    for concept in concepts:
        assert concept["category"] in valid, \
            f"Concept '{concept['name']}' has invalid category: '{concept['category']}'"


def test_key_facts_non_empty(concepts):
    for concept in concepts:
        assert len(concept["key_facts"]) >= 2, \
            f"Concept '{concept['name']}' has fewer than 2 key_facts"


def test_notes_non_empty(concepts):
    for concept in concepts:
        assert concept["notes"].strip(), f"Concept '{concept['name']}' has empty notes"


def test_tips_non_empty(data):
    assert len(data.get("tips", [])) >= 3, "Expected at least 3 tips"


# ── Category coverage ──────────────────────────────────────────────────────────

def test_has_physical_defence_concepts(concepts):
    phys = [c for c in concepts if c["category"] == "Physical Defence"]
    assert len(phys) >= 2, f"Expected at least 2 Physical Defence concepts, got {len(phys)}"


def test_has_elemental_defence_concepts(concepts):
    elem = [c for c in concepts if c["category"] == "Elemental Defence"]
    assert len(elem) >= 1, "Expected at least 1 Elemental Defence concept"


def test_has_recovery_or_foundation_concepts(concepts):
    rec = [c for c in concepts if c["category"] in ("Recovery", "Foundation")]
    assert len(rec) >= 1, "Expected at least 1 Recovery or Foundation concept"


# ── Specific concepts present ──────────────────────────────────────────────────

def test_key_concepts_present(concepts):
    names = {c["name"] for c in concepts}
    expected = {"Armour", "Evasion", "Energy Shield", "Elemental Resistances",
                "Block", "Life (as Defence)"}
    for name in expected:
        assert name in names, f"Expected concept '{name}' not found"


def test_armour_formula_present(concepts):
    by_name = {c["name"]: c for c in concepts}
    armour = by_name.get("Armour")
    assert armour is not None, "Armour concept not found"
    assert "formula" in armour, "Armour concept missing formula"
    assert "Armour" in armour["formula"], "Armour formula should reference Armour"


def test_resistance_cap_mentioned(concepts):
    by_name = {c["name"]: c for c in concepts}
    res = by_name.get("Elemental Resistances")
    assert res is not None, "Elemental Resistances concept not found"
    cap_str = res.get("cap", "")
    assert "75" in cap_str, "Resistance concept should mention 75% cap"


def test_chaos_resistance_present(concepts):
    names = {c["name"] for c in concepts}
    assert "Chaos Resistance" in names, "Chaos Resistance concept not found"


def test_ehp_concept_present(concepts):
    names = {c["name"] for c in concepts}
    ehp_concepts = [n for n in names if "EHP" in n or "Effective" in n]
    assert len(ehp_concepts) >= 1, "Expected at least one EHP or Effective Hit Points concept"


# ── Search logic (data-level) ──────────────────────────────────────────────────

def _matches(concept: dict, query: str) -> bool:
    """Mirror of panel search logic for data-level testing."""
    if not query:
        return True
    key_facts_text = " ".join(concept.get("key_facts", []))
    searchable = " ".join([
        concept.get("name", ""),
        concept.get("category", ""),
        concept.get("formula", ""),
        concept.get("cap", ""),
        key_facts_text,
        concept.get("how_to_stack", ""),
        concept.get("active_skill", ""),
        concept.get("notes", ""),
    ]).lower()
    return query in searchable


def test_panel_module_importable():
    """Verify the panel module can be imported without a QApplication."""
    import importlib
    mod = importlib.import_module("ui.widgets.defense_primer_panel")
    assert hasattr(mod, "DefencePrimerPanel")


def test_search_matches_name(concepts):
    results = [c for c in concepts if _matches(c, "armour")]
    assert any(c["name"] == "Armour" for c in results)


def test_search_matches_formula(concepts):
    results = [c for c in concepts if _matches(c, "10 ×")]
    assert any(c["name"] == "Armour" for c in results)


def test_search_matches_key_fact(concepts):
    results = [c for c in concepts if _matches(c, "75%")]
    assert len(results) >= 1, "Expected at least one concept mentioning 75%"


def test_search_matches_cap(concepts):
    results = [c for c in concepts if _matches(c, "90%")]
    assert len(results) >= 1, "Expected at least one concept with a 90% cap"


def test_search_empty_returns_all(concepts):
    results = [c for c in concepts if _matches(c, "")]
    assert len(results) == len(concepts)


def test_search_no_match(concepts):
    results = [c for c in concepts if _matches(c, "xyzxyzxyz_no_match")]
    assert len(results) == 0
