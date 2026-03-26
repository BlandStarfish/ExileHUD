"""Tests for Expedition Faction Rewards Reference data and panel logic."""

import json
import os
import pytest

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "expedition_factions.json")


@pytest.fixture(scope="module")
def data():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def factions(data):
    return data["factions"]


# ── Data integrity ────────────────────────────────────────────────────────────

def test_data_file_exists():
    assert os.path.exists(DATA_PATH)


def test_has_required_top_level_keys(data):
    for key in ("factions", "expedition_mechanics", "tips", "intro"):
        assert key in data, f"Missing top-level key: {key}"


def test_four_factions(factions):
    assert len(factions) == 4, f"Expected exactly 4 factions, got {len(factions)}"


def test_all_factions_have_required_fields(factions):
    required = ("id", "name", "color", "merchant", "trade_currency",
                "specialty", "key_rewards", "merchant_offers",
                "best_for", "farming_tips", "notes")
    for faction in factions:
        for field in required:
            assert field in faction, \
                f"Faction '{faction.get('name')}' missing field: {field}"


def test_faction_ids_are_unique(factions):
    ids = [f["id"] for f in factions]
    assert len(ids) == len(set(ids)), "Duplicate faction IDs found"


def test_key_rewards_is_list(factions):
    for f in factions:
        assert isinstance(f["key_rewards"], list), \
            f"Faction '{f['name']}' key_rewards must be a list"
        assert len(f["key_rewards"]) >= 1


def test_merchant_offers_is_list(factions):
    for f in factions:
        assert isinstance(f["merchant_offers"], list), \
            f"Faction '{f['name']}' merchant_offers must be a list"
        assert len(f["merchant_offers"]) >= 2


def test_best_for_is_list(factions):
    for f in factions:
        assert isinstance(f["best_for"], list), \
            f"Faction '{f['name']}' best_for must be a list"
        assert len(f["best_for"]) >= 1


def test_farming_tips_is_list(factions):
    for f in factions:
        assert isinstance(f["farming_tips"], list), \
            f"Faction '{f['name']}' farming_tips must be a list"
        assert len(f["farming_tips"]) >= 2


def test_expedition_mechanics_non_empty(data):
    mechanics = data.get("expedition_mechanics", [])
    assert len(mechanics) >= 3


def test_tips_non_empty(data):
    assert len(data.get("tips", [])) >= 2


def test_colors_are_hex(factions):
    for f in factions:
        color = f.get("color", "")
        assert color.startswith("#"), \
            f"Faction '{f['name']}' color must be a hex string, got '{color}'"


# ── Content spot-checks ───────────────────────────────────────────────────────

def test_kalguuran_faction_present(factions):
    kalguuran = [f for f in factions if "Kalguuran" in f["name"]]
    assert len(kalguuran) == 1, "Expected Kalguuran Expedition faction"


def test_rog_merchant_present(factions):
    rog_factions = [f for f in factions if f.get("merchant") == "Rog"]
    assert len(rog_factions) == 1, "Expected faction with Rog as merchant"


def test_tujen_merchant_present(factions):
    tujen = [f for f in factions if f.get("merchant") == "Tujen"]
    assert len(tujen) == 1, "Expected faction with Tujen as merchant"


def test_gwennen_merchant_present(factions):
    gwennen = [f for f in factions if f.get("merchant") == "Gwennen"]
    assert len(gwennen) == 1, "Expected faction with Gwennen as merchant"


def test_dannig_merchant_present(factions):
    dannig = [f for f in factions if f.get("merchant") == "Dannig"]
    assert len(dannig) == 1, "Expected faction with Dannig as merchant"


def test_all_merchants_unique(factions):
    merchants = [f["merchant"] for f in factions]
    assert len(merchants) == len(set(merchants)), "All merchants must be unique"


def test_divine_orbs_in_rewards(factions):
    all_rewards = [r for f in factions for r in f.get("key_rewards", [])]
    assert any("Divine" in r for r in all_rewards), \
        "Expected Divine Orbs mentioned in at least one faction's rewards"


# ── Panel import and logic ────────────────────────────────────────────────────

def test_panel_imports_without_error():
    from ui.widgets.expedition_factions_panel import ExpeditionFactionsPanel


def test_panel_load_data_returns_dict():
    from ui.widgets.expedition_factions_panel import _load_data
    result = _load_data()
    assert isinstance(result, dict)
    assert "factions" in result


def test_panel_matches_logic():
    from ui.widgets.expedition_factions_panel import ExpeditionFactionsPanel
    panel = ExpeditionFactionsPanel.__new__(ExpeditionFactionsPanel)
    faction = {
        "id": "kalguuran",
        "name": "Kalguuran Expedition",
        "color": "#e8a030",
        "merchant": "Rog",
        "trade_currency": "Exotic Coinage",
        "specialty": "Currency crafting",
        "logbook_region": "Kalguur",
        "key_rewards": ["Chaos Orbs", "Divine Orbs"],
        "merchant_offers": ["Rog reforges items"],
        "best_for": ["Currency generation"],
        "farming_tips": ["Stack Kalguuran remnant keywords"],
        "notes": "Most popular faction.",
    }
    assert panel._matches(faction, "rog")
    assert panel._matches(faction, "divine")
    assert panel._matches(faction, "exotic coinage")
    assert panel._matches(faction, "currency generation")
    assert panel._matches(faction, "remnant")
    assert not panel._matches(faction, "gwennen")
    assert panel._matches(faction, "")


def test_panel_faction_filter():
    from ui.widgets.expedition_factions_panel import ExpeditionFactionsPanel
    panel = ExpeditionFactionsPanel.__new__(ExpeditionFactionsPanel)
    factions = [
        {"name": "Kalguuran Expedition", "merchant": "Rog", "trade_currency": "Exotic Coinage",
         "specialty": "Currency", "logbook_region": "K", "key_rewards": [],
         "merchant_offers": [], "best_for": [], "farming_tips": [], "notes": ""},
        {"name": "Order of the Chalice", "merchant": "Gwennen", "trade_currency": "Sun Artifacts",
         "specialty": "Uniques", "logbook_region": "O", "key_rewards": [],
         "merchant_offers": [], "best_for": [], "farming_tips": [], "notes": ""},
    ]
    kalguuran_only = [f for f in factions if f["name"] == "Kalguuran Expedition"]
    assert len(kalguuran_only) == 1
    assert kalguuran_only[0]["merchant"] == "Rog"
