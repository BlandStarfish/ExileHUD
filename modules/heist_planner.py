"""
Heist Blueprint Organizer.

Scans stash tabs via the OAuth Stash API for Heist Contracts and Blueprints.
Groups contracts by rogue job type and shows blueprint wing unlock status.

Rogue jobs: Lockpicking, Agility, Brute Force, Counter-Thaumaturgy,
            Deception, Demolition, Engineering, Perception, Trap Disarmament

TOS: reads stash via official OAuth API only. No game memory access.
"""

import threading
from typing import Callable

# All rogue job types in PoE Heist (display order)
ROGUE_JOBS = [
    "Lockpicking",
    "Agility",
    "Brute Force",
    "Counter-Thaumaturgy",
    "Deception",
    "Demolition",
    "Engineering",
    "Perception",
    "Trap Disarmament",
]


class HeistPlanner:
    def __init__(self, stash_api):
        self._stash_api  = stash_api
        self._on_update: list[Callable] = []
        self._last_result: dict | None  = None

    def on_update(self, callback: Callable):
        self._on_update.append(callback)

    def scan(self, league: str, on_done: Callable[[bool, str], None]):
        """
        Scan stash for Heist Contracts and Blueprints.
        Runs in a background thread; calls on_done(ok, error_msg) when complete.
        """
        def _fetch():
            try:
                raw = self._stash_api.get_heist_items(league)
                result = _process(raw)
                self._last_result = result
                self._fire_update()
                on_done(True, "")
            except Exception as e:
                on_done(False, str(e))

        threading.Thread(target=_fetch, daemon=True).start()

    def get_last_result(self) -> dict | None:
        return self._last_result

    def _fire_update(self):
        if self._last_result is None:
            return
        for cb in self._on_update:
            try:
                cb(self._last_result)
            except Exception as e:
                print(f"[HeistPlanner] callback error: {e}")


def _process(raw: dict) -> dict:
    """
    Process raw stash data into a structured result:
      {
        "contracts_by_job": {job: [contract_dict, ...], ...}  — sorted by ilvl desc
        "blueprints":       [blueprint_dict, ...]             — sorted by ilvl desc
        "total_contracts":  int
        "total_blueprints": int
      }
    """
    contracts  = raw.get("contracts", [])
    blueprints = raw.get("blueprints", [])

    contracts_by_job: dict[str, list[dict]] = {}
    for contract in contracts:
        job = contract.get("job", "Unknown")
        contracts_by_job.setdefault(job, []).append(contract)

    # Sort each job's contracts by ilvl descending
    for job in contracts_by_job:
        contracts_by_job[job].sort(key=lambda c: -c["ilvl"])

    # Sort blueprints by ilvl descending, then by wings_unlocked descending
    blueprints_sorted = sorted(blueprints, key=lambda b: (-b["ilvl"], -b.get("wings_unlocked", 0)))

    return {
        "contracts_by_job": contracts_by_job,
        "blueprints":       blueprints_sorted,
        "total_contracts":  len(contracts),
        "total_blueprints": len(blueprints),
    }
