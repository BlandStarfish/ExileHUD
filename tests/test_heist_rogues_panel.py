"""Tests for Heist Rogue Skills data integrity."""
import json
import os
import pytest

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "heist_rogues.json")

VALID_JOBS = {
    "Lockpicking", "Agility", "Brute Force", "Counter-Thaumaturgy",
    "Deception", "Demolition", "Engineering", "Perception", "Trap Disarmament",
}


@pytest.fixture(scope="module")
def data():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def rogues(data):
    return data["rogues"]


def test_data_file_exists():
    assert os.path.exists(DATA_PATH)


def test_has_rogues(rogues):
    assert len(rogues) >= 10, "Expected at least 10 rogues"


def test_required_fields(rogues):
    required = {"name", "primary_job", "max_primary_level", "specialty", "reward_type", "notes"}
    for r in rogues:
        for field in required:
            assert field in r, f"Rogue {r.get('name', '?')} missing field {field!r}"


def test_unique_rogue_names(rogues):
    names = [r["name"] for r in rogues]
    assert len(set(names)) == len(names), "Duplicate rogue names"


def test_primary_jobs_valid(rogues):
    for r in rogues:
        assert r["primary_job"] in VALID_JOBS, \
            f"{r['name']}: unknown primary_job {r['primary_job']!r}"


def test_secondary_jobs_valid(rogues):
    for r in rogues:
        sec = r.get("secondary_job")
        if sec is not None:
            assert sec in VALID_JOBS, \
                f"{r['name']}: unknown secondary_job {sec!r}"


def test_max_primary_level_positive(rogues):
    for r in rogues:
        assert isinstance(r["max_primary_level"], int) and r["max_primary_level"] >= 1, \
            f"{r['name']}: max_primary_level must be a positive int"


def test_max_secondary_level_valid(rogues):
    for r in rogues:
        sec_lvl = r.get("max_secondary_level")
        if sec_lvl is not None:
            assert isinstance(sec_lvl, int) and sec_lvl >= 1, \
                f"{r['name']}: max_secondary_level must be a positive int or null"


def test_karst_present(rogues):
    names = {r["name"] for r in rogues}
    assert any("Karst" in n for n in names), "Karst (Lockpicking) not found"


def test_tullina_present(rogues):
    names = {r["name"] for r in rogues}
    assert any("Tullina" in n for n in names), "Tullina (Agility) not found"


def test_gianna_is_deception_specialist(rogues):
    gianna = next((r for r in rogues if "Gianna" in r["name"]), None)
    assert gianna is not None, "Gianna not found"
    assert gianna["primary_job"] == "Deception"


def test_tibbs_has_no_secondary(rogues):
    tibbs = next((r for r in rogues if "Tibbs" in r["name"]), None)
    assert tibbs is not None, "Tibbs not found"
    assert tibbs.get("secondary_job") is None


def test_job_types_present(data):
    job_types = data.get("job_types", [])
    assert len(job_types) >= 9, "Expected 9 job types"
    for jt in job_types:
        assert jt in VALID_JOBS, f"Unknown job type {jt!r}"


def test_tips_present(data):
    tips = data.get("tips", [])
    assert len(tips) >= 4
    for tip in tips:
        assert isinstance(tip, str) and tip.strip()


def test_how_it_works_present(data):
    assert data.get("how_it_works", "").strip()
