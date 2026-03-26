"""Tests for Unique Flask Reference data and panel logic."""

import json
import os
import pytest

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "unique_flasks.json")


@pytest.fixture(scope="module")
def data():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def flasks(data):
    return data["flasks"]


# ── Data integrity ─────────────────────────────────────────────────────────────

def test_data_file_exists():
    assert os.path.exists(DATA_PATH)


def test_has_required_top_level_keys(data):
    for key in ("flasks", "how_it_works", "categories", "tips"):
        assert key in data, f"Missing top-level key: {key}"


def test_flasks_non_empty(flasks):
    assert len(flasks) >= 10, "Expected at least 10 unique flasks"


def test_all_flasks_have_required_fields(flasks):
    required = {"name", "base", "category", "effect", "best_builds", "when_to_use", "value_tier"}
    for f in flasks:
        missing = required - set(f.keys())
        assert not missing, f"Flask '{f.get('name')}' missing fields: {missing}"


def test_all_categories_valid(flasks, data):
    valid_cats = set(data["categories"])
    for f in flasks:
        assert f["category"] in valid_cats, \
            f"Flask '{f['name']}' has invalid category: {f['category']}"


def test_all_value_tiers_valid(flasks):
    valid_tiers = {"Very High", "High", "Medium", "Low"}
    for f in flasks:
        assert f["value_tier"] in valid_tiers, \
            f"Flask '{f['name']}' has invalid value_tier: {f['value_tier']}"


def test_flask_names_unique(flasks):
    names = [f["name"] for f in flasks]
    assert len(names) == len(set(names)), "Duplicate flask names found"


def test_best_builds_is_list(flasks):
    for f in flasks:
        assert isinstance(f["best_builds"], list), \
            f"Flask '{f['name']}' best_builds is not a list"


def test_categories_cover_dps_defense_utility(flasks):
    cats = {f["category"] for f in flasks}
    assert "DPS" in cats
    assert "Defense" in cats
    assert "Utility" in cats


def test_tips_non_empty(data):
    assert len(data["tips"]) >= 3, "Expected at least 3 tips"


# ── Spot checks ────────────────────────────────────────────────────────────────

def test_atziris_promise_exists(flasks):
    names = {f["name"] for f in flasks}
    assert "Atziri's Promise" in names


def test_taste_of_hate_category(flasks):
    toh = next((f for f in flasks if f["name"] == "Taste of Hate"), None)
    assert toh is not None, "Taste of Hate not found"
    assert toh["category"] == "Defense"


def test_dying_sun_dps(flasks):
    ds = next((f for f in flasks if f["name"] == "Dying Sun"), None)
    assert ds is not None, "Dying Sun not found"
    assert ds["category"] == "DPS"


def test_progenesis_defense(flasks):
    prog = next((f for f in flasks if f["name"] == "Progenesis"), None)
    assert prog is not None, "Progenesis not found"
    assert prog["category"] == "Defense"


def test_bottled_faith_value_tier(flasks):
    bf = next((f for f in flasks if f["name"] == "Bottled Faith"), None)
    assert bf is not None, "Bottled Faith not found"
    assert bf["value_tier"] in ("Very High", "High")


def test_rumi_concoction_block(flasks):
    rumi = next((f for f in flasks if "Rumi" in f["name"]), None)
    assert rumi is not None, "Rumi's Concoction not found"
    assert "block" in rumi["effect"].lower() or "block" in rumi["notes"].lower()


def test_all_effects_non_empty(flasks):
    for f in flasks:
        assert f["effect"].strip(), f"Flask '{f['name']}' has empty effect"


def test_all_when_to_use_non_empty(flasks):
    for f in flasks:
        assert f["when_to_use"].strip(), f"Flask '{f['name']}' has empty when_to_use"
