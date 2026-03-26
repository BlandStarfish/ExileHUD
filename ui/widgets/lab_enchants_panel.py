"""
Labyrinth Enchantment Reference panel.

Reference for key helmet, boots, and gloves lab enchantments — what they do,
which builds want them, and which lab difficulty they are available from.

Data source: data/lab_enchants.json
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
    os.path.dirname(__file__), "..", "..", "data", "lab_enchants.json"
)

_SLOT_COLORS = {
    "Helmet": ORANGE,
    "Boots":  TEAL,
    "Gloves": PURPLE,
}

_DIFFICULTY_COLORS = {
    "Normal":    DIM,
    "Cruel":     TEAL,
    "Merciless": ORANGE,
    "Eternal":   GOLD,
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
        print(f"[LabEnchantsPanel] failed to load data: {e}")
        return {}


class LabEnchantsPanel(QWidget):
    def __init__(self):
        super().__init__()
        data = _load_data()
        self._enchants     = data.get("enchants", [])
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

        header = QLabel(f"Lab Enchantment Reference  •  {len(self._enchants)} enchants")
        header.setStyleSheet(f"color: {ACCENT}; font-weight: bold; font-size: 13px;")
        layout.addWidget(header)

        if self._how_it_works:
            how_lbl = QLabel(self._how_it_works)
            how_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px;")
            how_lbl.setWordWrap(True)
            layout.addWidget(how_lbl)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Search by skill name, effect, or best-for builds…")
        self._search.setStyleSheet(
            "QLineEdit { background: #0f0f23; color: #d4c5a9; border: 1px solid #2a2a4a; "
            "border-radius: 4px; padding: 4px 8px; }"
        )
        self._search.textChanged.connect(self._refresh)
        layout.addWidget(self._search)

        # Slot filter buttons
        cat_row = QHBoxLayout()
        cat_row.setSpacing(5)
        self._cat_buttons: dict[str, QPushButton] = {}
        for cat in self._categories:
            color = _SLOT_COLORS.get(cat, ACCENT)
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

    def _matches(self, enchant: dict, query: str) -> bool:
        if not query:
            return True
        searchable = " ".join([
            enchant.get("slot", ""),
            enchant.get("skill_name", ""),
            enchant.get("enchant_effect", ""),
            enchant.get("lab_difficulty", ""),
            enchant.get("value_tier", ""),
            " ".join(enchant.get("best_for", [])),
            enchant.get("notes", ""),
        ]).lower()
        return query in searchable

    def _refresh(self):
        query = self._search.text().strip().lower()
        pool = self._enchants
        if self._active_cat != _ALL:
            pool = [e for e in pool if e.get("slot") == self._active_cat]
        filtered = [e for e in pool if self._matches(e, query)]
        self._render(filtered)

    def _render(self, enchants: list[dict]):
        while self._list_layout.count() > 1:
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not enchants:
            empty = QLabel("No matching enchants.")
            empty.setStyleSheet(f"color: {DIM}; font-size: 11px;")
            self._list_layout.insertWidget(0, empty)
            return

        for i, enchant in enumerate(enchants):
            card = self._make_card(enchant)
            self._list_layout.insertWidget(i, card)

    def _make_card(self, enchant: dict) -> QFrame:
        slot       = enchant.get("slot", "")
        difficulty = enchant.get("lab_difficulty", "")
        color      = _SLOT_COLORS.get(slot, ACCENT)

        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background: #0f0f1e; border: 1px solid #2a2a4a; "
            f"border-left: 3px solid {color}; border-radius: 4px; padding: 4px; }}"
        )
        cl = QVBoxLayout(card)
        cl.setContentsMargins(6, 4, 6, 4)
        cl.setSpacing(3)

        # Header: skill name + slot badge + difficulty
        header_row = QHBoxLayout()
        skill_lbl = QLabel(enchant.get("skill_name", ""))
        skill_lbl.setStyleSheet(f"color: {ACCENT}; font-weight: bold; font-size: 12px;")
        header_row.addWidget(skill_lbl)
        header_row.addStretch()
        if slot:
            slot_badge = QLabel(f"[{slot}]")
            slot_badge.setStyleSheet(f"color: {color}; font-size: 10px;")
            header_row.addWidget(slot_badge)
        if difficulty:
            diff_color = _DIFFICULTY_COLORS.get(difficulty, DIM)
            diff_badge = QLabel(difficulty)
            diff_badge.setStyleSheet(f"color: {diff_color}; font-size: 10px; font-weight: bold;")
            header_row.addWidget(diff_badge)
        cl.addLayout(header_row)

        # Enchant effect
        effect = enchant.get("enchant_effect", "")
        if effect:
            eff_lbl = QLabel(effect)
            eff_lbl.setStyleSheet(f"color: {TEXT}; font-size: 10px;")
            eff_lbl.setWordWrap(True)
            cl.addWidget(eff_lbl)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #2a2a4a;")
        cl.addWidget(sep)

        # Value tier
        val_row = QHBoxLayout()
        val_row.addStretch()
        val_tier = enchant.get("value_tier", "")
        if val_tier:
            tier_color = _VALUE_COLORS.get(val_tier, DIM)
            tier_lbl = QLabel(val_tier)
            tier_lbl.setStyleSheet(f"color: {tier_color}; font-size: 10px; font-weight: bold;")
            val_row.addWidget(tier_lbl)
        cl.addLayout(val_row)

        # Best for
        best_for = enchant.get("best_for", [])
        if best_for:
            bf_lbl = QLabel("Best for: " + ", ".join(best_for))
            bf_lbl.setStyleSheet(f"color: {TEAL}; font-size: 10px;")
            bf_lbl.setWordWrap(True)
            cl.addWidget(bf_lbl)

        # Notes
        notes = enchant.get("notes", "")
        if notes:
            notes_lbl = QLabel(notes)
            notes_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px; font-style: italic;")
            notes_lbl.setWordWrap(True)
            cl.addWidget(notes_lbl)

        return card
