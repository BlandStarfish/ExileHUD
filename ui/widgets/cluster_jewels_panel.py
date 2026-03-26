"""
Cluster Jewel Reference panel.

Reference for Large, Medium, and Small Cluster Jewels — their enchants,
key notables, optimal passive counts, and best build applications.

Data source: data/cluster_jewels.json
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
    os.path.dirname(__file__), "..", "..", "data", "cluster_jewels.json"
)

_SIZE_COLORS = {
    "Large":  ORANGE,
    "Medium": TEAL,
    "Small":  BLUE,
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
        print(f"[ClusterJewelsPanel] failed to load data: {e}")
        return {}


class ClusterJewelsPanel(QWidget):
    def __init__(self):
        super().__init__()
        data = _load_data()
        self._jewels       = data.get("jewels", [])
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

        header = QLabel(f"Cluster Jewel Reference  •  {len(self._jewels)} jewels")
        header.setStyleSheet(f"color: {ACCENT}; font-weight: bold; font-size: 13px;")
        layout.addWidget(header)

        if self._how_it_works:
            how_lbl = QLabel(self._how_it_works)
            how_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px;")
            how_lbl.setWordWrap(True)
            layout.addWidget(how_lbl)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Search by name, enchant, notable, or build type…")
        self._search.setStyleSheet(
            "QLineEdit { background: #0f0f23; color: #d4c5a9; border: 1px solid #2a2a4a; "
            "border-radius: 4px; padding: 4px 8px; }"
        )
        self._search.textChanged.connect(self._refresh)
        layout.addWidget(self._search)

        # Size filter buttons
        cat_row = QHBoxLayout()
        cat_row.setSpacing(5)
        self._cat_buttons: dict[str, QPushButton] = {}
        for cat in self._categories:
            color = _SIZE_COLORS.get(cat, ACCENT)
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

    def _matches(self, jewel: dict, query: str) -> bool:
        if not query:
            return True
        searchable = " ".join([
            jewel.get("name", ""),
            jewel.get("size", ""),
            jewel.get("enchant", ""),
            " ".join(jewel.get("key_notables", [])),
            jewel.get("notable_count", ""),
            jewel.get("optimal_passive_count", ""),
            " ".join(jewel.get("best_for", [])),
            jewel.get("value_tier", ""),
            jewel.get("notes", ""),
        ]).lower()
        return query in searchable

    def _refresh(self):
        query = self._search.text().strip().lower()
        pool = self._jewels
        if self._active_cat != _ALL:
            pool = [j for j in pool if j.get("size") == self._active_cat]
        filtered = [j for j in pool if self._matches(j, query)]
        self._render(filtered)

    def _render(self, jewels: list[dict]):
        while self._list_layout.count() > 1:
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not jewels:
            empty = QLabel("No matching cluster jewels.")
            empty.setStyleSheet(f"color: {DIM}; font-size: 11px;")
            self._list_layout.insertWidget(0, empty)
            return

        for i, jewel in enumerate(jewels):
            card = self._make_card(jewel)
            self._list_layout.insertWidget(i, card)

    def _make_card(self, jewel: dict) -> QFrame:
        size  = jewel.get("size", "")
        color = _SIZE_COLORS.get(size, ACCENT)

        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background: #0f0f1e; border: 1px solid #2a2a4a; "
            f"border-left: 3px solid {color}; border-radius: 4px; padding: 4px; }}"
        )
        cl = QVBoxLayout(card)
        cl.setContentsMargins(6, 4, 6, 4)
        cl.setSpacing(3)

        # Header: jewel name + size badge + value tier
        header_row = QHBoxLayout()
        name_lbl = QLabel(jewel.get("name", ""))
        name_lbl.setStyleSheet(f"color: {ACCENT}; font-weight: bold; font-size: 12px;")
        header_row.addWidget(name_lbl)
        header_row.addStretch()
        if size:
            size_badge = QLabel(f"[{size}]")
            size_badge.setStyleSheet(f"color: {color}; font-size: 10px;")
            header_row.addWidget(size_badge)
        val_tier = jewel.get("value_tier", "")
        if val_tier:
            tier_color = _VALUE_COLORS.get(val_tier, DIM)
            tier_lbl = QLabel(val_tier)
            tier_lbl.setStyleSheet(f"color: {tier_color}; font-size: 10px; font-weight: bold;")
            header_row.addWidget(tier_lbl)
        cl.addLayout(header_row)

        # Enchant
        enchant = jewel.get("enchant", "")
        if enchant:
            enc_lbl = QLabel(f"Enchant: {enchant}")
            enc_lbl.setStyleSheet(f"color: {TEXT}; font-size: 10px;")
            enc_lbl.setWordWrap(True)
            cl.addWidget(enc_lbl)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #2a2a4a;")
        cl.addWidget(sep)

        # Key notables
        notables = jewel.get("key_notables", [])
        if notables:
            not_lbl = QLabel("Notables: " + ", ".join(notables))
            not_lbl.setStyleSheet(f"color: {GOLD}; font-size: 10px;")
            not_lbl.setWordWrap(True)
            cl.addWidget(not_lbl)

        # Notable count + optimal passives
        meta_row = QHBoxLayout()
        notable_count = jewel.get("notable_count", "")
        if notable_count:
            nc_lbl = QLabel(notable_count)
            nc_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px;")
            meta_row.addWidget(nc_lbl)
        meta_row.addStretch()
        opt_count = jewel.get("optimal_passive_count", "")
        if opt_count:
            oc_lbl = QLabel(f"Target: {opt_count} passives")
            oc_lbl.setStyleSheet(f"color: {ORANGE}; font-size: 10px;")
            meta_row.addWidget(oc_lbl)
        cl.addLayout(meta_row)

        # Best for
        best_for = jewel.get("best_for", [])
        if best_for:
            bf_lbl = QLabel("Best for: " + ", ".join(best_for))
            bf_lbl.setStyleSheet(f"color: {TEAL}; font-size: 10px;")
            bf_lbl.setWordWrap(True)
            cl.addWidget(bf_lbl)

        # Notes
        notes = jewel.get("notes", "")
        if notes:
            notes_lbl = QLabel(notes)
            notes_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px; font-style: italic;")
            notes_lbl.setWordWrap(True)
            cl.addWidget(notes_lbl)

        return card
