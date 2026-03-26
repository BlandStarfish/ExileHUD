"""
Passive Tree Starting Area Guide panel.

Reference for each of the 7 passive skill tree starting positions.
Covers ascendancies, key node clusters, recommended/avoided build types,
and nearby keystones for each class starting area.

Data source: data/starting_areas.json
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
GOLD   = "#f5c842"

_DATA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "starting_areas.json"
)

_AREA_COLORS = {
    "Marauder": RED,
    "Duelist":  ORANGE,
    "Ranger":   GREEN,
    "Shadow":   PURPLE,
    "Witch":    BLUE,
    "Templar":  GOLD,
    "Scion":    TEAL,
}

_VALUE_COLORS = {
    "Extremely High": GOLD,
    "High":           ORANGE,
    "Medium":         TEAL,
    "Low":            DIM,
}

_ALL = "All"


def _load_data() -> dict:
    if not os.path.exists(_DATA_PATH):
        return {}
    try:
        with open(_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[StartingAreasPanel] failed to load data: {e}")
        return {}


class StartingAreasPanel(QWidget):
    def __init__(self):
        super().__init__()
        data = _load_data()
        self._areas        = data.get("starting_areas", [])
        self._how_it_works = data.get("how_it_works", "")
        self._tips         = data.get("tips", [])
        self._area_names   = [_ALL] + [a["area"] for a in self._areas]
        self._active_area  = _ALL
        self._build_ui()
        self._set_area(_ALL)

    # ------------------------------------------------------------------

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        header = QLabel(f"Passive Tree Starting Areas  •  {len(self._areas)} classes")
        header.setStyleSheet(f"color: {ACCENT}; font-weight: bold; font-size: 13px;")
        layout.addWidget(header)

        if self._how_it_works:
            how_lbl = QLabel(self._how_it_works)
            how_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px;")
            how_lbl.setWordWrap(True)
            layout.addWidget(how_lbl)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Search by class, build type, ascendancy, keystone…")
        self._search.setStyleSheet(
            "QLineEdit { background: #0f0f23; color: #d4c5a9; border: 1px solid #2a2a4a; "
            "border-radius: 4px; padding: 4px 8px; }"
        )
        self._search.textChanged.connect(self._refresh)
        layout.addWidget(self._search)

        # Area filter buttons
        area_row = QHBoxLayout()
        area_row.setSpacing(4)
        self._area_buttons: dict[str, QPushButton] = {}
        for area in self._area_names:
            color = _AREA_COLORS.get(area, ACCENT)
            btn = QPushButton(area)
            btn.setFixedHeight(22)
            btn.setStyleSheet(
                f"QPushButton {{ background: #0f0f23; color: {DIM}; border: 1px solid #2a2a4a; "
                f"border-radius: 3px; padding: 0 6px; font-size: 10px; }}"
                f"QPushButton:hover {{ background: #1a1a3a; }}"
                f"QPushButton[active='true'] {{ color: {color}; border-color: {color}; }}"
            )
            btn.clicked.connect(lambda _, a=area: self._set_area(a))
            self._area_buttons[area] = btn
            area_row.addWidget(btn)
        area_row.addStretch()
        layout.addLayout(area_row)

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
            tips_lbl = QLabel("Tips: " + "  •  ".join(self._tips[:2]))
            tips_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px; font-style: italic;")
            tips_lbl.setWordWrap(True)
            layout.addWidget(tips_lbl)

    def _set_area(self, area: str):
        self._active_area = area
        for a, btn in self._area_buttons.items():
            btn.setProperty("active", "true" if a == area else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self._refresh()

    def _matches(self, area: dict, query: str) -> bool:
        if not query:
            return True
        searchable = " ".join([
            area.get("area", ""),
            area.get("location", ""),
            " ".join(area.get("primary_stats", [])),
            " ".join(area.get("ascendancies", [])),
            " ".join(area.get("key_node_clusters", [])),
            " ".join(area.get("recommended_for", [])),
            " ".join(area.get("avoid_for", [])),
            " ".join(area.get("notable_keystones_nearby", [])),
            area.get("ascendancy_highlights", ""),
            area.get("notes", ""),
        ]).lower()
        return query in searchable

    def _refresh(self):
        query = self._search.text().strip().lower()
        pool = self._areas
        if self._active_area != _ALL:
            pool = [a for a in pool if a.get("area") == self._active_area]
        filtered = [a for a in pool if self._matches(a, query)]
        self._render(filtered)

    def _render(self, areas: list[dict]):
        while self._list_layout.count() > 1:
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not areas:
            empty = QLabel("No matching starting areas.")
            empty.setStyleSheet(f"color: {DIM}; font-size: 11px;")
            self._list_layout.insertWidget(0, empty)
            return

        for i, area in enumerate(areas):
            card = self._make_card(area)
            self._list_layout.insertWidget(i, card)

    def _make_card(self, area: dict) -> QFrame:
        area_name = area.get("area", "")
        color = _AREA_COLORS.get(area_name, ACCENT)

        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background: #0f0f1e; border: 1px solid #2a2a4a; "
            f"border-left: 3px solid {color}; border-radius: 4px; padding: 4px; }}"
        )
        cl = QVBoxLayout(card)
        cl.setContentsMargins(6, 4, 6, 4)
        cl.setSpacing(3)

        # Header: class name + location + value tier
        header_row = QHBoxLayout()
        name_lbl = QLabel(area_name)
        name_lbl.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 13px;")
        header_row.addWidget(name_lbl)
        location = area.get("location", "")
        if location:
            loc_lbl = QLabel(f"  {location}")
            loc_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px;")
            header_row.addWidget(loc_lbl)
        header_row.addStretch()
        val_tier = area.get("value_tier", "")
        if val_tier:
            tier_color = _VALUE_COLORS.get(val_tier, DIM)
            tier_lbl = QLabel(val_tier)
            tier_lbl.setStyleSheet(f"color: {tier_color}; font-size: 10px; font-weight: bold;")
            header_row.addWidget(tier_lbl)
        cl.addLayout(header_row)

        # Stats + ascendancies row
        meta_row = QHBoxLayout()
        stats = area.get("primary_stats", [])
        if stats:
            stats_lbl = QLabel("Stats: " + " / ".join(stats))
            stats_lbl.setStyleSheet(f"color: {TEAL}; font-size: 10px;")
            meta_row.addWidget(stats_lbl)
        meta_row.addStretch()
        ascendancies = area.get("ascendancies", [])
        if ascendancies:
            asc_lbl = QLabel(" | ".join(ascendancies))
            asc_lbl.setStyleSheet(f"color: {GOLD}; font-size: 10px; font-weight: bold;")
            meta_row.addWidget(asc_lbl)
        cl.addLayout(meta_row)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #2a2a4a;")
        cl.addWidget(sep)

        # Key node clusters
        clusters = area.get("key_node_clusters", [])
        if clusters:
            clusters_lbl = QLabel("Key clusters: " + ", ".join(clusters))
            clusters_lbl.setStyleSheet(f"color: {TEXT}; font-size: 10px;")
            clusters_lbl.setWordWrap(True)
            cl.addWidget(clusters_lbl)

        # Recommended for
        recommended = area.get("recommended_for", [])
        if recommended:
            rec_lbl = QLabel("✓ " + "  •  ".join(recommended))
            rec_lbl.setStyleSheet(f"color: {GREEN}; font-size: 10px;")
            rec_lbl.setWordWrap(True)
            cl.addWidget(rec_lbl)

        # Avoid for
        avoid = area.get("avoid_for", [])
        if avoid:
            avoid_lbl = QLabel("✗ " + "  •  ".join(avoid))
            avoid_lbl.setStyleSheet(f"color: {RED}; font-size: 10px;")
            avoid_lbl.setWordWrap(True)
            cl.addWidget(avoid_lbl)

        # Keystones
        keystones = area.get("notable_keystones_nearby", [])
        if keystones:
            ks_lbl = QLabel("Keystones nearby: " + ", ".join(keystones))
            ks_lbl.setStyleSheet(f"color: {PURPLE}; font-size: 10px;")
            ks_lbl.setWordWrap(True)
            cl.addWidget(ks_lbl)

        # Ascendancy highlights
        asc_hl = area.get("ascendancy_highlights", "")
        if asc_hl:
            asc_hl_lbl = QLabel(asc_hl)
            asc_hl_lbl.setStyleSheet(f"color: {GOLD}; font-size: 10px;")
            asc_hl_lbl.setWordWrap(True)
            cl.addWidget(asc_hl_lbl)

        # Notes
        notes = area.get("notes", "")
        if notes:
            notes_lbl = QLabel(notes)
            notes_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px; font-style: italic;")
            notes_lbl.setWordWrap(True)
            cl.addWidget(notes_lbl)

        return card
