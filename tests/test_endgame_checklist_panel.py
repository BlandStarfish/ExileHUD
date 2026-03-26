"""Tests for Endgame Progression Checklist data and panel logic."""

import json
import os
import pytest

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "endgame_checklist.json")


@pytest.fixture(scope="module")
def data():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def stages(data):
    return data["stages"]


# ── Data integrity ─────────────────────────────────────────────────────────────

def test_data_file_exists():
    assert os.path.exists(DATA_PATH)


def test_has_required_top_level_keys(data):
    for key in ("stages", "categories", "tips"):
        assert key in data, f"Missing top-level key: {key}"


def test_stages_non_empty(stages):
    assert len(stages) >= 4, f"Expected at least 4 stages, got {len(stages)}"


def test_all_stages_have_required_fields(stages):
    required = ("name", "category", "order", "objectives", "gear_targets")
    for stage in stages:
        for field in required:
            assert field in stage, f"Stage '{stage.get('name')}' missing field: {field}"


def test_stage_names_unique(stages):
    names = [s["name"] for s in stages]
    assert len(names) == len(set(names)), "Duplicate stage names found"


def test_valid_categories(stages, data):
    valid = set(data.get("categories", []))
    for stage in stages:
        assert stage["category"] in valid, \
            f"Stage '{stage['name']}' has invalid category: '{stage['category']}'"


def test_order_values_unique(stages):
    orders = [s["order"] for s in stages]
    assert len(orders) == len(set(orders)), "Duplicate order values found"


def test_order_values_sequential(stages):
    orders = sorted(s["order"] for s in stages)
    assert orders == list(range(1, len(orders) + 1)), \
        f"Order values should be sequential starting from 1, got {orders}"


def test_objectives_non_empty(stages):
    for stage in stages:
        assert len(stage["objectives"]) >= 2, \
            f"Stage '{stage['name']}' has fewer than 2 objectives"


def test_gear_targets_non_empty(stages):
    for stage in stages:
        assert stage["gear_targets"].strip(), \
            f"Stage '{stage['name']}' has empty gear_targets"


def test_tips_non_empty(data):
    assert len(data.get("tips", [])) >= 3, "Expected at least 3 tips"


# ── Category coverage ──────────────────────────────────────────────────────────

def test_has_foundation_stage(stages):
    foundation = [s for s in stages if s["category"] == "Foundation"]
    assert len(foundation) >= 1, "Expected at least 1 Foundation stage"


def test_has_mapping_stages(stages):
    mapping = [s for s in stages if s["category"] == "Mapping"]
    assert len(mapping) >= 1, "Expected at least 1 Mapping stage"


def test_has_endgame_or_pinnacle_stages(stages):
    ep = [s for s in stages if s["category"] in ("Endgame", "Pinnacle")]
    assert len(ep) >= 2, "Expected at least 2 Endgame or Pinnacle stages"


# ── Specific stages present ────────────────────────────────────────────────────

def test_campaign_stage_present(stages):
    names = [s["name"] for s in stages]
    assert any("Campaign" in name or "Acts" in name for name in names), \
        "Expected a Campaign/Acts stage"


def test_campaign_has_kitava_warning(stages):
    campaign = next((s for s in stages if "Campaign" in s["name"] or "Acts" in s["name"]), None)
    assert campaign is not None
    warnings_text = " ".join(campaign.get("key_warnings", []))
    assert "Kitava" in warnings_text or "resistance" in warnings_text.lower(), \
        "Campaign stage should warn about Kitava resistance penalty"


def test_pinnacle_stage_mentions_sirus_or_shaper(stages):
    pinnacle_stages = [s for s in stages if s["category"] in ("Endgame", "Pinnacle")]
    all_text = " ".join(
        " ".join(s.get("objectives", [])) + " " + " ".join(s.get("key_warnings", []))
        for s in pinnacle_stages
    )
    assert "Sirus" in all_text or "Shaper" in all_text, \
        "Pinnacle stages should mention Sirus or Shaper"


def test_first_stage_is_campaign(stages):
    ordered = sorted(stages, key=lambda s: s["order"])
    assert "Campaign" in ordered[0]["name"] or "Acts" in ordered[0]["name"], \
        "First stage should be Campaign/Acts"


# ── Search logic (data-level) ──────────────────────────────────────────────────

def _matches(stage: dict, query: str) -> bool:
    """Mirror of panel search logic for data-level testing."""
    if not query:
        return True
    objectives_text = " ".join(stage.get("objectives", []))
    warnings_text   = " ".join(stage.get("key_warnings", []))
    searchable = " ".join([
        stage.get("name", ""),
        stage.get("category", ""),
        objectives_text,
        stage.get("gear_targets", ""),
        warnings_text,
        stage.get("unlock", ""),
        stage.get("next_step", ""),
    ]).lower()
    return query in searchable


def test_panel_module_importable():
    """Verify the panel module can be imported without a QApplication."""
    import importlib
    mod = importlib.import_module("ui.widgets.endgame_checklist_panel")
    assert hasattr(mod, "EndgameChecklistPanel")


def test_search_matches_stage_name(stages):
    results = [s for s in stages if _matches(s, "campaign")]
    assert len(results) >= 1


def test_search_matches_objective(stages):
    results = [s for s in stages if _matches(s, "lab")]
    assert len(results) >= 1, "Expected at least one stage mentioning lab"


def test_search_matches_warning(stages):
    results = [s for s in stages if _matches(s, "kitava")]
    assert len(results) >= 1, "Expected campaign stage to match 'kitava' search"


def test_search_matches_gear_targets(stages):
    results = [s for s in stages if _matches(s, "life")]
    assert len(results) >= 1


def test_search_empty_returns_all(stages):
    results = [s for s in stages if _matches(s, "")]
    assert len(results) == len(stages)


def test_search_no_match(stages):
    results = [s for s in stages if _matches(s, "xyzxyzxyz_no_match")]
    assert len(results) == 0
