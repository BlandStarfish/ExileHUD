"""Tests for Lab Enchantment Reference data and panel logic."""

import json
import os
import pytest

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "lab_enchants.json")


@pytest.fixture(scope="module")
def data():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def enchants(data):
    return data["enchants"]


# ── Data integrity ───────────────────────────────────────────────────────────

def test_data_file_exists():
    assert os.path.exists(DATA_PATH)


def test_has_required_top_level_keys(data):
    for key in ("enchants", "how_it_works", "tips", "categories", "difficulties"):
        assert key in data, f"Missing top-level key: {key}"


def test_enchants_non_empty(enchants):
    assert len(enchants) >= 20, f"Expected at least 20 enchants, got {len(enchants)}"


def test_all_enchants_have_required_fields(enchants):
    required = ("slot", "skill_name", "enchant_effect", "lab_difficulty",
                "value_tier", "best_for", "notes")
    for enchant in enchants:
        for field in required:
            assert field in enchant, \
                f"Enchant '{enchant.get('skill_name')}' missing field: {field}"


def test_valid_slots(enchants, data):
    valid = set(data.get("categories", []))
    for enchant in enchants:
        assert enchant["slot"] in valid, \
            f"Enchant '{enchant['skill_name']}' has invalid slot: '{enchant['slot']}'"


def test_valid_difficulties(enchants, data):
    valid = set(data.get("difficulties", []))
    for enchant in enchants:
        assert enchant["lab_difficulty"] in valid, \
            f"Enchant '{enchant['skill_name']}' has invalid difficulty: '{enchant['lab_difficulty']}'"


def test_valid_value_tiers(enchants):
    valid = {"Extremely High", "High", "Medium", "Low"}
    for enchant in enchants:
        assert enchant["value_tier"] in valid, \
            f"Enchant '{enchant['skill_name']}' has invalid value_tier: '{enchant['value_tier']}'"


def test_best_for_is_list(enchants):
    for enchant in enchants:
        assert isinstance(enchant["best_for"], list), \
            f"Enchant '{enchant['skill_name']}' best_for must be a list"


def test_all_three_slots_represented(enchants):
    slots = {e["slot"] for e in enchants}
    assert "Helmet" in slots and "Boots" in slots and "Gloves" in slots, \
        f"Not all slots represented: {slots}"


def test_helmet_enchants_present(enchants):
    helms = [e for e in enchants if e["slot"] == "Helmet"]
    assert len(helms) >= 8, f"Expected at least 8 helmet enchants, got {len(helms)}"


def test_boots_enchants_present(enchants):
    boots = [e for e in enchants if e["slot"] == "Boots"]
    assert len(boots) >= 3, f"Expected at least 3 boots enchants, got {len(boots)}"


def test_gloves_enchants_present(enchants):
    gloves = [e for e in enchants if e["slot"] == "Gloves"]
    assert len(gloves) >= 4, f"Expected at least 4 gloves enchants, got {len(gloves)}"


def test_movement_speed_boots_enchant_present(enchants):
    boots = [e for e in enchants if e["slot"] == "Boots"]
    assert any("Movement Speed" in e["skill_name"] or "Movement Speed" in e["enchant_effect"]
               for e in boots), "Movement speed boots enchant should be present"


def test_tips_is_list(data):
    assert isinstance(data.get("tips", []), list)


def test_difficulties_correct(data):
    diffs = data.get("difficulties", [])
    assert "Merciless" in diffs and "Eternal" in diffs


# ── Panel import ─────────────────────────────────────────────────────────────

def test_panel_imports_without_error():
    from ui.widgets.lab_enchants_panel import LabEnchantsPanel


def test_panel_load_data_returns_dict():
    from ui.widgets.lab_enchants_panel import _load_data
    result = _load_data()
    assert isinstance(result, dict)
    assert "enchants" in result


def test_panel_matches_logic():
    from ui.widgets.lab_enchants_panel import LabEnchantsPanel
    panel = LabEnchantsPanel.__new__(LabEnchantsPanel)
    enchant = {
        "slot": "Helmet",
        "skill_name": "Cyclone",
        "enchant_effect": "Cyclone has 12% increased Area of Effect",
        "lab_difficulty": "Eternal",
        "value_tier": "High",
        "best_for": ["Cyclone builds"],
        "notes": "Larger Cyclone radius.",
    }
    assert panel._matches(enchant, "cyclone")
    assert panel._matches(enchant, "helmet")
    assert panel._matches(enchant, "eternal")
    assert panel._matches(enchant, "area of effect")
    assert not panel._matches(enchant, "tornado shot")
    assert panel._matches(enchant, "")
