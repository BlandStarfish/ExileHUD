"""Tests for Breach Domain data integrity."""
import json
import os
import pytest

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "breaches.json")


@pytest.fixture(scope="module")
def data():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def breaches(data):
    return data["breaches"]


def test_data_file_exists():
    assert os.path.exists(DATA_PATH)


def test_has_five_breaches(breaches):
    assert len(breaches) == 5


def test_required_fields(breaches):
    required = {"deity", "element", "splinter", "breachstone", "keystone",
                "keystone_effect", "blessing", "blessing_effect", "notable_uniques", "notes"}
    for b in breaches:
        for field in required:
            assert field in b, f"{b.get('deity')} missing field {field!r}"


def test_unique_deities(breaches):
    deities = [b["deity"] for b in breaches]
    assert len(set(deities)) == len(deities), "Duplicate deity names"


def test_known_deities_present(breaches):
    deities = {b["deity"] for b in breaches}
    for expected in ["Xoph", "Tul", "Esh", "Uul-Netol", "Chayula"]:
        assert expected in deities, f"{expected} not found in breaches"


def test_elements_are_valid(breaches):
    valid_elements = {"Fire", "Cold", "Lightning", "Physical", "Chaos"}
    for b in breaches:
        assert b["element"] in valid_elements, \
            f"{b['deity']} has unknown element {b['element']!r}"


def test_splinter_names_contain_deity(breaches):
    for b in breaches:
        assert b["deity"] in b["splinter"], \
            f"{b['deity']}: splinter name should contain deity name"


def test_breachstone_names_contain_deity(breaches):
    for b in breaches:
        assert b["deity"] in b["breachstone"], \
            f"{b['deity']}: breachstone name should contain deity name"


def test_notable_uniques_are_lists(breaches):
    for b in breaches:
        assert isinstance(b["notable_uniques"], list), \
            f"{b['deity']}: notable_uniques must be a list"
        assert len(b["notable_uniques"]) >= 1, \
            f"{b['deity']}: notable_uniques must have at least one entry"


def test_xoph_is_fire(breaches):
    xoph = next(b for b in breaches if b["deity"] == "Xoph")
    assert xoph["element"] == "Fire"


def test_chayula_is_chaos(breaches):
    chayula = next(b for b in breaches if b["deity"] == "Chayula")
    assert chayula["element"] == "Chaos"


def test_breachstone_tiers_present(data):
    tiers = data.get("breachstone_tiers", [])
    assert len(tiers) == 5
    assert tiers[0] == "Normal"
    assert tiers[-1] == "Flawless"


def test_all_keystone_effects_nonempty(breaches):
    for b in breaches:
        assert b["keystone_effect"].strip(), f"{b['deity']}: keystone_effect is empty"


def test_all_blessing_effects_nonempty(breaches):
    for b in breaches:
        assert b["blessing_effect"].strip(), f"{b['deity']}: blessing_effect is empty"
