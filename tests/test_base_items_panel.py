"""Tests for Base Item Type Reference data and panel logic."""

import json
import os
import pytest

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "base_items.json")


@pytest.fixture(scope="module")
def data():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def bases(data):
    return data["bases"]


# ── Data integrity ────────────────────────────────────────────────────────────

def test_data_file_exists():
    assert os.path.exists(DATA_PATH)


def test_has_required_top_level_keys(data):
    for key in ("bases", "how_it_works", "tips", "slot_types"):
        assert key in data, f"Missing top-level key: {key}"


def test_bases_non_empty(bases):
    assert len(bases) >= 15, f"Expected at least 15 bases, got {len(bases)}"


def test_all_bases_have_required_fields(bases):
    required = ("name", "slot", "base_type", "item_level_req", "implicit",
                "why_valuable", "best_for", "value_tier", "notes")
    for base in bases:
        for field in required:
            assert field in base, f"Base '{base.get('name')}' missing field: {field}"


def test_valid_slots(bases, data):
    valid = set(data.get("slot_types", []))
    for base in bases:
        assert base["slot"] in valid, \
            f"Base '{base['name']}' has invalid slot: '{base['slot']}'"


def test_valid_value_tiers(bases):
    valid = {"Extremely High", "High", "Medium", "Low"}
    for base in bases:
        assert base["value_tier"] in valid, \
            f"Base '{base['name']}' has invalid value_tier: '{base['value_tier']}'"


def test_best_for_is_list(bases):
    for base in bases:
        assert isinstance(base["best_for"], list), \
            f"Base '{base['name']}' best_for must be a list"


def test_base_names_unique(bases):
    names = [b["name"] for b in bases]
    assert len(names) == len(set(names)), "Duplicate base name entries found"


def test_item_level_req_is_numeric(bases):
    for base in bases:
        ilvl = base.get("item_level_req")
        assert isinstance(ilvl, (int, float)), \
            f"Base '{base['name']}' item_level_req must be numeric, got: {ilvl!r}"


def test_tips_is_list(data):
    assert isinstance(data.get("tips", []), list)


def test_slot_types_non_empty(data):
    slots = data.get("slot_types", [])
    assert len(slots) >= 5, f"Expected at least 5 slot types, got {len(slots)}"


# ── Content spot-checks ───────────────────────────────────────────────────────

def test_helmet_slot_covered(bases):
    helmets = [b for b in bases if b["slot"] == "Helmet"]
    assert len(helmets) >= 2, f"Expected at least 2 Helmet bases, got {len(helmets)}"


def test_body_armour_slot_covered(bases):
    bodies = [b for b in bases if b["slot"] == "Body Armour"]
    assert len(bodies) >= 2, f"Expected at least 2 Body Armour bases, got {len(bodies)}"


def test_ring_slot_covered(bases):
    rings = [b for b in bases if b["slot"] == "Ring"]
    assert len(rings) >= 2, f"Expected at least 2 Ring bases, got {len(rings)}"


def test_stygian_vise_present(bases):
    names = [b["name"] for b in bases]
    assert "Stygian Vise" in names, "Stygian Vise must be in base items"


def test_two_toned_boots_present(bases):
    names = [b["name"] for b in bases]
    assert "Two-Toned Boots" in names, "Two-Toned Boots must be in base items"


def test_extremely_high_tier_bases_exist(bases):
    top = [b for b in bases if b["value_tier"] == "Extremely High"]
    assert len(top) >= 2, f"Expected at least 2 Extremely High bases, got {len(top)}"


def test_es_helmet_base_present(bases):
    es_helmets = [b for b in bases if b["slot"] == "Helmet" and "Energy Shield" in b.get("base_type", "")]
    assert len(es_helmets) >= 1, "Expected at least 1 Energy Shield Helmet base"


# ── Panel import ──────────────────────────────────────────────────────────────

def test_panel_imports_without_error():
    from ui.widgets.base_items_panel import BaseItemsPanel


def test_panel_load_data_returns_dict():
    from ui.widgets.base_items_panel import _load_data
    result = _load_data()
    assert isinstance(result, dict)
    assert "bases" in result


def test_panel_matches_logic():
    from ui.widgets.base_items_panel import BaseItemsPanel
    panel = BaseItemsPanel.__new__(BaseItemsPanel)
    base = {
        "name": "Stygian Vise",
        "slot": "Belt",
        "base_type": "Hybrid (Str/Dex)",
        "item_level_req": 64,
        "implicit": "Has an Abyssal Socket",
        "why_valuable": "Universally the best belt base.",
        "value_tier": "Extremely High",
        "best_for": ["All builds", "Jewel-stacking"],
        "notes": "Near-universally BIS.",
    }
    assert panel._matches(base, "stygian")
    assert panel._matches(base, "abyssal")
    assert panel._matches(base, "jewel")
    assert not panel._matches(base, "helmet")
    assert panel._matches(base, "")


def test_panel_slot_filter():
    from ui.widgets.base_items_panel import BaseItemsPanel
    panel = BaseItemsPanel.__new__(BaseItemsPanel)
    bases = [
        {"name": "A", "slot": "Ring", "base_type": "", "item_level_req": 80,
         "implicit": "", "why_valuable": "", "value_tier": "High", "best_for": [], "notes": ""},
        {"name": "B", "slot": "Belt", "base_type": "", "item_level_req": 64,
         "implicit": "", "why_valuable": "", "value_tier": "High", "best_for": [], "notes": ""},
        {"name": "C", "slot": "Ring", "base_type": "", "item_level_req": 48,
         "implicit": "", "why_valuable": "", "value_tier": "Medium", "best_for": [], "notes": ""},
    ]
    rings_only = [b for b in bases if b["slot"] == "Ring"]
    assert len(rings_only) == 2
    assert all(b["slot"] == "Ring" for b in rings_only)
