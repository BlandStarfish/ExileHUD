"""Tests for Incursion Temple Room data integrity."""
import json
import os
import pytest

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "incursion_rooms.json")

VALID_PRIORITIES  = {"must_have", "high", "medium", "low"}
VALID_CATEGORIES  = {"Boss", "Crafting", "Gems", "Currency", "Breach", "Maps",
                     "Items", "Strongboxes", "Flask", "Monsters", "Defenses", "Passage"}


@pytest.fixture(scope="module")
def data():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def rooms(data):
    return data["rooms"]


def test_data_file_exists():
    assert os.path.exists(DATA_PATH)


def test_has_rooms(rooms):
    assert len(rooms) >= 10, "Expected at least 10 room chains"


def test_required_fields(rooms):
    required = {"t1", "t2", "t3", "category", "priority", "drops"}
    for r in rooms:
        for field in required:
            assert field in r, f"Room {r.get('t3', '?')} missing field {field!r}"


def test_all_priorities_valid(rooms):
    for r in rooms:
        assert r["priority"] in VALID_PRIORITIES, \
            f"{r.get('t3')}: unknown priority {r['priority']!r}"


def test_all_categories_valid(rooms):
    for r in rooms:
        assert r["category"] in VALID_CATEGORIES, \
            f"{r.get('t3')}: unknown category {r['category']!r}"


def test_t3_names_nonempty(rooms):
    for r in rooms:
        assert r["t3"].strip(), f"Room has empty t3 name"


def test_drops_nonempty(rooms):
    for r in rooms:
        assert r["drops"].strip(), f"{r.get('t3')}: drops is empty"


def test_unique_t3_names(rooms):
    names = [r["t3"] for r in rooms]
    assert len(set(names)) == len(names), "Duplicate T3 room names"


def test_apex_of_ascension_present(rooms):
    t3_names = {r["t3"] for r in rooms}
    assert "Apex of Ascension" in t3_names


def test_locus_of_corruption_present(rooms):
    t3_names = {r["t3"] for r in rooms}
    assert "Locus of Corruption" in t3_names


def test_locus_must_have_priority(rooms):
    locus = next((r for r in rooms if r["t3"] == "Locus of Corruption"), None)
    assert locus is not None
    assert locus["priority"] == "must_have"


def test_tips_present(data):
    tips = data.get("tips", [])
    assert len(tips) >= 3, "Expected at least 3 tips"
    for tip in tips:
        assert isinstance(tip, str) and tip.strip()


def test_chain_length(rooms):
    """Each room chain must have non-empty T1, T2, T3."""
    for r in rooms:
        assert r["t1"].strip(), f"Room {r.get('t3')}: empty t1"
        assert r["t2"].strip(), f"Room {r.get('t3')}: empty t2"
        assert r["t3"].strip(), f"Room {r.get('t3')}: empty t3"
