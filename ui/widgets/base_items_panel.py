"""
Base Item Type Reference panel.

Reference for important crafting base item types across all slots.
Covers implicits, defense values, why each base is valuable, and which builds use them.

Data source: data/base_items.json
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
    os.path.dirname(__file__), "..", "..", "data", "base_items.json"
)

_SLOT_COLORS = {
    "Helmet":            PURPLE,
    "Body Armour":       BLUE,
    "Gloves":            TEAL,
    "Boots":             GREEN,
    "Belt":              ORANGE,
    "Ring":              RED,
    "Amulet":            GOLD,
    "One-Handed Weapon": ACCENT,
    "Two-Handed Weapon": ACCENT,
    "Shield":            BLUE,
    "Quiver":            GREEN,
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
        print(f"[BaseItemsPanel] failed to load data: {e}")
        return {}


class BaseItemsPanel(QWidget):
    def __init__(self):
        super().__init__()
        data = _load_data()
        self._bases        = data.get("bases", [])
        self._how_it_works = data.get("how_it_works", "")
        self._tips         = data.get("tips", [])
        self._slot_types   = [_ALL] + data.get("slot_types", [])
        self._active_slot  = _ALL
        self._build_ui()
        self._set_slot(_ALL)

    # ------------------------------------------------------------------

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        header = QLabel(f"Base Item Reference  •  {len(self._bases)} bases")
        header.setStyleSheet(f"color: {ACCENT}; font-weight: bold; font-size: 13px;")
        layout.addWidget(header)

        if self._how_it_works:
            how_lbl = QLabel(self._how_it_works)
            how_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px;")
            how_lbl.setWordWrap(True)
            layout.addWidget(how_lbl)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Search by base name, implicit, slot, best-for builds…")
        self._search.setStyleSheet(
            "QLineEdit { background: #0f0f23; color: #d4c5a9; border: 1px solid #2a2a4a; "
            "border-radius: 4px; padding: 4px 8px; }"
        )
        self._search.textChanged.connect(self._refresh)
        layout.addWidget(self._search)

        # Slot filter buttons
        slot_row = QHBoxLayout()
        slot_row.setSpacing(4)
        self._slot_buttons: dict[str, QPushButton] = {}
        for slot in self._slot_types:
            color = _SLOT_COLORS.get(slot, ACCENT)
            btn = QPushButton(slot)
            btn.setFixedHeight(22)
            btn.setStyleSheet(
                f"QPushButton {{ background: #0f0f23; color: {DIM}; border: 1px solid #2a2a4a; "
                f"border-radius: 3px; padding: 0 6px; font-size: 10px; }}"
                f"QPushButton:hover {{ background: #1a1a3a; }}"
                f"QPushButton[active='true'] {{ color: {color}; border-color: {color}; }}"
            )
            btn.clicked.connect(lambda _, s=slot: self._set_slot(s))
            self._slot_buttons[slot] = btn
            slot_row.addWidget(btn)
        slot_row.addStretch()
        layout.addLayout(slot_row)

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

    def _set_slot(self, slot: str):
        self._active_slot = slot
        for s, btn in self._slot_buttons.items():
            btn.setProperty("active", "true" if s == slot else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self._refresh()

    def _matches(self, base: dict, query: str) -> bool:
        if not query:
            return True
        searchable = " ".join([
            base.get("name", ""),
            base.get("slot", ""),
            base.get("base_type", ""),
            base.get("implicit", ""),
            base.get("why_valuable", ""),
            base.get("value_tier", ""),
            " ".join(base.get("best_for", [])),
            base.get("notes", ""),
        ]).lower()
        return query in searchable

    def _refresh(self):
        query = self._search.text().strip().lower()
        pool = self._bases
        if self._active_slot != _ALL:
            pool = [b for b in pool if b.get("slot") == self._active_slot]
        filtered = [b for b in pool if self._matches(b, query)]
        self._render(filtered)

    def _render(self, bases: list[dict]):
        while self._list_layout.count() > 1:
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not bases:
            empty = QLabel("No matching base items.")
            empty.setStyleSheet(f"color: {DIM}; font-size: 11px;")
            self._list_layout.insertWidget(0, empty)
            return

        for i, base in enumerate(bases):
            card = self._make_card(base)
            self._list_layout.insertWidget(i, card)

    def _make_card(self, base: dict) -> QFrame:
        slot = base.get("slot", "")
        color = _SLOT_COLORS.get(slot, ACCENT)

        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background: #0f0f1e; border: 1px solid #2a2a4a; "
            f"border-left: 3px solid {color}; border-radius: 4px; padding: 4px; }}"
        )
        cl = QVBoxLayout(card)
        cl.setContentsMargins(6, 4, 6, 4)
        cl.setSpacing(3)

        # Header: base name + slot badge + value tier
        header_row = QHBoxLayout()
        name_lbl = QLabel(base.get("name", ""))
        name_lbl.setStyleSheet(f"color: {ACCENT}; font-weight: bold; font-size: 12px;")
        header_row.addWidget(name_lbl)
        header_row.addStretch()
        if slot:
            slot_badge = QLabel(f"[{slot}]")
            slot_badge.setStyleSheet(f"color: {color}; font-size: 10px; font-weight: bold;")
            header_row.addWidget(slot_badge)
        cl.addLayout(header_row)

        # Base type + item level req
        meta_row = QHBoxLayout()
        base_type = base.get("base_type", "")
        if base_type:
            type_lbl = QLabel(base_type)
            type_lbl.setStyleSheet(f"color: {TEAL}; font-size: 10px;")
            meta_row.addWidget(type_lbl)
        ilvl = base.get("item_level_req", "")
        if ilvl:
            ilvl_lbl = QLabel(f"ilvl {ilvl}+")
            ilvl_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px;")
            meta_row.addWidget(ilvl_lbl)
        meta_row.addStretch()
        val_tier = base.get("value_tier", "")
        if val_tier:
            tier_color = _VALUE_COLORS.get(val_tier, DIM)
            tier_lbl = QLabel(val_tier)
            tier_lbl.setStyleSheet(f"color: {tier_color}; font-size: 10px; font-weight: bold;")
            meta_row.addWidget(tier_lbl)
        cl.addLayout(meta_row)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #2a2a4a;")
        cl.addWidget(sep)

        # Implicit
        implicit = base.get("implicit", "")
        if implicit and implicit != "None":
            imp_lbl = QLabel(f"Implicit: {implicit}")
            imp_lbl.setStyleSheet(f"color: {GOLD}; font-size: 10px; font-style: italic;")
            imp_lbl.setWordWrap(True)
            cl.addWidget(imp_lbl)

        # Max defense
        max_def = base.get("max_defense", "")
        if max_def and max_def != "N/A":
            def_lbl = QLabel(f"Defence: {max_def}")
            def_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px;")
            cl.addWidget(def_lbl)

        # Why valuable
        why = base.get("why_valuable", "")
        if why:
            why_lbl = QLabel(why)
            why_lbl.setStyleSheet(f"color: {TEXT}; font-size: 11px;")
            why_lbl.setWordWrap(True)
            cl.addWidget(why_lbl)

        # Best for
        best_for = base.get("best_for", [])
        if best_for:
            bf_lbl = QLabel("Best for: " + ", ".join(best_for))
            bf_lbl.setStyleSheet(f"color: {TEAL}; font-size: 10px;")
            bf_lbl.setWordWrap(True)
            cl.addWidget(bf_lbl)

        # Notes
        notes = base.get("notes", "")
        if notes:
            notes_lbl = QLabel(notes)
            notes_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px; font-style: italic;")
            notes_lbl.setWordWrap(True)
            cl.addWidget(notes_lbl)

        return card
