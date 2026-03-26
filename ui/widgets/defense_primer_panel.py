"""
Resistances & Defence Calculations Primer panel.

Reference for all major PoE defence concepts: Armour, Evasion, Energy Shield,
Resistances, Spell Suppression, Block, Guard Skills, and EHP theory.

Includes formulas, key breakpoints, how to stack each layer, and strategic notes.

Data source: data/defense_primer.json
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
YELLOW = "#e8c84a"

_DATA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "defense_primer.json"
)

_CATEGORY_COLORS = {
    "Physical Defence":  TEAL,
    "Elemental Defence": ORANGE,
    "Spell Defence":     PURPLE,
    "Universal Defence": BLUE,
    "Recovery":          GREEN,
    "Active Defence":    YELLOW,
    "Foundation":        ACCENT,
    "Concept":           DIM,
}

_ALL = "All"


def _load_data() -> dict:
    if not os.path.exists(_DATA_PATH):
        return {}
    try:
        with open(_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[DefencePrimerPanel] failed to load data: {e}")
        return {}


class DefencePrimerPanel(QWidget):
    def __init__(self):
        super().__init__()
        data = _load_data()
        self._concepts   = data.get("concepts", [])
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

        header = QLabel(f"Defence & Resistance Primer  •  {len(self._concepts)} concepts")
        header.setStyleSheet(f"color: {ACCENT}; font-weight: bold; font-size: 13px;")
        layout.addWidget(header)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Search by concept, formula, or mechanic…")
        self._search.setStyleSheet(
            "QLineEdit { background: #0f0f23; color: #d4c5a9; border: 1px solid #2a2a4a; "
            "border-radius: 4px; padding: 4px 8px; }"
        )
        self._search.textChanged.connect(self._refresh)
        layout.addWidget(self._search)

        cat_row = QHBoxLayout()
        cat_row.setSpacing(4)
        self._cat_buttons: dict[str, QPushButton] = {}
        for cat in self._categories:
            color = _CATEGORY_COLORS.get(cat, ACCENT)
            btn = QPushButton(cat)
            btn.setFixedHeight(22)
            btn.setStyleSheet(
                f"QPushButton {{ background: #0f0f23; color: {DIM}; border: 1px solid #2a2a4a; "
                f"border-radius: 3px; padding: 0 6px; font-size: 9px; }}"
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
            tips_lbl = QLabel(self._tips[0])
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

    def _matches(self, concept: dict, query: str) -> bool:
        if not query:
            return True
        key_facts_text = " ".join(concept.get("key_facts", []))
        searchable = " ".join([
            concept.get("name", ""),
            concept.get("category", ""),
            concept.get("formula", ""),
            concept.get("cap", ""),
            key_facts_text,
            concept.get("how_to_stack", ""),
            concept.get("active_skill", ""),
            concept.get("notes", ""),
        ]).lower()
        return query in searchable

    def _refresh(self):
        query = self._search.text().strip().lower()
        pool = self._concepts
        if self._active_cat != _ALL:
            pool = [c for c in pool if c.get("category") == self._active_cat]
        filtered = [c for c in pool if self._matches(c, query)]
        self._render(filtered)

    def _render(self, concepts: list[dict]):
        while self._list_layout.count() > 1:
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not concepts:
            empty = QLabel("No matching concepts.")
            empty.setStyleSheet(f"color: {DIM}; font-size: 11px;")
            self._list_layout.insertWidget(0, empty)
            return

        for i, concept in enumerate(concepts):
            card = self._make_card(concept)
            self._list_layout.insertWidget(i, card)

    def _make_card(self, concept: dict) -> QFrame:
        cat   = concept.get("category", "")
        color = _CATEGORY_COLORS.get(cat, ACCENT)

        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background: #0f0f1e; border: 1px solid #2a2a4a; "
            f"border-left: 3px solid {color}; border-radius: 4px; padding: 4px; }}"
        )
        cl = QVBoxLayout(card)
        cl.setContentsMargins(6, 4, 6, 4)
        cl.setSpacing(3)

        # Header row: name + category badge
        header_row = QHBoxLayout()
        name_lbl = QLabel(concept.get("name", ""))
        name_lbl.setStyleSheet(f"color: {ACCENT}; font-weight: bold; font-size: 12px;")
        header_row.addWidget(name_lbl)
        header_row.addStretch()
        if cat:
            cat_badge = QLabel(f"[{cat}]")
            cat_badge.setStyleSheet(f"color: {color}; font-size: 10px;")
            header_row.addWidget(cat_badge)
        cl.addLayout(header_row)

        # Formula
        formula = concept.get("formula", "")
        if formula:
            formula_lbl = QLabel(f"Formula: {formula}")
            formula_lbl.setStyleSheet(f"color: {YELLOW}; font-size: 10px; font-style: italic;")
            formula_lbl.setWordWrap(True)
            cl.addWidget(formula_lbl)

        # Cap
        cap = concept.get("cap", "")
        if cap:
            cap_lbl = QLabel(f"Cap: {cap}")
            cap_lbl.setStyleSheet(f"color: {ORANGE}; font-size: 10px;")
            cap_lbl.setWordWrap(True)
            cl.addWidget(cap_lbl)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #2a2a4a;")
        cl.addWidget(sep)

        # Key facts
        key_facts = concept.get("key_facts", [])
        for fact in key_facts:
            fact_lbl = QLabel(f"• {fact}")
            fact_lbl.setStyleSheet(f"color: {TEXT}; font-size: 10px;")
            fact_lbl.setWordWrap(True)
            cl.addWidget(fact_lbl)

        # How to stack
        how_to_stack = concept.get("how_to_stack", "")
        if how_to_stack:
            stack_lbl = QLabel(f"Stack: {how_to_stack}")
            stack_lbl.setStyleSheet(f"color: {TEAL}; font-size: 10px;")
            stack_lbl.setWordWrap(True)
            cl.addWidget(stack_lbl)

        # Active skill
        active_skill = concept.get("active_skill", "")
        if active_skill:
            skill_lbl = QLabel(f"Skill: {active_skill}")
            skill_lbl.setStyleSheet(f"color: {GREEN}; font-size: 10px;")
            skill_lbl.setWordWrap(True)
            cl.addWidget(skill_lbl)

        # Notes
        notes = concept.get("notes", "")
        if notes:
            notes_lbl = QLabel(notes)
            notes_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px; font-style: italic;")
            notes_lbl.setWordWrap(True)
            cl.addWidget(notes_lbl)

        return card
