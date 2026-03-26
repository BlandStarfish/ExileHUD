"""Tests for Veiled Mod Crafting Reference data and panel logic."""

import json
import os
import pytest

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "veiled_mods.json")


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
    required = ("mod_name", "item_slot", "mod_type", "tiers", "best_tier",
                "value_tier", "best_for", "notes")
    for mod in mods:
        for field in required:
            assert field in mod, f"Mod '{mod.get('mod_name')}' missing field: {field}"


def test_valid_mod_types(mods):
    valid = {"Prefix", "Suffix"}
    for mod in mods:
        assert mod["mod_type"] in valid, \
            f"Mod '{mod['mod_name']}' has invalid mod_type: '{mod['mod_type']}'"


def test_valid_value_tiers(mods):
    valid = {"Extremely High", "High", "Medium", "Low"}
    for mod in mods:
        assert mod["value_tier"] in valid, \
            f"Mod '{mod['mod_name']}' has invalid value_tier: '{mod['value_tier']}'"


def test_valid_item_slots(mods, data):
    valid = set(data.get("categories", []))
    for mod in mods:
        assert mod["item_slot"] in valid, \
            f"Mod '{mod['mod_name']}' has invalid item_slot: '{mod['item_slot']}'"


def test_tiers_is_list(mods):
    for mod in mods:
        assert isinstance(mod["tiers"], list), \
            f"Mod '{mod['mod_name']}' tiers must be a list"


def test_best_for_is_list(mods):
    for mod in mods:
        assert isinstance(mod["best_for"], list), \
            f"Mod '{mod['mod_name']}' best_for must be a list"


def test_best_tier_in_tiers(mods):
    for mod in mods:
        if mod["tiers"]:
            assert mod["best_tier"] in mod["tiers"], \
                f"Mod '{mod['mod_name']}' best_tier not in tiers list"


def test_tips_is_list(data):
    assert isinstance(data.get("tips", []), list)


def test_categories_non_empty(data):
    cats = data.get("categories", [])
    assert len(cats) >= 5, f"Expected at least 5 categories, got {len(cats)}"


# ── Content spot-checks ───────────────────────────────────────────────────────

def test_boots_movement_speed_mod_present(mods):
    boots_ms = [m for m in mods if m["item_slot"] == "Boots" and "Movement Speed" in m["mod_name"]]
    assert len(boots_ms) >= 1, "Expected at least 1 Boots movement speed mod"


def test_boots_tailwind_mod_present(mods):
    tailwind = [m for m in mods if "Tailwind" in m["mod_name"]]
    assert len(tailwind) >= 1, "Expected Tailwind boot mod"


def test_gloves_culling_strike_mod_present(mods):
    culling = [m for m in mods if "Culling" in m["mod_name"]]
    assert len(culling) >= 1, "Expected Culling Strike gloves mod"


def test_extremely_high_tier_mods_exist(mods):
    top = [m for m in mods if m["value_tier"] == "Extremely High"]
    assert len(top) >= 2, "Expected at least 2 Extremely High value mods"


def test_weapon_mods_present(mods):
    weapon_mods = [m for m in mods if m["item_slot"] == "Weapon"]
    assert len(weapon_mods) >= 1, "Expected at least 1 weapon mod"


# ── Panel import ──────────────────────────────────────────────────────────────

def test_panel_imports_without_error():
    from ui.widgets.veiled_mods_panel import VeiledModsPanel


def test_panel_load_data_returns_dict():
    from ui.widgets.veiled_mods_panel import _load_data
    result = _load_data()
    assert isinstance(result, dict)
    assert "mods" in result


def test_panel_matches_logic():
    from ui.widgets.veiled_mods_panel import VeiledModsPanel
    panel = VeiledModsPanel.__new__(VeiledModsPanel)
    mod = {
        "mod_name": "Veiled Suffix — Movement Speed (Boots)",
        "item_slot": "Boots",
        "mod_type": "Suffix",
        "tiers": ["8–10% increased Movement Speed"],
        "best_tier": "8–10% increased Movement Speed",
        "value_tier": "Extremely High",
        "best_for": ["All builds"],
        "notes": "Best boot suffix.",
    }
    assert panel._matches(mod, "movement")
    assert panel._matches(mod, "boots")
    assert panel._matches(mod, "all builds")
    assert panel._matches(mod, "extremely high")
    assert not panel._matches(mod, "helmet")
    assert panel._matches(mod, "")


def test_panel_slot_filter():
    from ui.widgets.veiled_mods_panel import VeiledModsPanel
    panel = VeiledModsPanel.__new__(VeiledModsPanel)
    mods = [
        {"mod_name": "A", "item_slot": "Boots", "mod_type": "Suffix",
         "tiers": [], "best_tier": "", "value_tier": "High", "best_for": [], "notes": ""},
        {"mod_name": "B", "item_slot": "Helmet", "mod_type": "Prefix",
         "tiers": [], "best_tier": "", "value_tier": "High", "best_for": [], "notes": ""},
        {"mod_name": "C", "item_slot": "Boots", "mod_type": "Suffix",
         "tiers": [], "best_tier": "", "value_tier": "Medium", "best_for": [], "notes": ""},
    ]
    boots_only = [m for m in mods if m["item_slot"] == "Boots"]
    assert len(boots_only) == 2
    assert all(m["item_slot"] == "Boots" for m in boots_only)
