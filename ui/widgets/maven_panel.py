"""
Maven Boss Witness Guide panel.

Static reference for all Maven invitations — which boss sets to witness for each
invitation, how to access each boss, and the path to fighting The Maven herself.

Data source: data/maven_invitations.json
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
RED    = "#e05050"
PURPLE = "#9a4ae8"

_DATA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "maven_invitations.json"
)

_DIFFICULTY_COLORS = {
    "Beginner":             TEAL,
    "Intermediate":         GREEN,
    "Advanced":             ORANGE,
    "Endgame (pinnacle)":   RED,
}


def _load_data() -> dict:
    if not os.path.exists(_DATA_PATH):
        return {}
    try:
        with open(_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[MavenPanel] failed to load data: {e}")
        return {}


class MavenPanel(QWidget):
    def __init__(self):
        super().__init__()
        data = _load_data()
        self._all_invitations = data.get("invitations", [])
        self._maven_fight     = data.get("maven_fight", {})
        self._how_it_works    = data.get("how_maven_works", "")
        self._tips            = data.get("tips", [])
        self._build_ui()
        self._render_invitations(self._all_invitations)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        header = QLabel(f"Maven Witness Guide  •  {len(self._all_invitations)} invitations")
        header.setStyleSheet(f"color: {ACCENT}; font-weight: bold; font-size: 13px;")
        layout.addWidget(header)

        if self._how_it_works:
            how_lbl = QLabel(self._how_it_works)
            how_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px;")
            how_lbl.setWordWrap(True)
            layout.addWidget(how_lbl)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Search by invitation name, boss, or map…")
        self._search.setStyleSheet(
            "QLineEdit { background: #0f0f23; color: #d4c5a9; border: 1px solid #2a2a4a; "
            "border-radius: 4px; padding: 4px 8px; }"
        )
        self._search.textChanged.connect(self._on_search)
        layout.addWidget(self._search)

        # Scrollable invitation list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        self._inv_container = QWidget()
        self._inv_layout    = QVBoxLayout(self._inv_container)
        self._inv_layout.setContentsMargins(0, 0, 0, 0)
        self._inv_layout.setSpacing(6)
        self._inv_layout.addStretch()
        scroll.setWidget(self._inv_container)
        layout.addWidget(scroll)

        # Maven fight summary footer
        if self._maven_fight:
            mvn_lbl = QLabel(
                f"<b style='color:{PURPLE}'>The Maven:</b> "
                f"<span style='color:{DIM}'>{self._maven_fight.get('requirement', '')}</span>"
            )
            mvn_lbl.setTextFormat(Qt.TextFormat.RichText)
            mvn_lbl.setWordWrap(True)
            mvn_lbl.setStyleSheet("font-size: 10px;")
            layout.addWidget(mvn_lbl)

    def _on_search(self, text: str):
        query = text.strip().lower()
        if not query:
            self._render_invitations(self._all_invitations)
            return

        filtered = []
        for inv in self._all_invitations:
            if (query in inv.get("name", "").lower()
                    or query in inv.get("difficulty", "").lower()
                    or query in inv.get("reward", "").lower()
                    or query in inv.get("notes", "").lower()):
                filtered.append(inv)
                continue
            # Also search boss names and found_in locations
            for wg in inv.get("witness_groups", []):
                if (query in wg.get("boss", "").lower()
                        or query in wg.get("found_in", "").lower()
                        or query in wg.get("notes", "").lower()):
                    filtered.append(inv)
                    break
        self._render_invitations(filtered)

    def _render_invitations(self, invitations: list[dict]):
        while self._inv_layout.count() > 1:
            item = self._inv_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not invitations:
            empty = QLabel("No matching invitations.")
            empty.setStyleSheet(f"color: {DIM}; font-size: 11px;")
            self._inv_layout.insertWidget(0, empty)
            return

        for i, inv in enumerate(invitations):
            card = self._make_invitation_card(inv)
            self._inv_layout.insertWidget(i, card)

    def _make_invitation_card(self, inv: dict) -> QWidget:
        difficulty = inv.get("difficulty", "")
        diff_color = _DIFFICULTY_COLORS.get(difficulty, DIM)

        card = QWidget()
        card.setStyleSheet(
            f"background: #0f0f23; border-left: 3px solid {diff_color}; border-radius: 2px;"
        )
        vl = QVBoxLayout(card)
        vl.setContentsMargins(8, 6, 8, 6)
        vl.setSpacing(4)

        # Invitation name + difficulty badge
        top_row = QHBoxLayout()
        top_row.setSpacing(8)
        name_lbl = QLabel(inv.get("name", ""))
        name_lbl.setStyleSheet(f"color: {ACCENT}; font-weight: bold; font-size: 12px;")
        top_row.addWidget(name_lbl, 1)

        if difficulty:
            badge = QLabel(difficulty)
            badge.setStyleSheet(
                f"color: {diff_color}; font-size: 9px; background: #1a1a3a; "
                f"border-radius: 2px; padding: 1px 5px;"
            )
            top_row.addWidget(badge)
        vl.addLayout(top_row)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #1a1a3a;")
        vl.addWidget(sep)

        # Witness groups
        witness_groups = inv.get("witness_groups", [])
        if witness_groups:
            wg_header = QLabel(
                f"<b style='color:{TEAL}'>Witnesses required (10× each):</b>"
            )
            wg_header.setTextFormat(Qt.TextFormat.RichText)
            wg_header.setStyleSheet("font-size: 10px;")
            vl.addWidget(wg_header)
            for wg in witness_groups:
                boss_name = wg.get("boss", "")
                found_in  = wg.get("found_in", "")
                wg_notes  = wg.get("notes", "")

                boss_lbl = QLabel(f"  • <b style='color:{TEXT}'>{boss_name}</b>")
                boss_lbl.setTextFormat(Qt.TextFormat.RichText)
                boss_lbl.setStyleSheet("font-size: 10px;")
                vl.addWidget(boss_lbl)

                if found_in:
                    loc_lbl = QLabel(f"    <i style='color:{DIM}'>{found_in}</i>")
                    loc_lbl.setTextFormat(Qt.TextFormat.RichText)
                    loc_lbl.setWordWrap(True)
                    loc_lbl.setStyleSheet("font-size: 10px;")
                    vl.addWidget(loc_lbl)

                if wg_notes:
                    wg_note_lbl = QLabel(f"    {wg_notes}")
                    wg_note_lbl.setStyleSheet(
                        f"color: {DIM}; font-size: 10px; font-style: italic;"
                    )
                    wg_note_lbl.setWordWrap(True)
                    vl.addWidget(wg_note_lbl)

        # Reward
        reward = inv.get("reward", "")
        if reward:
            reward_lbl = QLabel(
                f"<b style='color:{GREEN}'>Reward:</b> "
                f"<span style='color:{DIM}'>{reward}</span>"
            )
            reward_lbl.setTextFormat(Qt.TextFormat.RichText)
            reward_lbl.setWordWrap(True)
            reward_lbl.setStyleSheet("font-size: 10px;")
            vl.addWidget(reward_lbl)

        # Notes
        notes = inv.get("notes", "")
        if notes:
            notes_lbl = QLabel(notes)
            notes_lbl.setStyleSheet(
                f"color: {DIM}; font-size: 10px; font-style: italic;"
            )
            notes_lbl.setWordWrap(True)
            vl.addWidget(notes_lbl)

        return card
