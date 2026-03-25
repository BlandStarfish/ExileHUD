"""
Divination Card Tracker.

Scans DivinationStash tabs via the OAuth Stash API and cross-references with
poe.ninja to show stack completion progress and chaos value per card.

Requires OAuth (account:stashes scope). Scan is user-triggered.

TOS: reads stash via official OAuth API only. No game memory access.
"""

import threading
from typing import Callable


class DivCardTracker:
    def __init__(self, stash_api, ninja):
        self._stash_api = stash_api
        self._ninja     = ninja
        self._on_update: list[Callable] = []
        self._last_result: list[dict] | None = None

    def on_update(self, callback: Callable):
        self._on_update.append(callback)

    def scan(self, league: str, on_done: Callable[[bool, str], None]):
        """
        Scan DivinationStash tabs and merge with poe.ninja card data.
        Runs in a background thread; calls on_done(ok, error_msg) when complete.
        """
        def _fetch():
            try:
                stash_counts = self._stash_api.get_divination_items(league)
                ninja_data   = self._ninja.get_divination_card_data()

                # Build combined list for all cards found in stash
                cards = []
                for name, current in stash_counts.items():
                    ninja_entry = ninja_data.get(name, {})
                    full_stack  = ninja_entry.get("stack_size", 1)
                    chaos_value = ninja_entry.get("chaos", 0.0)
                    pct         = min(100.0, current / full_stack * 100) if full_stack > 0 else 0.0
                    cards.append({
                        "name":       name,
                        "current":    current,
                        "full_stack": full_stack,
                        "pct":        pct,
                        "chaos":      chaos_value,
                    })

                # Sort by completion % descending, then by name for stability
                cards.sort(key=lambda c: (-c["pct"], c["name"]))

                self._last_result = cards
                self._fire_update()
                on_done(True, "")
            except Exception as e:
                on_done(False, str(e))

        threading.Thread(target=_fetch, daemon=True).start()

    def get_last_result(self) -> list[dict] | None:
        return self._last_result

    def _fire_update(self):
        if self._last_result is None:
            return
        for cb in self._on_update:
            try:
                cb(self._last_result)
            except Exception as e:
                print(f"[DivCardTracker] callback error: {e}")
