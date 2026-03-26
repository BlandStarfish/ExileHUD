"""
Unique Flask Reference panel.

Static reference for important PoE unique flasks — effects, best builds,
when to use, and value tiers.

Data source: data/unique_flasks.json
No API calls — zero latency, always accurate.
"""

import json
import os

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QScrollArea, QFrame, QPushButton,
)

ACCENT  = "#e2b96f"
TEXT    = "#d4c5a9"
DIM     = "#8a7a65"
RED     = "#e05050"
ORANGE  = "#e8864a"
YELLOW  = "#e8c84a"
GREEN   = "#5cba6e"
TEAL    = "#4ae8c8"
PURPLE  = "#a070e8"
BLUE    = "#6090e8"

_DATA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "unique_flasks.json"
)

_VALUE_COLORS = {
    "Very High": GREEN,
    "High":      TEAL,
    "Medium":    ACCENT,
    "Low":       DIM,
}

_CATEGORY_COLORS = {
    "DPS":     RED,
    "Defense": BLUE,
    "Utility": PURPLE,
}

_ALL = "All"


def _load_data() -> dict:
    if not os.path.exists(_DATA_PATH):
        return {}
    try:
        with open(_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[UniqueFlaskPanel] failed to load data: {e}")
        return {}


class UniqueFlaskPanel(QWidget):
    def __init__(self):
        super().__init__()
        data = _load_data()
        self._flasks       = data.get("flasks", [])
        self._how_it_works = data.get("how_it_works", "")
        self._craft_note   = data.get("craft_note", "")
        self._tips         = data.get("tips", [])
        self._categories   = [_ALL] + data.get("categories", [])
        self._active_cat   = _ALL
        self._build_ui()
        self._set_category(_ALL)

    # ------------------------------------------------------------------

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        header = QLabel(f"Unique Flask Reference  •  {len(self._flasks)} flasks")
        header.setStyleSheet(f"color: {ACCENT}; font-weight: bold; font-size: 13px;")
        layout.addWidget(header)

        if self._how_it_works:
            how_lbl = QLabel(self._how_it_works)
            how_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px;")
            how_lbl.setWordWrap(True)
            layout.addWidget(how_lbl)

        if self._craft_note:
            craft_lbl = QLabel(self._craft_note)
            craft_lbl.setStyleSheet(
                f"color: {TEAL}; font-size: 10px; font-style: italic;"
            )
            craft_lbl.setWordWrap(True)
            layout.addWidget(craft_lbl)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Search by name, base, effect, or build…")
        self._search.setStyleSheet(
            "QLineEdit { background: #0f0f23; color: #d4c5a9; border: 1px solid #2a2a4a; "
            "border-radius: 4px; padding: 4px 8px; }"
        )
        self._search.textChanged.connect(self._refresh)
        layout.addWidget(self._search)

        # Category filter buttons
        cat_row = QHBoxLayout()
        cat_row.setSpacing(5)
        self._cat_buttons: dict[str, QPushButton] = {}
        for cat in self._categories:
            color = _CATEGORY_COLORS.get(cat, ACCENT)
            btn = QPushButton(cat)
            btn.setFixedHeight(22)
            btn.setStyleSheet(
                f"QPushButton {{ background: #0f0f23; color: {DIM}; border: 1px solid #2a2a4a; "
                f"border-radius: 3px; padding: 0 8px; font-size: 10px; }}"
                f"QPushButton:hover {{ background: #1a1a3a; }}"
                f"QPushButton[active='true'] {{ color: {color}; border-color: {color}; }}"
            )
            btn.clicked.connect(lambda _, c=cat: self._set_category(c))
            self._cat_buttons[cat] = btn
            cat_row.addWidget(btn)
        cat_row.addStretch()
        layout.addLayout(cat_row)

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

        # Tips footer
        if self._tips:
            tips_lbl = QLabel("Tips: " + "  •  ".join(self._tips[:2]))
            tips_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px; font-style: italic;")
            tips_lbl.setWordWrap(True)
            layout.addWidget(tips_lbl)

    def _set_category(self, cat: str):
        self._active_cat = cat
        for c, btn in self._cat_buttons.items():
            btn.setProperty("active", "true" if c == cat else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self._refresh()

    def _flask_matches(self, flask: dict, query: str) -> bool:
        if not query:
            return True
        searchable = " ".join([
            flask.get("name", ""),
            flask.get("base", ""),
            flask.get("effect", ""),
            flask.get("when_to_use", ""),
            flask.get("notes", ""),
            flask.get("category", ""),
            " ".join(flask.get("best_builds", [])),
        ]).lower()
        return query in searchable

    def _refresh(self):
        query = self._search.text().strip().lower()
        pool = self._flasks
        if self._active_cat != _ALL:
            pool = [f for f in pool if f.get("category") == self._active_cat]
        filtered = [f for f in pool if self._flask_matches(f, query)]
        self._render(filtered)

    def _render(self, flasks: list[dict]):
        while self._list_layout.count() > 1:
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not flasks:
            empty = QLabel("No matching flasks.")
            empty.setStyleSheet(f"color: {DIM}; font-size: 11px;")
            self._list_layout.insertWidget(0, empty)
            return

        for i, flask in enumerate(flasks):
            card = self._make_card(flask)
            self._list_layout.insertWidget(i, card)

    def _make_card(self, flask: dict) -> QFrame:
        cat   = flask.get("category", "")
        tier  = flask.get("value_tier", "")
        color = _CATEGORY_COLORS.get(cat, ACCENT)
        tier_color = _VALUE_COLORS.get(tier, DIM)

        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background: #0f0f1e; border: 1px solid #2a2a4a; "
            f"border-left: 3px solid {color}; border-radius: 4px; padding: 4px; }}"
        )
        cl = QVBoxLayout(card)
        cl.setContentsMargins(6, 4, 6, 4)
        cl.setSpacing(3)

        # Header row: name + base + value tier badge
        header_row = QHBoxLayout()
        name_lbl = QLabel(flask.get("name", ""))
        name_lbl.setStyleSheet(f"color: {ACCENT}; font-weight: bold; font-size: 12px;")
        header_row.addWidget(name_lbl)

        base_lbl = QLabel(flask.get("base", ""))
        base_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px; font-style: italic;")
        header_row.addWidget(base_lbl)
        header_row.addStretch()

        if tier:
            tier_badge = QLabel(tier)
            tier_badge.setStyleSheet(
                f"color: {tier_color}; font-size: 10px; font-weight: bold;"
            )
            header_row.addWidget(tier_badge)

        if cat:
            cat_badge = QLabel(f"[{cat}]")
            cat_badge.setStyleSheet(f"color: {color}; font-size: 10px;")
            header_row.addWidget(cat_badge)

        cl.addLayout(header_row)

        # Effect
        effect = flask.get("effect", "")
        if effect:
            eff_lbl = QLabel(effect)
            eff_lbl.setStyleSheet(f"color: {TEXT}; font-size: 11px;")
            eff_lbl.setWordWrap(True)
            cl.addWidget(eff_lbl)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: #2a2a4a;")
        cl.addWidget(sep)

        # When to use
        when = flask.get("when_to_use", "")
        if when:
            when_lbl = QLabel(f"When: {when}")
            when_lbl.setStyleSheet(f"color: {GREEN}; font-size: 10px;")
            when_lbl.setWordWrap(True)
            cl.addWidget(when_lbl)

        # Best builds
        builds = flask.get("best_builds", [])
        if builds:
            builds_lbl = QLabel("Builds: " + " / ".join(builds))
            builds_lbl.setStyleSheet(f"color: {TEAL}; font-size: 10px;")
            builds_lbl.setWordWrap(True)
            cl.addWidget(builds_lbl)

        # Notes
        notes = flask.get("notes", "")
        if notes:
            notes_lbl = QLabel(notes)
            notes_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px; font-style: italic;")
            notes_lbl.setWordWrap(True)
            cl.addWidget(notes_lbl)

        return card
