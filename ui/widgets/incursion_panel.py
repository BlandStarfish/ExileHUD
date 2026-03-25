"""
Incursion Temple Room Reference panel.

Static reference for all Alva temple room chains — T1/T2/T3 names, what each T3
room drops, and upgrade priority.

Data source: data/incursion_rooms.json
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
    os.path.dirname(__file__), "..", "..", "data", "incursion_rooms.json"
)

_PRIORITY_COLORS = {
    "must_have": RED,
    "high":      ORANGE,
    "medium":    TEAL,
    "low":       DIM,
}

_PRIORITY_LABELS = {
    "must_have": "Must Have",
    "high":      "High",
    "medium":    "Medium",
    "low":       "Low",
}

_PRIORITY_ORDER = ["must_have", "high", "medium", "low"]


def _load_data() -> dict:
    if not os.path.exists(_DATA_PATH):
        return {}
    try:
        with open(_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[IncursionPanel] failed to load data: {e}")
        return {}


class IncursionPanel(QWidget):
    def __init__(self):
        super().__init__()
        data = _load_data()
        self._all_rooms = data.get("rooms", [])
        self._tips      = data.get("tips", [])
        self._active_priority: str | None = None
        self._build_ui()
        self._render_rooms(self._all_rooms)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        header = QLabel(f"Incursion Temple Rooms  •  {len(self._all_rooms)} room chains")
        header.setStyleSheet(f"color: {ACCENT}; font-weight: bold; font-size: 13px;")
        layout.addWidget(header)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Search by room name, drops, category…")
        self._search.setStyleSheet(
            "QLineEdit { background: #0f0f23; color: #d4c5a9; border: 1px solid #2a2a4a; "
            "border-radius: 4px; padding: 4px 8px; }"
        )
        self._search.textChanged.connect(self._on_search)
        layout.addWidget(self._search)

        # Priority filter buttons
        filter_row = QHBoxLayout()
        filter_row.setSpacing(4)
        filter_lbl = QLabel("Priority:")
        filter_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px;")
        filter_row.addWidget(filter_lbl)
        self._filter_buttons: dict[str, QPushButton] = {}
        for label in ["All", "Must Have", "High", "Medium", "Low"]:
            btn = QPushButton(label)
            btn.setFixedHeight(22)
            key = label.lower().replace(" ", "_")
            color = _PRIORITY_COLORS.get(key, ACCENT)
            btn.setStyleSheet(
                f"QPushButton {{ background: #0f0f23; color: {DIM}; border: 1px solid #2a2a4a; "
                f"border-radius: 3px; padding: 0 6px; font-size: 10px; }}"
                f"QPushButton:hover {{ background: #1a1a3a; }}"
                f"QPushButton[active='true'] {{ color: {color}; border-color: {color}; }}"
            )
            btn.clicked.connect(lambda _, lbl=label: self._on_priority_filter(lbl))
            self._filter_buttons[label] = btn
            filter_row.addWidget(btn)
        filter_row.addStretch()
        layout.addLayout(filter_row)
        self._set_active_filter("All")

        # Scrollable room list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        self._room_container = QWidget()
        self._room_layout    = QVBoxLayout(self._room_container)
        self._room_layout.setContentsMargins(0, 0, 0, 0)
        self._room_layout.setSpacing(5)
        self._room_layout.addStretch()
        scroll.setWidget(self._room_container)
        layout.addWidget(scroll)

    def _on_priority_filter(self, label: str):
        self._set_active_filter(label)
        self._on_search(self._search.text())

    def _set_active_filter(self, label: str):
        key = label.lower().replace(" ", "_")
        self._active_priority = None if label == "All" else key
        for btn_label, btn in self._filter_buttons.items():
            btn.setProperty("active", "true" if btn_label == label else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _on_search(self, text: str):
        query = text.strip().lower()
        pool  = self._all_rooms

        if self._active_priority:
            pool = [r for r in pool if r.get("priority") == self._active_priority]

        if not query:
            self._render_rooms(pool)
            return

        filtered = [
            r for r in pool
            if query in r.get("t1", "").lower()
            or query in r.get("t2", "").lower()
            or query in r.get("t3", "").lower()
            or query in r.get("category", "").lower()
            or query in r.get("drops", "").lower()
            or query in r.get("notes", "").lower()
            or query in r.get("priority", "").lower()
        ]
        self._render_rooms(filtered)

    def _render_rooms(self, rooms: list[dict]):
        while self._room_layout.count() > 1:
            item = self._room_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not rooms:
            empty = QLabel("No matching rooms.")
            empty.setStyleSheet(f"color: {DIM}; font-size: 11px;")
            self._room_layout.insertWidget(0, empty)
            return

        for i, room in enumerate(rooms):
            card = self._make_room_card(room)
            self._room_layout.insertWidget(i, card)

    def _make_room_card(self, room: dict) -> QWidget:
        priority     = room.get("priority", "low")
        border_color = _PRIORITY_COLORS.get(priority, DIM)
        priority_lbl = _PRIORITY_LABELS.get(priority, priority.title())

        card = QWidget()
        card.setStyleSheet(
            f"background: #0f0f23; border-left: 3px solid {border_color}; border-radius: 2px;"
        )
        vl = QVBoxLayout(card)
        vl.setContentsMargins(8, 6, 8, 6)
        vl.setSpacing(3)

        # Room chain: T1 → T2 → T3 + priority badge
        top_row = QHBoxLayout()
        top_row.setSpacing(6)

        chain_text = (
            f"{room.get('t1', '')}  →  "
            f"{room.get('t2', '')}  →  "
            f"<b style='color:{ACCENT}'>{room.get('t3', '')}</b>"
        )
        chain_lbl = QLabel(chain_text)
        chain_lbl.setTextFormat(Qt.TextFormat.RichText)
        chain_lbl.setStyleSheet(f"color: {TEXT}; font-size: 11px;")
        top_row.addWidget(chain_lbl, 1)

        badge = QLabel(priority_lbl)
        badge.setStyleSheet(
            f"color: {border_color}; font-size: 9px; background: #1a1a3a; "
            f"border-radius: 2px; padding: 1px 5px;"
        )
        top_row.addWidget(badge)

        cat = room.get("category", "")
        if cat:
            cat_lbl = QLabel(cat)
            cat_lbl.setStyleSheet(f"color: {DIM}; font-size: 9px;")
            top_row.addWidget(cat_lbl)

        vl.addLayout(top_row)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #1a1a3a;")
        vl.addWidget(sep)

        # Drops
        drops = room.get("drops", "")
        if drops:
            drops_lbl = QLabel(
                f"<b style='color:{GREEN}'>T3 drops:</b> "
                f"<span style='color:{TEXT}'>{drops}</span>"
            )
            drops_lbl.setTextFormat(Qt.TextFormat.RichText)
            drops_lbl.setWordWrap(True)
            drops_lbl.setStyleSheet("font-size: 10px;")
            vl.addWidget(drops_lbl)

        # Notes
        notes = room.get("notes", "")
        if notes:
            notes_lbl = QLabel(notes)
            notes_lbl.setStyleSheet(
                f"color: {DIM}; font-size: 10px; font-style: italic;"
            )
            notes_lbl.setWordWrap(True)
            vl.addWidget(notes_lbl)

        return card
