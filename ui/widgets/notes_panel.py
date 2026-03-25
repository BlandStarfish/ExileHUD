"""
Build notes panel.

A personal plain-text notepad saved to state/notes.json (gitignored).
Use cases: boss strategies, league goals, build reminders, map target lists.
"""

import json
import os

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton,
)

ACCENT = "#e2b96f"
DIM    = "#8a7a65"
GREEN  = "#5cba6e"
RED    = "#e05050"

_NOTES_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "state", "notes.json")


def _load_notes() -> str:
    if os.path.exists(_NOTES_PATH):
        try:
            with open(_NOTES_PATH, "r") as f:
                return json.load(f).get("text", "")
        except Exception:
            return ""
    return ""


def _save_notes(text: str):
    os.makedirs(os.path.dirname(_NOTES_PATH), exist_ok=True)
    with open(_NOTES_PATH, "w") as f:
        json.dump({"text": text}, f)


class NotesPanel(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        hint = QLabel("Personal notes — boss strategies, league goals, build reminders, map targets.")
        hint.setStyleSheet(f"color: {DIM}; font-size: 10px;")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self._editor = QTextEdit()
        self._editor.setStyleSheet(
            "background: #0f0f23; color: #d4c5a9; border: 1px solid #2a2a4a;"
            " border-radius: 4px; padding: 4px; font-family: 'Segoe UI'; font-size: 11px;"
        )
        self._editor.setPlainText(_load_notes())
        layout.addWidget(self._editor, 1)

        btn_row = QHBoxLayout()
        self._status = QLabel("")
        self._status.setStyleSheet(f"color: {DIM}; font-size: 10px;")
        btn_row.addWidget(self._status, 1)

        save_btn = QPushButton("Save Notes")
        save_btn.setStyleSheet(
            f"QPushButton {{ background: {ACCENT}; color: #1a1a2e; font-weight: bold; padding: 4px 12px; }}"
            f"QPushButton:hover {{ background: #c8a84b; }}"
        )
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _save(self):
        try:
            _save_notes(self._editor.toPlainText())
            self._status.setStyleSheet(f"color: {GREEN}; font-size: 10px;")
            self._status.setText("Saved.")
        except Exception as e:
            self._status.setStyleSheet(f"color: {RED}; font-size: 10px;")
            self._status.setText(f"Error: {e}")
