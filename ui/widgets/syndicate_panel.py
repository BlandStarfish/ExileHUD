"""
Syndicate Member Planner panel.

Static reference for all 22 Betrayal Syndicate members: their division affinities,
safehouse rewards per division, and intel rewards. Searchable and filterable.

Data source: data/syndicate_members.json
No API calls — zero latency, always accurate.
"""

import json
import os

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QScrollArea, QFrame, QPushButton,
)
from PyQt6.QtCore import Qt

ACCENT = "#e2b96f"
TEXT   = "#d4c5a9"
DIM    = "#8a7a65"
TEAL   = "#4ae8c8"
RED    = "#e05050"
ORANGE = "#e8864a"
GREEN  = "#5cba6e"
BLUE   = "#4a9de8"
PURPLE = "#9a4ae8"

_DATA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "syndicate_members.json"
)

# Color per division
_DIVISION_COLORS = {
    "Transportation": TEAL,
    "Research":       ACCENT,
    "Fortification":  ORANGE,
    "Intervention":   RED,
}

# All 4 divisions for filter buttons
_DIVISIONS = ["Transportation", "Research", "Fortification", "Intervention"]


def _load_members() -> list[dict]:
    if not os.path.exists(_DATA_PATH):
        return []
    try:
        with open(_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f).get("members", [])
    except Exception as e:
        print(f"[SyndicatePanel] failed to load members: {e}")
        return []


class SyndicatePanel(QWidget):
    def __init__(self):
        super().__init__()
        self._all_members = _load_members()
        self._active_division: str | None = None
        self._build_ui()
        self._render_members(self._all_members)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        header = QLabel(f"Syndicate Members  •  {len(self._all_members)} members")
        header.setStyleSheet(f"color: {ACCENT}; font-weight: bold; font-size: 13px;")
        layout.addWidget(header)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Search by name, reward, or division…")
        self._search.setStyleSheet(
            "QLineEdit { background: #0f0f23; color: #d4c5a9; border: 1px solid #2a2a4a; "
            "border-radius: 4px; padding: 4px 8px; }"
        )
        self._search.textChanged.connect(self._on_search)
        layout.addWidget(self._search)

        # Division filter buttons
        filter_row = QHBoxLayout()
        filter_row.setSpacing(6)
        filter_lbl = QLabel("Division:")
        filter_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px;")
        filter_row.addWidget(filter_lbl)
        self._filter_buttons: dict[str, QPushButton] = {}
        for label in ["All"] + _DIVISIONS:
            btn = QPushButton(label)
            btn.setFixedHeight(22)
            color = _DIVISION_COLORS.get(label, ACCENT)
            btn.setStyleSheet(
                f"QPushButton {{ background: #0f0f23; color: {DIM}; border: 1px solid #2a2a4a; "
                f"border-radius: 3px; padding: 0 8px; font-size: 10px; }}"
                f"QPushButton:hover {{ background: #1a1a3a; }}"
                f"QPushButton[active='true'] {{ color: {color}; border-color: {color}; }}"
            )
            btn.clicked.connect(lambda _, lbl=label: self._on_division_filter(lbl))
            self._filter_buttons[label] = btn
            filter_row.addWidget(btn)
        filter_row.addStretch()
        layout.addLayout(filter_row)
        self._set_active_filter("All")

        # Division color legend
        legend_row = QHBoxLayout()
        legend_row.setSpacing(10)
        for div, color in _DIVISION_COLORS.items():
            lbl = QLabel(f"● {div}")
            lbl.setStyleSheet(f"color: {color}; font-size: 10px;")
            legend_row.addWidget(lbl)
        legend_row.addStretch()
        layout.addLayout(legend_row)

        # Scrollable member list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        self._member_container = QWidget()
        self._member_layout    = QVBoxLayout(self._member_container)
        self._member_layout.setContentsMargins(0, 0, 0, 0)
        self._member_layout.setSpacing(4)
        self._member_layout.addStretch()
        scroll.setWidget(self._member_container)
        layout.addWidget(scroll)

        note = QLabel(
            "Safehouse rewards unlock crafting bench recipes when you defeat the leader. "
            "Prioritize Research for crafting, Transportation for Vorici/Aisling."
        )
        note.setStyleSheet(f"color: {DIM}; font-size: 10px;")
        note.setWordWrap(True)
        layout.addWidget(note)

    def _on_division_filter(self, label: str):
        self._set_active_filter(label)
        self._on_search(self._search.text())

    def _set_active_filter(self, label: str):
        self._active_division = None if label == "All" else label
        for btn_label, btn in self._filter_buttons.items():
            btn.setProperty("active", "true" if btn_label == label else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _on_search(self, text: str):
        query = text.strip().lower()
        pool = self._all_members

        # Apply division filter
        if self._active_division:
            pool = [m for m in pool if self._active_division in m.get("factions", [])]

        if not query:
            self._render_members(pool)
            return

        filtered = [
            m for m in pool
            if query in m.get("name", "").lower()
            or any(query in div.lower() for div in m.get("factions", []))
            or query in m.get("intel_reward", "").lower()
            or query in m.get("notes", "").lower()
            or any(
                query in reward.lower()
                for reward in m.get("safehouse_rewards", {}).values()
            )
        ]
        self._render_members(filtered)

    def _render_members(self, members: list[dict]):
        # Clear existing cards (preserve trailing stretch)
        while self._member_layout.count() > 1:
            item = self._member_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not members:
            empty = QLabel("No matching members.")
            empty.setStyleSheet(f"color: {DIM}; font-size: 11px;")
            self._member_layout.insertWidget(0, empty)
            return

        for i, member in enumerate(members):
            card = self._make_member_card(member)
            self._member_layout.insertWidget(i, card)

    def _make_member_card(self, member: dict) -> QWidget:
        primary = member.get("primary_faction", "")
        accent_color = _DIVISION_COLORS.get(primary, DIM)

        card = QWidget()
        card.setStyleSheet(
            f"background: #0f0f23; border-left: 3px solid {accent_color}; border-radius: 2px;"
        )
        vl = QVBoxLayout(card)
        vl.setContentsMargins(8, 6, 8, 6)
        vl.setSpacing(4)

        # Name + faction badges
        top_row = QHBoxLayout()
        top_row.setSpacing(6)
        name_lbl = QLabel(member.get("name", ""))
        name_lbl.setStyleSheet(f"color: {ACCENT}; font-weight: bold; font-size: 11px;")
        name_lbl.setWordWrap(True)
        top_row.addWidget(name_lbl, 1)

        for faction in member.get("factions", []):
            color = _DIVISION_COLORS.get(faction, DIM)
            badge = QLabel(faction[:4])  # Abbrev: Tran/Rese/Fort/Inte
            badge.setStyleSheet(
                f"color: {color}; font-size: 9px; background: #1a1a3a; "
                f"border-radius: 2px; padding: 1px 4px;"
            )
            top_row.addWidget(badge)
        vl.addLayout(top_row)

        # Intel reward
        intel = member.get("intel_reward", "")
        if intel:
            intel_lbl = QLabel(f"Intel: {intel}")
            intel_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px;")
            intel_lbl.setWordWrap(True)
            vl.addWidget(intel_lbl)

        # Safehouse rewards per division
        safehouse = member.get("safehouse_rewards", {})
        if safehouse:
            sep = QFrame()
            sep.setFrameShape(QFrame.Shape.HLine)
            sep.setStyleSheet("color: #1a1a3a;")
            vl.addWidget(sep)

            for div, reward in safehouse.items():
                color = _DIVISION_COLORS.get(div, DIM)
                reward_lbl = QLabel(f"<b style='color:{color}'>{div}:</b> {reward}")
                reward_lbl.setStyleSheet(f"color: {TEXT}; font-size: 10px;")
                reward_lbl.setWordWrap(True)
                reward_lbl.setTextFormat(Qt.TextFormat.RichText)
                vl.addWidget(reward_lbl)

        # Notes
        notes = member.get("notes", "")
        if notes:
            notes_lbl = QLabel(notes)
            notes_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px; font-style: italic;")
            notes_lbl.setWordWrap(True)
            vl.addWidget(notes_lbl)

        return card
