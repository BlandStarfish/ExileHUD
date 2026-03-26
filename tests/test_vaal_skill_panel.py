"""Tests for Vaal Skill Reference data and panel logic."""

import json
import os
import pytest

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "vaal_skills.json")


@pytest.fixture(scope="module")
def data():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def skills(data):
    return data["skills"]


# ── Data integrity ─────────────────────────────────────────────────────────────

def test_data_file_exists():
    assert os.path.exists(DATA_PATH)


def test_has_required_top_level_keys(data):
    for key in ("skills", "how_it_works", "soul_note", "tips"):
        assert key in data, f"Missing top-level key: {key}"


def test_skills_non_empty(skills):
    assert len(skills) >= 15, "Expected at least 15 Vaal skills"


def test_all_skills_have_required_fields(skills):
    required = {"name", "element", "souls_normal", "souls_merciless", "effect", "when_to_use", "best_builds"}
    for s in skills:
        missing = required - set(s.keys())
        assert not missing, f"Skill '{s.get('name')}' missing fields: {missing}"


def test_soul_requirements_positive(skills):
    for s in skills:
        assert s["souls_normal"] > 0, f"Skill '{s['name']}' has non-positive souls_normal"
        assert s["souls_merciless"] > 0, f"Skill '{s['name']}' has non-positive souls_merciless"


def test_merciless_souls_double_normal(skills):
    for s in skills:
        assert s["souls_merciless"] == s["souls_normal"] * 2, \
            f"Skill '{s['name']}' merciless souls != 2x normal"


def test_skill_names_unique(skills):
    names = [s["name"] for s in skills]
    assert len(names) == len(set(names)), "Duplicate Vaal skill names found"


def test_all_skills_start_with_vaal(skills):
    for s in skills:
        assert s["name"].startswith("Vaal "), \
            f"Skill '{s['name']}' does not start with 'Vaal '"


def test_valid_elements(skills):
    valid_elements = {
        "Lightning", "Fire", "Cold", "Physical", "Chaos", "Aura", "Armour"
    }
    for s in skills:
        assert s["element"] in valid_elements, \
            f"Skill '{s['name']}' has unknown element: {s['element']}"


def test_best_builds_is_list(skills):
    for s in skills:
        assert isinstance(s["best_builds"], list), \
            f"Skill '{s['name']}' best_builds is not a list"


def test_soul_costs_valid_values(skills):
    valid_costs = {20, 30, 40}
    for s in skills:
        assert s["souls_normal"] in valid_costs, \
            f"Skill '{s['name']}' has unusual souls_normal: {s['souls_normal']}"


def test_tips_non_empty(data):
    assert len(data["tips"]) >= 3, "Expected at least 3 tips"


# ── Spot checks ────────────────────────────────────────────────────────────────

def test_vaal_haste_exists(skills):
    names = {s["name"] for s in skills}
    assert "Vaal Haste" in names


def test_vaal_molten_shell_exists(skills):
    names = {s["name"] for s in skills}
    assert "Vaal Molten Shell" in names


def test_vaal_haste_aura(skills):
    vh = next((s for s in skills if s["name"] == "Vaal Haste"), None)
    assert vh is not None
    assert vh["element"] == "Aura"


def test_vaal_flicker_strike_physical(skills):
    vfs = next((s for s in skills if s["name"] == "Vaal Flicker Strike"), None)
    assert vfs is not None
    assert vfs["element"] == "Physical"


def test_vaal_flicker_low_soul_cost(skills):
    vfs = next((s for s in skills if s["name"] == "Vaal Flicker Strike"), None)
    assert vfs is not None
    assert vfs["souls_normal"] <= 30, "Vaal Flicker Strike should have low soul cost"


def test_vaal_blight_chaos(skills):
    vb = next((s for s in skills if s["name"] == "Vaal Blight"), None)
    assert vb is not None
    assert vb["element"] == "Chaos"


def test_vaal_blight_low_soul_cost(skills):
    vb = next((s for s in skills if s["name"] == "Vaal Blight"), None)
    assert vb is not None
    assert vb["souls_normal"] == 20, "Vaal Blight should have 20 soul cost"


def test_elements_cover_major_types(skills):
    elements = {s["element"] for s in skills}
    assert "Lightning" in elements
    assert "Physical" in elements
    assert "Aura" in elements


def test_all_effects_non_empty(skills):
    for s in skills:
        assert s["effect"].strip(), f"Skill '{s['name']}' has empty effect"
