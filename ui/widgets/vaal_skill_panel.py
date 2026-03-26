"""
Vaal Skill Reference panel.

Static reference for all major Vaal skills — soul requirements, effects,
best builds, and tactical usage notes.

Data source: data/vaal_skills.json
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
    os.path.dirname(__file__), "..", "..", "data", "vaal_skills.json"
)

_ELEMENT_COLORS = {
    "Lightning": YELLOW,
    "Fire":      RED,
    "Cold":      TEAL,
    "Physical":  TEXT,
    "Chaos":     PURPLE,
    "Aura":      GREEN,
    "Armour":    ORANGE,
}

_ALL = "All"


def _load_data() -> dict:
    if not os.path.exists(_DATA_PATH):
        return {}
    try:
        with open(_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[VaalSkillPanel] failed to load data: {e}")
        return {}


class VaalSkillPanel(QWidget):
    def __init__(self):
        super().__init__()
        data = _load_data()
        self._skills       = data.get("skills", [])
        self._how_it_works = data.get("how_it_works", "")
        self._soul_note    = data.get("soul_note", "")
        self._tips         = data.get("tips", [])
        # Collect unique elements for filter buttons
        elements = []
        seen = set()
        for s in self._skills:
            e = s.get("element", "")
            if e and e not in seen:
                elements.append(e)
                seen.add(e)
        self._elements     = [_ALL] + elements
        self._active_elem  = _ALL
        self._build_ui()
        self._set_element(_ALL)

    # ------------------------------------------------------------------

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        header = QLabel(f"Vaal Skill Reference  •  {len(self._skills)} skills")
        header.setStyleSheet(f"color: {ACCENT}; font-weight: bold; font-size: 13px;")
        layout.addWidget(header)

        if self._how_it_works:
            how_lbl = QLabel(self._how_it_works)
            how_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px;")
            how_lbl.setWordWrap(True)
            layout.addWidget(how_lbl)

        if self._soul_note:
            soul_lbl = QLabel(self._soul_note)
            soul_lbl.setStyleSheet(
                f"color: {TEAL}; font-size: 10px; font-style: italic;"
            )
            soul_lbl.setWordWrap(True)
            layout.addWidget(soul_lbl)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Search by skill name, element, effect, or build…")
        self._search.setStyleSheet(
            "QLineEdit { background: #0f0f23; color: #d4c5a9; border: 1px solid #2a2a4a; "
            "border-radius: 4px; padding: 4px 8px; }"
        )
        self._search.textChanged.connect(self._refresh)
        layout.addWidget(self._search)

        # Element filter buttons
        elem_row = QHBoxLayout()
        elem_row.setSpacing(4)
        self._elem_buttons: dict[str, QPushButton] = {}
        for elem in self._elements:
            color = _ELEMENT_COLORS.get(elem, ACCENT)
            btn = QPushButton(elem)
            btn.setFixedHeight(22)
            btn.setStyleSheet(
                f"QPushButton {{ background: #0f0f23; color: {DIM}; border: 1px solid #2a2a4a; "
                f"border-radius: 3px; padding: 0 6px; font-size: 10px; }}"
                f"QPushButton:hover {{ background: #1a1a3a; }}"
                f"QPushButton[active='true'] {{ color: {color}; border-color: {color}; }}"
            )
            btn.clicked.connect(lambda _, e=elem: self._set_element(e))
            self._elem_buttons[elem] = btn
            elem_row.addWidget(btn)
        elem_row.addStretch()
        layout.addLayout(elem_row)

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

        # Tips footer (first two tips)
        if self._tips:
            tips_lbl = QLabel("Tips: " + "  •  ".join(self._tips[:2]))
            tips_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px; font-style: italic;")
            tips_lbl.setWordWrap(True)
            layout.addWidget(tips_lbl)

    def _set_element(self, elem: str):
        self._active_elem = elem
        for e, btn in self._elem_buttons.items():
            btn.setProperty("active", "true" if e == elem else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self._refresh()

    def _skill_matches(self, skill: dict, query: str) -> bool:
        if not query:
            return True
        searchable = " ".join([
            skill.get("name", ""),
            skill.get("element", ""),
            skill.get("effect", ""),
            skill.get("when_to_use", ""),
            skill.get("notes", ""),
            " ".join(skill.get("best_builds", [])),
        ]).lower()
        return query in searchable

    def _refresh(self):
        query = self._search.text().strip().lower()
        pool = self._skills
        if self._active_elem != _ALL:
            pool = [s for s in pool if s.get("element") == self._active_elem]
        filtered = [s for s in pool if self._skill_matches(s, query)]
        self._render(filtered)

    def _render(self, skills: list[dict]):
        while self._list_layout.count() > 1:
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not skills:
            empty = QLabel("No matching Vaal skills.")
            empty.setStyleSheet(f"color: {DIM}; font-size: 11px;")
            self._list_layout.insertWidget(0, empty)
            return

        for i, skill in enumerate(skills):
            card = self._make_card(skill)
            self._list_layout.insertWidget(i, card)

    def _make_card(self, skill: dict) -> QFrame:
        elem  = skill.get("element", "")
        color = _ELEMENT_COLORS.get(elem, DIM)

        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background: #0f0f1e; border: 1px solid #2a2a4a; "
            f"border-left: 3px solid {color}; border-radius: 4px; padding: 4px; }}"
        )
        cl = QVBoxLayout(card)
        cl.setContentsMargins(6, 4, 6, 4)
        cl.setSpacing(3)

        # Header row: name + element badge + soul requirements
        header_row = QHBoxLayout()
        name_lbl = QLabel(skill.get("name", ""))
        name_lbl.setStyleSheet(f"color: {ACCENT}; font-weight: bold; font-size: 12px;")
        header_row.addWidget(name_lbl)

        if elem:
            elem_badge = QLabel(f"[{elem}]")
            elem_badge.setStyleSheet(f"color: {color}; font-size: 10px; font-weight: bold;")
            header_row.addWidget(elem_badge)

        header_row.addStretch()

        souls_n = skill.get("souls_normal", 0)
        souls_m = skill.get("souls_merciless", 0)
        if souls_n:
            souls_lbl = QLabel(f"Souls: {souls_n} / {souls_m} (merciless)")
            souls_lbl.setStyleSheet(f"color: {YELLOW}; font-size: 10px;")
            header_row.addWidget(souls_lbl)

        cl.addLayout(header_row)

        # Effect
        effect = skill.get("effect", "")
        if effect:
            eff_lbl = QLabel(effect)
            eff_lbl.setStyleSheet(f"color: {TEXT}; font-size: 11px;")
            eff_lbl.setWordWrap(True)
            cl.addWidget(eff_lbl)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: #2a2a4a;")
        cl.addWidget(sep)

        # When to use
        when = skill.get("when_to_use", "")
        if when:
            when_lbl = QLabel(f"When: {when}")
            when_lbl.setStyleSheet(f"color: {GREEN}; font-size: 10px;")
            when_lbl.setWordWrap(True)
            cl.addWidget(when_lbl)

        # Best builds
        builds = skill.get("best_builds", [])
        if builds:
            builds_lbl = QLabel("Builds: " + " / ".join(builds))
            builds_lbl.setStyleSheet(f"color: {TEAL}; font-size: 10px;")
            builds_lbl.setWordWrap(True)
            cl.addWidget(builds_lbl)

        # Notes
        notes = skill.get("notes", "")
        if notes:
            notes_lbl = QLabel(notes)
            notes_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px; font-style: italic;")
            notes_lbl.setWordWrap(True)
            cl.addWidget(notes_lbl)

        return card
