"""Tests for Cluster Jewel Reference data and panel logic."""

import json
import os
import pytest

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "cluster_jewels.json")


@pytest.fixture(scope="module")
def data():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def jewels(data):
    return data["jewels"]


# ── Data integrity ───────────────────────────────────────────────────────────

def test_data_file_exists():
    assert os.path.exists(DATA_PATH)


def test_has_required_top_level_keys(data):
    for key in ("jewels", "how_it_works", "tips", "categories"):
        assert key in data, f"Missing top-level key: {key}"


def test_jewels_non_empty(jewels):
    assert len(jewels) >= 15, f"Expected at least 15 jewels, got {len(jewels)}"


def test_all_jewels_have_required_fields(jewels):
    required = ("name", "size", "enchant", "key_notables", "notable_count",
                "optimal_passive_count", "best_for", "value_tier", "notes")
    for jewel in jewels:
        for field in required:
            assert field in jewel, f"Jewel '{jewel.get('name')}' missing field: {field}"


def test_valid_sizes(jewels, data):
    valid = set(data.get("categories", []))
    for jewel in jewels:
        assert jewel["size"] in valid, \
            f"Jewel '{jewel['name']}' has invalid size: '{jewel['size']}'"


def test_valid_value_tiers(jewels):
    valid = {"Extremely High", "High", "Medium", "Low"}
    for jewel in jewels:
        assert jewel["value_tier"] in valid, \
            f"Jewel '{jewel['name']}' has invalid value_tier: '{jewel['value_tier']}'"


def test_key_notables_is_list(jewels):
    for jewel in jewels:
        assert isinstance(jewel["key_notables"], list), \
            f"Jewel '{jewel['name']}' key_notables must be a list"


def test_best_for_is_list(jewels):
    for jewel in jewels:
        assert isinstance(jewel["best_for"], list), \
            f"Jewel '{jewel['name']}' best_for must be a list"


def test_jewel_names_unique(jewels):
    names = [j["name"] for j in jewels]
    assert len(names) == len(set(names)), "Duplicate jewel names found"


def test_all_three_sizes_represented(jewels):
    sizes = {j["size"] for j in jewels}
    assert sizes == {"Large", "Medium", "Small"}, \
        f"Not all sizes represented: {sizes}"


def test_large_jewels_present(jewels):
    large = [j for j in jewels if j["size"] == "Large"]
    assert len(large) >= 5, f"Expected at least 5 large jewels, got {len(large)}"


def test_medium_jewels_present(jewels):
    medium = [j for j in jewels if j["size"] == "Medium"]
    assert len(medium) >= 4, f"Expected at least 4 medium jewels, got {len(medium)}"


def test_small_jewels_present(jewels):
    small = [j for j in jewels if j["size"] == "Small"]
    assert len(small) >= 4, f"Expected at least 4 small jewels, got {len(small)}"


def test_voices_present(jewels):
    names = [j["name"] for j in jewels]
    assert "Voices" in names, "Voices cluster jewel should be in the data"


def test_voices_is_extremely_high_value(jewels):
    voices = next(j for j in jewels if j["name"] == "Voices")
    assert voices["value_tier"] == "Extremely High"


def test_tips_is_list(data):
    assert isinstance(data.get("tips", []), list)


def test_categories_correct(data):
    cats = data.get("categories", [])
    assert "Large" in cats and "Medium" in cats and "Small" in cats


# ── Panel import ─────────────────────────────────────────────────────────────

def test_panel_imports_without_error():
    from ui.widgets.cluster_jewels_panel import ClusterJewelsPanel


def test_panel_load_data_returns_dict():
    from ui.widgets.cluster_jewels_panel import _load_data
    result = _load_data()
    assert isinstance(result, dict)
    assert "jewels" in result


def test_panel_matches_logic():
    from ui.widgets.cluster_jewels_panel import ClusterJewelsPanel
    panel = ClusterJewelsPanel.__new__(ClusterJewelsPanel)
    jewel = {
        "name": "Voices",
        "size": "Large",
        "enchant": "Adds 2 Passive Skills to Jewel Sockets",
        "key_notables": [],
        "notable_count": "0 notables",
        "optimal_passive_count": "2",
        "best_for": ["Aura stacking"],
        "value_tier": "Extremely High",
        "notes": "Core for aura stacking.",
    }
    assert panel._matches(jewel, "voices")
    assert panel._matches(jewel, "aura")
    assert panel._matches(jewel, "large")
    assert not panel._matches(jewel, "bleed")
    assert panel._matches(jewel, "")
