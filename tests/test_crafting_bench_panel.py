"""Tests for Crafting Bench Quick Reference data and panel logic."""

import json
import os
import pytest

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "crafting_bench.json")


@pytest.fixture(scope="module")
def data():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def mods(data):
    return data["bench_mods"]


# ── Data integrity ─────────────────────────────────────────────────────────────

def test_data_file_exists():
    assert os.path.exists(DATA_PATH)


def test_has_required_top_level_keys(data):
    for key in ("bench_mods", "categories", "tips"):
        assert key in data, f"Missing top-level key: {key}"


def test_mods_non_empty(mods):
    assert len(mods) >= 20, f"Expected at least 20 bench mods, got {len(mods)}"


def test_all_mods_have_required_fields(mods):
    required = ("name", "category", "mod_type", "best_tier", "slots", "cost")
    for mod in mods:
        for field in required:
            assert field in mod, f"Mod '{mod.get('name')}' missing field: {field}"


def test_mod_names_unique(mods):
    names = [m["name"] for m in mods]
    assert len(names) == len(set(names)), "Duplicate mod names found"


def test_valid_categories(mods, data):
    valid = set(data.get("categories", []))
    for mod in mods:
        assert mod["category"] in valid, \
            f"Mod '{mod['name']}' has invalid category: '{mod['category']}'"


def test_valid_mod_types(mods):
    valid = {"Prefix", "Suffix"}
    for mod in mods:
        assert mod["mod_type"] in valid, \
            f"Mod '{mod['name']}' has invalid mod_type: '{mod['mod_type']}'"


def test_best_tier_non_empty(mods):
    for mod in mods:
        assert mod["best_tier"].strip(), f"Mod '{mod['name']}' has empty best_tier"


def test_slots_non_empty(mods):
    for mod in mods:
        assert mod["slots"].strip(), f"Mod '{mod['name']}' has empty slots"


def test_cost_non_empty(mods):
    for mod in mods:
        assert mod["cost"].strip(), f"Mod '{mod['name']}' has empty cost"


def test_tips_non_empty(data):
    assert len(data.get("tips", [])) >= 3, "Expected at least 3 tips"


# ── Category coverage ──────────────────────────────────────────────────────────

def test_has_life_and_mana_mods(mods):
    lm = [m for m in mods if m["category"] == "Life & Mana"]
    assert len(lm) >= 3, f"Expected at least 3 Life & Mana mods, got {len(lm)}"


def test_has_resistance_mods(mods):
    res = [m for m in mods if m["category"] == "Resistances"]
    assert len(res) >= 3, f"Expected at least 3 Resistances mods, got {len(res)}"


def test_has_defence_mods(mods):
    df = [m for m in mods if m["category"] == "Defence"]
    assert len(df) >= 3, f"Expected at least 3 Defence mods, got {len(df)}"


def test_has_offence_mods(mods):
    off = [m for m in mods if m["category"] == "Offence"]
    assert len(off) >= 4, f"Expected at least 4 Offence mods, got {len(off)}"


def test_has_utility_mods(mods):
    ut = [m for m in mods if m["category"] == "Utility"]
    assert len(ut) >= 2, f"Expected at least 2 Utility mods, got {len(ut)}"


def test_has_both_prefixes_and_suffixes(mods):
    prefixes = [m for m in mods if m["mod_type"] == "Prefix"]
    suffixes = [m for m in mods if m["mod_type"] == "Suffix"]
    assert len(prefixes) >= 5, f"Expected at least 5 Prefix mods, got {len(prefixes)}"
    assert len(suffixes) >= 5, f"Expected at least 5 Suffix mods, got {len(suffixes)}"


# ── Specific mods present ──────────────────────────────────────────────────────

def test_key_mods_present(mods):
    names = {m["name"] for m in mods}
    expected = {"Maximum Life", "Fire Resistance", "Cold Resistance",
                "Lightning Resistance", "Movement Speed", "Attack Speed"}
    for name in expected:
        assert name in names, f"Expected mod '{name}' not found"


def test_movement_speed_is_boots_only(mods):
    by_name = {m["name"]: m for m in mods}
    ms = by_name.get("Movement Speed")
    assert ms is not None, "Movement Speed mod not found"
    assert "Boots" in ms["slots"], "Movement Speed should apply to Boots"


def test_all_elemental_resistances_mod_present(mods):
    names = {m["name"] for m in mods}
    assert "All Elemental Resistances" in names


# ── Search logic (data-level) ──────────────────────────────────────────────────

def _matches(mod: dict, query: str) -> bool:
    """Mirror of panel search logic for data-level testing."""
    if not query:
        return True
    searchable = " ".join([
        mod.get("name", ""),
        mod.get("category", ""),
        mod.get("mod_type", ""),
        mod.get("best_tier", ""),
        mod.get("slots", ""),
        mod.get("cost", ""),
        mod.get("notes", ""),
    ]).lower()
    return query in searchable


def test_panel_module_importable():
    """Verify the panel module can be imported without a QApplication."""
    import importlib
    mod = importlib.import_module("ui.widgets.crafting_bench_panel")
    assert hasattr(mod, "CraftingBenchPanel")


def test_search_matches_name(mods):
    results = [m for m in mods if _matches(m, "maximum life")]
    assert any(m["name"] == "Maximum Life" for m in results)


def test_search_matches_slot(mods):
    results = [m for m in mods if _matches(m, "boots")]
    assert any(m["name"] == "Movement Speed" for m in results)


def test_search_matches_cost(mods):
    results = [m for m in mods if _matches(m, "regal")]
    assert len(results) >= 3, "Expected several Regal Orb mods"


def test_search_matches_mod_type(mods):
    results = [m for m in mods if _matches(m, "prefix")]
    assert len(results) >= 5


def test_search_empty_returns_all(mods):
    results = [m for m in mods if _matches(m, "")]
    assert len(results) == len(mods)


def test_search_no_match(mods):
    results = [m for m in mods if _matches(m, "xyzxyzxyz_no_match")]
    assert len(results) == 0
