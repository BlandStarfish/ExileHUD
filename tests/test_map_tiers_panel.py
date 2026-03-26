"""Tests for Map Tier Progression Guide data and panel logic."""

import json
import os
import pytest

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "map_tiers.json")


@pytest.fixture(scope="module")
def data():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def tiers(data):
    return data["tiers"]


# ── Data integrity ────────────────────────────────────────────────────────────

def test_data_file_exists():
    assert os.path.exists(DATA_PATH)


def test_has_required_top_level_keys(data):
    for key in ("tiers", "how_it_works", "tips", "tier_groups"):
        assert key in data, f"Missing top-level key: {key}"


def test_tiers_non_empty(tiers):
    assert len(tiers) >= 5, f"Expected at least 5 tier entries, got {len(tiers)}"


def test_all_tiers_have_required_fields(tiers):
    required = ("tier_name", "tier_group", "typical_area_level", "rarity_requirement",
                "key_mechanics", "atlas_objective", "notable_maps", "value_tier", "notes")
    for tier in tiers:
        for field in required:
            assert field in tier, f"Tier '{tier.get('tier_name')}' missing field: {field}"


def test_valid_tier_groups(tiers, data):
    valid = set(data.get("tier_groups", []))
    for tier in tiers:
        assert tier["tier_group"] in valid, \
            f"Tier '{tier['tier_name']}' has invalid tier_group: '{tier['tier_group']}'"


def test_valid_value_tiers(tiers):
    valid = {"Extremely High", "High", "Medium", "Low"}
    for tier in tiers:
        assert tier["value_tier"] in valid, \
            f"Tier '{tier['tier_name']}' has invalid value_tier: '{tier['value_tier']}'"


def test_key_mechanics_is_list(tiers):
    for tier in tiers:
        assert isinstance(tier["key_mechanics"], list), \
            f"Tier '{tier['tier_name']}' key_mechanics must be a list"


def test_notable_maps_is_list(tiers):
    for tier in tiers:
        assert isinstance(tier["notable_maps"], list), \
            f"Tier '{tier['tier_name']}' notable_maps must be a list"


def test_tips_is_list(data):
    assert isinstance(data.get("tips", []), list)


def test_tier_groups_non_empty(data):
    groups = data.get("tier_groups", [])
    assert len(groups) >= 3, f"Expected at least 3 tier groups, got {len(groups)}"


# ── Content spot-checks ───────────────────────────────────────────────────────

def test_white_maps_present(tiers):
    white = [t for t in tiers if t["tier_group"] == "White (T1–5)"]
    assert len(white) >= 1, "Expected at least 1 white map entry"


def test_yellow_maps_present(tiers):
    yellow = [t for t in tiers if t["tier_group"] == "Yellow (T6–10)"]
    assert len(yellow) >= 1, "Expected at least 1 yellow map entry"


def test_red_maps_present(tiers):
    red = [t for t in tiers if t["tier_group"] == "Red (T11–16)"]
    assert len(red) >= 2, "Expected at least 2 red map entries"


def test_pinnacle_entry_present(tiers):
    pinnacle = [t for t in tiers if "Pinnacle" in t["tier_name"]]
    assert len(pinnacle) >= 1, "Expected Pinnacle Boss entry"


def test_extremely_high_entries_exist(tiers):
    top = [t for t in tiers if t["value_tier"] == "Extremely High"]
    assert len(top) >= 1, "Expected at least 1 Extremely High value tier entry"


# ── Panel import ──────────────────────────────────────────────────────────────

def test_panel_imports_without_error():
    from ui.widgets.map_tiers_panel import MapTiersPanel


def test_panel_load_data_returns_dict():
    from ui.widgets.map_tiers_panel import _load_data
    result = _load_data()
    assert isinstance(result, dict)
    assert "tiers" in result


def test_panel_matches_logic():
    from ui.widgets.map_tiers_panel import MapTiersPanel
    panel = MapTiersPanel.__new__(MapTiersPanel)
    tier = {
        "tier_name": "Red Maps (T15–16) — Endgame Red",
        "tier_group": "Red (T11–16)",
        "typical_area_level": "84–85",
        "rarity_requirement": "Chisel + alch + vaal",
        "key_mechanics": ["Maven invitations", "Pinnacle boss farming"],
        "atlas_objective": "Farm Voidstones",
        "notable_maps": ["Shaper's Realm"],
        "voidstone_requirement": 4,
        "value_tier": "Extremely High",
        "notes": "Endgame tier.",
    }
    assert panel._matches(tier, "endgame")
    assert panel._matches(tier, "maven")
    assert panel._matches(tier, "voidstone")
    assert panel._matches(tier, "chisel")
    assert not panel._matches(tier, "white maps")
    assert panel._matches(tier, "")


def test_panel_group_filter():
    from ui.widgets.map_tiers_panel import MapTiersPanel
    panel = MapTiersPanel.__new__(MapTiersPanel)
    tiers = [
        {"tier_name": "A", "tier_group": "White (T1–5)", "typical_area_level": 68,
         "rarity_requirement": "", "key_mechanics": [], "atlas_objective": "",
         "notable_maps": [], "value_tier": "Low", "notes": ""},
        {"tier_name": "B", "tier_group": "Red (T11–16)", "typical_area_level": 83,
         "rarity_requirement": "", "key_mechanics": [], "atlas_objective": "",
         "notable_maps": [], "value_tier": "High", "notes": ""},
        {"tier_name": "C", "tier_group": "White (T1–5)", "typical_area_level": 68,
         "rarity_requirement": "", "key_mechanics": [], "atlas_objective": "",
         "notable_maps": [], "value_tier": "Low", "notes": ""},
    ]
    white_only = [t for t in tiers if t["tier_group"] == "White (T1–5)"]
    assert len(white_only) == 2
    assert all(t["tier_group"] == "White (T1–5)" for t in white_only)
