"""
Heist Rogue Skills Quick Reference panel.

Static reference for all 11 Heist rogues — primary and secondary job skills,
max level caps, reward types, and usage notes. Complements the existing Heist
Blueprint Organizer (heist_panel.py) with rogue-specific guidance.

Data source: data/heist_rogues.json
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
    os.path.dirname(__file__), "..", "..", "data", "heist_rogues.json"
)

# One colour per job type for badges
_JOB_COLORS = {
    "Lockpicking":         ACCENT,
    "Agility":             GREEN,
    "Brute Force":         ORANGE,
    "Counter-Thaumaturgy": TEAL,
    "Deception":           RED,
    "Demolition":          ORANGE,
    "Engineering":         TEAL,
    "Perception":          ACCENT,
    "Trap Disarmament":    GREEN,
}


def _load_data() -> dict:
    if not os.path.exists(_DATA_PATH):
        return {}
    try:
        with open(_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[HeistRoguesPanel] failed to load data: {e}")
        return {}


class HeistRoguesPanel(QWidget):
    def __init__(self):
        super().__init__()
        data = _load_data()
        self._all_rogues  = data.get("rogues", [])
        self._job_types   = data.get("job_types", [])
        self._how_it_works = data.get("how_it_works", "")
        self._tips         = data.get("tips", [])
        self._active_job: str | None = None
        self._build_ui()
        self._render_rogues(self._all_rogues)

    # ------------------------------------------------------------------

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        header = QLabel(
            f"Heist Rogues  •  {len(self._all_rogues)} rogues  •  "
            f"{len(self._job_types)} job types"
        )
        header.setStyleSheet(f"color: {ACCENT}; font-weight: bold; font-size: 13px;")
        layout.addWidget(header)

        if self._how_it_works:
            how_lbl = QLabel(self._how_it_works)
            how_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px;")
            how_lbl.setWordWrap(True)
            layout.addWidget(how_lbl)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Search by rogue name, job, or reward type…")
        self._search.setStyleSheet(
            "QLineEdit { background: #0f0f23; color: #d4c5a9; border: 1px solid #2a2a4a; "
            "border-radius: 4px; padding: 4px 8px; }"
        )
        self._search.textChanged.connect(self._on_search)
        layout.addWidget(self._search)

        # Job filter buttons
        filter_row = QHBoxLayout()
        filter_row.setSpacing(4)
        job_lbl = QLabel("Job:")
        job_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px;")
        filter_row.addWidget(job_lbl)
        self._filter_buttons: dict[str, QPushButton] = {}
        for job in ["All"] + self._job_types:
            btn = QPushButton(job)
            btn.setFixedHeight(22)
            color = _JOB_COLORS.get(job, ACCENT)
            btn.setStyleSheet(
                f"QPushButton {{ background: #0f0f23; color: {DIM}; border: 1px solid #2a2a4a; "
                f"border-radius: 3px; padding: 0 5px; font-size: 10px; }}"
                f"QPushButton:hover {{ background: #1a1a3a; }}"
                f"QPushButton[active='true'] {{ color: {color}; border-color: {color}; }}"
            )
            btn.clicked.connect(lambda _, j=job: self._on_job_filter(j))
            self._filter_buttons[job] = btn
            filter_row.addWidget(btn)
        filter_row.addStretch()
        layout.addLayout(filter_row)
        self._set_active_job("All")

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

    def _on_job_filter(self, job: str):
        self._set_active_job(job)
        self._on_search(self._search.text())

    def _set_active_job(self, job: str):
        self._active_job = None if job == "All" else job
        for btn_name, btn in self._filter_buttons.items():
            btn.setProperty("active", "true" if btn_name == job else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _on_search(self, text: str):
        query = text.strip().lower()
        pool = self._all_rogues

        if self._active_job:
            pool = [
                r for r in pool
                if self._active_job == r.get("primary_job")
                or self._active_job == r.get("secondary_job")
            ]

        if query:
            pool = [
                r for r in pool
                if query in r.get("name", "").lower()
                or query in (r.get("primary_job") or "").lower()
                or query in (r.get("secondary_job") or "").lower()
                or query in r.get("reward_type", "").lower()
                or query in r.get("specialty", "").lower()
                or query in r.get("notes", "").lower()
            ]

        self._render_rogues(pool)

    def _render_rogues(self, rogues: list[dict]):
        while self._list_layout.count() > 1:
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not rogues:
            empty = QLabel("No matching rogues.")
            empty.setStyleSheet(f"color: {DIM}; font-size: 11px;")
            self._list_layout.insertWidget(0, empty)
            return

        for i, rogue in enumerate(rogues):
            card = self._make_card(rogue)
            self._list_layout.insertWidget(i, card)

    def _make_card(self, rogue: dict) -> QWidget:
        primary_job = rogue.get("primary_job", "")
        border_color = _JOB_COLORS.get(primary_job, TEAL)

        card = QWidget()
        card.setStyleSheet(
            f"background: #0f0f23; border-left: 3px solid {border_color}; border-radius: 2px;"
        )
        vl = QVBoxLayout(card)
        vl.setContentsMargins(8, 6, 8, 6)
        vl.setSpacing(3)

        # Name
        name_lbl = QLabel(rogue.get("name", ""))
        name_lbl.setStyleSheet(f"color: {ACCENT}; font-weight: bold; font-size: 12px;")
        vl.addWidget(name_lbl)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #1a1a3a;")
        vl.addWidget(sep)

        # Jobs row
        jobs_row = QHBoxLayout()
        jobs_row.setSpacing(6)

        pjob_color = _JOB_COLORS.get(primary_job, TEAL)
        pmax = rogue.get("max_primary_level", "?")
        pjob_lbl = QLabel(
            f"<b style='color:{pjob_color}'>{primary_job}</b> "
            f"<span style='color:{DIM}'>(max lvl {pmax})</span>"
        )
        pjob_lbl.setTextFormat(Qt.TextFormat.RichText)
        pjob_lbl.setStyleSheet("font-size: 11px;")
        jobs_row.addWidget(pjob_lbl)

        secondary_job = rogue.get("secondary_job")
        if secondary_job:
            smax = rogue.get("max_secondary_level", "?")
            sjob_color = _JOB_COLORS.get(secondary_job, DIM)
            sjob_lbl = QLabel(
                f"<span style='color:{DIM}'>+</span> "
                f"<b style='color:{sjob_color}'>{secondary_job}</b> "
                f"<span style='color:{DIM}'>(max lvl {smax})</span>"
            )
            sjob_lbl.setTextFormat(Qt.TextFormat.RichText)
            sjob_lbl.setStyleSheet("font-size: 11px;")
            jobs_row.addWidget(sjob_lbl)

        jobs_row.addStretch()
        vl.addLayout(jobs_row)

        # Specialty
        specialty = rogue.get("specialty", "")
        if specialty:
            spec_lbl = QLabel(specialty)
            spec_lbl.setStyleSheet(f"color: {TEXT}; font-size: 10px;")
            spec_lbl.setWordWrap(True)
            vl.addWidget(spec_lbl)

        # Reward type + notes row
        bottom_row = QHBoxLayout()
        reward = rogue.get("reward_type", "")
        if reward:
            rew_lbl = QLabel(
                f"<b style='color:{GREEN}'>Reward:</b> "
                f"<span style='color:{TEXT}'>{reward}</span>"
            )
            rew_lbl.setTextFormat(Qt.TextFormat.RichText)
            rew_lbl.setStyleSheet("font-size: 10px;")
            bottom_row.addWidget(rew_lbl)
        bottom_row.addStretch()
        vl.addLayout(bottom_row)

        notes = rogue.get("notes", "")
        if notes:
            notes_lbl = QLabel(notes)
            notes_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px; font-style: italic;")
            notes_lbl.setWordWrap(True)
            vl.addWidget(notes_lbl)

        return card
