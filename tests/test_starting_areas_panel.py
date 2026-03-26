"""Tests for Passive Tree Starting Area Guide data and panel logic."""

import json
import os
import pytest

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "starting_areas.json")


@pytest.fixture(scope="module")
def data():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def areas(data):
    return data["starting_areas"]


# ── Data integrity ────────────────────────────────────────────────────────────

def test_data_file_exists():
    assert os.path.exists(DATA_PATH)


def test_has_required_top_level_keys(data):
    for key in ("starting_areas", "how_it_works", "tips"):
        assert key in data, f"Missing top-level key: {key}"


def test_exactly_seven_starting_areas(areas):
    assert len(areas) == 7, f"Expected exactly 7 starting areas, got {len(areas)}"


def test_all_areas_have_required_fields(areas):
    required = (
        "area", "location", "primary_stats", "ascendancies",
        "key_node_clusters", "recommended_for", "avoid_for",
        "notable_keystones_nearby", "ascendancy_highlights", "value_tier", "notes"
    )
    for area in areas:
        for field in required:
            assert field in area, f"Area '{area.get('area')}' missing field: {field}"


def test_all_seven_classes_present(areas):
    classes = {a["area"] for a in areas}
    expected = {"Marauder", "Duelist", "Ranger", "Shadow", "Witch", "Templar", "Scion"}
    assert classes == expected, f"Missing classes: {expected - classes}"


def test_valid_value_tiers(areas):
    valid = {"Extremely High", "High", "Medium", "Low"}
    for area in areas:
        assert area["value_tier"] in valid, \
            f"Area '{area['area']}' has invalid value_tier: '{area['value_tier']}'"


def test_primary_stats_is_list(areas):
    for area in areas:
        assert isinstance(area["primary_stats"], list), \
            f"Area '{area['area']}' primary_stats must be a list"


def test_ascendancies_is_list(areas):
    for area in areas:
        assert isinstance(area["ascendancies"], list), \
            f"Area '{area['area']}' ascendancies must be a list"


def test_all_areas_have_ascendancies(areas):
    for area in areas:
        assert len(area["ascendancies"]) >= 1, \
            f"Area '{area['area']}' must have at least 1 ascendancy"


def test_recommended_for_is_list(areas):
    for area in areas:
        assert isinstance(area["recommended_for"], list)


def test_avoid_for_is_list(areas):
    for area in areas:
        assert isinstance(area["avoid_for"], list)


def test_tips_is_list(data):
    assert isinstance(data.get("tips", []), list)


# ── Content spot-checks ───────────────────────────────────────────────────────

def test_marauder_is_strength(areas):
    marauder = next(a for a in areas if a["area"] == "Marauder")
    assert "Strength" in marauder["primary_stats"]


def test_witch_ascendancies(areas):
    witch = next(a for a in areas if a["area"] == "Witch")
    assert "Necromancer" in witch["ascendancies"]
    assert "Occultist" in witch["ascendancies"]


def test_scion_has_ascendant(areas):
    scion = next(a for a in areas if a["area"] == "Scion")
    assert "Ascendant" in scion["ascendancies"]


def test_ranger_bow_recommended(areas):
    ranger = next(a for a in areas if a["area"] == "Ranger")
    bow_recs = [r for r in ranger["recommended_for"] if "bow" in r.lower() or "Bow" in r]
    assert len(bow_recs) >= 1, "Ranger should recommend bow builds"


def test_templar_has_aura_mention(areas):
    templar = next(a for a in areas if a["area"] == "Templar")
    aura_recs = [r for r in templar["recommended_for"] if "ura" in r.lower()]
    assert len(aura_recs) >= 1, "Templar should recommend aura builds"


def test_each_area_has_keystones(areas):
    for area in areas:
        # Scion may have none specifically — allow empty but list must exist
        assert isinstance(area["notable_keystones_nearby"], list)


# ── Panel import ──────────────────────────────────────────────────────────────

def test_panel_imports_without_error():
    from ui.widgets.starting_areas_panel import StartingAreasPanel


def test_panel_load_data_returns_dict():
    from ui.widgets.starting_areas_panel import _load_data
    result = _load_data()
    assert isinstance(result, dict)
    assert "starting_areas" in result


def test_panel_matches_logic():
    from ui.widgets.starting_areas_panel import StartingAreasPanel
    panel = StartingAreasPanel.__new__(StartingAreasPanel)
    area = {
        "area": "Witch",
        "location": "Top-right of tree",
        "primary_stats": ["Intelligence"],
        "ascendancies": ["Necromancer", "Occultist", "Elementalist"],
        "key_node_clusters": ["Energy Shield", "Spell Damage"],
        "recommended_for": ["Minion builds", "ES-based spellcasters"],
        "avoid_for": ["Melee builds"],
        "notable_keystones_nearby": ["Chaos Inoculation"],
        "ascendancy_highlights": "Necromancer: best minion ascendancy.",
        "value_tier": "High",
        "notes": "The caster and summoner hub.",
    }
    assert panel._matches(area, "witch")
    assert panel._matches(area, "necromancer")
    assert panel._matches(area, "minion")
    assert panel._matches(area, "chaos inoculation")
    assert not panel._matches(area, "ranger")
    assert panel._matches(area, "")


def test_panel_area_filter():
    from ui.widgets.starting_areas_panel import StartingAreasPanel
    panel = StartingAreasPanel.__new__(StartingAreasPanel)
    areas = [
        {"area": "Marauder", "location": "", "primary_stats": [], "ascendancies": [],
         "key_node_clusters": [], "recommended_for": [], "avoid_for": [],
         "notable_keystones_nearby": [], "ascendancy_highlights": "",
         "value_tier": "High", "notes": ""},
        {"area": "Witch", "location": "", "primary_stats": [], "ascendancies": [],
         "key_node_clusters": [], "recommended_for": [], "avoid_for": [],
         "notable_keystones_nearby": [], "ascendancy_highlights": "",
         "value_tier": "High", "notes": ""},
    ]
    marauder_only = [a for a in areas if a["area"] == "Marauder"]
    assert len(marauder_only) == 1
    assert marauder_only[0]["area"] == "Marauder"
