"""
Item Corruption Reference panel.

Static reference for what Vaal Orb corruption does to each item type —
outcome possibilities, probabilities, double corruption, and notable
Corrupted Implicits.

Data source: data/corruption_reference.json
No API calls — zero latency, always accurate.
"""

import json
import os

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QScrollArea, QFrame, QPushButton,
)

ACCENT  = "#e2b96f"
TEXT    = "#d4c5a9"
DIM     = "#8a7a65"
RED     = "#e05050"
ORANGE  = "#e8864a"
YELLOW  = "#e8c84a"
GREEN   = "#5cba6e"
TEAL    = "#4ae8c8"
PURPLE  = "#a070e8"
BLUE    = "#6090e8"

_DATA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "corruption_reference.json"
)

_PROB_COLORS = {
    "Always": GREEN,
    "High":   TEAL,
    "Medium": ACCENT,
    "Low":    ORANGE,
}

_VALUE_COLORS = {
    "Very High": GREEN,
    "High":      TEAL,
    "Medium":    ACCENT,
    "Low":       DIM,
}

_SHOW_OUTCOMES  = "Outcomes"
_SHOW_IMPLICITS = "Implicits"
_SHOW_BOTH      = "Both"


def _load_data() -> dict:
    if not os.path.exists(_DATA_PATH):
        return {}
    try:
        with open(_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[CorruptionPanel] failed to load data: {e}")
        return {}


class CorruptionPanel(QWidget):
    def __init__(self):
        super().__init__()
        data = _load_data()
        self._outcomes         = data.get("outcomes", [])
        self._implicits        = data.get("notable_implicits", [])
        self._how_it_works     = data.get("how_it_works", "")
        self._double_corrupt   = data.get("double_corruption", "")
        self._tips             = data.get("tips", [])
        self._active_section   = _SHOW_BOTH
        self._build_ui()
        self._refresh()

    # ------------------------------------------------------------------

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        header = QLabel(
            f"Corruption Reference  •  {len(self._outcomes)} item types  •  "
            f"{len(self._implicits)} notable implicits"
        )
        header.setStyleSheet(f"color: {ACCENT}; font-weight: bold; font-size: 13px;")
        layout.addWidget(header)

        if self._how_it_works:
            how_lbl = QLabel(self._how_it_works)
            how_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px;")
            how_lbl.setWordWrap(True)
            layout.addWidget(how_lbl)

        if self._double_corrupt:
            dc_lbl = QLabel(self._double_corrupt)
            dc_lbl.setStyleSheet(
                f"color: {PURPLE}; font-size: 10px; font-style: italic;"
            )
            dc_lbl.setWordWrap(True)
            layout.addWidget(dc_lbl)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Search by item type, outcome, or implicit…")
        self._search.setStyleSheet(
            "QLineEdit { background: #0f0f23; color: #d4c5a9; border: 1px solid #2a2a4a; "
            "border-radius: 4px; padding: 4px 8px; }"
        )
        self._search.textChanged.connect(self._refresh)
        layout.addWidget(self._search)

        # Section toggle
        section_row = QHBoxLayout()
        section_row.setSpacing(6)
        sec_lbl = QLabel("Show:")
        sec_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px;")
        section_row.addWidget(sec_lbl)
        self._section_buttons: dict[str, QPushButton] = {}
        for label in (_SHOW_BOTH, _SHOW_OUTCOMES, _SHOW_IMPLICITS):
            btn = QPushButton(label)
            btn.setFixedHeight(22)
            btn.setStyleSheet(
                "QPushButton { background: #0f0f23; color: #8a7a65; border: 1px solid #2a2a4a; "
                "border-radius: 3px; padding: 0 8px; font-size: 10px; }"
                "QPushButton:hover { background: #1a1a3a; }"
                "QPushButton[active='true'] { color: #e2b96f; border-color: #e2b96f; }"
            )
            btn.clicked.connect(lambda _, lbl=label: self._on_section(lbl))
            self._section_buttons[label] = btn
            section_row.addWidget(btn)
        section_row.addStretch()
        layout.addLayout(section_row)
        self._set_active_section(_SHOW_BOTH)

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

        # Tips footer
        if self._tips:
            tips_lbl = QLabel("Tips: " + "  •  ".join(self._tips[:2]))
            tips_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px; font-style: italic;")
            tips_lbl.setWordWrap(True)
            layout.addWidget(tips_lbl)

    def _on_section(self, label: str):
        self._set_active_section(label)
        self._refresh()

    def _set_active_section(self, label: str):
        self._active_section = label
        for btn_label, btn in self._section_buttons.items():
            btn.setProperty("active", "true" if btn_label == label else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _outcome_matches(self, entry: dict, query: str) -> bool:
        if not query:
            return True
        outcomes_text = " ".join(
            o.get("result", "") + " " + o.get("notes", "")
            for o in entry.get("outcomes", [])
        )
        searchable = " ".join([
            entry.get("item_type", ""),
            entry.get("category", ""),
            outcomes_text,
        ]).lower()
        return query in searchable

    def _implicit_matches(self, imp: dict, query: str) -> bool:
        if not query:
            return True
        searchable = " ".join([
            imp.get("implicit", ""),
            imp.get("source", ""),
            imp.get("notes", ""),
        ]).lower()
        return query in searchable

    def _refresh(self):
        query = self._search.text().strip().lower()
        show_outcomes  = self._active_section in (_SHOW_BOTH, _SHOW_OUTCOMES)
        show_implicits = self._active_section in (_SHOW_BOTH, _SHOW_IMPLICITS)

        outcomes  = [e for e in self._outcomes  if self._outcome_matches(e, query)]  if show_outcomes  else []
        implicits = [i for i in self._implicits if self._implicit_matches(i, query)] if show_implicits else []

        self._render(outcomes, implicits)

    def _render(self, outcomes: list[dict], implicits: list[dict]):
        while self._list_layout.count() > 1:
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        insert_idx = 0

        if not outcomes and not implicits:
            empty = QLabel("No matching entries.")
            empty.setStyleSheet(f"color: {DIM}; font-size: 11px;")
            self._list_layout.insertWidget(0, empty)
            return

        if outcomes:
            sec_hdr = QLabel(f"Corruption Outcomes by Item Type ({len(outcomes)})")
            sec_hdr.setStyleSheet(f"color: {ACCENT}; font-size: 11px; font-weight: bold;")
            self._list_layout.insertWidget(insert_idx, sec_hdr)
            insert_idx += 1
            for entry in outcomes:
                card = self._make_outcome_card(entry)
                self._list_layout.insertWidget(insert_idx, card)
                insert_idx += 1

        if implicits:
            imp_hdr = QLabel(f"Notable Corrupted Implicits ({len(implicits)})")
            imp_hdr.setStyleSheet(f"color: {PURPLE}; font-size: 11px; font-weight: bold;")
            self._list_layout.insertWidget(insert_idx, imp_hdr)
            insert_idx += 1
            for imp in implicits:
                card = self._make_implicit_card(imp)
                self._list_layout.insertWidget(insert_idx, card)
                insert_idx += 1

    def _make_outcome_card(self, entry: dict) -> QFrame:
        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background: #0f0f1e; border: 1px solid #2a2a4a; "
            f"border-left: 3px solid {ORANGE}; border-radius: 4px; padding: 4px; }}"
        )
        cl = QVBoxLayout(card)
        cl.setContentsMargins(6, 4, 6, 4)
        cl.setSpacing(2)

        # Item type header
        item_type = entry.get("item_type", "")
        type_lbl = QLabel(item_type)
        type_lbl.setStyleSheet(f"color: {ACCENT}; font-weight: bold; font-size: 12px;")
        cl.addWidget(type_lbl)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: #2a2a4a;")
        cl.addWidget(sep)

        # Each outcome row
        for outcome in entry.get("outcomes", []):
            result = outcome.get("result", "")
            prob   = outcome.get("probability", "")
            notes  = outcome.get("notes", "")
            prob_color = _PROB_COLORS.get(prob, DIM)

            row = QHBoxLayout()
            if prob:
                prob_lbl = QLabel(f"[{prob}]")
                prob_lbl.setFixedWidth(52)
                prob_lbl.setStyleSheet(f"color: {prob_color}; font-size: 10px; font-weight: bold;")
                row.addWidget(prob_lbl)

            result_lbl = QLabel(result)
            result_lbl.setStyleSheet(f"color: {TEXT}; font-size: 11px;")
            result_lbl.setWordWrap(True)
            row.addWidget(result_lbl, 1)
            cl.addLayout(row)

            if notes:
                note_lbl = QLabel(f"    {notes}")
                note_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px; font-style: italic;")
                note_lbl.setWordWrap(True)
                cl.addWidget(note_lbl)

        return card

    def _make_implicit_card(self, imp: dict) -> QFrame:
        value = imp.get("value", "")
        val_color = _VALUE_COLORS.get(value, DIM)

        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background: #0f0f1e; border: 1px solid #2a2a4a; "
            f"border-left: 3px solid {PURPLE}; border-radius: 4px; padding: 4px; }}"
        )
        cl = QVBoxLayout(card)
        cl.setContentsMargins(6, 4, 6, 4)
        cl.setSpacing(2)

        header_row = QHBoxLayout()
        impl_lbl = QLabel(imp.get("implicit", ""))
        impl_lbl.setStyleSheet(f"color: {TEAL}; font-size: 11px; font-weight: bold;")
        impl_lbl.setWordWrap(True)
        header_row.addWidget(impl_lbl, 1)

        if value:
            val_badge = QLabel(value)
            val_badge.setStyleSheet(f"color: {val_color}; font-size: 10px; font-weight: bold;")
            header_row.addWidget(val_badge)

        cl.addLayout(header_row)

        source = imp.get("source", "")
        if source:
            src_lbl = QLabel(f"Source: {source}")
            src_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px; font-style: italic;")
            cl.addWidget(src_lbl)

        notes = imp.get("notes", "")
        if notes:
            notes_lbl = QLabel(notes)
            notes_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px;")
            notes_lbl.setWordWrap(True)
            cl.addWidget(notes_lbl)

        return card
