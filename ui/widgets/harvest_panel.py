"""
Harvest Craft Reference panel.

Static reference for all Harvest craft categories — reforges, augments,
remove/add, split/duplicate, and enchants. The most important crafts are
highlighted by value tier.

Data source: data/harvest_crafts.json
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
PURPLE = "#9a4ae8"

_DATA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "harvest_crafts.json"
)

_VALUE_COLORS = {
    "Extremely High": RED,
    "Very High":      ORANGE,
    "High":           ACCENT,
    "Medium":         TEAL,
    "Low":            DIM,
}

_CATEGORY_COLORS = {
    "Reforge":          ORANGE,
    "Augment":          GREEN,
    "Remove/Add":       TEAL,
    "Set Numeric Value": RED,
    "Split / Duplicate": PURPLE,
    "Enchant":          DIM,
}


def _load_data() -> dict:
    if not os.path.exists(_DATA_PATH):
        return {}
    try:
        with open(_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[HarvestPanel] failed to load data: {e}")
        return {}


class HarvestPanel(QWidget):
    def __init__(self):
        super().__init__()
        data = _load_data()
        self._categories    = data.get("craft_categories", [])
        self._how_it_works  = data.get("how_it_works", "")
        self._lifeforce     = data.get("lifeforce_types", {})
        self._tips          = data.get("tips", [])
        self._active_cat: str | None = None
        self._build_ui()
        self._render_all()

    # ------------------------------------------------------------------

    def _all_crafts(self) -> list[tuple[str, str, dict]]:
        """Flat list of (category_name, lifeforce, craft_dict)."""
        result = []
        for cat in self._categories:
            for craft in cat.get("crafts", []):
                result.append((cat["category"], cat.get("lifeforce", "Any"), craft))
        return result

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        total = sum(len(c.get("crafts", [])) for c in self._categories)
        header = QLabel(f"Harvest Crafting Reference  •  {total} crafts")
        header.setStyleSheet(f"color: {ACCENT}; font-weight: bold; font-size: 13px;")
        layout.addWidget(header)

        if self._how_it_works:
            how_lbl = QLabel(self._how_it_works)
            how_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px;")
            how_lbl.setWordWrap(True)
            layout.addWidget(how_lbl)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Search craft name or effect…")
        self._search.setStyleSheet(
            "QLineEdit { background: #0f0f23; color: #d4c5a9; border: 1px solid #2a2a4a; "
            "border-radius: 4px; padding: 4px 8px; }"
        )
        self._search.textChanged.connect(self._on_search)
        layout.addWidget(self._search)

        # Category filter
        filter_row = QHBoxLayout()
        filter_row.setSpacing(4)
        lbl = QLabel("Type:")
        lbl.setStyleSheet(f"color: {DIM}; font-size: 10px;")
        filter_row.addWidget(lbl)
        self._filter_buttons: dict[str, QPushButton] = {}
        for cat_name in ["All"] + [c["category"] for c in self._categories]:
            btn = QPushButton(cat_name)
            btn.setFixedHeight(22)
            color = _CATEGORY_COLORS.get(cat_name, ACCENT)
            btn.setStyleSheet(
                f"QPushButton {{ background: #0f0f23; color: {DIM}; border: 1px solid #2a2a4a; "
                f"border-radius: 3px; padding: 0 5px; font-size: 10px; }}"
                f"QPushButton:hover {{ background: #1a1a3a; }}"
                f"QPushButton[active='true'] {{ color: {color}; border-color: {color}; }}"
            )
            btn.clicked.connect(lambda _, n=cat_name: self._on_cat_filter(n))
            self._filter_buttons[cat_name] = btn
            filter_row.addWidget(btn)
        filter_row.addStretch()
        layout.addLayout(filter_row)
        self._set_active_cat("All")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        self._container = QWidget()
        self._list_layout = QVBoxLayout(self._container)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(4)
        self._list_layout.addStretch()
        scroll.setWidget(self._container)
        layout.addWidget(scroll)

    def _on_cat_filter(self, name: str):
        self._set_active_cat(name)
        self._on_search(self._search.text())

    def _set_active_cat(self, name: str):
        self._active_cat = None if name == "All" else name
        for btn_name, btn in self._filter_buttons.items():
            btn.setProperty("active", "true" if btn_name == name else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _on_search(self, text: str):
        query = text.strip().lower()
        pool = self._all_crafts()

        if self._active_cat:
            pool = [(cat, lf, c) for cat, lf, c in pool if cat == self._active_cat]

        if query:
            pool = [
                (cat, lf, c) for cat, lf, c in pool
                if query in c.get("name", "").lower()
                or query in c.get("effect", "").lower()
                or query in c.get("notes", "").lower()
                or query in cat.lower()
                or query in lf.lower()
            ]

        self._render_crafts(pool)

    def _render_all(self):
        self._render_crafts(self._all_crafts())

    def _render_crafts(self, crafts: list[tuple[str, str, dict]]):
        while self._list_layout.count() > 1:
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not crafts:
            empty = QLabel("No matching crafts.")
            empty.setStyleSheet(f"color: {DIM}; font-size: 11px;")
            self._list_layout.insertWidget(0, empty)
            return

        for i, (cat_name, lifeforce, craft) in enumerate(crafts):
            card = self._make_card(cat_name, lifeforce, craft)
            self._list_layout.insertWidget(i, card)

    def _make_card(self, cat_name: str, lifeforce: str, craft: dict) -> QWidget:
        border_color = _CATEGORY_COLORS.get(cat_name, TEAL)
        value        = craft.get("value", "")
        value_color  = _VALUE_COLORS.get(value, DIM)

        card = QWidget()
        card.setStyleSheet(
            f"background: #0f0f23; border-left: 3px solid {border_color}; border-radius: 2px;"
        )
        vl = QVBoxLayout(card)
        vl.setContentsMargins(8, 5, 8, 5)
        vl.setSpacing(2)

        # Top row: name + category badge + value badge
        top_row = QHBoxLayout()
        top_row.setSpacing(6)

        name_lbl = QLabel(craft.get("name", ""))
        name_lbl.setStyleSheet(f"color: {TEXT}; font-weight: bold; font-size: 11px;")
        top_row.addWidget(name_lbl, 1)

        cat_badge = QLabel(cat_name)
        cat_badge.setStyleSheet(
            f"color: {border_color}; font-size: 9px; background: #1a1a3a; "
            f"border-radius: 2px; padding: 1px 4px;"
        )
        top_row.addWidget(cat_badge)

        if value:
            val_badge = QLabel(value)
            val_badge.setStyleSheet(
                f"color: {value_color}; font-size: 9px; background: #1a1a3a; "
                f"border-radius: 2px; padding: 1px 4px;"
            )
            top_row.addWidget(val_badge)

        vl.addLayout(top_row)

        # Effect
        effect = craft.get("effect", "")
        if effect:
            eff_lbl = QLabel(effect)
            eff_lbl.setStyleSheet(f"color: {TEXT}; font-size: 10px;")
            eff_lbl.setWordWrap(True)
            vl.addWidget(eff_lbl)

        # Lifeforce requirement (show only if not "Any")
        if lifeforce and lifeforce != "Any":
            lf_lbl = QLabel(f"Requires: {lifeforce}")
            lf_lbl.setStyleSheet(f"color: {ORANGE}; font-size: 9px;")
            vl.addWidget(lf_lbl)

        # Notes
        notes = craft.get("notes", "")
        if notes:
            notes_lbl = QLabel(notes)
            notes_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px; font-style: italic;")
            notes_lbl.setWordWrap(True)
            vl.addWidget(notes_lbl)

        return card
