"""Tests for Influence Modifier Reference data and panel logic."""

import json
import os
import pytest

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "influence_mods.json")


@pytest.fixture(scope="module")
def data():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def mods(data):
    return data["mods"]


# ── Data integrity ───────────────────────────────────────────────────────────

def test_data_file_exists():
    assert os.path.exists(DATA_PATH)


def test_has_required_top_level_keys(data):
    for key in ("mods", "how_it_works", "tips", "categories", "slots"):
        assert key in data, f"Missing top-level key: {key}"


def test_mods_non_empty(mods):
    assert len(mods) >= 20, f"Expected at least 20 mods, got {len(mods)}"


def test_all_mods_have_required_fields(mods):
    required = ("influence", "slot", "mod_name", "value_range", "value_tier", "best_for", "notes")
    for mod in mods:
        for field in required:
            assert field in mod, f"Mod '{mod.get('mod_name')}' missing field: {field}"


def test_valid_influences(mods, data):
    valid = set(data.get("categories", []))
    for mod in mods:
        assert mod["influence"] in valid, \
            f"Mod '{mod['mod_name']}' has invalid influence: '{mod['influence']}'"


def test_valid_slots(mods, data):
    valid = set(data.get("slots", []))
    for mod in mods:
        assert mod["slot"] in valid, \
            f"Mod '{mod['mod_name']}' has invalid slot: '{mod['slot']}'"


def test_valid_value_tiers(mods):
    valid = {"Extremely High", "High", "Medium", "Low"}
    for mod in mods:
        assert mod["value_tier"] in valid, \
            f"Mod '{mod['mod_name']}' has invalid value_tier: '{mod['value_tier']}'"


def test_best_for_is_list(mods):
    for mod in mods:
        assert isinstance(mod["best_for"], list), \
            f"Mod '{mod['mod_name']}' best_for must be a list"


def test_influence_slot_pairs_unique(mods):
    pairs = [(m["influence"], m["slot"], m["mod_name"]) for m in mods]
    assert len(pairs) == len(set(pairs)), "Duplicate (influence, slot, mod_name) combinations found"


def test_all_six_influences_represented(mods):
    influences = {m["influence"] for m in mods}
    expected = {"Shaper", "Elder", "Warlord", "Crusader", "Redeemer", "Hunter"}
    assert influences == expected, f"Missing influences: {expected - influences}"


def test_tips_is_list(data):
    assert isinstance(data.get("tips", []), list)


def test_categories_non_empty(data):
    cats = data.get("categories", [])
    assert len(cats) >= 6, f"Expected at least 6 categories, got {len(cats)}"


# ── Content spot-checks ──────────────────────────────────────────────────────

def test_shaper_mods_present(mods):
    shaper = [m for m in mods if m["influence"] == "Shaper"]
    assert len(shaper) >= 4, f"Expected at least 4 Shaper mods, got {len(shaper)}"


def test_elder_mods_present(mods):
    elder = [m for m in mods if m["influence"] == "Elder"]
    assert len(elder) >= 3, f"Expected at least 3 Elder mods, got {len(elder)}"


def test_hunter_chaos_damage_mod_present(mods):
    names = [m["mod_name"] for m in mods if m["influence"] == "Hunter"]
    assert any("Chaos" in n for n in names), "Expected at least one Hunter chaos mod"


def test_slot_coverage(mods):
    slots = {m["slot"] for m in mods}
    key_slots = {"Helmet", "Gloves", "Belt", "Body Armour"}
    for slot in key_slots:
        assert slot in slots, f"No mods found for slot: {slot}"


# ── Panel import ─────────────────────────────────────────────────────────────

def test_panel_imports_without_error():
    from ui.widgets.influence_mods_panel import InfluenceModsPanel


def test_panel_load_data_returns_dict():
    from ui.widgets.influence_mods_panel import _load_data
    result = _load_data()
    assert isinstance(result, dict)
    assert "mods" in result


def test_panel_matches_logic():
    from ui.widgets.influence_mods_panel import InfluenceModsPanel
    panel = InfluenceModsPanel.__new__(InfluenceModsPanel)
    mod = {
        "influence": "Hunter",
        "slot": "Gloves",
        "mod_name": "Adds Chaos Damage",
        "value_range": "7-11",
        "value_tier": "High",
        "best_for": ["Poison builds"],
        "notes": "Key mod for chaos attack builds.",
    }
    assert panel._matches(mod, "chaos")
    assert panel._matches(mod, "hunter")
    assert panel._matches(mod, "poison")
    assert not panel._matches(mod, "shaper")
    assert panel._matches(mod, "")
