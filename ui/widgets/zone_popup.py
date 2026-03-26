"""
Zone info popup — auto-shows when zone changes, near the PoE minimap.
Fades out after 15 seconds. Dismiss with Escape.
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout
from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtGui import QPainter, QColor

ACCENT = "#e2b96f"
TEXT   = "#d4c5a9"
DIM    = "#8a7a65"
GREEN  = "#5cba6e"
RED    = "#e05050"
TEAL   = "#4ae8c8"
BG     = "rgba(8, 8, 20, 200)"   # CSS for labels — not used for window itself


class ZonePopup(QWidget):
    """
    Transparent floating popup shown when the player enters a new zone.
    Position: top-right corner, y=80 (below PoE's health orb area).
    Auto-fades after `timeout_ms` milliseconds.
    """

    def __init__(self, timeout_ms: int = 15000):
        super().__init__()
        self._timeout_ms = timeout_ms
        self._opacity = 0.88
        self._fade_steps = 20
        self._fade_interval = 60   # ms per step → ~1.2s fade

        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowOpacity(self._opacity)
        self.setFixedWidth(300)

        self._build_ui()
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._start_fade)

        self._fade_timer = QTimer(self)
        self._fade_timer.setInterval(self._fade_interval)
        self._fade_timer.timeout.connect(self._fade_step)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)

        # Zone name header
        self._zone_lbl = QLabel("—")
        self._zone_lbl.setStyleSheet(
            f"color: {ACCENT}; font-size: 14px; font-weight: bold; background: transparent;"
        )
        layout.addWidget(self._zone_lbl)

        # Tier + type row
        self._tier_lbl = QLabel("")
        self._tier_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px; background: transparent;")
        layout.addWidget(self._tier_lbl)

        # Boss
        self._boss_lbl = QLabel("")
        self._boss_lbl.setStyleSheet(f"color: {RED}; font-size: 10px; background: transparent;")
        layout.addWidget(self._boss_lbl)

        # Farm tip
        self._tip_lbl = QLabel("")
        self._tip_lbl.setStyleSheet(f"color: {GREEN}; font-size: 10px; background: transparent;")
        self._tip_lbl.setWordWrap(True)
        layout.addWidget(self._tip_lbl)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(QColor(8, 8, 20, 200))
        p.setPen(QColor(0xe2, 0xb9, 0x6f, 80))
        p.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 6, 6)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self._dismiss()

    def show_zone(self, zone_info: dict):
        """
        Display zone info. zone_info keys:
          name, tier (int or None), type ("map"|"town"|"act"),
          boss (str or None), layout (str), notes (str)
        """
        self._timer.stop()
        self._fade_timer.stop()
        self.setWindowOpacity(self._opacity)

        name  = zone_info.get("name", "Unknown Zone")
        tier  = zone_info.get("tier")
        btype = zone_info.get("type", "zone")
        boss  = zone_info.get("boss")
        notes = zone_info.get("notes", "")

        self._zone_lbl.setText(name)

        tier_txt = f"T{tier} Map" if tier else btype.capitalize()
        lvl = zone_info.get("area_level")
        if lvl:
            tier_txt += f" · Area Lv {lvl}"
        self._tier_lbl.setText(tier_txt)

        self._boss_lbl.setText(f"Boss: {boss}" if boss else "")
        self._boss_lbl.setVisible(bool(boss))
        self._tip_lbl.setText(notes[:120] if notes else "")
        self._tip_lbl.setVisible(bool(notes))

        self.adjustSize()
        self._reposition()
        self.show()
        self.raise_()
        self._timer.start(self._timeout_ms)

    def _reposition(self):
        """Place near PoE minimap — top-right corner, below y=70."""
        screen = self.screen()
        if screen:
            sg = screen.geometry()
            self.move(sg.right() - self.width() - 16, 80)

    def _start_fade(self):
        self._current_opacity = self._opacity
        self._fade_timer.start()

    def _fade_step(self):
        self._current_opacity -= self._opacity / self._fade_steps
        if self._current_opacity <= 0.0:
            self._dismiss()
        else:
            self.setWindowOpacity(max(0.0, self._current_opacity))

    def _dismiss(self):
        self._fade_timer.stop()
        self._timer.stop()
        self.hide()
        self.setWindowOpacity(self._opacity)
