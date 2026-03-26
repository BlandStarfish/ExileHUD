"""
Map Tier Progression Guide panel.

Reference for Atlas map tier structure, white/yellow/red progression,
pinnacle boss access, and atlas region strategy.

Data source: data/map_tiers.json
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
    os.path.dirname(__file__), "..", "..", "data", "map_tiers.json"
)

_TIER_GROUP_COLORS = {
    "White (T1–5)":   GREEN,
    "Yellow (T6–10)": GOLD,
    "Red (T11–16)":   RED,
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
        print(f"[MapTiersPanel] failed to load data: {e}")
        return {}


class MapTiersPanel(QWidget):
    def __init__(self):
        super().__init__()
        data = _load_data()
        self._tiers        = data.get("tiers", [])
        self._how_it_works = data.get("how_it_works", "")
        self._tips         = data.get("tips", [])
        self._tier_groups  = [_ALL] + data.get("tier_groups", [])
        self._active_group = _ALL
        self._build_ui()
        self._set_group(_ALL)

    # ------------------------------------------------------------------

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        header = QLabel(f"Map Tier Progression  •  {len(self._tiers)} entries")
        header.setStyleSheet(f"color: {ACCENT}; font-weight: bold; font-size: 13px;")
        layout.addWidget(header)

        if self._how_it_works:
            how_lbl = QLabel(self._how_it_works)
            how_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px;")
            how_lbl.setWordWrap(True)
            layout.addWidget(how_lbl)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Search by tier, map name, mechanic, strategy…")
        self._search.setStyleSheet(
            "QLineEdit { background: #0f0f23; color: #d4c5a9; border: 1px solid #2a2a4a; "
            "border-radius: 4px; padding: 4px 8px; }"
        )
        self._search.textChanged.connect(self._refresh)
        layout.addWidget(self._search)

        # Tier group filter buttons
        group_row = QHBoxLayout()
        group_row.setSpacing(4)
        self._group_buttons: dict[str, QPushButton] = {}
        for group in self._tier_groups:
            color = _TIER_GROUP_COLORS.get(group, ACCENT)
            btn = QPushButton(group)
            btn.setFixedHeight(22)
            btn.setStyleSheet(
                f"QPushButton {{ background: #0f0f23; color: {DIM}; border: 1px solid #2a2a4a; "
                f"border-radius: 3px; padding: 0 6px; font-size: 10px; }}"
                f"QPushButton:hover {{ background: #1a1a3a; }}"
                f"QPushButton[active='true'] {{ color: {color}; border-color: {color}; }}"
            )
            btn.clicked.connect(lambda _, g=group: self._set_group(g))
            self._group_buttons[group] = btn
            group_row.addWidget(btn)
        group_row.addStretch()
        layout.addLayout(group_row)

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

    def _set_group(self, group: str):
        self._active_group = group
        for g, btn in self._group_buttons.items():
            btn.setProperty("active", "true" if g == group else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self._refresh()

    def _matches(self, tier: dict, query: str) -> bool:
        if not query:
            return True
        searchable = " ".join([
            tier.get("tier_name", ""),
            tier.get("tier_group", ""),
            str(tier.get("typical_area_level", "")),
            tier.get("rarity_requirement", ""),
            " ".join(tier.get("key_mechanics", [])),
            tier.get("atlas_objective", ""),
            " ".join(tier.get("notable_maps", [])),
            tier.get("value_tier", ""),
            tier.get("notes", ""),
        ]).lower()
        return query in searchable

    def _refresh(self):
        query = self._search.text().strip().lower()
        pool = self._tiers
        if self._active_group != _ALL:
            pool = [t for t in pool if t.get("tier_group") == self._active_group]
        filtered = [t for t in pool if self._matches(t, query)]
        self._render(filtered)

    def _render(self, tiers: list[dict]):
        while self._list_layout.count() > 1:
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not tiers:
            empty = QLabel("No matching tier entries.")
            empty.setStyleSheet(f"color: {DIM}; font-size: 11px;")
            self._list_layout.insertWidget(0, empty)
            return

        for i, tier in enumerate(tiers):
            card = self._make_card(tier)
            self._list_layout.insertWidget(i, card)

    def _make_card(self, tier: dict) -> QFrame:
        group = tier.get("tier_group", "")
        color = _TIER_GROUP_COLORS.get(group, ACCENT)

        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background: #0f0f1e; border: 1px solid #2a2a4a; "
            f"border-left: 3px solid {color}; border-radius: 4px; padding: 4px; }}"
        )
        cl = QVBoxLayout(card)
        cl.setContentsMargins(6, 4, 6, 4)
        cl.setSpacing(3)

        # Header: tier name + group badge + value tier
        header_row = QHBoxLayout()
        name_lbl = QLabel(tier.get("tier_name", ""))
        name_lbl.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 12px;")
        name_lbl.setWordWrap(True)
        header_row.addWidget(name_lbl, 1)
        val_tier = tier.get("value_tier", "")
        if val_tier:
            tier_color = _VALUE_COLORS.get(val_tier, DIM)
            tier_lbl = QLabel(val_tier)
            tier_lbl.setStyleSheet(f"color: {tier_color}; font-size: 10px; font-weight: bold;")
            header_row.addWidget(tier_lbl)
        cl.addLayout(header_row)

        # Meta: area level + voidstones + map count
        meta_row = QHBoxLayout()
        area_level = tier.get("typical_area_level", "")
        if area_level:
            al_lbl = QLabel(f"Area Level: {area_level}")
            al_lbl.setStyleSheet(f"color: {TEAL}; font-size: 10px;")
            meta_row.addWidget(al_lbl)
        voidstones = tier.get("voidstone_requirement")
        if voidstones is not None:
            vs_lbl = QLabel(f"Voidstones: {voidstones}")
            vs_lbl.setStyleSheet(f"color: {PURPLE}; font-size: 10px;")
            meta_row.addWidget(vs_lbl)
        map_count = tier.get("map_count", "")
        if map_count:
            mc_lbl = QLabel(map_count)
            mc_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px;")
            meta_row.addWidget(mc_lbl)
        meta_row.addStretch()
        cl.addLayout(meta_row)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #2a2a4a;")
        cl.addWidget(sep)

        # Rarity requirement
        rarity = tier.get("rarity_requirement", "")
        if rarity and rarity != "N/A":
            rar_lbl = QLabel(f"Strategy: {rarity}")
            rar_lbl.setStyleSheet(f"color: {TEXT}; font-size: 10px;")
            rar_lbl.setWordWrap(True)
            cl.addWidget(rar_lbl)

        # Key mechanics
        mechanics = tier.get("key_mechanics", [])
        if mechanics:
            mech_lbl = QLabel("Key mechanics: " + "  •  ".join(mechanics))
            mech_lbl.setStyleSheet(f"color: {TEAL}; font-size: 10px;")
            mech_lbl.setWordWrap(True)
            cl.addWidget(mech_lbl)

        # Atlas objective
        objective = tier.get("atlas_objective", "")
        if objective:
            obj_lbl = QLabel(f"Objective: {objective}")
            obj_lbl.setStyleSheet(f"color: {GOLD}; font-size: 10px;")
            obj_lbl.setWordWrap(True)
            cl.addWidget(obj_lbl)

        # Notable maps
        notable_maps = tier.get("notable_maps", [])
        if notable_maps:
            maps_lbl = QLabel("Notable: " + ", ".join(notable_maps))
            maps_lbl.setStyleSheet(f"color: {ORANGE}; font-size: 10px;")
            maps_lbl.setWordWrap(True)
            cl.addWidget(maps_lbl)

        # Notes
        notes = tier.get("notes", "")
        if notes:
            notes_lbl = QLabel(notes)
            notes_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px; font-style: italic;")
            notes_lbl.setWordWrap(True)
            cl.addWidget(notes_lbl)

        return card
