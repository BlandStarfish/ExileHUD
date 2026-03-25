"""
Delirium Reward Type Reference panel.

Static reference for all Delirium reward cluster types — what they generate,
high-value drops, and which builds/strategies benefit most.

Apply a Delirium Orb to a map to add a cluster. Up to 5 Orbs can be stacked.

Data source: data/delirium_rewards.json
No API calls — zero latency, always accurate.
"""

import json
import os

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QScrollArea, QFrame,
)

ACCENT = "#e2b96f"
TEXT   = "#d4c5a9"
DIM    = "#8a7a65"
GREEN  = "#5cba6e"
TEAL   = "#4ae8c8"
ORANGE = "#e8864a"
PURPLE = "#9a4ae8"

_DATA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "delirium_rewards.json"
)


def _load_data() -> dict:
    if not os.path.exists(_DATA_PATH):
        return {}
    try:
        with open(_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[DeliriumPanel] failed to load data: {e}")
        return {}


class DeliriumPanel(QWidget):
    def __init__(self):
        super().__init__()
        data = _load_data()
        self._all_types = data.get("reward_types", [])
        self._mechanic_note = data.get("mechanic_note", "")
        self._sim_note      = data.get("simulacrum_note", "")
        self._build_ui()
        self._render_types(self._all_types)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        header = QLabel(f"Delirium Reward Types  •  {len(self._all_types)} types")
        header.setStyleSheet(f"color: {ACCENT}; font-weight: bold; font-size: 13px;")
        layout.addWidget(header)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Search by reward type, drops, or strategy…")
        self._search.setStyleSheet(
            "QLineEdit { background: #0f0f23; color: #d4c5a9; border: 1px solid #2a2a4a; "
            "border-radius: 4px; padding: 4px 8px; }"
        )
        self._search.textChanged.connect(self._on_search)
        layout.addWidget(self._search)

        # Scrollable reward list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        self._reward_container = QWidget()
        self._reward_layout    = QVBoxLayout(self._reward_container)
        self._reward_layout.setContentsMargins(0, 0, 0, 0)
        self._reward_layout.setSpacing(4)
        self._reward_layout.addStretch()
        scroll.setWidget(self._reward_container)
        layout.addWidget(scroll)

        if self._mechanic_note:
            note = QLabel(self._mechanic_note)
            note.setStyleSheet(f"color: {DIM}; font-size: 10px;")
            note.setWordWrap(True)
            layout.addWidget(note)

        if self._sim_note:
            sim = QLabel(self._sim_note)
            sim.setStyleSheet(f"color: {TEAL}; font-size: 10px;")
            sim.setWordWrap(True)
            layout.addWidget(sim)

    def _on_search(self, text: str):
        query = text.strip().lower()
        if not query:
            self._render_types(self._all_types)
            return
        filtered = [
            t for t in self._all_types
            if query in t.get("name", "").lower()
            or query in t.get("description", "").lower()
            or query in t.get("high_value_drops", "").lower()
            or query in t.get("best_for", "").lower()
            or query in t.get("notes", "").lower()
        ]
        self._render_types(filtered)

    def _render_types(self, reward_types: list[dict]):
        while self._reward_layout.count() > 1:
            item = self._reward_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not reward_types:
            empty = QLabel("No matching reward types.")
            empty.setStyleSheet(f"color: {DIM}; font-size: 11px;")
            self._reward_layout.insertWidget(0, empty)
            return

        for i, rtype in enumerate(reward_types):
            card = self._make_reward_card(rtype)
            self._reward_layout.insertWidget(i, card)

    def _make_reward_card(self, rtype: dict) -> QWidget:
        card = QWidget()
        card.setStyleSheet(
            f"background: #0f0f23; border-left: 3px solid {ACCENT}; border-radius: 2px;"
        )
        vl = QVBoxLayout(card)
        vl.setContentsMargins(8, 6, 8, 6)
        vl.setSpacing(3)

        # Name header
        name_lbl = QLabel(rtype.get("name", ""))
        name_lbl.setStyleSheet(f"color: {ACCENT}; font-weight: bold; font-size: 12px;")
        vl.addWidget(name_lbl)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #1a1a3a;")
        vl.addWidget(sep)

        # Description
        desc = rtype.get("description", "")
        if desc:
            desc_lbl = QLabel(desc)
            desc_lbl.setStyleSheet(f"color: {TEXT}; font-size: 11px;")
            desc_lbl.setWordWrap(True)
            vl.addWidget(desc_lbl)

        # High-value drops
        hvd = rtype.get("high_value_drops", "")
        if hvd:
            hvd_lbl = QLabel(
                f"<b style='color:{GREEN}'>High value:</b> "
                f"<span style='color:{TEXT}'>{hvd}</span>"
            )
            hvd_lbl.setTextFormat(Qt.TextFormat.RichText)
            hvd_lbl.setWordWrap(True)
            hvd_lbl.setStyleSheet("font-size: 10px;")
            vl.addWidget(hvd_lbl)

        # Best for
        best = rtype.get("best_for", "")
        if best:
            best_lbl = QLabel(
                f"<b style='color:{TEAL}'>Best for:</b> "
                f"<span style='color:{DIM}'>{best}</span>"
            )
            best_lbl.setTextFormat(Qt.TextFormat.RichText)
            best_lbl.setWordWrap(True)
            best_lbl.setStyleSheet("font-size: 10px;")
            vl.addWidget(best_lbl)

        # Notes
        notes = rtype.get("notes", "")
        if notes:
            notes_lbl = QLabel(notes)
            notes_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px; font-style: italic;")
            notes_lbl.setWordWrap(True)
            vl.addWidget(notes_lbl)

        return card
