"""
Atlas Map Completion Tracker panel.

Shows which atlas maps have been visited vs. total, with a breakdown of
unvisited maps by tier. Updates in real-time as the player enters new maps.

No OAuth required — reads only Client.txt zone_change events.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QScrollArea, QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot

ACCENT = "#e2b96f"
TEXT   = "#d4c5a9"
DIM    = "#8a7a65"
GREEN  = "#5cba6e"
TEAL   = "#4ae8c8"
RED    = "#e05050"


class AtlasPanel(QWidget):
    _updated = pyqtSignal(object)   # stats dict from AtlasTracker.get_stats()

    def __init__(self, atlas_tracker):
        super().__init__()
        self._tracker = atlas_tracker
        self._build_ui()

        self._updated.connect(self._on_update)
        atlas_tracker.on_update(lambda stats: self._updated.emit(stats))

        # Populate from persisted data immediately
        self._on_update(atlas_tracker.get_stats())

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # Progress summary
        self._progress_label = QLabel("—")
        self._progress_label.setStyleSheet(
            f"color: {ACCENT}; font-weight: bold; font-size: 14px;"
        )
        layout.addWidget(self._progress_label)

        self._bar_label = QLabel("")
        self._bar_label.setStyleSheet(f"color: {TEAL}; font-size: 11px;")
        layout.addWidget(self._bar_label)

        self._session_label = QLabel("")
        self._session_label.setStyleSheet(f"color: {DIM}; font-size: 11px;")
        layout.addWidget(self._session_label)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #2a2a4a;")
        layout.addWidget(sep)

        # Unvisited maps header
        unvisited_hdr = QLabel("Unvisited Maps")
        unvisited_hdr.setStyleSheet(f"color: {TEXT}; font-weight: bold; font-size: 12px;")
        layout.addWidget(unvisited_hdr)

        # Scrollable tier sections
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        self._tier_container = QWidget()
        self._tier_layout    = QVBoxLayout(self._tier_container)
        self._tier_layout.setContentsMargins(0, 0, 0, 0)
        self._tier_layout.setSpacing(4)
        self._tier_layout.addStretch()
        scroll.setWidget(self._tier_container)
        layout.addWidget(scroll)

        note = QLabel("Updates automatically as you enter maps.")
        note.setStyleSheet(f"color: {DIM}; font-size: 10px;")
        layout.addWidget(note)

        # Reset button
        self._reset_btn = QPushButton("Reset Atlas Progress")
        self._reset_btn.setStyleSheet(
            "QPushButton { background: #3a1a1a; color: #e05050; border: 1px solid #5a2020; "
            "border-radius: 4px; padding: 4px 10px; } "
            "QPushButton:hover { background: #5a2020; }"
        )
        self._reset_btn.clicked.connect(self._confirm_reset)
        layout.addWidget(self._reset_btn)

    @pyqtSlot(object)
    def _on_update(self, stats: dict):
        total   = stats.get("total", 0)
        visited = stats.get("visited", 0)
        pct     = stats.get("pct", 0.0)
        new     = stats.get("session_new", 0)

        self._progress_label.setText(f"{visited} / {total}  ({pct:.1f}% complete)")

        # Progress bar: 20-char wide
        bar_width = 20
        filled    = int(pct / 100 * bar_width)
        bar       = "━" * filled + "─" * (bar_width - filled)
        self._bar_label.setText(f"[{bar}]")

        if new > 0:
            self._session_label.setText(f"+{new} new this session")
        else:
            self._session_label.setText("No new maps this session yet")

        # Rebuild tier sections
        while self._tier_layout.count() > 1:
            item = self._tier_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        unvisited = stats.get("unvisited_by_tier", {})
        if not unvisited:
            done = QLabel("All atlas maps visited!")
            done.setStyleSheet(f"color: {GREEN}; font-weight: bold; font-size: 12px;")
            self._tier_layout.insertWidget(0, done)
            return

        insert_idx = 0
        for tier in sorted(unvisited.keys()):
            maps = unvisited[tier]
            if not maps:
                continue

            hdr = QLabel(f"Tier {tier}  ({len(maps)} unvisited)")
            hdr.setStyleSheet(f"color: {TEAL}; font-size: 10px; font-weight: bold;")
            self._tier_layout.insertWidget(insert_idx, hdr)
            insert_idx += 1

            # Up to 8 map names per tier to avoid drowning the panel
            display = maps[:8]
            remainder = len(maps) - 8
            names_text = "  ".join(display)
            if remainder > 0:
                names_text += f"  … +{remainder} more"
            names_lbl = QLabel(names_text)
            names_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px;")
            names_lbl.setWordWrap(True)
            self._tier_layout.insertWidget(insert_idx, names_lbl)
            insert_idx += 1

    def _confirm_reset(self):
        reply = QMessageBox.question(
            self,
            "Reset Atlas Progress",
            "This will clear all recorded atlas map visits.\n\n"
            "Your progress will be lost. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._tracker.reset()
