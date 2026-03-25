"""Tests for Currency Quick Reference data integrity."""
import json
import os
import pytest

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "currency_reference.json")

VALID_CATEGORIES = {"Basic", "Crafting", "Trade", "Sockets", "Maps", "Unique", "Flasks", "Pantheon"}


@pytest.fixture(scope="module")
def currencies():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)["currencies"]


def test_data_file_exists():
    assert os.path.exists(DATA_PATH)


def test_has_currencies(currencies):
    assert len(currencies) >= 15, "Expected at least 15 currency entries"


def test_required_fields(currencies):
    required = {"name", "short", "category", "effect", "primary_use", "notes"}
    for c in currencies:
        for field in required:
            assert field in c, f"{c.get('name')} missing field {field!r}"


def test_unique_names(currencies):
    names = [c["name"] for c in currencies]
    assert len(set(names)) == len(names), "Duplicate currency names"


def test_categories_are_valid(currencies):
    for c in currencies:
        assert c["category"] in VALID_CATEGORIES, \
            f"{c['name']}: invalid category {c['category']!r}"


def test_known_currencies_present(currencies):
    names = {c["name"] for c in currencies}
    for expected in [
        "Chaos Orb", "Divine Orb", "Exalted Orb",
        "Vaal Orb", "Orb of Alteration", "Orb of Fusing",
        "Mirror of Kalandra",
    ]:
        assert expected in names, f"Expected currency {expected!r} not found"


def test_all_effects_nonempty(currencies):
    for c in currencies:
        assert c["effect"].strip(), f"{c['name']}: effect is empty"


def test_all_primary_uses_nonempty(currencies):
    for c in currencies:
        assert c["primary_use"].strip(), f"{c['name']}: primary_use is empty"


def test_chaos_orb_is_trade_category(currencies):
    chaos = next(c for c in currencies if c["name"] == "Chaos Orb")
    assert chaos["category"] == "Trade"


def test_vaal_orb_mentions_corruption(currencies):
    vaal = next(c for c in currencies if c["name"] == "Vaal Orb")
    assert "corrupt" in vaal["effect"].lower()


def test_fusing_orb_is_sockets_category(currencies):
    fuse = next(c for c in currencies if c["name"] == "Orb of Fusing")
    assert fuse["category"] == "Sockets"


def test_mirror_is_trade_category(currencies):
    mirror = next(c for c in currencies if c["name"] == "Mirror of Kalandra")
    assert mirror["category"] == "Trade"


def test_short_names_nonempty(currencies):
    for c in currencies:
        assert c["short"].strip(), f"{c['name']}: short name is empty"
