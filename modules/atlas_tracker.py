"""
Atlas Map Completion Tracker.

Subscribes to zone_change events from Client.txt and tracks which atlas maps
have been visited. Persists visited set across sessions in state/atlas_progress.json.

Uses zones.json atlas entries to identify atlas maps and provide tier/level data.

TOS-safe: reads only Client.txt zone_change events via the event bus.
"""

import json
import os
import time
from typing import Callable

_ZONES_PATH   = os.path.join(os.path.dirname(__file__), "..", "data", "zones.json")
_PERSIST_PATH = os.path.join(os.path.dirname(__file__), "..", "state", "atlas_progress.json")


class AtlasTracker:
    def __init__(self):
        self._atlas_zones: dict[str, dict] = self._load_atlas_zones()
        self._visited: set[str]            = self._load_progress()
        self._session_visited: set[str]    = set()
        self._on_update: list[Callable]    = []

    def on_update(self, callback: Callable):
        self._on_update.append(callback)

    def handle_zone_change(self, data: dict):
        """Called by ClientLogWatcher on zone_change events."""
        zone_name = data.get("zone", "").strip()
        if not zone_name or zone_name not in self._atlas_zones:
            return

        is_new = zone_name not in self._visited
        self._visited.add(zone_name)
        self._session_visited.add(zone_name)

        if is_new:
            self._save_progress()

        self._fire_update()

    def get_stats(self) -> dict:
        """
        Returns completion statistics dict:
          {
            "total":          int — total atlas map zones in database
            "visited":        int — total distinct maps ever visited (all sessions)
            "session_new":    int — maps visited for the first time this session
            "pct":            float — visited / total * 100
            "unvisited_by_tier": {tier: [name, ...], ...} — unvisited maps by tier
            "visited_names":  set[str] — visited map names
          }
        """
        total   = len(self._atlas_zones)
        visited = len(self._visited)
        pct     = visited / total * 100 if total > 0 else 0.0

        unvisited_by_tier: dict[int, list[str]] = {}
        for name, info in self._atlas_zones.items():
            if name not in self._visited:
                tier = info.get("tier", 0)
                unvisited_by_tier.setdefault(tier, []).append(name)

        for tier in unvisited_by_tier:
            unvisited_by_tier[tier].sort()

        return {
            "total":             total,
            "visited":           visited,
            "session_new":       len(self._session_visited - (self._visited - self._session_visited)),
            "pct":               pct,
            "unvisited_by_tier": unvisited_by_tier,
            "visited_names":     set(self._visited),
        }

    def reset(self):
        """Clear all atlas completion data (start fresh)."""
        self._visited.clear()
        self._session_visited.clear()
        self._save_progress()
        self._fire_update()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load_atlas_zones(self) -> dict[str, dict]:
        if not os.path.exists(_ZONES_PATH):
            return {}
        try:
            with open(_ZONES_PATH, "r", encoding="utf-8") as f:
                zones = json.load(f).get("zones", {})
            return {
                name: info
                for name, info in zones.items()
                if isinstance(info, dict) and info.get("type") == "atlas"
            }
        except Exception as e:
            print(f"[AtlasTracker] failed to load zones: {e}")
            return {}

    def _load_progress(self) -> set[str]:
        if not os.path.exists(_PERSIST_PATH):
            return set()
        try:
            with open(_PERSIST_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            visited = set(data.get("visited", []))
            # Only keep names that are still in the current atlas zone DB
            return visited & set(self._atlas_zones)
        except Exception as e:
            print(f"[AtlasTracker] failed to load progress: {e}")
            return set()

    def _save_progress(self):
        os.makedirs(os.path.dirname(_PERSIST_PATH), exist_ok=True)
        try:
            with open(_PERSIST_PATH, "w", encoding="utf-8") as f:
                json.dump(
                    {"visited": sorted(self._visited), "saved_at": time.time()},
                    f, indent=2,
                )
        except Exception as e:
            print(f"[AtlasTracker] failed to save progress: {e}")

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _fire_update(self):
        stats = self.get_stats()
        for cb in self._on_update:
            try:
                cb(stats)
            except Exception as e:
                print(f"[AtlasTracker] callback error: {e}")
