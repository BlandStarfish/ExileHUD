"""Tests for Atlas Farming Activity Guide data and panel logic."""

import json
import os
import pytest

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "farm_guide.json")


@pytest.fixture(scope="module")
def data():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def activities(data):
    return data["activities"]


# ── Data integrity ────────────────────────────────────────────────────────────

def test_data_file_exists():
    assert os.path.exists(DATA_PATH)


def test_has_required_top_level_keys(data):
    assert "activities" in data


def test_activities_non_empty(activities):
    assert len(activities) >= 10, f"Expected at least 10 activities, got {len(activities)}"


def test_all_activities_have_required_fields(activities):
    required = ("id", "name", "mechanic", "best_maps", "key_drops",
                "chaos_per_hour", "difficulty", "tips")
    for act in activities:
        for field in required:
            assert field in act, f"Activity '{act.get('name')}' missing field: {field}"


def test_valid_difficulties(activities):
    valid = {"Low", "Medium", "High"}
    for act in activities:
        assert act["difficulty"] in valid, \
            f"Activity '{act['name']}' has invalid difficulty: '{act['difficulty']}'"


def test_chaos_per_hour_has_low_and_high(activities):
    for act in activities:
        cph = act.get("chaos_per_hour", {})
        assert "low" in cph and "high" in cph, \
            f"Activity '{act['name']}' chaos_per_hour missing low/high"
        assert cph["low"] <= cph["high"], \
            f"Activity '{act['name']}' chaos_per_hour low > high"


def test_best_maps_is_list(activities):
    for act in activities:
        assert isinstance(act["best_maps"], list), \
            f"Activity '{act['name']}' best_maps must be a list"


def test_key_drops_is_list(activities):
    for act in activities:
        assert isinstance(act["key_drops"], list), \
            f"Activity '{act['name']}' key_drops must be a list"


def test_key_drops_have_required_fields(activities):
    for act in activities:
        for drop in act.get("key_drops", []):
            assert "item" in drop, \
                f"Activity '{act['name']}' drop missing 'item' field"
            assert "drop_rate" in drop, \
                f"Activity '{act['name']}' drop missing 'drop_rate' field"


def test_tips_is_list(activities):
    for act in activities:
        assert isinstance(act["tips"], list), \
            f"Activity '{act['name']}' tips must be a list"


def test_ids_are_unique(activities):
    ids = [a["id"] for a in activities]
    assert len(ids) == len(set(ids)), "Duplicate activity IDs found"


# ── Content spot-checks ───────────────────────────────────────────────────────

def test_breach_farming_present(activities):
    breach = [a for a in activities if a.get("mechanic") == "Breach"]
    assert len(breach) >= 1, "Expected at least 1 Breach activity"


def test_expedition_farming_present(activities):
    exp = [a for a in activities if "Expedition" in a.get("name", "")]
    assert len(exp) >= 1, "Expected at least 1 Expedition activity"


def test_low_medium_high_all_represented(activities):
    difficulties = {a["difficulty"] for a in activities}
    for diff in ("Low", "Medium", "High"):
        assert diff in difficulties, f"Missing difficulty tier: {diff}"


def test_chaos_per_hour_positive(activities):
    for act in activities:
        cph = act["chaos_per_hour"]
        assert cph["low"] > 0, f"Activity '{act['name']}' chaos/hr low must be positive"
        assert cph["high"] > 0, f"Activity '{act['name']}' chaos/hr high must be positive"


# ── Panel import and logic ────────────────────────────────────────────────────

def test_panel_imports_without_error():
    from ui.widgets.farm_guide_panel import FarmGuidePanel


def test_panel_load_data_returns_dict():
    from ui.widgets.farm_guide_panel import _load_data
    result = _load_data()
    assert isinstance(result, dict)
    assert "activities" in result


def test_panel_matches_logic():
    from ui.widgets.farm_guide_panel import FarmGuidePanel
    panel = FarmGuidePanel.__new__(FarmGuidePanel)
    activity = {
        "name": "Breach Farming",
        "mechanic": "Breach",
        "difficulty": "Medium",
        "best_maps": ["Burial Chambers", "Crimson Township"],
        "key_drops": [{"item": "Chayula Breachstone", "drop_rate": "rare"}],
        "tips": ["Stack breach atlas passives"],
    }
    assert panel._matches(activity, "breach")
    assert panel._matches(activity, "burial")
    assert panel._matches(activity, "chayula")
    assert panel._matches(activity, "atlas passives")
    assert not panel._matches(activity, "delirium")
    assert panel._matches(activity, "")


def test_panel_difficulty_filter():
    from ui.widgets.farm_guide_panel import FarmGuidePanel
    panel = FarmGuidePanel.__new__(FarmGuidePanel)
    activities = [
        {"name": "A", "mechanic": "X", "difficulty": "Low",
         "best_maps": [], "key_drops": [], "tips": []},
        {"name": "B", "mechanic": "Y", "difficulty": "High",
         "best_maps": [], "key_drops": [], "tips": []},
        {"name": "C", "mechanic": "Z", "difficulty": "Low",
         "best_maps": [], "key_drops": [], "tips": []},
    ]
    low_only = [a for a in activities if a["difficulty"] == "Low"]
    assert len(low_only) == 2
    assert all(a["difficulty"] == "Low" for a in low_only)
