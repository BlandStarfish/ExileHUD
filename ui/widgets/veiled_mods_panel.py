"""
Veiled Mod Crafting Reference panel.

Reference for Betrayal veiled modifier crafting via Jun Ortoi.
Covers all major veiled mods by item slot with tiers, value ratings,
and best-for guidance.

Data source: data/veiled_mods.json
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
    os.path.dirname(__file__), "..", "..", "data", "veiled_mods.json"
)

_SLOT_COLORS = {
    "Helmet":       PURPLE,
    "Body Armour":  BLUE,
    "Gloves":       TEAL,
    "Boots":        GREEN,
    "Belt":         ORANGE,
    "Ring":         RED,
    "Amulet":       GOLD,
    "Weapon":       ACCENT,
    "Shield":       BLUE,
}

_TYPE_COLORS = {
    "Prefix": ORANGE,
    "Suffix": TEAL,
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
        print(f"[VeiledModsPanel] failed to load data: {e}")
        return {}


class VeiledModsPanel(QWidget):
    def __init__(self):
        super().__init__()
        data = _load_data()
        self._mods         = data.get("mods", [])
        self._how_it_works = data.get("how_it_works", "")
        self._tips         = data.get("tips", [])
        self._categories   = data.get("categories", [])
        self._slot_filter  = [_ALL] + self._categories
        self._active_slot  = _ALL
        self._build_ui()
        self._set_slot(_ALL)

    # ------------------------------------------------------------------

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        header = QLabel(f"Veiled Mod Reference  •  {len(self._mods)} mods")
        header.setStyleSheet(f"color: {ACCENT}; font-weight: bold; font-size: 13px;")
        layout.addWidget(header)

        if self._how_it_works:
            how_lbl = QLabel(self._how_it_works)
            how_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px;")
            how_lbl.setWordWrap(True)
            layout.addWidget(how_lbl)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Search by mod name, slot, effect, best-for builds…")
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
        for slot in self._slot_filter:
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

    def _matches(self, mod: dict, query: str) -> bool:
        if not query:
            return True
        searchable = " ".join([
            mod.get("mod_name", ""),
            mod.get("item_slot", ""),
            mod.get("mod_type", ""),
            mod.get("best_tier", ""),
            " ".join(mod.get("tiers", [])),
            mod.get("value_tier", ""),
            " ".join(mod.get("best_for", [])),
            mod.get("notes", ""),
        ]).lower()
        return query in searchable

    def _refresh(self):
        query = self._search.text().strip().lower()
        pool = self._mods
        if self._active_slot != _ALL:
            pool = [m for m in pool if m.get("item_slot") == self._active_slot]
        filtered = [m for m in pool if self._matches(m, query)]
        self._render(filtered)

    def _render(self, mods: list[dict]):
        while self._list_layout.count() > 1:
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not mods:
            empty = QLabel("No matching veiled mods.")
            empty.setStyleSheet(f"color: {DIM}; font-size: 11px;")
            self._list_layout.insertWidget(0, empty)
            return

        for i, mod in enumerate(mods):
            card = self._make_card(mod)
            self._list_layout.insertWidget(i, card)

    def _make_card(self, mod: dict) -> QFrame:
        slot = mod.get("item_slot", "")
        mod_type = mod.get("mod_type", "")
        color = _SLOT_COLORS.get(slot, ACCENT)
        type_color = _TYPE_COLORS.get(mod_type, DIM)

        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background: #0f0f1e; border: 1px solid #2a2a4a; "
            f"border-left: 3px solid {color}; border-radius: 4px; padding: 4px; }}"
        )
        cl = QVBoxLayout(card)
        cl.setContentsMargins(6, 4, 6, 4)
        cl.setSpacing(3)

        # Header: mod name + slot badge + prefix/suffix badge
        header_row = QHBoxLayout()
        name_lbl = QLabel(mod.get("mod_name", ""))
        name_lbl.setStyleSheet(f"color: {ACCENT}; font-weight: bold; font-size: 12px;")
        name_lbl.setWordWrap(True)
        header_row.addWidget(name_lbl, 1)
        if slot:
            slot_badge = QLabel(f"[{slot}]")
            slot_badge.setStyleSheet(f"color: {color}; font-size: 10px; font-weight: bold;")
            header_row.addWidget(slot_badge)
        if mod_type:
            type_badge = QLabel(mod_type)
            type_badge.setStyleSheet(f"color: {type_color}; font-size: 10px;")
            header_row.addWidget(type_badge)
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

        # Tiers
        tiers = mod.get("tiers", [])
        best_tier = mod.get("best_tier", "")
        if tiers:
            for i, tier in enumerate(tiers):
                tier_lbl = QLabel(f"T{i+1}: {tier}")
                is_best = tier == best_tier
                tier_color_lbl = GOLD if is_best else TEXT
                tier_lbl.setStyleSheet(
                    f"color: {tier_color_lbl}; font-size: 10px;"
                    + (" font-weight: bold;" if is_best else "")
                )
                cl.addWidget(tier_lbl)

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
