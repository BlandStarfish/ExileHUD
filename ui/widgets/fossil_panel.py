"""
Delve Fossil Guide panel.

Static reference for all major Delve fossils — what mod tags they add, what they
block, minimum depth to find them, and primary crafting applications.

Data source: data/fossils.json
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

_DATA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "fossils.json"
)

_RARITY_COLORS = {
    "common":    TEAL,
    "uncommon":  ACCENT,
    "rare":      ORANGE,
    "very_rare": RED,
}

_RARITY_LABELS = {
    "common":    "Common",
    "uncommon":  "Uncommon",
    "rare":      "Rare",
    "very_rare": "Very Rare",
}


def _load_data() -> dict:
    if not os.path.exists(_DATA_PATH):
        return {}
    try:
        with open(_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[FossilPanel] failed to load data: {e}")
        return {}


class FossilPanel(QWidget):
    def __init__(self):
        super().__init__()
        data = _load_data()
        self._all_fossils  = data.get("fossils", [])
        self._resonators   = data.get("resonators", {})
        self._tips         = data.get("tips", [])
        self._active_rarity: str | None = None
        self._build_ui()
        self._render_fossils(self._all_fossils)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        header = QLabel(f"Delve Fossils  •  {len(self._all_fossils)} fossils")
        header.setStyleSheet(f"color: {ACCENT}; font-weight: bold; font-size: 13px;")
        layout.addWidget(header)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Search by name, mod tag, or crafting use…")
        self._search.setStyleSheet(
            "QLineEdit { background: #0f0f23; color: #d4c5a9; border: 1px solid #2a2a4a; "
            "border-radius: 4px; padding: 4px 8px; }"
        )
        self._search.textChanged.connect(self._on_search)
        layout.addWidget(self._search)

        # Rarity filter buttons
        filter_row = QHBoxLayout()
        filter_row.setSpacing(4)
        filter_lbl = QLabel("Rarity:")
        filter_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px;")
        filter_row.addWidget(filter_lbl)
        self._filter_buttons: dict[str, QPushButton] = {}
        for label in ["All", "Common", "Uncommon", "Rare", "Very Rare"]:
            btn = QPushButton(label)
            btn.setFixedHeight(22)
            key = label.lower().replace(" ", "_")
            color = _RARITY_COLORS.get(key, ACCENT)
            btn.setStyleSheet(
                f"QPushButton {{ background: #0f0f23; color: {DIM}; border: 1px solid #2a2a4a; "
                f"border-radius: 3px; padding: 0 6px; font-size: 10px; }}"
                f"QPushButton:hover {{ background: #1a1a3a; }}"
                f"QPushButton[active='true'] {{ color: {color}; border-color: {color}; }}"
            )
            btn.clicked.connect(lambda _, lbl=label: self._on_rarity_filter(lbl))
            self._filter_buttons[label] = btn
            filter_row.addWidget(btn)
        filter_row.addStretch()
        layout.addLayout(filter_row)
        self._set_active_filter("All")

        # Resonator reference (compact)
        if self._resonators:
            res_row = QHBoxLayout()
            res_row.setSpacing(10)
            res_lbl = QLabel("Resonators:")
            res_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px;")
            res_row.addWidget(res_lbl)
            for name, info in self._resonators.items():
                slots = info.get("slots", "?")
                short = name.replace("Alchemical Resonator", "Res.").replace("Primitive ", "Prim.").replace("Potent ", "Potent ").replace("Powerful ", "Pwrfl.").replace("Prime ", "Prime ")
                lbl = QLabel(f"{short} ({slots}-slot)")
                lbl.setStyleSheet(f"color: {TEAL}; font-size: 10px;")
                res_row.addWidget(lbl)
            res_row.addStretch()
            layout.addLayout(res_row)

        # Scrollable fossil list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        self._fossil_container = QWidget()
        self._fossil_layout    = QVBoxLayout(self._fossil_container)
        self._fossil_layout.setContentsMargins(0, 0, 0, 0)
        self._fossil_layout.setSpacing(4)
        self._fossil_layout.addStretch()
        scroll.setWidget(self._fossil_container)
        layout.addWidget(scroll)

    def _on_rarity_filter(self, label: str):
        self._set_active_filter(label)
        self._on_search(self._search.text())

    def _set_active_filter(self, label: str):
        key = label.lower().replace(" ", "_")
        self._active_rarity = None if label == "All" else key
        for btn_label, btn in self._filter_buttons.items():
            btn.setProperty("active", "true" if btn_label == label else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _on_search(self, text: str):
        query = text.strip().lower()
        pool  = self._all_fossils

        if self._active_rarity:
            pool = [f for f in pool if f.get("rarity") == self._active_rarity]

        if not query:
            self._render_fossils(pool)
            return

        filtered = [
            f for f in pool
            if query in f.get("name", "").lower()
            or query in f.get("effect", "").lower()
            or query in f.get("crafting_use", "").lower()
            or query in f.get("notes", "").lower()
            or query in f.get("rarity", "").lower()
            or any(query in tag.lower() for tag in f.get("adds_tags", []))
            or any(query in tag.lower() for tag in f.get("blocks_tags", []))
        ]
        self._render_fossils(filtered)

    def _render_fossils(self, fossils: list[dict]):
        while self._fossil_layout.count() > 1:
            item = self._fossil_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not fossils:
            empty = QLabel("No matching fossils.")
            empty.setStyleSheet(f"color: {DIM}; font-size: 11px;")
            self._fossil_layout.insertWidget(0, empty)
            return

        for i, fossil in enumerate(fossils):
            card = self._make_fossil_card(fossil)
            self._fossil_layout.insertWidget(i, card)

    def _make_fossil_card(self, fossil: dict) -> QWidget:
        rarity       = fossil.get("rarity", "common")
        border_color = _RARITY_COLORS.get(rarity, DIM)
        rarity_lbl   = _RARITY_LABELS.get(rarity, rarity.title())

        card = QWidget()
        card.setStyleSheet(
            f"background: #0f0f23; border-left: 3px solid {border_color}; border-radius: 2px;"
        )
        vl = QVBoxLayout(card)
        vl.setContentsMargins(8, 5, 8, 5)
        vl.setSpacing(3)

        # Name + rarity badge + min depth
        top_row = QHBoxLayout()
        top_row.setSpacing(6)
        name_lbl = QLabel(fossil.get("name", ""))
        name_lbl.setStyleSheet(f"color: {ACCENT}; font-weight: bold; font-size: 11px;")
        top_row.addWidget(name_lbl, 1)

        badge = QLabel(rarity_lbl)
        badge.setStyleSheet(
            f"color: {border_color}; font-size: 9px; background: #1a1a3a; "
            f"border-radius: 2px; padding: 1px 4px;"
        )
        top_row.addWidget(badge)

        depth = fossil.get("min_depth", 0)
        if depth:
            depth_lbl = QLabel(f"Depth {depth}+")
            depth_lbl.setStyleSheet(f"color: {DIM}; font-size: 9px;")
            top_row.addWidget(depth_lbl)

        vl.addLayout(top_row)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #1a1a3a;")
        vl.addWidget(sep)

        # Adds / Blocks tags
        adds   = fossil.get("adds_tags", [])
        blocks = fossil.get("blocks_tags", [])
        if adds or blocks:
            tag_row = QHBoxLayout()
            tag_row.setSpacing(8)
            if adds:
                adds_lbl = QLabel(
                    f"<b style='color:{GREEN}'>Adds:</b> "
                    f"<span style='color:{TEXT}'>{', '.join(adds)}</span>"
                )
                adds_lbl.setTextFormat(Qt.TextFormat.RichText)
                adds_lbl.setStyleSheet("font-size: 10px;")
                tag_row.addWidget(adds_lbl)
            if blocks:
                blocks_lbl = QLabel(
                    f"<b style='color:{RED}'>Blocks:</b> "
                    f"<span style='color:{TEXT}'>{', '.join(blocks)}</span>"
                )
                blocks_lbl.setTextFormat(Qt.TextFormat.RichText)
                blocks_lbl.setStyleSheet("font-size: 10px;")
                tag_row.addWidget(blocks_lbl)
            tag_row.addStretch()
            vl.addLayout(tag_row)

        # Effect
        effect = fossil.get("effect", "")
        if effect:
            fx_lbl = QLabel(effect)
            fx_lbl.setStyleSheet(f"color: {TEXT}; font-size: 10px;")
            fx_lbl.setWordWrap(True)
            vl.addWidget(fx_lbl)

        # Crafting use
        use = fossil.get("crafting_use", "")
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
        notes = fossil.get("notes", "")
        if notes:
            notes_lbl = QLabel(notes)
            notes_lbl.setStyleSheet(
                f"color: {DIM}; font-size: 10px; font-style: italic;"
            )
            notes_lbl.setWordWrap(True)
            vl.addWidget(notes_lbl)

        return card
