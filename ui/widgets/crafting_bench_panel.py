"""
Crafting Bench Quick Reference panel.

Reference for the 30 most-used crafting bench modifiers. Shows mod type
(Prefix/Suffix), best tier, applicable item slots, crafting cost, and notes.

Data source: data/crafting_bench.json
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

_DATA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "crafting_bench.json"
)

_CATEGORY_COLORS = {
    "Life & Mana":  GREEN,
    "Resistances":  BLUE,
    "Defence":      TEAL,
    "Offence":      ORANGE,
    "Utility":      PURPLE,
}

_MOD_TYPE_COLORS = {
    "Prefix":  ORANGE,
    "Suffix":  TEAL,
}

_ALL = "All"


def _load_data() -> dict:
    if not os.path.exists(_DATA_PATH):
        return {}
    try:
        with open(_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[CraftingBenchPanel] failed to load data: {e}")
        return {}


class CraftingBenchPanel(QWidget):
    def __init__(self):
        super().__init__()
        data = _load_data()
        self._mods       = data.get("bench_mods", [])
        self._tips       = data.get("tips", [])
        self._categories = [_ALL] + data.get("categories", [])
        self._active_cat = _ALL
        self._build_ui()
        self._set_category(_ALL)

    # ------------------------------------------------------------------

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        header = QLabel(f"Crafting Bench Quick Reference  •  {len(self._mods)} mods")
        header.setStyleSheet(f"color: {ACCENT}; font-weight: bold; font-size: 13px;")
        layout.addWidget(header)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Search by mod name, slot, cost, or effect…")
        self._search.setStyleSheet(
            "QLineEdit { background: #0f0f23; color: #d4c5a9; border: 1px solid #2a2a4a; "
            "border-radius: 4px; padding: 4px 8px; }"
        )
        self._search.textChanged.connect(self._refresh)
        layout.addWidget(self._search)

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
            mod.get("name", ""),
            mod.get("category", ""),
            mod.get("mod_type", ""),
            mod.get("best_tier", ""),
            mod.get("slots", ""),
            mod.get("cost", ""),
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
            empty = QLabel("No matching mods.")
            empty.setStyleSheet(f"color: {DIM}; font-size: 11px;")
            self._list_layout.insertWidget(0, empty)
            return

        for i, mod in enumerate(mods):
            card = self._make_card(mod)
            self._list_layout.insertWidget(i, card)

    def _make_card(self, mod: dict) -> QFrame:
        cat      = mod.get("category", "")
        mod_type = mod.get("mod_type", "")
        color    = _CATEGORY_COLORS.get(cat, ACCENT)
        mt_color = _MOD_TYPE_COLORS.get(mod_type, DIM)

        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background: #0f0f1e; border: 1px solid #2a2a4a; "
            f"border-left: 3px solid {color}; border-radius: 4px; padding: 4px; }}"
        )
        cl = QVBoxLayout(card)
        cl.setContentsMargins(6, 4, 6, 4)
        cl.setSpacing(3)

        # Header row: name + mod_type badge + category badge
        header_row = QHBoxLayout()
        name_lbl = QLabel(mod.get("name", ""))
        name_lbl.setStyleSheet(f"color: {ACCENT}; font-weight: bold; font-size: 12px;")
        header_row.addWidget(name_lbl)
        header_row.addStretch()

        if mod_type:
            mt_badge = QLabel(mod_type)
            mt_badge.setStyleSheet(f"color: {mt_color}; font-size: 10px; font-weight: bold;")
            header_row.addWidget(mt_badge)

        if cat:
            cat_badge = QLabel(f"[{cat}]")
            cat_badge.setStyleSheet(f"color: {color}; font-size: 10px;")
            header_row.addWidget(cat_badge)
        cl.addLayout(header_row)

        # Best tier
        best_tier = mod.get("best_tier", "")
        if best_tier:
            ilvl = mod.get("min_ilvl", 0)
            tier_text = best_tier
            if ilvl:
                tier_text += f"  (ilvl {ilvl}+)"
            tier_lbl = QLabel(tier_text)
            tier_lbl.setStyleSheet(f"color: {TEXT}; font-size: 10px; font-weight: bold;")
            tier_lbl.setWordWrap(True)
            cl.addWidget(tier_lbl)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #2a2a4a;")
        cl.addWidget(sep)

        # Slots
        slots = mod.get("slots", "")
        if slots:
            slots_lbl = QLabel(f"Slots: {slots}")
            slots_lbl.setStyleSheet(f"color: {TEAL}; font-size: 10px;")
            slots_lbl.setWordWrap(True)
            cl.addWidget(slots_lbl)

        # Cost
        cost = mod.get("cost", "")
        if cost:
            cost_lbl = QLabel(f"Cost: {cost}")
            cost_lbl.setStyleSheet(f"color: {GREEN}; font-size: 10px;")
            cl.addWidget(cost_lbl)

        # Notes
        notes = mod.get("notes", "")
        if notes:
            notes_lbl = QLabel(notes)
            notes_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px; font-style: italic;")
            notes_lbl.setWordWrap(True)
            cl.addWidget(notes_lbl)

        return card
