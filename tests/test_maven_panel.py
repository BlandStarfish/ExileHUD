"""Tests for Maven Invitation data integrity."""
import json
import os
import pytest

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "maven_invitations.json")

VALID_DIFFICULTIES = {"Beginner", "Intermediate", "Advanced", "Endgame (pinnacle)"}

KNOWN_INVITATIONS = {
    "The Formed",
    "The Twisted",
    "The Hidden",
    "The Forgotten",
    "The Elderslayers",
    "The Feared",
}


@pytest.fixture(scope="module")
def data():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def invitations(data):
    return data["invitations"]


def test_data_file_exists():
    assert os.path.exists(DATA_PATH)


def test_has_invitations(invitations):
    assert len(invitations) >= 4, "Expected at least 4 invitations"


def test_required_fields(invitations):
    required = {"name", "difficulty", "witness_groups", "reward"}
    for inv in invitations:
        for field in required:
            assert field in inv, f"Invitation {inv.get('name', '?')} missing field {field!r}"


def test_difficulties_valid(invitations):
    for inv in invitations:
        assert inv["difficulty"] in VALID_DIFFICULTIES, \
            f"{inv['name']}: unknown difficulty {inv['difficulty']!r}"


def test_known_invitations_present(invitations):
    names = {inv["name"] for inv in invitations}
    for expected in KNOWN_INVITATIONS:
        assert expected in names, f"Expected invitation {expected!r} not found"


def test_unique_invitation_names(invitations):
    names = [inv["name"] for inv in invitations]
    assert len(set(names)) == len(names), "Duplicate invitation names"


def test_witness_groups_are_lists(invitations):
    for inv in invitations:
        assert isinstance(inv["witness_groups"], list), \
            f"{inv['name']}: witness_groups must be a list"
        assert len(inv["witness_groups"]) >= 1, \
            f"{inv['name']}: witness_groups must not be empty"


def test_witness_groups_have_boss(invitations):
    for inv in invitations:
        for wg in inv["witness_groups"]:
            assert "boss" in wg and wg["boss"].strip(), \
                f"{inv['name']}: witness group missing non-empty 'boss'"
            assert "found_in" in wg, \
                f"{inv['name']}: witness group missing 'found_in'"


def test_rewards_nonempty(invitations):
    for inv in invitations:
        assert inv["reward"].strip(), f"{inv['name']}: reward is empty"


def test_the_feared_is_hardest(invitations):
    feared = next(inv for inv in invitations if inv["name"] == "The Feared")
    assert feared["difficulty"] == "Endgame (pinnacle)"


def test_maven_fight_section_present(data):
    mvn = data.get("maven_fight", {})
    assert mvn, "maven_fight section missing"
    assert "requirement" in mvn and mvn["requirement"].strip()
    assert "access" in mvn and mvn["access"].strip()
    assert "rewards" in mvn and mvn["rewards"].strip()


def test_tips_present(data):
    tips = data.get("tips", [])
    assert len(tips) >= 3
    for tip in tips:
        assert isinstance(tip, str) and tip.strip()


def test_how_maven_works_present(data):
    how = data.get("how_maven_works", "")
    assert how.strip(), "how_maven_works is empty"
