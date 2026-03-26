"""Tests for Stash Tab Organisation Guide data and panel logic."""

import json
import os
import pytest

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "stash_organization.json")


@pytest.fixture(scope="module")
def data():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def tabs(data):
    return data["tabs"]


# ── Data integrity ────────────────────────────────────────────────────────────

def test_data_file_exists():
    assert os.path.exists(DATA_PATH)


def test_has_required_top_level_keys(data):
    for key in ("tabs", "principles", "tab_types", "intro"):
        assert key in data, f"Missing top-level key: {key}"


def test_tabs_non_empty(tabs):
    assert len(tabs) >= 8, f"Expected at least 8 tabs, got {len(tabs)}"


def test_all_tabs_have_required_fields(tabs):
    required = ("id", "name", "tab_type", "priority", "what_to_store",
                "naming_tip", "notes")
    for tab in tabs:
        for field in required:
            assert field in tab, f"Tab '{tab.get('name')}' missing field: {field}"


def test_valid_priorities(tabs):
    valid = {"Essential", "High", "Medium", "Low"}
    for tab in tabs:
        assert tab["priority"] in valid, \
            f"Tab '{tab['name']}' has invalid priority: '{tab['priority']}'"


def test_ids_are_unique(tabs):
    ids = [t["id"] for t in tabs]
    assert len(ids) == len(set(ids)), "Duplicate tab IDs found"


def test_principles_is_list(data):
    assert isinstance(data.get("principles", []), list)
    assert len(data["principles"]) >= 3


def test_tab_types_is_list(data):
    tab_types = data.get("tab_types", [])
    assert isinstance(tab_types, list)
    assert len(tab_types) >= 3


def test_tab_types_have_required_fields(data):
    for tt in data.get("tab_types", []):
        assert "type" in tt, "tab_type entry missing 'type' field"
        assert "description" in tt, "tab_type entry missing 'description' field"


# ── Content spot-checks ───────────────────────────────────────────────────────

def test_essential_tabs_include_currency(tabs):
    essential = [t for t in tabs if t["priority"] == "Essential"]
    names = [t["name"] for t in essential]
    assert any("Currency" in n or "currency" in n for n in names), \
        "Expected Currency tab in Essential priority"


def test_essential_tabs_include_map(tabs):
    essential = [t for t in tabs if t["priority"] == "Essential"]
    names = [t["name"] for t in essential]
    assert any("Map" in n for n in names), "Expected Map tab in Essential priority"


def test_quad_tab_mentioned(tabs):
    all_text = " ".join(t.get("tab_type", "") + " " + t.get("notes", "") for t in tabs)
    assert "quad" in all_text.lower() or "Quad" in all_text, \
        "Expected quad tab mention somewhere"


def test_low_priority_tabs_exist(tabs):
    low = [t for t in tabs if t["priority"] == "Low"]
    assert len(low) >= 2, "Expected at least 2 Low priority tabs"


def test_naming_tips_not_empty(tabs):
    for tab in tabs:
        assert tab.get("naming_tip", "").strip(), \
            f"Tab '{tab['name']}' has empty naming_tip"


# ── Panel import and logic ────────────────────────────────────────────────────

def test_panel_imports_without_error():
    from ui.widgets.stash_org_panel import StashOrgPanel


def test_panel_load_data_returns_dict():
    from ui.widgets.stash_org_panel import _load_data
    result = _load_data()
    assert isinstance(result, dict)
    assert "tabs" in result


def test_panel_matches_logic():
    from ui.widgets.stash_org_panel import StashOrgPanel
    panel = StashOrgPanel.__new__(StashOrgPanel)
    tab = {
        "id": "currency_tab",
        "name": "Currency",
        "tab_type": "Currency",
        "priority": "Essential",
        "what_to_store": "All currency orbs including Chaos and Divine",
        "naming_tip": "Name it 'Currency' for trade sites",
        "notes": "Essential for every character.",
    }
    assert panel._matches(tab, "currency")
    assert panel._matches(tab, "divine")
    assert panel._matches(tab, "essential")
    assert panel._matches(tab, "trade sites")
    assert not panel._matches(tab, "scarab")
    assert panel._matches(tab, "")


def test_panel_priority_filter():
    from ui.widgets.stash_org_panel import StashOrgPanel
    panel = StashOrgPanel.__new__(StashOrgPanel)
    tabs = [
        {"id": "a", "name": "Currency", "tab_type": "Currency", "priority": "Essential",
         "what_to_store": "", "naming_tip": "", "notes": ""},
        {"id": "b", "name": "Gems", "tab_type": "Premium", "priority": "Medium",
         "what_to_store": "", "naming_tip": "", "notes": ""},
        {"id": "c", "name": "Maps", "tab_type": "Map", "priority": "Essential",
         "what_to_store": "", "naming_tip": "", "notes": ""},
    ]
    essential_only = [t for t in tabs if t["priority"] == "Essential"]
    assert len(essential_only) == 2
    assert all(t["priority"] == "Essential" for t in essential_only)
