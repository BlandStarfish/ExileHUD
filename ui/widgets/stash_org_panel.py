"""
Stash Tab Organisation Guide panel.

Reference for optimal stash tab setup — tab types, what to store in each,
naming conventions for trade site indexing, and general organisation principles.

Data source: data/stash_organization.json
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
GOLD   = "#f5c842"

_DATA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "stash_organization.json"
)

_PRIORITY_COLORS = {
    "Essential": GOLD,
    "High":      ORANGE,
    "Medium":    TEAL,
    "Low":       DIM,
}

_ALL = "All"
_PRIORITIES = ["Essential", "High", "Medium", "Low"]


def _load_data() -> dict:
    if not os.path.exists(_DATA_PATH):
        return {}
    try:
        with open(_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[StashOrgPanel] failed to load data: {e}")
        return {}


class StashOrgPanel(QWidget):
    def __init__(self):
        super().__init__()
        data = _load_data()
        self._tabs        = data.get("tabs", [])
        self._principles  = data.get("principles", [])
        self._tab_types   = data.get("tab_types", [])
        self._intro       = data.get("intro", "")
        self._active_pri  = _ALL
        self._build_ui()
        self._set_priority(_ALL)

    # ------------------------------------------------------------------

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        header = QLabel(f"Stash Organisation Guide  •  {len(self._tabs)} tab types")
        header.setStyleSheet(f"color: {ACCENT}; font-weight: bold; font-size: 13px;")
        layout.addWidget(header)

        if self._intro:
            intro_lbl = QLabel(self._intro)
            intro_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px;")
            intro_lbl.setWordWrap(True)
            layout.addWidget(intro_lbl)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Search by tab name, type, what to store, or tip…")
        self._search.setStyleSheet(
            "QLineEdit { background: #0f0f23; color: #d4c5a9; border: 1px solid #2a2a4a; "
            "border-radius: 4px; padding: 4px 8px; }"
        )
        self._search.textChanged.connect(self._refresh)
        layout.addWidget(self._search)

        # Priority filter buttons
        pri_row = QHBoxLayout()
        pri_row.setSpacing(4)
        self._pri_buttons: dict[str, QPushButton] = {}
        for pri in [_ALL] + _PRIORITIES:
            color = _PRIORITY_COLORS.get(pri, ACCENT)
            btn = QPushButton(pri)
            btn.setFixedHeight(22)
            btn.setStyleSheet(
                f"QPushButton {{ background: #0f0f23; color: {DIM}; border: 1px solid #2a2a4a; "
                f"border-radius: 3px; padding: 0 6px; font-size: 10px; }}"
                f"QPushButton:hover {{ background: #1a1a3a; }}"
                f"QPushButton[active='true'] {{ color: {color}; border-color: {color}; }}"
            )
            btn.clicked.connect(lambda _, p=pri: self._set_priority(p))
            self._pri_buttons[pri] = btn
            pri_row.addWidget(btn)
        pri_row.addStretch()
        layout.addLayout(pri_row)

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

        if self._principles:
            tips_lbl = QLabel("Key principle: " + self._principles[0])
            tips_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px; font-style: italic;")
            tips_lbl.setWordWrap(True)
            layout.addWidget(tips_lbl)

    def _set_priority(self, pri: str):
        self._active_pri = pri
        for p, btn in self._pri_buttons.items():
            btn.setProperty("active", "true" if p == pri else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self._refresh()

    def _matches(self, tab: dict, query: str) -> bool:
        if not query:
            return True
        searchable = " ".join([
            tab.get("name", ""),
            tab.get("tab_type", ""),
            tab.get("priority", ""),
            tab.get("what_to_store", ""),
            tab.get("naming_tip", ""),
            tab.get("notes", ""),
        ]).lower()
        return query in searchable

    def _refresh(self):
        query = self._search.text().strip().lower()
        pool = self._tabs
        if self._active_pri != _ALL:
            pool = [t for t in pool if t.get("priority") == self._active_pri]
        filtered = [t for t in pool if self._matches(t, query)]
        self._render(filtered)

    def _render(self, tabs: list[dict]):
        while self._list_layout.count() > 1:
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not tabs:
            empty = QLabel("No matching stash tabs.")
            empty.setStyleSheet(f"color: {DIM}; font-size: 11px;")
            self._list_layout.insertWidget(0, empty)
            return

        for i, tab in enumerate(tabs):
            card = self._make_card(tab)
            self._list_layout.insertWidget(i, card)

    def _make_card(self, tab: dict) -> QFrame:
        priority = tab.get("priority", "")
        color = _PRIORITY_COLORS.get(priority, ACCENT)

        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background: #0f0f1e; border: 1px solid #2a2a4a; "
            f"border-left: 3px solid {color}; border-radius: 4px; padding: 4px; }}"
        )
        cl = QVBoxLayout(card)
        cl.setContentsMargins(6, 4, 6, 4)
        cl.setSpacing(3)

        # Header: tab name + type badge + priority badge
        header_row = QHBoxLayout()
        name_lbl = QLabel(tab.get("name", ""))
        name_lbl.setStyleSheet(f"color: {ACCENT}; font-weight: bold; font-size: 12px;")
        header_row.addWidget(name_lbl, 1)
        tab_type = tab.get("tab_type", "")
        if tab_type:
            type_badge = QLabel(tab_type)
            type_badge.setStyleSheet(f"color: {TEAL}; font-size: 10px; font-weight: bold;")
            header_row.addWidget(type_badge)
        if priority:
            pri_badge = QLabel(priority)
            pri_badge.setStyleSheet(f"color: {color}; font-size: 10px;")
            header_row.addWidget(pri_badge)
        cl.addLayout(header_row)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #2a2a4a;")
        cl.addWidget(sep)

        # What to store
        what = tab.get("what_to_store", "")
        if what:
            what_lbl = QLabel(f"Store: {what}")
            what_lbl.setStyleSheet(f"color: {TEXT}; font-size: 10px;")
            what_lbl.setWordWrap(True)
            cl.addWidget(what_lbl)

        # Naming tip
        naming = tab.get("naming_tip", "")
        if naming:
            naming_lbl = QLabel(f"Name: {naming}")
            naming_lbl.setStyleSheet(f"color: {GREEN}; font-size: 10px;")
            naming_lbl.setWordWrap(True)
            cl.addWidget(naming_lbl)

        # Notes
        notes = tab.get("notes", "")
        if notes:
            notes_lbl = QLabel(notes)
            notes_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px; font-style: italic;")
            notes_lbl.setWordWrap(True)
            cl.addWidget(notes_lbl)

        return card
