"""
Bestiary Recipe Browser panel.

Displays PoE Bestiary crafting recipes from a static data file.
Searchable by modifier name or beast type. No API calls — zero latency.

Data source: data/bestiary_recipes.json
"""

import json
import os

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QScrollArea, QFrame, QHBoxLayout,
)
from PyQt6.QtCore import Qt

ACCENT = "#e2b96f"
TEXT   = "#d4c5a9"
DIM    = "#8a7a65"
TEAL   = "#4ae8c8"
GREEN  = "#5cba6e"

_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "bestiary_recipes.json")

# Color per beast family
_BEAST_COLORS = {
    "Craicic": "#e2b96f",   # gold
    "Fenumal": "#c87be8",   # purple
    "Eber":    "#4ae8c8",   # teal
    "Farric":  "#e86b4a",   # orange
    "Unique":  "#aa9e6e",   # dim gold
}


def _load_recipes() -> list[dict]:
    if not os.path.exists(_DATA_PATH):
        return []
    try:
        with open(_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f).get("recipes", [])
    except Exception as e:
        print(f"[BestiaryPanel] failed to load recipes: {e}")
        return []


class BestiaryPanel(QWidget):
    def __init__(self):
        super().__init__()
        self._all_recipes = _load_recipes()
        self._build_ui()
        self._render_recipes(self._all_recipes)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        header = QLabel(f"Bestiary Crafting  •  {len(self._all_recipes)} recipes")
        header.setStyleSheet(f"color: {ACCENT}; font-weight: bold; font-size: 13px;")
        layout.addWidget(header)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Search by modifier or beast name…")
        self._search.setStyleSheet(
            "QLineEdit { background: #0f0f23; color: #d4c5a9; border: 1px solid #2a2a4a; "
            "border-radius: 4px; padding: 4px 8px; }"
        )
        self._search.textChanged.connect(self._on_search)
        layout.addWidget(self._search)

        # Scrollable recipe list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        self._recipe_container = QWidget()
        self._recipe_layout    = QVBoxLayout(self._recipe_container)
        self._recipe_layout.setContentsMargins(0, 0, 0, 0)
        self._recipe_layout.setSpacing(4)
        self._recipe_layout.addStretch()
        scroll.setWidget(self._recipe_container)
        layout.addWidget(scroll)

        note = QLabel("Beast names match Einhar capture names. All recipes require Bestiary crafting bench.")
        note.setStyleSheet(f"color: {DIM}; font-size: 10px;")
        note.setWordWrap(True)
        layout.addWidget(note)

    def _on_search(self, text: str):
        query = text.strip().lower()
        if not query:
            self._render_recipes(self._all_recipes)
            return

        filtered = [
            r for r in self._all_recipes
            if query in r.get("modifier", "").lower()
            or query in r.get("result", "").lower()
            or query in r.get("category", "").lower()
            or any(
                query in b.get("name", "").lower() or query in b.get("type", "").lower()
                for b in r.get("beasts", [])
            )
        ]
        self._render_recipes(filtered)

    def _render_recipes(self, recipes: list[dict]):
        # Clear existing recipe cards (preserve trailing stretch)
        while self._recipe_layout.count() > 1:
            item = self._recipe_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not recipes:
            empty = QLabel("No matching recipes.")
            empty.setStyleSheet(f"color: {DIM}; font-size: 11px;")
            self._recipe_layout.insertWidget(0, empty)
            return

        # Group by category
        by_category: dict[str, list[dict]] = {}
        for r in recipes:
            cat = r.get("category", "Other")
            by_category.setdefault(cat, []).append(r)

        insert_idx = 0
        for category, cat_recipes in by_category.items():
            hdr = QLabel(category)
            hdr.setStyleSheet(f"color: {TEAL}; font-size: 10px; font-weight: bold;")
            self._recipe_layout.insertWidget(insert_idx, hdr)
            insert_idx += 1

            for recipe in cat_recipes:
                card = self._make_recipe_card(recipe)
                self._recipe_layout.insertWidget(insert_idx, card)
                insert_idx += 1

    def _make_recipe_card(self, recipe: dict) -> QWidget:
        card = QWidget()
        card.setStyleSheet("background: #0f0f23; border-radius: 4px;")
        vl = QVBoxLayout(card)
        vl.setContentsMargins(8, 6, 8, 6)
        vl.setSpacing(3)

        # Modifier name
        mod_lbl = QLabel(recipe.get("modifier", ""))
        mod_lbl.setStyleSheet(f"color: {ACCENT}; font-weight: bold; font-size: 11px;")
        vl.addWidget(mod_lbl)

        # Result
        result_lbl = QLabel(recipe.get("result", ""))
        result_lbl.setStyleSheet(f"color: {TEXT}; font-size: 11px;")
        result_lbl.setWordWrap(True)
        vl.addWidget(result_lbl)

        # Beasts
        beasts = recipe.get("beasts", [])
        if beasts:
            beast_row = QHBoxLayout()
            beast_row.setSpacing(4)
            beast_row.setContentsMargins(0, 0, 0, 0)
            for beast in beasts:
                btype = beast.get("type", "")
                color = _BEAST_COLORS.get(btype, DIM)
                blbl  = QLabel(beast.get("name", ""))
                blbl.setStyleSheet(
                    f"color: {color}; font-size: 10px; background: #1a1a3a; "
                    f"border-radius: 2px; padding: 1px 4px;"
                )
                beast_row.addWidget(blbl)
            beast_row.addStretch()
            vl.addLayout(beast_row)

        # Notes (if any)
        notes = recipe.get("notes", "")
        if notes:
            sep = QFrame()
            sep.setFrameShape(QFrame.Shape.HLine)
            sep.setStyleSheet("color: #1a1a3a;")
            vl.addWidget(sep)
            notes_lbl = QLabel(notes)
            notes_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px;")
            notes_lbl.setWordWrap(True)
            vl.addWidget(notes_lbl)

        return card
