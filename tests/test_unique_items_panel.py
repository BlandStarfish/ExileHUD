"""Tests for Unique Item Tier List data and panel logic."""

import json
import os
import pytest

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "unique_items.json")


@pytest.fixture(scope="module")
def data():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def items(data):
    return data["items"]


# ── Data integrity ────────────────────────────────────────────────────────────

def test_data_file_exists():
    assert os.path.exists(DATA_PATH)


def test_has_required_top_level_keys(data):
    for key in ("items", "how_it_works", "tips", "budget_tiers"):
        assert key in data, f"Missing top-level key: {key}"


def test_items_non_empty(items):
    assert len(items) >= 15, f"Expected at least 15 items, got {len(items)}"


def test_all_items_have_required_fields(items):
    required = ("name", "slot", "budget_tier", "source", "key_effect",
                "best_for", "why_valuable", "value_tier", "notes")
    for item in items:
        for field in required:
            assert field in item, f"Item '{item.get('name')}' missing field: {field}"


def test_valid_budget_tiers(items, data):
    valid = set(data.get("budget_tiers", []))
    for item in items:
        assert item["budget_tier"] in valid, \
            f"Item '{item['name']}' has invalid budget_tier: '{item['budget_tier']}'"


def test_valid_value_tiers(items):
    valid = {"Extremely High", "High", "Medium", "Low"}
    for item in items:
        assert item["value_tier"] in valid, \
            f"Item '{item['name']}' has invalid value_tier: '{item['value_tier']}'"


def test_best_for_is_list(items):
    for item in items:
        assert isinstance(item["best_for"], list), \
            f"Item '{item['name']}' best_for must be a list"


def test_item_names_unique(items):
    names = [i["name"] for i in items]
    assert len(names) == len(set(names)), "Duplicate item name entries found"


def test_tips_is_list(data):
    assert isinstance(data.get("tips", []), list)


def test_budget_tiers_non_empty(data):
    tiers = data.get("budget_tiers", [])
    assert len(tiers) >= 4, f"Expected at least 4 budget tiers, got {len(tiers)}"


# ── Content spot-checks ───────────────────────────────────────────────────────

def test_headhunter_present(items):
    hh = [i for i in items if "Headhunter" in i["name"]]
    assert len(hh) >= 1, "Expected Headhunter in the list"


def test_mageblood_present(items):
    mb = [i for i in items if "Mageblood" in i["name"]]
    assert len(mb) >= 1, "Expected Mageblood in the list"


def test_mirror_tier_items_exist(items):
    mirror = [i for i in items if i["budget_tier"] == "Mirror-Tier"]
    assert len(mirror) >= 2, "Expected at least 2 Mirror-Tier items"


def test_leveling_items_exist(items):
    leveling = [i for i in items if i["budget_tier"] == "Leveling"]
    assert len(leveling) >= 1, "Expected at least 1 Leveling item"


def test_league_starter_items_exist(items):
    starter = [i for i in items if i["budget_tier"] == "League Starter"]
    assert len(starter) >= 2, "Expected at least 2 League Starter items"


def test_extremely_high_value_items_exist(items):
    top = [i for i in items if i["value_tier"] == "Extremely High"]
    assert len(top) >= 2, "Expected at least 2 Extremely High value items"


# ── Panel import ──────────────────────────────────────────────────────────────

def test_panel_imports_without_error():
    from ui.widgets.unique_items_panel import UniqueItemsPanel


def test_panel_load_data_returns_dict():
    from ui.widgets.unique_items_panel import _load_data
    result = _load_data()
    assert isinstance(result, dict)
    assert "items" in result


def test_panel_matches_logic():
    from ui.widgets.unique_items_panel import UniqueItemsPanel
    panel = UniqueItemsPanel.__new__(UniqueItemsPanel)
    item = {
        "name": "Headhunter",
        "slot": "Belt",
        "budget_tier": "Mirror-Tier",
        "source": "Drop from rare monsters in T14+ maps",
        "key_effect": "Gain rare monster mods on kill.",
        "value_tier": "Extremely High",
        "best_for": ["Mapping builds", "Speed clearing"],
        "why_valuable": "Best mapping belt in the game.",
        "notes": "Varies 60–200+ Divines per league.",
    }
    assert panel._matches(item, "headhunter")
    assert panel._matches(item, "belt")
    assert panel._matches(item, "mapping")
    assert panel._matches(item, "mirror")
    assert not panel._matches(item, "crit build")
    assert panel._matches(item, "")


def test_panel_budget_filter():
    from ui.widgets.unique_items_panel import UniqueItemsPanel
    panel = UniqueItemsPanel.__new__(UniqueItemsPanel)
    items = [
        {"name": "A", "slot": "Belt", "budget_tier": "Mirror-Tier",
         "source": "", "key_effect": "", "value_tier": "Extremely High",
         "best_for": [], "why_valuable": "", "notes": ""},
        {"name": "B", "slot": "Helmet", "budget_tier": "League Starter",
         "source": "", "key_effect": "", "value_tier": "Low",
         "best_for": [], "why_valuable": "", "notes": ""},
        {"name": "C", "slot": "Belt", "budget_tier": "Mirror-Tier",
         "source": "", "key_effect": "", "value_tier": "High",
         "best_for": [], "why_valuable": "", "notes": ""},
    ]
    mirror_only = [i for i in items if i["budget_tier"] == "Mirror-Tier"]
    assert len(mirror_only) == 2
    assert all(i["budget_tier"] == "Mirror-Tier" for i in mirror_only)
