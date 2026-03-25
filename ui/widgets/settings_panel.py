"""
Settings panel — configure PoELens from the overlay UI.

Exposes: Client.txt path, league, overlay opacity, hotkeys.
Writes to state/config.json via config.save().
Changes take effect on the next app restart (except opacity, applied immediately).
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QScrollArea,
    QLabel, QLineEdit, QPushButton, QDoubleSpinBox, QSpinBox,
    QGroupBox, QFileDialog, QFrame, QMessageBox,
)
from PyQt6.QtCore import Qt
from typing import Callable, Optional

import config as cfg
from config import CLIENT_LOG_PATHS as _LOG_PATHS

ACCENT = "#e2b96f"
TEXT   = "#d4c5a9"
DIM    = "#8a7a65"
GREEN  = "#5cba6e"
RED    = "#e05050"

_HOTKEY_LABELS = {
    "price_check":    "Price check",
    "toggle_hud":     "Toggle HUD",
    "passive_tree":   "Passive tree",
    "crafting_queue": "Crafting queue",
    "map_overlay":    "Map overlay",
}


class SettingsPanel(QWidget):
    def __init__(self, config: dict, on_opacity_change: Optional[Callable[[float], None]] = None,
                 state=None):
        """
        config             — the live config dict (from config.load())
        on_opacity_change  — optional callback(opacity: float) applied immediately on save
        state              — AppState instance (for New Character reset)
        """
        super().__init__()
        self._config = config
        self._on_opacity_change = on_opacity_change
        self._state = state
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        outer.addWidget(scroll, 1)

        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)
        scroll.setWidget(inner)

        # ── Game settings ──────────────────────────────────────────────
        game_group = QGroupBox("Game")
        game_group.setStyleSheet(f"QGroupBox {{ color: {ACCENT}; font-weight: bold; font-size: 11px; }}")
        game_form = QFormLayout(game_group)
        game_form.setSpacing(6)
        game_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        log_row = QHBoxLayout()
        self._log_path = QLineEdit(self._config.get("client_log_path", ""))
        self._log_path.setStyleSheet(_field_style())
        browse_btn = QPushButton("Browse…")
        browse_btn.setFixedWidth(70)
        browse_btn.clicked.connect(self._browse_log)
        log_row.addWidget(self._log_path, 1)
        log_row.addWidget(browse_btn)
        game_form.addRow(_lbl("Client.txt path:"), log_row)

        # Quick-fill preset buttons for PoE1 / PoE2 default paths
        preset_row = QHBoxLayout()
        poe1_btn = QPushButton("PoE 1 path")
        poe1_btn.setFixedWidth(80)
        poe1_btn.setToolTip(_LOG_PATHS["poe1"][0])
        poe1_btn.clicked.connect(lambda: self._log_path.setText(_LOG_PATHS["poe1"][0]))
        poe2_btn = QPushButton("PoE 2 path")
        poe2_btn.setFixedWidth(80)
        poe2_btn.setToolTip(_LOG_PATHS["poe2"][0])
        poe2_btn.clicked.connect(lambda: self._log_path.setText(_LOG_PATHS["poe2"][0]))
        preset_row.addWidget(poe1_btn)
        preset_row.addWidget(poe2_btn)
        preset_row.addStretch()
        game_form.addRow(_lbl("Path preset:"), preset_row)

        self._league = QLineEdit(self._config.get("league", ""))
        self._league.setStyleSheet(_field_style())
        self._league.setPlaceholderText("e.g. Standard")
        game_form.addRow(_lbl("League:"), self._league)

        # New Character reset button (only shown when state is available)
        if self._state is not None:
            new_char_btn = QPushButton("New Character")
            new_char_btn.setToolTip(
                "Resets quest tracker and XP session for a fresh character.\n"
                "Currency history, crafting queue, and notes are kept."
            )
            new_char_btn.clicked.connect(self._new_character)
            new_char_row = QHBoxLayout()
            new_char_row.addWidget(new_char_btn)
            new_char_row.addStretch()
            game_form.addRow(_lbl("Character:"), new_char_row)

        layout.addWidget(game_group)

        # ── Overlay settings ───────────────────────────────────────────
        overlay_group = QGroupBox("Overlay")
        overlay_group.setStyleSheet(f"QGroupBox {{ color: {ACCENT}; font-weight: bold; font-size: 11px; }}")
        overlay_form = QFormLayout(overlay_group)
        overlay_form.setSpacing(6)
        overlay_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._opacity = QDoubleSpinBox()
        self._opacity.setRange(0.10, 1.0)
        self._opacity.setSingleStep(0.05)
        self._opacity.setDecimals(2)
        self._opacity.setValue(self._config.get("overlay_opacity", 0.92))
        self._opacity.setStyleSheet(_field_style())
        self._opacity.setToolTip("Overlay transparency (0.10 = nearly invisible, 1.0 = fully opaque).\nApplied immediately when you save.")
        overlay_form.addRow(_lbl("Opacity:"), self._opacity)

        self._auto_scan = QSpinBox()
        self._auto_scan.setRange(0, 120)
        self._auto_scan.setSingleStep(5)
        self._auto_scan.setValue(self._config.get("auto_scan_minutes", 0))
        self._auto_scan.setStyleSheet(_field_style())
        self._auto_scan.setToolTip(
            "Auto-scan interval for Div Card and Chaos Recipe panels (minutes).\n"
            "0 = disabled. Scans fire automatically when your PoE account is connected.\n"
            "Requires restart to take effect."
        )
        overlay_form.addRow(_lbl("Auto-scan (min):"), self._auto_scan)

        layout.addWidget(overlay_group)

        # ── Hotkeys ────────────────────────────────────────────────────
        hk_group = QGroupBox("Hotkeys")
        hk_group.setStyleSheet(f"QGroupBox {{ color: {ACCENT}; font-weight: bold; font-size: 11px; }}")
        hk_form = QFormLayout(hk_group)
        hk_form.setSpacing(6)
        hk_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        hotkeys = self._config.get("hotkeys", {})
        self._hk_inputs: dict[str, QLineEdit] = {}
        for key, label in _HOTKEY_LABELS.items():
            inp = QLineEdit(hotkeys.get(key, ""))
            inp.setStyleSheet(_field_style())
            inp.setPlaceholderText("e.g. ctrl+shift+p")
            self._hk_inputs[key] = inp
            hk_form.addRow(_lbl(f"{label}:"), inp)

        hint = QLabel("Hotkeys use the format: ctrl+shift+h, ctrl+c, f5, etc.\nChanges take effect on next restart.")
        hint.setStyleSheet(f"color: {DIM}; font-size: 10px;")
        hint.setWordWrap(True)
        hk_form.addRow(hint)

        layout.addWidget(hk_group)
        layout.addStretch()

        # ── Save row ───────────────────────────────────────────────────
        save_sep = QFrame()
        save_sep.setFrameShape(QFrame.Shape.HLine)
        save_sep.setStyleSheet("color: #2a2a4a;")
        outer.addWidget(save_sep)

        save_row = QHBoxLayout()
        save_row.setContentsMargins(8, 6, 8, 6)
        self._status = QLabel("")
        self._status.setStyleSheet(f"color: {DIM}; font-size: 11px;")
        self._status.setWordWrap(True)
        save_row.addWidget(self._status, 1)

        save_btn = QPushButton("Save Settings")
        save_btn.setStyleSheet(
            f"QPushButton {{ background: {ACCENT}; color: #1a1a2e; font-weight: bold; padding: 5px 14px; }}"
            f"QPushButton:hover {{ background: #c8a84b; }}"
        )
        save_btn.clicked.connect(self._save)
        save_row.addWidget(save_btn)

        outer.addLayout(save_row)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _new_character(self):
        reply = QMessageBox.question(
            self,
            "New Character",
            "Reset quest tracker and XP session for a new character?\n\n"
            "This will clear:\n"
            "  • All completed quests\n"
            "  • Passive / ascendancy point counts\n"
            "  • Current XP tracking session\n\n"
            "Currency history, crafting queue, and notes will be kept.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._state.reset_character()
            self._status.setStyleSheet(f"color: {GREEN}; font-size: 11px;")
            self._status.setText("Character reset. Quest tracker and XP session cleared.")

    def _browse_log(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Client.txt",
            self._log_path.text() or "C:/",
            "Text files (*.txt);;All files (*)",
        )
        if path:
            self._log_path.setText(path)

    def _save(self):
        hotkeys = {
            k: inp.text().strip()
            for k, inp in self._hk_inputs.items()
            if inp.text().strip()
        }
        updates = {
            "client_log_path":  self._log_path.text().strip(),
            "league":           self._league.text().strip(),
            "overlay_opacity":  self._opacity.value(),
            "auto_scan_minutes": self._auto_scan.value(),
            "hotkeys":          hotkeys,
        }
        try:
            cfg.save(updates)
            # Apply opacity immediately (no restart needed for this one setting)
            if self._on_opacity_change:
                self._on_opacity_change(self._opacity.value())
            self._status.setStyleSheet(f"color: {GREEN}; font-size: 11px;")
            self._status.setText("Saved. Restart PoELens to apply hotkey and path changes.")
        except Exception as e:
            self._status.setStyleSheet(f"color: {RED}; font-size: 11px;")
            self._status.setText(f"Error: {e}")


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _lbl(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(f"color: {TEXT}; font-size: 11px;")
    return lbl


def _field_style() -> str:
    return (
        "background: #0f0f23; color: #d4c5a9; border: 1px solid #2a2a4a;"
        " border-radius: 3px; padding: 3px;"
    )
