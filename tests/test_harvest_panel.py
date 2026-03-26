"""Tests for Harvest Craft Reference data integrity."""
import json
import os
import pytest

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "harvest_crafts.json")

VALID_VALUES = {"Extremely High", "Very High", "High", "Medium", "Low", ""}
VALID_CATEGORIES = {"Reforge", "Augment", "Remove/Add", "Set Numeric Value", "Split / Duplicate", "Enchant"}


@pytest.fixture(scope="module")
def data():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def categories(data):
    return data["craft_categories"]


@pytest.fixture(scope="module")
def all_crafts(categories):
    crafts = []
    for cat in categories:
        for craft in cat.get("crafts", []):
            crafts.append((cat["category"], craft))
    return crafts


def test_data_file_exists():
    assert os.path.exists(DATA_PATH)


def test_has_categories(categories):
    assert len(categories) >= 4, "Expected at least 4 craft categories"


def test_category_names_valid(categories):
    for cat in categories:
        assert cat["category"] in VALID_CATEGORIES, \
            f"Unknown category: {cat['category']!r}"


def test_each_category_has_crafts(categories):
    for cat in categories:
        assert len(cat.get("crafts", [])) >= 1, \
            f"Category {cat['category']!r} has no crafts"


def test_required_craft_fields(all_crafts):
    for cat_name, craft in all_crafts:
        assert "name" in craft, f"[{cat_name}] craft missing 'name'"
        assert "effect" in craft, f"[{cat_name}] {craft.get('name', '?')} missing 'effect'"


def test_craft_names_nonempty(all_crafts):
    for _, craft in all_crafts:
        assert craft["name"].strip(), "Craft name is empty"


def test_craft_effects_nonempty(all_crafts):
    for cat_name, craft in all_crafts:
        assert craft["effect"].strip(), \
            f"[{cat_name}] {craft['name']}: effect is empty"


def test_value_fields_valid(all_crafts):
    for cat_name, craft in all_crafts:
        val = craft.get("value", "")
        assert val in VALID_VALUES, \
            f"[{cat_name}] {craft['name']}: unknown value tier {val!r}"


def test_reforge_keeping_prefixes_present(all_crafts):
    names = {craft["name"] for _, craft in all_crafts}
    assert "Reforge Keeping Prefixes" in names


def test_reforge_keeping_suffixes_present(all_crafts):
    names = {craft["name"] for _, craft in all_crafts}
    assert "Reforge Keeping Suffixes" in names


def test_split_craft_present(all_crafts):
    names = {craft["name"] for _, craft in all_crafts}
    assert "Split" in names


def test_duplicate_craft_is_extremely_high(all_crafts):
    for _, craft in all_crafts:
        if craft["name"] == "Duplicate":
            assert craft["value"] == "Extremely High"
            return
    pytest.fail("Duplicate craft not found")


def test_reforge_keeping_prefixes_very_high(all_crafts):
    for _, craft in all_crafts:
        if craft["name"] == "Reforge Keeping Prefixes":
            assert craft["value"] == "Very High"
            return
    pytest.fail("Reforge Keeping Prefixes craft not found")


def test_lifeforce_types_present(data):
    lf = data.get("lifeforce_types", {})
    assert len(lf) >= 4
    assert "Vivid" in lf
    assert "Sacred" in lf


def test_tips_present(data):
    tips = data.get("tips", [])
    assert len(tips) >= 4
    for tip in tips:
        assert isinstance(tip, str) and tip.strip()


def test_total_crafts_count(all_crafts):
    assert len(all_crafts) >= 25, "Expected at least 25 harvest crafts"
