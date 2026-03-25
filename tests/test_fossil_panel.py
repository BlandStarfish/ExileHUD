"""Tests for Delve Fossil data integrity."""
import json
import os
import pytest

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "fossils.json")

VALID_RARITIES = {"common", "uncommon", "rare", "very_rare"}


@pytest.fixture(scope="module")
def data():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def fossils(data):
    return data["fossils"]


def test_data_file_exists():
    assert os.path.exists(DATA_PATH)


def test_has_fossils(fossils):
    assert len(fossils) >= 15, "Expected at least 15 fossils"


def test_required_fields(fossils):
    required = {"name", "rarity", "min_depth", "adds_tags", "blocks_tags",
                "effect", "crafting_use"}
    for f in fossils:
        for field in required:
            assert field in f, f"Fossil {f.get('name', '?')} missing field {field!r}"


def test_rarities_valid(fossils):
    for f in fossils:
        assert f["rarity"] in VALID_RARITIES, \
            f"{f['name']}: unknown rarity {f['rarity']!r}"


def test_adds_tags_are_lists(fossils):
    for f in fossils:
        assert isinstance(f["adds_tags"], list), \
            f"{f['name']}: adds_tags must be a list"


def test_blocks_tags_are_lists(fossils):
    for f in fossils:
        assert isinstance(f["blocks_tags"], list), \
            f"{f['name']}: blocks_tags must be a list"


def test_min_depth_is_nonnegative(fossils):
    for f in fossils:
        assert isinstance(f["min_depth"], int) and f["min_depth"] >= 0, \
            f"{f['name']}: min_depth must be a non-negative integer"


def test_effect_nonempty(fossils):
    for f in fossils:
        assert f["effect"].strip(), f"{f['name']}: effect is empty"


def test_crafting_use_nonempty(fossils):
    for f in fossils:
        assert f["crafting_use"].strip(), f"{f['name']}: crafting_use is empty"


def test_unique_fossil_names(fossils):
    names = [f["name"] for f in fossils]
    assert len(set(names)) == len(names), "Duplicate fossil names"


def test_pristine_fossil_present(fossils):
    names = {f["name"] for f in fossils}
    assert "Pristine Fossil" in names


def test_fractured_fossil_present(fossils):
    names = {f["name"] for f in fossils}
    assert "Fractured Fossil" in names


def test_pristine_blocks_attack(fossils):
    pristine = next(f for f in fossils if f["name"] == "Pristine Fossil")
    assert "attack" in pristine["blocks_tags"]


def test_rare_fossils_have_higher_depth(fossils):
    """Rare and very_rare fossils should require deeper delving than common ones."""
    for f in fossils:
        if f["rarity"] in ("rare", "very_rare"):
            assert f["min_depth"] >= 100, \
                f"{f['name']}: rare fossil should have min_depth >= 100"


def test_resonators_present(data):
    res = data.get("resonators", {})
    assert len(res) >= 4, "Expected 4 resonator types"
    for name, info in res.items():
        assert "slots" in info, f"Resonator {name} missing 'slots'"
        assert isinstance(info["slots"], int) and 1 <= info["slots"] <= 4


def test_tips_present(data):
    tips = data.get("tips", [])
    assert len(tips) >= 3
    for tip in tips:
        assert isinstance(tip, str) and tip.strip()
