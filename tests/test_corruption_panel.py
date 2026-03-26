"""Tests for Item Corruption Reference data and panel logic."""

import json
import os
import pytest

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "corruption_reference.json")


@pytest.fixture(scope="module")
def data():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def outcomes(data):
    return data["outcomes"]


@pytest.fixture(scope="module")
def implicits(data):
    return data["notable_implicits"]


# ── Data integrity ─────────────────────────────────────────────────────────────

def test_data_file_exists():
    assert os.path.exists(DATA_PATH)


def test_has_required_top_level_keys(data):
    for key in ("outcomes", "notable_implicits", "how_it_works", "double_corruption", "tips"):
        assert key in data, f"Missing top-level key: {key}"


def test_outcomes_non_empty(outcomes):
    assert len(outcomes) >= 5, "Expected at least 5 outcome entries"


def test_implicits_non_empty(implicits):
    assert len(implicits) >= 3, "Expected at least 3 notable implicits"


def test_all_outcomes_have_required_fields(outcomes):
    for entry in outcomes:
        assert "item_type" in entry, f"Outcome entry missing 'item_type'"
        assert "outcomes" in entry, f"Entry '{entry.get('item_type')}' missing 'outcomes' list"
        assert isinstance(entry["outcomes"], list) and len(entry["outcomes"]) > 0, \
            f"Entry '{entry['item_type']}' has empty outcomes list"


def test_all_outcome_rows_have_result(outcomes):
    for entry in outcomes:
        for o in entry["outcomes"]:
            assert "result" in o and o["result"].strip(), \
                f"Outcome in '{entry['item_type']}' has empty result"


def test_valid_probabilities(outcomes):
    valid_probs = {"Always", "High", "Medium", "Low"}
    for entry in outcomes:
        for o in entry["outcomes"]:
            if "probability" in o:
                assert o["probability"] in valid_probs, \
                    f"Invalid probability '{o['probability']}' in '{entry['item_type']}'"


def test_item_type_names_unique(outcomes):
    names = [e["item_type"] for e in outcomes]
    assert len(names) == len(set(names)), "Duplicate item_type entries found"


def test_all_implicits_have_required_fields(implicits):
    for imp in implicits:
        for key in ("implicit", "source", "value", "notes"):
            assert key in imp, f"Implicit missing field: {key}"


def test_all_implicit_values_valid(implicits):
    valid_values = {"Very High", "High", "Medium", "Low"}
    for imp in implicits:
        assert imp["value"] in valid_values, \
            f"Implicit '{imp['implicit'][:30]}' has invalid value: {imp['value']}"


def test_tips_non_empty(data):
    assert len(data["tips"]) >= 3, "Expected at least 3 tips"


# ── Spot checks ────────────────────────────────────────────────────────────────

def test_skill_gem_outcomes_exist(outcomes):
    types = {e["item_type"] for e in outcomes}
    assert any("Gem" in t for t in types), "No Skill Gem entry found"


def test_map_outcomes_exist(outcomes):
    types = {e["item_type"] for e in outcomes}
    assert any("Map" in t for t in types), "No Map entry found"


def test_equipment_outcomes_exist(outcomes):
    types = {e["item_type"] for e in outcomes}
    assert any("Equipment" in t or "Weapon" in t or "Armour" in t for t in types), \
        "No Equipment entry found"


def test_gem_can_level_up(outcomes):
    gem_entry = next((e for e in outcomes if "Gem" in e["item_type"]), None)
    assert gem_entry is not None
    results = [o["result"].lower() for o in gem_entry["outcomes"]]
    assert any("level" in r for r in results), "No gem level-up outcome found"


def test_corrupted_blood_implicit_exists(implicits):
    names = [imp["implicit"].lower() for imp in implicits]
    assert any("corrupted blood" in n for n in names), \
        "Corrupted Blood implicit not found"


def test_explosion_implicit_exists(implicits):
    results = [imp["implicit"].lower() for imp in implicits]
    assert any("explode" in r for r in results), "Explode on kill implicit not found"


def test_double_corruption_note_non_empty(data):
    assert data["double_corruption"].strip(), "double_corruption note is empty"


def test_how_it_works_non_empty(data):
    assert data["how_it_works"].strip(), "how_it_works is empty"
