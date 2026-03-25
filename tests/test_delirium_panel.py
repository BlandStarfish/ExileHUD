"""Tests for Delirium Reward Types data integrity."""
import json
import os
import pytest

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "delirium_rewards.json")


@pytest.fixture(scope="module")
def data():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def reward_types(data):
    return data["reward_types"]


def test_data_file_exists():
    assert os.path.exists(DATA_PATH)


def test_has_reward_types(reward_types):
    assert len(reward_types) >= 8, "Expected at least 8 reward types"


def test_required_fields(reward_types):
    required = {"name", "description", "high_value_drops", "best_for", "notes"}
    for rt in reward_types:
        for field in required:
            assert field in rt, f"Reward type {rt.get('name')} missing field {field!r}"


def test_unique_names(reward_types):
    names = [rt["name"] for rt in reward_types]
    assert len(set(names)) == len(names), "Duplicate reward type names"


def test_known_types_present(reward_types):
    names = {rt["name"] for rt in reward_types}
    for expected in ["Currency", "Maps", "Scarabs", "Gems", "Fossils"]:
        assert expected in names, f"Expected reward type {expected!r} not found"


def test_all_descriptions_nonempty(reward_types):
    for rt in reward_types:
        assert rt["description"].strip(), f"{rt['name']}: description is empty"


def test_all_high_value_drops_nonempty(reward_types):
    for rt in reward_types:
        assert rt["high_value_drops"].strip(), f"{rt['name']}: high_value_drops is empty"


def test_mechanic_note_present(data):
    assert "mechanic_note" in data
    assert data["mechanic_note"].strip()


def test_simulacrum_note_present(data):
    assert "simulacrum_note" in data
    assert data["simulacrum_note"].strip()


def test_currency_type_mentions_chaos(reward_types):
    currency = next(rt for rt in reward_types if rt["name"] == "Currency")
    assert "chaos" in currency["high_value_drops"].lower() or \
           "Chaos" in currency["high_value_drops"]


def test_harbinger_type_mentions_shards(reward_types):
    harbinger = next((rt for rt in reward_types if rt["name"] == "Harbinger"), None)
    if harbinger:
        assert "shard" in harbinger["description"].lower() or \
               "shard" in harbinger["high_value_drops"].lower()
