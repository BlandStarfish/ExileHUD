"""
Compass/Sextant Mod Reference panel.

Reference for Atlas compass modifiers applied via Charged Compasses to Watchstones.
Covers all major league mechanic and utility mods with value tier and usage tips.

Data source: data/compass_mods.json
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
    os.path.dirname(__file__), "..", "..", "data", "compass_mods.json"
)

_CATEGORY_COLORS = {
    "Beyond":    PURPLE,
    "Delirium":  TEAL,
    "Ritual":    RED,
    "Harvest":   GREEN,
    "Expedition": ORANGE,
    "Heist":     BLUE,
    "Bestiary":  GREEN,
    "Betrayal":  RED,
    "Incursion": GOLD,
    "Delve":     BLUE,
    "Monster":   DIM,
    "Item":      ACCENT,
}

_VALUE_COLORS = {
    "Extremely High": GOLD,
    "High":           ORANGE,
    "Medium":         TEAL,
    "Low":            DIM,
}

_ALL = "All"


def _load_data() -> dict:
    if not os.path.exists(_DATA_PATH):
        return {}
    try:
        with open(_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[CompassModsPanel] failed to load data: {e}")
        return {}


class CompassModsPanel(QWidget):
    def __init__(self):
        super().__init__()
        data = _load_data()
        self._mods         = data.get("mods", [])
        self._how_it_works = data.get("how_it_works", "")
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

        header = QLabel(f"Compass Mod Reference  •  {len(self._mods)} mods")
        header.setStyleSheet(f"color: {ACCENT}; font-weight: bold; font-size: 13px;")
        layout.addWidget(header)

        if self._how_it_works:
            how_lbl = QLabel(self._how_it_works)
            how_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px;")
            how_lbl.setWordWrap(True)
            layout.addWidget(how_lbl)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Search by mod name, category, best-for builds…")
        self._search.setStyleSheet(
            "QLineEdit { background: #0f0f23; color: #d4c5a9; border: 1px solid #2a2a4a; "
            "border-radius: 4px; padding: 4px 8px; }"
        )
        self._search.textChanged.connect(self._refresh)
        layout.addWidget(self._search)

        # Category filter buttons
        cat_row = QHBoxLayout()
        cat_row.setSpacing(4)
        self._cat_buttons: dict[str, QPushButton] = {}
        for cat in self._categories:
            color = _CATEGORY_COLORS.get(cat, ACCENT)
            btn = QPushButton(cat)
            btn.setFixedHeight(22)
            btn.setStyleSheet(
                f"QPushButton {{ background: #0f0f23; color: {DIM}; border: 1px solid #2a2a4a; "
                f"border-radius: 3px; padding: 0 6px; font-size: 10px; }}"
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

    def _matches(self, mod: dict, query: str) -> bool:
        if not query:
            return True
        searchable = " ".join([
            mod.get("mod_name", ""),
            mod.get("category", ""),
            mod.get("effect", ""),
            mod.get("value_tier", ""),
            " ".join(mod.get("best_for", [])),
            mod.get("notes", ""),
        ]).lower()
        return query in searchable

    def _refresh(self):
        query = self._search.text().strip().lower()
        pool = self._mods
        if self._active_cat != _ALL:
            pool = [m for m in pool if m.get("category") == self._active_cat]
        filtered = [m for m in pool if self._matches(m, query)]
        self._render(filtered)

    def _render(self, mods: list[dict]):
        while self._list_layout.count() > 1:
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not mods:
            empty = QLabel("No matching compass mods.")
            empty.setStyleSheet(f"color: {DIM}; font-size: 11px;")
            self._list_layout.insertWidget(0, empty)
            return

        for i, mod in enumerate(mods):
            card = self._make_card(mod)
            self._list_layout.insertWidget(i, card)

    def _make_card(self, mod: dict) -> QFrame:
        category = mod.get("category", "")
        color = _CATEGORY_COLORS.get(category, ACCENT)

        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background: #0f0f1e; border: 1px solid #2a2a4a; "
            f"border-left: 3px solid {color}; border-radius: 4px; padding: 4px; }}"
        )
        cl = QVBoxLayout(card)
        cl.setContentsMargins(6, 4, 6, 4)
        cl.setSpacing(3)

        # Header: mod name + category badge + value tier
        header_row = QHBoxLayout()
        mod_name = mod.get("mod_name", "")
        name_lbl = QLabel(mod_name)
        name_lbl.setStyleSheet(f"color: {ACCENT}; font-weight: bold; font-size: 12px;")
        name_lbl.setWordWrap(True)
        header_row.addWidget(name_lbl, 1)
        if category:
            cat_badge = QLabel(f"[{category}]")
            cat_badge.setStyleSheet(f"color: {color}; font-size: 10px; font-weight: bold;")
            header_row.addWidget(cat_badge)
        cl.addLayout(header_row)

        # Value tier
        val_tier = mod.get("value_tier", "")
        if val_tier:
            tier_color = _VALUE_COLORS.get(val_tier, DIM)
            tier_lbl = QLabel(f"Value: {val_tier}")
            tier_lbl.setStyleSheet(f"color: {tier_color}; font-size: 10px; font-weight: bold;")
            cl.addWidget(tier_lbl)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #2a2a4a;")
        cl.addWidget(sep)

        # Effect
        effect = mod.get("effect", "")
        if effect:
            effect_lbl = QLabel(effect)
            effect_lbl.setStyleSheet(f"color: {TEXT}; font-size: 11px;")
            effect_lbl.setWordWrap(True)
            cl.addWidget(effect_lbl)

        # Best for
        best_for = mod.get("best_for", [])
        if best_for:
            bf_lbl = QLabel("Best for: " + ", ".join(best_for))
            bf_lbl.setStyleSheet(f"color: {TEAL}; font-size: 10px;")
            bf_lbl.setWordWrap(True)
            cl.addWidget(bf_lbl)

        # Notes
        notes = mod.get("notes", "")
        if notes:
            notes_lbl = QLabel(notes)
            notes_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px; font-style: italic;")
            notes_lbl.setWordWrap(True)
            cl.addWidget(notes_lbl)

        return card
