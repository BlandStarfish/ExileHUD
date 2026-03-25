"""
Currency Quick Reference panel.

Static reference for major PoE currency orbs: what they do, primary crafting use, notes.
Useful for new players learning currency function or experienced players verifying edge cases.

Categories: Basic, Crafting, Trade, Sockets, Maps, Unique, Flasks, Pantheon.

Data source: data/currency_reference.json
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
PURPLE = "#9a4ae8"
RED    = "#e05050"

_DATA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "currency_reference.json"
)

_CATEGORY_COLORS = {
    "Basic":    DIM,
    "Crafting": ACCENT,
    "Trade":    GREEN,
    "Sockets":  TEAL,
    "Maps":     ORANGE,
    "Unique":   PURPLE,
    "Flasks":   "#4a9ae8",
    "Pantheon": "#e8c84a",
}

_CATEGORIES = list(_CATEGORY_COLORS.keys())


def _load_currencies() -> list[dict]:
    if not os.path.exists(_DATA_PATH):
        return []
    try:
        with open(_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f).get("currencies", [])
    except Exception as e:
        print(f"[CurrencyRefPanel] failed to load data: {e}")
        return []


class CurrencyRefPanel(QWidget):
    def __init__(self):
        super().__init__()
        self._all_currencies  = _load_currencies()
        self._active_category: str | None = None
        self._build_ui()
        self._render_currencies(self._all_currencies)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        header = QLabel(f"Currency Reference  •  {len(self._all_currencies)} currencies")
        header.setStyleSheet(f"color: {ACCENT}; font-weight: bold; font-size: 13px;")
        layout.addWidget(header)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Search by name, effect, or use case…")
        self._search.setStyleSheet(
            "QLineEdit { background: #0f0f23; color: #d4c5a9; border: 1px solid #2a2a4a; "
            "border-radius: 4px; padding: 4px 8px; }"
        )
        self._search.textChanged.connect(self._on_search)
        layout.addWidget(self._search)

        # Category filter buttons
        filter_row = QHBoxLayout()
        filter_row.setSpacing(4)
        filter_lbl = QLabel("Category:")
        filter_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px;")
        filter_row.addWidget(filter_lbl)
        self._filter_buttons: dict[str, QPushButton] = {}
        for label in ["All"] + _CATEGORIES:
            btn = QPushButton(label)
            btn.setFixedHeight(22)
            color = _CATEGORY_COLORS.get(label, ACCENT)
            btn.setStyleSheet(
                f"QPushButton {{ background: #0f0f23; color: {DIM}; border: 1px solid #2a2a4a; "
                f"border-radius: 3px; padding: 0 6px; font-size: 9px; }}"
                f"QPushButton:hover {{ background: #1a1a3a; }}"
                f"QPushButton[active='true'] {{ color: {color}; border-color: {color}; }}"
            )
            btn.clicked.connect(lambda _, lbl=label: self._on_category_filter(lbl))
            self._filter_buttons[label] = btn
            filter_row.addWidget(btn)
        filter_row.addStretch()
        layout.addLayout(filter_row)
        self._set_active_filter("All")

        # Scrollable currency list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        self._currency_container = QWidget()
        self._currency_layout    = QVBoxLayout(self._currency_container)
        self._currency_layout.setContentsMargins(0, 0, 0, 0)
        self._currency_layout.setSpacing(4)
        self._currency_layout.addStretch()
        scroll.setWidget(self._currency_container)
        layout.addWidget(scroll)

        note = QLabel(
            "Hover over items in-game to see their currency effect tooltip. "
            "Values shown here are effect descriptions, not market prices."
        )
        note.setStyleSheet(f"color: {DIM}; font-size: 10px;")
        note.setWordWrap(True)
        layout.addWidget(note)

    def _on_category_filter(self, label: str):
        self._set_active_filter(label)
        self._on_search(self._search.text())

    def _set_active_filter(self, label: str):
        self._active_category = None if label == "All" else label
        for btn_label, btn in self._filter_buttons.items():
            btn.setProperty("active", "true" if btn_label == label else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _on_search(self, text: str):
        query = text.strip().lower()
        pool  = self._all_currencies

        if self._active_category:
            pool = [c for c in pool if c.get("category") == self._active_category]

        if not query:
            self._render_currencies(pool)
            return

        filtered = [
            c for c in pool
            if query in c.get("name", "").lower()
            or query in c.get("short", "").lower()
            or query in c.get("effect", "").lower()
            or query in c.get("primary_use", "").lower()
            or query in c.get("notes", "").lower()
            or query in c.get("category", "").lower()
        ]
        self._render_currencies(filtered)

    def _render_currencies(self, currencies: list[dict]):
        while self._currency_layout.count() > 1:
            item = self._currency_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not currencies:
            empty = QLabel("No matching currencies.")
            empty.setStyleSheet(f"color: {DIM}; font-size: 11px;")
            self._currency_layout.insertWidget(0, empty)
            return

        for i, currency in enumerate(currencies):
            card = self._make_currency_card(currency)
            self._currency_layout.insertWidget(i, card)

    def _make_currency_card(self, currency: dict) -> QWidget:
        category     = currency.get("category", "")
        accent_color = _CATEGORY_COLORS.get(category, DIM)

        card = QWidget()
        card.setStyleSheet(
            f"background: #0f0f23; border-left: 3px solid {accent_color}; border-radius: 2px;"
        )
        vl = QVBoxLayout(card)
        vl.setContentsMargins(8, 5, 8, 5)
        vl.setSpacing(3)

        # Name + short + category badge
        top_row = QHBoxLayout()
        top_row.setSpacing(6)
        short = currency.get("short", "")
        name_text = currency.get("name", "")
        if short:
            name_text += f"  <span style='color:{DIM};font-size:10px'>({short})</span>"
        name_lbl = QLabel(name_text)
        name_lbl.setTextFormat(Qt.TextFormat.RichText)
        name_lbl.setStyleSheet(f"color: {ACCENT}; font-weight: bold; font-size: 11px;")
        top_row.addWidget(name_lbl, 1)
        badge = QLabel(category)
        badge.setStyleSheet(
            f"color: {accent_color}; font-size: 9px; background: #1a1a3a; "
            f"border-radius: 2px; padding: 1px 4px;"
        )
        top_row.addWidget(badge)
        vl.addLayout(top_row)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #1a1a3a;")
        vl.addWidget(sep)

        # Effect
        effect = currency.get("effect", "")
        if effect:
            fx_lbl = QLabel(effect)
            fx_lbl.setStyleSheet(f"color: {TEXT}; font-size: 10px;")
            fx_lbl.setWordWrap(True)
            vl.addWidget(fx_lbl)

        # Primary use
        use = currency.get("primary_use", "")
        if use:
            use_lbl = QLabel(
                f"<b style='color:{TEAL}'>Use:</b> "
                f"<span style='color:{DIM}'>{use}</span>"
            )
            use_lbl.setTextFormat(Qt.TextFormat.RichText)
            use_lbl.setWordWrap(True)
            use_lbl.setStyleSheet("font-size: 10px;")
            vl.addWidget(use_lbl)

        # Notes
        notes = currency.get("notes", "")
        if notes:
            notes_lbl = QLabel(notes)
            notes_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px; font-style: italic;")
            notes_lbl.setWordWrap(True)
            vl.addWidget(notes_lbl)

        return card
