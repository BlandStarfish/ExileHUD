"""
Metamorph Catalyst Reference panel.

Static reference for all PoE catalyst types — which item modifier category each
catalyst improves, what items it applies to, and which organ sources to target.

Data source: data/metamorph_catalysts.json
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

_DATA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "metamorph_catalysts.json"
)


def _load_data() -> dict:
    if not os.path.exists(_DATA_PATH):
        return {}
    try:
        with open(_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[MetamorphPanel] failed to load data: {e}")
        return {}


class MetamorphPanel(QWidget):
    def __init__(self):
        super().__init__()
        data = _load_data()
        self._all_catalysts = data.get("catalysts", [])
        self._how_it_works  = data.get("how_it_works", "")
        self._max_note      = data.get("max_quality_note", "")
        self._applicable    = data.get("applicable_items", [])
        self._tips          = data.get("tips", [])
        self._build_ui()
        self._render_catalysts(self._all_catalysts)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        header = QLabel(
            f"Metamorph Catalysts  •  {len(self._all_catalysts)} types  •  "
            f"Applies to: {', '.join(self._applicable)}"
        )
        header.setStyleSheet(f"color: {ACCENT}; font-weight: bold; font-size: 13px;")
        layout.addWidget(header)

        if self._how_it_works:
            how_lbl = QLabel(self._how_it_works)
            how_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px;")
            how_lbl.setWordWrap(True)
            layout.addWidget(how_lbl)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Search by catalyst name, modifier type, or use…")
        self._search.setStyleSheet(
            "QLineEdit { background: #0f0f23; color: #d4c5a9; border: 1px solid #2a2a4a; "
            "border-radius: 4px; padding: 4px 8px; }"
        )
        self._search.textChanged.connect(self._on_search)
        layout.addWidget(self._search)

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

    def _on_search(self, text: str):
        query = text.strip().lower()
        if not query:
            self._render_catalysts(self._all_catalysts)
            return
        filtered = [
            c for c in self._all_catalysts
            if query in c.get("name", "").lower()
            or query in c.get("improves", "").lower()
            or query in c.get("examples", "").lower()
            or query in c.get("best_for", "").lower()
            or query in c.get("organ_source", "").lower()
        ]
        self._render_catalysts(filtered)

    def _render_catalysts(self, catalysts: list[dict]):
        while self._list_layout.count() > 1:
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not catalysts:
            empty = QLabel("No matching catalysts.")
            empty.setStyleSheet(f"color: {DIM}; font-size: 11px;")
            self._list_layout.insertWidget(0, empty)
            return

        for i, catalyst in enumerate(catalysts):
            card = self._make_card(catalyst)
            self._list_layout.insertWidget(i, card)

    def _make_card(self, catalyst: dict) -> QWidget:
        card = QWidget()
        card.setStyleSheet(
            f"background: #0f0f23; border-left: 3px solid {ORANGE}; border-radius: 2px;"
        )
        vl = QVBoxLayout(card)
        vl.setContentsMargins(8, 6, 8, 6)
        vl.setSpacing(3)

        # Name
        name_lbl = QLabel(catalyst.get("name", ""))
        name_lbl.setStyleSheet(f"color: {ACCENT}; font-weight: bold; font-size: 12px;")
        vl.addWidget(name_lbl)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #1a1a3a;")
        vl.addWidget(sep)

        # Improves
        improves = catalyst.get("improves", "")
        if improves:
            imp_lbl = QLabel(
                f"<b style='color:{TEAL}'>Improves:</b> "
                f"<span style='color:{TEXT}'>{improves}</span>"
            )
            imp_lbl.setTextFormat(Qt.TextFormat.RichText)
            imp_lbl.setWordWrap(True)
            imp_lbl.setStyleSheet("font-size: 11px;")
            vl.addWidget(imp_lbl)

        # Examples
        examples = catalyst.get("examples", "")
        if examples:
            ex_lbl = QLabel(
                f"<span style='color:{DIM}'>e.g. {examples}</span>"
            )
            ex_lbl.setTextFormat(Qt.TextFormat.RichText)
            ex_lbl.setWordWrap(True)
            ex_lbl.setStyleSheet("font-size: 10px;")
            vl.addWidget(ex_lbl)

        # Best for
        best_for = catalyst.get("best_for", "")
        if best_for:
            bf_lbl = QLabel(
                f"<b style='color:{GREEN}'>Best for:</b> "
                f"<span style='color:{TEXT}'>{best_for}</span>"
            )
            bf_lbl.setTextFormat(Qt.TextFormat.RichText)
            bf_lbl.setWordWrap(True)
            bf_lbl.setStyleSheet("font-size: 10px;")
            vl.addWidget(bf_lbl)

        # Organ source
        organ = catalyst.get("organ_source", "")
        if organ:
            org_lbl = QLabel(
                f"<b style='color:{DIM}'>Organ source:</b> "
                f"<span style='color:{DIM}'>{organ}</span>"
            )
            org_lbl.setTextFormat(Qt.TextFormat.RichText)
            org_lbl.setWordWrap(True)
            org_lbl.setStyleSheet("font-size: 10px; font-style: italic;")
            vl.addWidget(org_lbl)

        return card
