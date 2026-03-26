"""
Expedition Faction Rewards Reference panel.

Reference for all 4 Expedition factions — merchants, trade currencies,
reward specialties, best-for use cases, and farming tips.

Data source: data/expedition_factions.json
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
BLUE   = "#6090e8"
GOLD   = "#f5c842"

_DATA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "expedition_factions.json"
)

_ALL = "All"


def _load_data() -> dict:
    if not os.path.exists(_DATA_PATH):
        return {}
    try:
        with open(_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ExpeditionFactionsPanel] failed to load data: {e}")
        return {}


class ExpeditionFactionsPanel(QWidget):
    def __init__(self):
        super().__init__()
        data = _load_data()
        self._factions   = data.get("factions", [])
        self._mechanics  = data.get("expedition_mechanics", [])
        self._tips       = data.get("tips", [])
        self._intro      = data.get("intro", "")
        self._active_faction = _ALL
        self._faction_names  = [f["name"] for f in self._factions]
        self._build_ui()
        self._set_faction(_ALL)

    # ------------------------------------------------------------------

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        header = QLabel(f"Expedition Faction Rewards  •  {len(self._factions)} factions")
        header.setStyleSheet(f"color: {ACCENT}; font-weight: bold; font-size: 13px;")
        layout.addWidget(header)

        if self._intro:
            intro_lbl = QLabel(self._intro)
            intro_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px;")
            intro_lbl.setWordWrap(True)
            layout.addWidget(intro_lbl)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Search by faction, merchant, reward, or tip…")
        self._search.setStyleSheet(
            "QLineEdit { background: #0f0f23; color: #d4c5a9; border: 1px solid #2a2a4a; "
            "border-radius: 4px; padding: 4px 8px; }"
        )
        self._search.textChanged.connect(self._refresh)
        layout.addWidget(self._search)

        # Faction filter buttons
        faction_row = QHBoxLayout()
        faction_row.setSpacing(4)
        self._faction_buttons: dict[str, QPushButton] = {}

        # "All" button
        all_btn = QPushButton(_ALL)
        all_btn.setFixedHeight(22)
        all_btn.setStyleSheet(
            f"QPushButton {{ background: #0f0f23; color: {DIM}; border: 1px solid #2a2a4a; "
            f"border-radius: 3px; padding: 0 6px; font-size: 10px; }}"
            f"QPushButton:hover {{ background: #1a1a3a; }}"
            f"QPushButton[active='true'] {{ color: {ACCENT}; border-color: {ACCENT}; }}"
        )
        all_btn.clicked.connect(lambda _: self._set_faction(_ALL))
        self._faction_buttons[_ALL] = all_btn
        faction_row.addWidget(all_btn)

        for faction in self._factions:
            name = faction["name"]
            color = faction.get("color", ACCENT)
            merchant = faction.get("merchant", "")
            label = merchant if merchant else name.split()[0]
            btn = QPushButton(label)
            btn.setFixedHeight(22)
            btn.setToolTip(name)
            btn.setStyleSheet(
                f"QPushButton {{ background: #0f0f23; color: {DIM}; border: 1px solid #2a2a4a; "
                f"border-radius: 3px; padding: 0 6px; font-size: 10px; }}"
                f"QPushButton:hover {{ background: #1a1a3a; }}"
                f"QPushButton[active='true'] {{ color: {color}; border-color: {color}; }}"
            )
            btn.clicked.connect(lambda _, n=name: self._set_faction(n))
            self._faction_buttons[name] = btn
            faction_row.addWidget(btn)
        faction_row.addStretch()
        layout.addLayout(faction_row)

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

        if self._mechanics:
            mech_lbl = QLabel("Mechanic: " + self._mechanics[0])
            mech_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px; font-style: italic;")
            mech_lbl.setWordWrap(True)
            layout.addWidget(mech_lbl)

    def _set_faction(self, faction: str):
        self._active_faction = faction
        for name, btn in self._faction_buttons.items():
            btn.setProperty("active", "true" if name == faction else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self._refresh()

    def _matches(self, faction: dict, query: str) -> bool:
        if not query:
            return True
        rewards_text = " ".join(faction.get("key_rewards", []))
        offers_text  = " ".join(faction.get("merchant_offers", []))
        best_text    = " ".join(faction.get("best_for", []))
        tips_text    = " ".join(faction.get("farming_tips", []))
        searchable = " ".join([
            faction.get("name", ""),
            faction.get("merchant", ""),
            faction.get("trade_currency", ""),
            faction.get("specialty", ""),
            faction.get("logbook_region", ""),
            rewards_text,
            offers_text,
            best_text,
            tips_text,
            faction.get("notes", ""),
        ]).lower()
        return query in searchable

    def _refresh(self):
        query = self._search.text().strip().lower()
        pool = self._factions
        if self._active_faction != _ALL:
            pool = [f for f in pool if f.get("name") == self._active_faction]
        filtered = [f for f in pool if self._matches(f, query)]
        self._render(filtered)

    def _render(self, factions: list[dict]):
        while self._list_layout.count() > 1:
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not factions:
            empty = QLabel("No matching factions.")
            empty.setStyleSheet(f"color: {DIM}; font-size: 11px;")
            self._list_layout.insertWidget(0, empty)
            return

        for i, faction in enumerate(factions):
            card = self._make_card(faction)
            self._list_layout.insertWidget(i, card)

    def _make_card(self, faction: dict) -> QFrame:
        color = faction.get("color", ACCENT)

        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background: #0f0f1e; border: 1px solid #2a2a4a; "
            f"border-left: 3px solid {color}; border-radius: 4px; padding: 4px; }}"
        )
        cl = QVBoxLayout(card)
        cl.setContentsMargins(6, 4, 6, 4)
        cl.setSpacing(3)

        # Header: faction name + merchant badge + specialty
        header_row = QHBoxLayout()
        name_lbl = QLabel(faction.get("name", ""))
        name_lbl.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 12px;")
        header_row.addWidget(name_lbl, 1)
        merchant = faction.get("merchant", "")
        if merchant:
            merch_badge = QLabel(f"NPC: {merchant}")
            merch_badge.setStyleSheet(f"color: {TEAL}; font-size: 10px; font-weight: bold;")
            header_row.addWidget(merch_badge)
        cl.addLayout(header_row)

        # Trade currency + specialty
        currency = faction.get("trade_currency", "")
        specialty = faction.get("specialty", "")
        if currency or specialty:
            sub_row = QHBoxLayout()
            if currency:
                cur_lbl = QLabel(f"Currency: {currency}")
                cur_lbl.setStyleSheet(f"color: {GOLD}; font-size: 10px;")
                sub_row.addWidget(cur_lbl)
            if specialty:
                spec_lbl = QLabel(f"  •  {specialty}")
                spec_lbl.setStyleSheet(f"color: {ACCENT}; font-size: 10px;")
                sub_row.addWidget(spec_lbl)
            sub_row.addStretch()
            cl.addLayout(sub_row)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #2a2a4a;")
        cl.addWidget(sep)

        # Key rewards
        rewards = faction.get("key_rewards", [])[:4]
        if rewards:
            rewards_lbl = QLabel("Key drops: " + ", ".join(rewards))
            rewards_lbl.setStyleSheet(f"color: {TEXT}; font-size: 10px;")
            rewards_lbl.setWordWrap(True)
            cl.addWidget(rewards_lbl)

        # Merchant offers (top 2)
        offers = faction.get("merchant_offers", [])[:2]
        for offer in offers:
            offer_lbl = QLabel(f"• {offer}")
            offer_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px;")
            offer_lbl.setWordWrap(True)
            cl.addWidget(offer_lbl)

        # Best for
        best_for = faction.get("best_for", [])
        if best_for:
            bf_lbl = QLabel("Best for: " + ", ".join(best_for))
            bf_lbl.setStyleSheet(f"color: {TEAL}; font-size: 10px;")
            bf_lbl.setWordWrap(True)
            cl.addWidget(bf_lbl)

        # Farming tips (top 2)
        tips = faction.get("farming_tips", [])[:2]
        for tip in tips:
            tip_lbl = QLabel(f"→ {tip}")
            tip_lbl.setStyleSheet(f"color: {GREEN}; font-size: 10px;")
            tip_lbl.setWordWrap(True)
            cl.addWidget(tip_lbl)

        # Notes
        notes = faction.get("notes", "")
        if notes:
            notes_lbl = QLabel(notes)
            notes_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px; font-style: italic;")
            notes_lbl.setWordWrap(True)
            cl.addWidget(notes_lbl)

        return card
