"""
Endgame Progression Checklist panel.

Step-by-step progression guide from Acts 1-10 through the full endgame:
Campaign → Early Atlas → Yellow Maps & Conquerors → Red Maps & Sirus →
Pinnacle Content → Uber Pinnacles.

Each stage shows objectives, gear targets, key warnings, and the unlock gate
for the next stage.

Data source: data/endgame_checklist.json
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
YELLOW = "#e8c84a"

_DATA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "endgame_checklist.json"
)

_CATEGORY_COLORS = {
    "Foundation": GREEN,
    "Mapping":    TEAL,
    "Endgame":    ORANGE,
    "Pinnacle":   PURPLE,
}

_ALL = "All"


def _load_data() -> dict:
    if not os.path.exists(_DATA_PATH):
        return {}
    try:
        with open(_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[EndgameChecklistPanel] failed to load data: {e}")
        return {}


class EndgameChecklistPanel(QWidget):
    def __init__(self):
        super().__init__()
        data = _load_data()
        self._stages     = sorted(data.get("stages", []), key=lambda s: s.get("order", 99))
        self._tips       = data.get("tips", [])
        self._categories = [_ALL] + data.get("categories", [])
        self._active_cat = _ALL
        self._build_ui()
        self._set_category(_ALL)

    # ------------------------------------------------------------------

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        header = QLabel(f"Endgame Progression Checklist  •  {len(self._stages)} stages")
        header.setStyleSheet(f"color: {ACCENT}; font-weight: bold; font-size: 13px;")
        layout.addWidget(header)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Search objectives, gear targets, or warnings…")
        self._search.setStyleSheet(
            "QLineEdit { background: #0f0f23; color: #d4c5a9; border: 1px solid #2a2a4a; "
            "border-radius: 4px; padding: 4px 8px; }"
        )
        self._search.textChanged.connect(self._refresh)
        layout.addWidget(self._search)

        cat_row = QHBoxLayout()
        cat_row.setSpacing(5)
        self._cat_buttons: dict[str, QPushButton] = {}
        for cat in self._categories:
            color = _CATEGORY_COLORS.get(cat, ACCENT)
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
            tips_lbl = QLabel(self._tips[0])
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

    def _matches(self, stage: dict, query: str) -> bool:
        if not query:
            return True
        objectives_text  = " ".join(stage.get("objectives", []))
        warnings_text    = " ".join(stage.get("key_warnings", []))
        searchable = " ".join([
            stage.get("name", ""),
            stage.get("category", ""),
            objectives_text,
            stage.get("gear_targets", ""),
            warnings_text,
            stage.get("unlock", ""),
            stage.get("next_step", ""),
        ]).lower()
        return query in searchable

    def _refresh(self):
        query = self._search.text().strip().lower()
        pool = self._stages
        if self._active_cat != _ALL:
            pool = [s for s in pool if s.get("category") == self._active_cat]
        filtered = [s for s in pool if self._matches(s, query)]
        self._render(filtered)

    def _render(self, stages: list[dict]):
        while self._list_layout.count() > 1:
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not stages:
            empty = QLabel("No matching stages.")
            empty.setStyleSheet(f"color: {DIM}; font-size: 11px;")
            self._list_layout.insertWidget(0, empty)
            return

        for i, stage in enumerate(stages):
            card = self._make_card(stage)
            self._list_layout.insertWidget(i, card)

    def _make_card(self, stage: dict) -> QFrame:
        cat   = stage.get("category", "")
        order = stage.get("order", 0)
        color = _CATEGORY_COLORS.get(cat, ACCENT)

        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background: #0f0f1e; border: 1px solid #2a2a4a; "
            f"border-left: 3px solid {color}; border-radius: 4px; padding: 4px; }}"
        )
        cl = QVBoxLayout(card)
        cl.setContentsMargins(6, 4, 6, 4)
        cl.setSpacing(3)

        # Header: order badge + name + category badge
        header_row = QHBoxLayout()
        if order:
            order_badge = QLabel(f"[{order}]")
            order_badge.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 11px;")
            header_row.addWidget(order_badge)
        name_lbl = QLabel(stage.get("name", ""))
        name_lbl.setStyleSheet(f"color: {ACCENT}; font-weight: bold; font-size: 11px;")
        header_row.addWidget(name_lbl)
        header_row.addStretch()
        if cat:
            cat_badge = QLabel(f"[{cat}]")
            cat_badge.setStyleSheet(f"color: {color}; font-size: 10px;")
            header_row.addWidget(cat_badge)
        cl.addLayout(header_row)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #2a2a4a;")
        cl.addWidget(sep)

        # Objectives
        objectives = stage.get("objectives", [])
        if objectives:
            obj_header = QLabel("Objectives:")
            obj_header.setStyleSheet(f"color: {TEAL}; font-size: 10px; font-weight: bold;")
            cl.addWidget(obj_header)
            for obj in objectives:
                obj_lbl = QLabel(f"  ☐  {obj}")
                obj_lbl.setStyleSheet(f"color: {TEXT}; font-size: 10px;")
                obj_lbl.setWordWrap(True)
                cl.addWidget(obj_lbl)

        # Gear targets
        gear = stage.get("gear_targets", "")
        if gear:
            gear_lbl = QLabel(f"Gear: {gear}")
            gear_lbl.setStyleSheet(f"color: {GREEN}; font-size: 10px;")
            gear_lbl.setWordWrap(True)
            cl.addWidget(gear_lbl)

        # Key warnings
        warnings = stage.get("key_warnings", [])
        if warnings:
            warn_header = QLabel("Warnings:")
            warn_header.setStyleSheet(f"color: {RED}; font-size: 10px; font-weight: bold;")
            cl.addWidget(warn_header)
            for warn in warnings:
                warn_lbl = QLabel(f"  ⚠  {warn}")
                warn_lbl.setStyleSheet(f"color: {ORANGE}; font-size: 10px;")
                warn_lbl.setWordWrap(True)
                cl.addWidget(warn_lbl)

        # Unlock / next step
        unlock = stage.get("unlock", "")
        if unlock:
            unlock_lbl = QLabel(f"Unlocks: {unlock}")
            unlock_lbl.setStyleSheet(f"color: {PURPLE}; font-size: 10px;")
            unlock_lbl.setWordWrap(True)
            cl.addWidget(unlock_lbl)

        next_step = stage.get("next_step", "")
        if next_step:
            next_lbl = QLabel(f"Next: {next_step}")
            next_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px; font-style: italic;")
            next_lbl.setWordWrap(True)
            cl.addWidget(next_lbl)

        return card
