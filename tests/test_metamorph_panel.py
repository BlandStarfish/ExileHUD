"""Tests for Metamorph Catalyst data integrity."""
import json
import os
import pytest

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "metamorph_catalysts.json")


@pytest.fixture(scope="module")
def data():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def catalysts(data):
    return data["catalysts"]


def test_data_file_exists():
    assert os.path.exists(DATA_PATH)


def test_has_catalysts(catalysts):
    assert len(catalysts) >= 10, "Expected at least 10 catalyst types"


def test_required_fields(catalysts):
    required = {"name", "improves", "examples", "best_for", "organ_source"}
    for c in catalysts:
        for field in required:
            assert field in c, f"Catalyst {c.get('name', '?')} missing field {field!r}"


def test_name_nonempty(catalysts):
    for c in catalysts:
        assert c["name"].strip(), "Catalyst name is empty"


def test_improves_nonempty(catalysts):
    for c in catalysts:
        assert c["improves"].strip(), f"{c['name']}: improves is empty"


def test_examples_nonempty(catalysts):
    for c in catalysts:
        assert c["examples"].strip(), f"{c['name']}: examples is empty"


def test_unique_catalyst_names(catalysts):
    names = [c["name"] for c in catalysts]
    assert len(set(names)) == len(names), "Duplicate catalyst names"


def test_abrasive_catalyst_present(catalysts):
    names = {c["name"] for c in catalysts}
    assert "Abrasive Catalyst" in names


def test_prismatic_catalyst_present(catalysts):
    names = {c["name"] for c in catalysts}
    assert "Prismatic Catalyst" in names


def test_prismatic_improves_resistances(catalysts):
    prismatic = next(c for c in catalysts if c["name"] == "Prismatic Catalyst")
    assert "resistance" in prismatic["improves"].lower() or "res" in prismatic["improves"].lower()


def test_fertile_catalyst_improves_life(catalysts):
    fertile = next(c for c in catalysts if c["name"] == "Fertile Catalyst")
    assert "life" in fertile["improves"].lower()


def test_tips_present(data):
    tips = data.get("tips", [])
    assert len(tips) >= 3
    for tip in tips:
        assert isinstance(tip, str) and tip.strip()


def test_applicable_items_present(data):
    items = data.get("applicable_items", [])
    assert len(items) >= 3, "Expected at least 3 applicable item types (rings, amulets, belts)"
    lower = [x.lower() for x in items]
    assert any("ring" in x for x in lower)
    assert any("belt" in x for x in lower)


def test_how_it_works_present(data):
    assert data.get("how_it_works", "").strip()
