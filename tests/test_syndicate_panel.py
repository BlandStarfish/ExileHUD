"""
Tests for syndicate_members.json data integrity.

Validates that the data file is well-formed and all members have required fields.
No UI tests — Qt widgets are tested indirectly through the data layer.
"""

import json
import os
import pytest

_DATA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "syndicate_members.json"
)

_VALID_FACTIONS = {"Transportation", "Research", "Fortification", "Intervention"}
_VALID_DANGER   = {"high", "medium", "none"}


@pytest.fixture(scope="module")
def members():
    with open(_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)["members"]


def test_data_file_exists():
    assert os.path.exists(_DATA_PATH), "syndicate_members.json not found"


def test_has_members(members):
    assert len(members) > 0


def test_minimum_member_count(members):
    # There are 22 named Syndicate members in PoE
    assert len(members) >= 18, f"Expected at least 18 members, got {len(members)}"


def test_all_members_have_name(members):
    for m in members:
        assert m.get("name"), f"Member missing name: {m}"


def test_all_members_have_factions(members):
    for m in members:
        factions = m.get("factions", [])
        assert factions, f"Member '{m.get('name')}' has no factions"
        assert all(f in _VALID_FACTIONS for f in factions), \
            f"Member '{m.get('name')}' has invalid faction(s): {factions}"


def test_all_members_have_primary_faction(members):
    for m in members:
        primary = m.get("primary_faction")
        assert primary in _VALID_FACTIONS, \
            f"Member '{m.get('name')}' has invalid primary_faction: {primary!r}"


def test_primary_faction_in_factions_list(members):
    for m in members:
        primary = m.get("primary_faction")
        factions = m.get("factions", [])
        assert primary in factions, \
            f"Member '{m.get('name')}' primary_faction '{primary}' not in factions list"


def test_all_members_have_intel_reward(members):
    for m in members:
        assert m.get("intel_reward"), \
            f"Member '{m.get('name')}' missing intel_reward"


def test_all_members_have_safehouse_rewards(members):
    for m in members:
        rewards = m.get("safehouse_rewards", {})
        assert rewards, f"Member '{m.get('name')}' has no safehouse_rewards"


def test_safehouse_reward_divisions_valid(members):
    for m in members:
        for div in m.get("safehouse_rewards", {}):
            assert div in _VALID_FACTIONS, \
                f"Member '{m.get('name')}' has invalid division '{div}' in safehouse_rewards"


def test_all_members_have_notes(members):
    for m in members:
        assert m.get("notes"), f"Member '{m.get('name')}' missing notes"


def test_unique_member_names(members):
    names = [m["name"] for m in members]
    assert len(names) == len(set(names)), "Duplicate member names found"


def test_all_four_divisions_represented(members):
    """Every division should have at least one member assigned."""
    represented = set()
    for m in members:
        represented.update(m.get("factions", []))
    for div in _VALID_FACTIONS:
        assert div in represented, f"No member assigned to division: {div}"


def test_catarina_in_research(members):
    """Catarina is always Research mastermind — verify she's present and correct."""
    catarina = next((m for m in members if "Catarina" in m.get("name", "")), None)
    assert catarina is not None, "Catarina not found in member list"
    assert "Research" in catarina.get("factions", []), \
        "Catarina should be in Research division"


def test_vorici_in_transportation(members):
    """Vorici is Transportation — white socket crafting. Verify present."""
    vorici = next((m for m in members if "Vorici" in m.get("name", "")), None)
    assert vorici is not None, "Vorici not found in member list"
    assert "Transportation" in vorici.get("factions", []), \
        "Vorici should be in Transportation division"


def test_elreon_in_research(members):
    """Elreon gives the valuable Prefixes/Suffixes Cannot Be Changed recipe."""
    elreon = next((m for m in members if "Elreon" in m.get("name", "")), None)
    assert elreon is not None, "Elreon not found in member list"
    assert "Research" in elreon.get("factions", []), \
        "Elreon should be in Research division"


def test_aisling_in_transportation(members):
    """Aisling gives the Add/Remove Influence recipe."""
    aisling = next((m for m in members if "Aisling" in m.get("name", "")), None)
    assert aisling is not None, "Aisling not found in member list"
    assert "Transportation" in aisling.get("factions", []), \
        "Aisling should be in Transportation division"
