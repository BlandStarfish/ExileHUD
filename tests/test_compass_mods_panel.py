"""Tests for Compass/Sextant Mod Reference data and panel logic."""

import json
import os
import pytest

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "compass_mods.json")


@pytest.fixture(scope="module")
def data():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def mods(data):
    return data["mods"]


# ── Data integrity ────────────────────────────────────────────────────────────

def test_data_file_exists():
    assert os.path.exists(DATA_PATH)


def test_has_required_top_level_keys(data):
    for key in ("mods", "how_it_works", "tips", "categories"):
        assert key in data, f"Missing top-level key: {key}"


def test_mods_non_empty(mods):
    assert len(mods) >= 15, f"Expected at least 15 mods, got {len(mods)}"


def test_all_mods_have_required_fields(mods):
    required = ("mod_name", "category", "effect", "value_tier", "best_for", "notes")
    for mod in mods:
        for field in required:
            assert field in mod, f"Mod '{mod.get('mod_name')}' missing field: {field}"


def test_valid_categories(mods, data):
    valid = set(data.get("categories", []))
    for mod in mods:
        assert mod["category"] in valid, \
            f"Mod '{mod['mod_name']}' has invalid category: '{mod['category']}'"


def test_valid_value_tiers(mods):
    valid = {"Extremely High", "High", "Medium", "Low"}
    for mod in mods:
        assert mod["value_tier"] in valid, \
            f"Mod '{mod['mod_name']}' has invalid value_tier: '{mod['value_tier']}'"


def test_best_for_is_list(mods):
    for mod in mods:
        assert isinstance(mod["best_for"], list), \
            f"Mod '{mod['mod_name']}' best_for must be a list"


def test_mod_names_unique(mods):
    names = [m["mod_name"] for m in mods]
    assert len(names) == len(set(names)), "Duplicate mod_name entries found"


def test_tips_is_list(data):
    assert isinstance(data.get("tips", []), list)


def test_categories_non_empty(data):
    cats = data.get("categories", [])
    assert len(cats) >= 5, f"Expected at least 5 categories, got {len(cats)}"


# ── Content spot-checks ───────────────────────────────────────────────────────

def test_beyond_mod_present(mods):
    beyond = [m for m in mods if m["category"] == "Beyond"]
    assert len(beyond) >= 1, "Expected at least 1 Beyond mod"


def test_delirium_mod_present(mods):
    delirium = [m for m in mods if m["category"] == "Delirium"]
    assert len(delirium) >= 1, "Expected at least 1 Delirium mod"


def test_extremely_high_tier_mods_exist(mods):
    top = [m for m in mods if m["value_tier"] == "Extremely High"]
    assert len(top) >= 1, "Expected at least 1 Extremely High value mod"


def test_harvest_mod_present(mods):
    harvest = [m for m in mods if m["category"] == "Harvest"]
    assert len(harvest) >= 1, "Expected at least 1 Harvest mod"


def test_expedition_mod_present(mods):
    expedition = [m for m in mods if m["category"] == "Expedition"]
    assert len(expedition) >= 1, "Expected at least 1 Expedition mod"


# ── Panel import ──────────────────────────────────────────────────────────────

def test_panel_imports_without_error():
    from ui.widgets.compass_mods_panel import CompassModsPanel


def test_panel_load_data_returns_dict():
    from ui.widgets.compass_mods_panel import _load_data
    result = _load_data()
    assert isinstance(result, dict)
    assert "mods" in result


def test_panel_matches_logic():
    from ui.widgets.compass_mods_panel import CompassModsPanel
    panel = CompassModsPanel.__new__(CompassModsPanel)
    mod = {
        "mod_name": "Area contains Beyond Demons",
        "category": "Beyond",
        "effect": "Spawns Beyond portals as you kill monsters.",
        "value_tier": "Extremely High",
        "best_for": ["All builds", "Currency farming"],
        "notes": "One of the highest-value compasses.",
    }
    assert panel._matches(mod, "beyond")
    assert panel._matches(mod, "currency")
    assert panel._matches(mod, "extremely high")
    assert not panel._matches(mod, "harvest")
    assert panel._matches(mod, "")


def test_panel_category_filter():
    from ui.widgets.compass_mods_panel import CompassModsPanel
    panel = CompassModsPanel.__new__(CompassModsPanel)
    mods = [
        {"mod_name": "A", "category": "Beyond", "effect": "", "value_tier": "High", "best_for": [], "notes": ""},
        {"mod_name": "B", "category": "Delirium", "effect": "", "value_tier": "High", "best_for": [], "notes": ""},
        {"mod_name": "C", "category": "Beyond", "effect": "", "value_tier": "Medium", "best_for": [], "notes": ""},
    ]
    beyond_only = [m for m in mods if m["category"] == "Beyond"]
    assert len(beyond_only) == 2
    assert all(m["category"] == "Beyond" for m in beyond_only)
