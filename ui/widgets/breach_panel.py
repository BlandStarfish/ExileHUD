"""
Breach Domain Reference panel.

Static reference for all 5 Breach domains: element, keystone, blessing, notable uniques.
Useful during Breach encounters to plan which splinters/blessings to prioritise.

Data source: data/breaches.json
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
    os.path.dirname(__file__), "..", "..", "data", "breaches.json"
)

# Color per element
_ELEMENT_COLORS = {
    "Fire":      ORANGE,
    "Cold":      TEAL,
    "Lightning": ACCENT,
    "Physical":  "#a0a0a0",
    "Chaos":     PURPLE,
}


def _load_data() -> dict:
    if not os.path.exists(_DATA_PATH):
        return {}
    try:
        with open(_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[BreachPanel] failed to load data: {e}")
        return {}


class BreachPanel(QWidget):
    def __init__(self):
        super().__init__()
        data = _load_data()
        self._all_breaches = data.get("breaches", [])
        self._stone_tiers  = data.get("breachstone_tiers", [])
        self._stone_note   = data.get("breachstone_note", "")
        self._build_ui()
        self._render_breaches(self._all_breaches)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        header = QLabel(f"Breach Domains  •  {len(self._all_breaches)} domains")
        header.setStyleSheet(f"color: {ACCENT}; font-weight: bold; font-size: 13px;")
        layout.addWidget(header)

        # Breachstone tier legend
        if self._stone_tiers:
            tiers_lbl = QLabel("Breachstone tiers: " + " < ".join(self._stone_tiers))
            tiers_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px;")
            layout.addWidget(tiers_lbl)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Search by deity, element, keystone, or unique…")
        self._search.setStyleSheet(
            "QLineEdit { background: #0f0f23; color: #d4c5a9; border: 1px solid #2a2a4a; "
            "border-radius: 4px; padding: 4px 8px; }"
        )
        self._search.textChanged.connect(self._on_search)
        layout.addWidget(self._search)

        # Element color legend
        legend_row = QHBoxLayout()
        legend_row.setSpacing(10)
        for element, color in _ELEMENT_COLORS.items():
            lbl = QLabel(f"● {element}")
            lbl.setStyleSheet(f"color: {color}; font-size: 10px;")
            legend_row.addWidget(lbl)
        legend_row.addStretch()
        layout.addLayout(legend_row)

        # Scrollable breach list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        self._breach_container = QWidget()
        self._breach_layout    = QVBoxLayout(self._breach_container)
        self._breach_layout.setContentsMargins(0, 0, 0, 0)
        self._breach_layout.setSpacing(6)
        self._breach_layout.addStretch()
        scroll.setWidget(self._breach_container)
        layout.addWidget(scroll)

        if self._stone_note:
            note = QLabel(self._stone_note)
            note.setStyleSheet(f"color: {DIM}; font-size: 10px;")
            note.setWordWrap(True)
            layout.addWidget(note)

    def _on_search(self, text: str):
        query = text.strip().lower()
        if not query:
            self._render_breaches(self._all_breaches)
            return
        filtered = [
            b for b in self._all_breaches
            if query in b.get("deity", "").lower()
            or query in b.get("element", "").lower()
            or query in b.get("keystone", "").lower()
            or query in b.get("keystone_effect", "").lower()
            or query in b.get("blessing", "").lower()
            or query in b.get("blessing_effect", "").lower()
            or query in b.get("notes", "").lower()
            or any(query in u.lower() for u in b.get("notable_uniques", []))
        ]
        self._render_breaches(filtered)

    def _render_breaches(self, breaches: list[dict]):
        while self._breach_layout.count() > 1:
            item = self._breach_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not breaches:
            empty = QLabel("No matching breach domains.")
            empty.setStyleSheet(f"color: {DIM}; font-size: 11px;")
            self._breach_layout.insertWidget(0, empty)
            return

        for i, breach in enumerate(breaches):
            card = self._make_breach_card(breach)
            self._breach_layout.insertWidget(i, card)

    def _make_breach_card(self, breach: dict) -> QWidget:
        element = breach.get("element", "")
        color   = _ELEMENT_COLORS.get(element, DIM)

        card = QWidget()
        card.setStyleSheet(
            f"background: #0f0f23; border-left: 3px solid {color}; border-radius: 2px;"
        )
        vl = QVBoxLayout(card)
        vl.setContentsMargins(8, 6, 8, 6)
        vl.setSpacing(4)

        # Deity name + element badge
        top_row = QHBoxLayout()
        top_row.setSpacing(8)
        deity_lbl = QLabel(breach.get("deity", ""))
        deity_lbl.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 13px;")
        top_row.addWidget(deity_lbl)

        elem_badge = QLabel(element)
        elem_badge.setStyleSheet(
            f"color: {color}; font-size: 9px; background: #1a1a3a; "
            f"border-radius: 2px; padding: 1px 5px;"
        )
        top_row.addWidget(elem_badge)
        top_row.addStretch()

        splinter_lbl = QLabel(breach.get("splinter", ""))
        splinter_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px;")
        top_row.addWidget(splinter_lbl)
        vl.addLayout(top_row)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #1a1a3a;")
        vl.addWidget(sep)

        # Keystone
        ks_name = breach.get("keystone", "")
        ks_fx   = breach.get("keystone_effect", "")
        ks_lbl  = QLabel(
            f"<b style='color:{ACCENT}'>Keystone:</b> {ks_name}"
            f"<br><span style='color:{DIM};font-size:10px'>{ks_fx}</span>"
        )
        ks_lbl.setTextFormat(Qt.TextFormat.RichText)
        ks_lbl.setWordWrap(True)
        ks_lbl.setStyleSheet(f"color: {TEXT}; font-size: 11px;")
        vl.addWidget(ks_lbl)

        # Blessing
        bl_name = breach.get("blessing", "")
        bl_fx   = breach.get("blessing_effect", "")
        bl_lbl  = QLabel(
            f"<b style='color:{GREEN}'>Blessing:</b> {bl_name}"
            f"<br><span style='color:{DIM};font-size:10px'>{bl_fx}</span>"
        )
        bl_lbl.setTextFormat(Qt.TextFormat.RichText)
        bl_lbl.setWordWrap(True)
        bl_lbl.setStyleSheet(f"color: {TEXT}; font-size: 11px;")
        vl.addWidget(bl_lbl)

        # Notable uniques
        uniques = breach.get("notable_uniques", [])
        if uniques:
            uniq_header = QLabel("<b style='color:#8a7a65'>Notable Uniques:</b>")
            uniq_header.setTextFormat(Qt.TextFormat.RichText)
            uniq_header.setStyleSheet(f"color: {DIM}; font-size: 10px;")
            vl.addWidget(uniq_header)
            for u in uniques:
                u_lbl = QLabel(f"  • {u}")
                u_lbl.setStyleSheet(f"color: {TEXT}; font-size: 10px;")
                u_lbl.setWordWrap(True)
                vl.addWidget(u_lbl)

        # Notes
        notes = breach.get("notes", "")
        if notes:
            notes_lbl = QLabel(notes)
            notes_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px; font-style: italic;")
            notes_lbl.setWordWrap(True)
            vl.addWidget(notes_lbl)

        return card
