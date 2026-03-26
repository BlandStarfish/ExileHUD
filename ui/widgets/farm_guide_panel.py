"""
Atlas Farming Activity Guide panel.

Reference for 15 major farming strategies — expected chaos/hr range,
best maps, key drops, difficulty, and practical tips.

Data source: data/farm_guide.json
No API calls — zero latency, always accurate.
"""

import json
import os

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QScrollArea, QFrame, QPushButton,
)

ACCENT = "#e2b96f"
TEXT   = "#d4c5a9"
DIM    = "#8a7a65"
GREEN  = "#5cba6e"
TEAL   = "#4ae8c8"
ORANGE = "#e8864a"
RED    = "#e05050"
PURPLE = "#a070e8"
BLUE   = "#6090e8"
GOLD   = "#f5c842"

_DATA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "farm_guide.json"
)

_DIFFICULTY_COLORS = {
    "Low":    GREEN,
    "Medium": ORANGE,
    "High":   RED,
}

_ALL = "All"
_DIFFICULTIES = ["Low", "Medium", "High"]


def _load_data() -> dict:
    if not os.path.exists(_DATA_PATH):
        return {}
    try:
        with open(_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[FarmGuidePanel] failed to load data: {e}")
        return {}


class FarmGuidePanel(QWidget):
    def __init__(self):
        super().__init__()
        data = _load_data()
        self._activities    = data.get("activities", [])
        self._tips          = data.get("tips", [])
        self._active_diff   = _ALL
        self._build_ui()
        self._set_difficulty(_ALL)

    # ------------------------------------------------------------------

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        header = QLabel(f"Farming Activity Guide  •  {len(self._activities)} strategies")
        header.setStyleSheet(f"color: {ACCENT}; font-weight: bold; font-size: 13px;")
        layout.addWidget(header)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Search by mechanic, map, drop, or tip…")
        self._search.setStyleSheet(
            "QLineEdit { background: #0f0f23; color: #d4c5a9; border: 1px solid #2a2a4a; "
            "border-radius: 4px; padding: 4px 8px; }"
        )
        self._search.textChanged.connect(self._refresh)
        layout.addWidget(self._search)

        # Difficulty filter buttons
        diff_row = QHBoxLayout()
        diff_row.setSpacing(4)
        self._diff_buttons: dict[str, QPushButton] = {}
        for diff in [_ALL] + _DIFFICULTIES:
            color = _DIFFICULTY_COLORS.get(diff, ACCENT)
            btn = QPushButton(diff)
            btn.setFixedHeight(22)
            btn.setStyleSheet(
                f"QPushButton {{ background: #0f0f23; color: {DIM}; border: 1px solid #2a2a4a; "
                f"border-radius: 3px; padding: 0 6px; font-size: 10px; }}"
                f"QPushButton:hover {{ background: #1a1a3a; }}"
                f"QPushButton[active='true'] {{ color: {color}; border-color: {color}; }}"
            )
            btn.clicked.connect(lambda _, d=diff: self._set_difficulty(d))
            self._diff_buttons[diff] = btn
            diff_row.addWidget(btn)
        diff_row.addStretch()
        layout.addLayout(diff_row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        self._container = QWidget()
        self._list_layout = QVBoxLayout(self._container)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(5)
        self._list_layout.addStretch()
        scroll.setWidget(self._container)
        layout.addWidget(scroll)

        if self._tips:
            tips_lbl = QLabel("Tip: " + self._tips[0])
            tips_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px; font-style: italic;")
            tips_lbl.setWordWrap(True)
            layout.addWidget(tips_lbl)

    def _set_difficulty(self, diff: str):
        self._active_diff = diff
        for d, btn in self._diff_buttons.items():
            color = _DIFFICULTY_COLORS.get(d, ACCENT)
            btn.setProperty("active", "true" if d == diff else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self._refresh()

    def _matches(self, activity: dict, query: str) -> bool:
        if not query:
            return True
        drops_text = " ".join(
            d.get("item", "") for d in activity.get("key_drops", [])
        )
        tips_text = " ".join(activity.get("tips", []))
        maps_text = " ".join(activity.get("best_maps", []))
        searchable = " ".join([
            activity.get("name", ""),
            activity.get("mechanic", ""),
            activity.get("difficulty", ""),
            drops_text,
            maps_text,
            tips_text,
        ]).lower()
        return query in searchable

    def _refresh(self):
        query = self._search.text().strip().lower()
        pool = self._activities
        if self._active_diff != _ALL:
            pool = [a for a in pool if a.get("difficulty") == self._active_diff]
        filtered = [a for a in pool if self._matches(a, query)]
        self._render(filtered)

    def _render(self, activities: list[dict]):
        while self._list_layout.count() > 1:
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not activities:
            empty = QLabel("No matching farming activities.")
            empty.setStyleSheet(f"color: {DIM}; font-size: 11px;")
            self._list_layout.insertWidget(0, empty)
            return

        for i, activity in enumerate(activities):
            card = self._make_card(activity)
            self._list_layout.insertWidget(i, card)

    def _make_card(self, activity: dict) -> QFrame:
        diff = activity.get("difficulty", "")
        color = _DIFFICULTY_COLORS.get(diff, ACCENT)

        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background: #0f0f1e; border: 1px solid #2a2a4a; "
            f"border-left: 3px solid {color}; border-radius: 4px; padding: 4px; }}"
        )
        cl = QVBoxLayout(card)
        cl.setContentsMargins(6, 4, 6, 4)
        cl.setSpacing(3)

        # Header: name + mechanic badge + difficulty badge
        header_row = QHBoxLayout()
        name_lbl = QLabel(activity.get("name", ""))
        name_lbl.setStyleSheet(f"color: {ACCENT}; font-weight: bold; font-size: 12px;")
        header_row.addWidget(name_lbl, 1)
        mechanic = activity.get("mechanic", "")
        if mechanic:
            mech_badge = QLabel(mechanic)
            mech_badge.setStyleSheet(f"color: {TEAL}; font-size: 10px; font-weight: bold;")
            header_row.addWidget(mech_badge)
        if diff:
            diff_badge = QLabel(diff)
            diff_badge.setStyleSheet(f"color: {color}; font-size: 10px;")
            header_row.addWidget(diff_badge)
        cl.addLayout(header_row)

        # Chaos/hr estimate
        cph = activity.get("chaos_per_hour", {})
        if cph:
            lo = cph.get("low", 0)
            hi = cph.get("high", 0)
            cph_lbl = QLabel(f"Chaos/hr: {lo}–{hi}c")
            cph_lbl.setStyleSheet(f"color: {GOLD}; font-size: 10px; font-weight: bold;")
            cl.addWidget(cph_lbl)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #2a2a4a;")
        cl.addWidget(sep)

        # Best maps
        best_maps = activity.get("best_maps", [])
        if best_maps:
            maps_lbl = QLabel("Best maps: " + ", ".join(best_maps))
            maps_lbl.setStyleSheet(f"color: {TEXT}; font-size: 10px;")
            maps_lbl.setWordWrap(True)
            cl.addWidget(maps_lbl)

        # Key drops (top 3)
        drops = activity.get("key_drops", [])[:3]
        for drop in drops:
            item_name = drop.get("item", "")
            rate = drop.get("drop_rate", "")
            val = drop.get("value_chaos", 0)
            val_str = f"  (~{val}c)" if val else ""
            drop_lbl = QLabel(f"• {item_name}  [{rate}]{val_str}")
            drop_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px;")
            drop_lbl.setWordWrap(True)
            cl.addWidget(drop_lbl)

        # Tips (top 2)
        tips = activity.get("tips", [])[:2]
        for tip in tips:
            tip_lbl = QLabel(f"→ {tip}")
            tip_lbl.setStyleSheet(f"color: {GREEN}; font-size: 10px;")
            tip_lbl.setWordWrap(True)
            cl.addWidget(tip_lbl)

        return card
