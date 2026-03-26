"""
Unique Item Tier List panel.

Reference for top-tier unique items sorted by budget tier.
Covers mirror-tier, high-budget, mid-budget, league-starter,
and leveling uniques with source, key effect, and build guidance.

Data source: data/unique_items.json
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
    os.path.dirname(__file__), "..", "..", "data", "unique_items.json"
)

_BUDGET_COLORS = {
    "Mirror-Tier":    GOLD,
    "High Budget":    ORANGE,
    "Mid Budget":     TEAL,
    "League Starter": GREEN,
    "Leveling":       BLUE,
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
        print(f"[UniqueItemsPanel] failed to load data: {e}")
        return {}


class UniqueItemsPanel(QWidget):
    def __init__(self):
        super().__init__()
        data = _load_data()
        self._items        = data.get("items", [])
        self._how_it_works = data.get("how_it_works", "")
        self._tips         = data.get("tips", [])
        self._budget_tiers = [_ALL] + data.get("budget_tiers", [])
        self._active_tier  = _ALL
        self._build_ui()
        self._set_tier(_ALL)

    # ------------------------------------------------------------------

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        header = QLabel(f"Unique Item Tier List  •  {len(self._items)} items")
        header.setStyleSheet(f"color: {ACCENT}; font-weight: bold; font-size: 13px;")
        layout.addWidget(header)

        if self._how_it_works:
            how_lbl = QLabel(self._how_it_works)
            how_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px;")
            how_lbl.setWordWrap(True)
            layout.addWidget(how_lbl)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Search by item name, slot, effect, best-for builds…")
        self._search.setStyleSheet(
            "QLineEdit { background: #0f0f23; color: #d4c5a9; border: 1px solid #2a2a4a; "
            "border-radius: 4px; padding: 4px 8px; }"
        )
        self._search.textChanged.connect(self._refresh)
        layout.addWidget(self._search)

        # Budget tier filter buttons
        tier_row = QHBoxLayout()
        tier_row.setSpacing(4)
        self._tier_buttons: dict[str, QPushButton] = {}
        for tier in self._budget_tiers:
            color = _BUDGET_COLORS.get(tier, ACCENT)
            btn = QPushButton(tier)
            btn.setFixedHeight(22)
            btn.setStyleSheet(
                f"QPushButton {{ background: #0f0f23; color: {DIM}; border: 1px solid #2a2a4a; "
                f"border-radius: 3px; padding: 0 6px; font-size: 10px; }}"
                f"QPushButton:hover {{ background: #1a1a3a; }}"
                f"QPushButton[active='true'] {{ color: {color}; border-color: {color}; }}"
            )
            btn.clicked.connect(lambda _, t=tier: self._set_tier(t))
            self._tier_buttons[tier] = btn
            tier_row.addWidget(btn)
        tier_row.addStretch()
        layout.addLayout(tier_row)

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

    def _set_tier(self, tier: str):
        self._active_tier = tier
        for t, btn in self._tier_buttons.items():
            btn.setProperty("active", "true" if t == tier else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self._refresh()

    def _matches(self, item: dict, query: str) -> bool:
        if not query:
            return True
        searchable = " ".join([
            item.get("name", ""),
            item.get("slot", ""),
            item.get("budget_tier", ""),
            item.get("source", ""),
            item.get("key_effect", ""),
            item.get("value_tier", ""),
            " ".join(item.get("best_for", [])),
            item.get("why_valuable", ""),
            item.get("notes", ""),
        ]).lower()
        return query in searchable

    def _refresh(self):
        query = self._search.text().strip().lower()
        pool = self._items
        if self._active_tier != _ALL:
            pool = [i for i in pool if i.get("budget_tier") == self._active_tier]
        filtered = [i for i in pool if self._matches(i, query)]
        self._render(filtered)

    def _render(self, items: list[dict]):
        while self._list_layout.count() > 1:
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not items:
            empty = QLabel("No matching unique items.")
            empty.setStyleSheet(f"color: {DIM}; font-size: 11px;")
            self._list_layout.insertWidget(0, empty)
            return

        for i, item in enumerate(items):
            card = self._make_card(item)
            self._list_layout.insertWidget(i, card)

    def _make_card(self, item: dict) -> QFrame:
        budget_tier = item.get("budget_tier", "")
        color = _BUDGET_COLORS.get(budget_tier, ACCENT)

        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background: #0f0f1e; border: 1px solid #2a2a4a; "
            f"border-left: 3px solid {color}; border-radius: 4px; padding: 4px; }}"
        )
        cl = QVBoxLayout(card)
        cl.setContentsMargins(6, 4, 6, 4)
        cl.setSpacing(3)

        # Header: item name + slot badge + budget tier
        header_row = QHBoxLayout()
        name_lbl = QLabel(item.get("name", ""))
        name_lbl.setStyleSheet(f"color: {ACCENT}; font-weight: bold; font-size: 12px;")
        name_lbl.setWordWrap(True)
        header_row.addWidget(name_lbl, 1)
        slot = item.get("slot", "")
        if slot:
            slot_badge = QLabel(f"[{slot}]")
            slot_badge.setStyleSheet(f"color: {DIM}; font-size: 10px;")
            header_row.addWidget(slot_badge)
        if budget_tier:
            bt_badge = QLabel(budget_tier)
            bt_badge.setStyleSheet(f"color: {color}; font-size: 10px; font-weight: bold;")
            header_row.addWidget(bt_badge)
        cl.addLayout(header_row)

        # Value tier
        val_tier = item.get("value_tier", "")
        if val_tier:
            tier_color = _VALUE_COLORS.get(val_tier, DIM)
            tier_lbl = QLabel(f"Value: {val_tier}")
            tier_lbl.setStyleSheet(f"color: {tier_color}; font-size: 10px; font-weight: bold;")
            cl.addWidget(tier_lbl)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #2a2a4a;")
        cl.addWidget(sep)

        # Key effect
        key_effect = item.get("key_effect", "")
        if key_effect:
            effect_lbl = QLabel(key_effect)
            effect_lbl.setStyleSheet(f"color: {TEXT}; font-size: 11px;")
            effect_lbl.setWordWrap(True)
            cl.addWidget(effect_lbl)

        # Why valuable
        why = item.get("why_valuable", "")
        if why:
            why_lbl = QLabel(why)
            why_lbl.setStyleSheet(f"color: {GOLD}; font-size: 10px;")
            why_lbl.setWordWrap(True)
            cl.addWidget(why_lbl)

        # Source
        source = item.get("source", "")
        if source:
            src_lbl = QLabel(f"Source: {source}")
            src_lbl.setStyleSheet(f"color: {ORANGE}; font-size: 10px;")
            src_lbl.setWordWrap(True)
            cl.addWidget(src_lbl)

        # Best for
        best_for = item.get("best_for", [])
        if best_for:
            bf_lbl = QLabel("Best for: " + ", ".join(best_for))
            bf_lbl.setStyleSheet(f"color: {TEAL}; font-size: 10px;")
            bf_lbl.setWordWrap(True)
            cl.addWidget(bf_lbl)

        # Notes
        notes = item.get("notes", "")
        if notes:
            notes_lbl = QLabel(notes)
            notes_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px; font-style: italic;")
            notes_lbl.setWordWrap(True)
            cl.addWidget(notes_lbl)

        return card
