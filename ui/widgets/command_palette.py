"""
Command palette — Spotlight-style overlay for quick access to all PoELens features.
Shows when triggered by hotkey. Hides on Escape or after action.

Commands:
  craft [item]    — crafting queue / next step
  price [item]    — price check
  farm [activity] — farm guide for activity
  build [class]   — meta build for class
  zone            — current zone info
  next            — next recommended action
  trade           — profitable trade suggestions
  help            — show all commands
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QScrollArea, QFrame,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QFont

ACCENT = "#e2b96f"
TEXT   = "#d4c5a9"
DIM    = "#8a7a65"
GREEN  = "#5cba6e"
TEAL   = "#4ae8c8"
BG_DARK = QColor(8, 8, 20, 230)
BG_ITEM = QColor(20, 20, 40, 180)

_COMMANDS = {
    "craft":  ("Crafting guide / next step", "craft [item type]"),
    "price":  ("Price check an item",        "price [item name]"),
    "farm":   ("Farming guide",              "farm [breach|delirium|expedition|harvest|...]"),
    "build":  ("Meta build preview",         "build [marauder|witch|ranger|...]"),
    "zone":   ("Current zone info",          "zone"),
    "next":   ("Recommended next action",    "next"),
    "trade":  ("Profitable trade routes",    "trade"),
    "help":   ("Show all commands",          "help"),
}


class CommandPalette(QWidget):
    """
    Floating centered command palette.
    Emits command_selected(command: str, args: str) when Enter is pressed.
    """
    command_selected = pyqtSignal(str, str)   # (command, args)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(480)
        self._build_ui()
        self.hide()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Search input
        self._input = QLineEdit()
        self._input.setPlaceholderText("Type a command — craft, farm, build, price, zone, next…")
        self._input.setStyleSheet(
            "QLineEdit {"
            "  background: rgba(14, 14, 32, 230);"
            "  color: #e2b96f;"
            "  border: 1px solid #2a2a4a;"
            "  border-bottom: none;"
            "  border-radius: 8px 8px 0 0;"
            "  padding: 10px 14px;"
            "  font-size: 13px;"
            "  font-family: 'Segoe UI';"
            "}"
        )
        self._input.textChanged.connect(self._on_text)
        self._input.returnPressed.connect(self._on_enter)
        layout.addWidget(self._input)

        # Results area
        self._results_frame = QWidget()
        self._results_frame.setStyleSheet(
            "background: rgba(8, 8, 20, 220);"
            "border: 1px solid #2a2a4a;"
            "border-top: none;"
            "border-radius: 0 0 8px 8px;"
        )
        self._results_layout = QVBoxLayout(self._results_frame)
        self._results_layout.setContentsMargins(8, 6, 8, 8)
        self._results_layout.setSpacing(2)
        layout.addWidget(self._results_frame)

        # Populate with default help
        self._show_default()

    def _show_default(self):
        self._clear_results()
        for cmd, (desc, usage) in _COMMANDS.items():
            row = self._make_row(cmd, desc, usage)
            self._results_layout.addWidget(row)
        self.adjustSize()

    def _clear_results(self):
        while self._results_layout.count():
            item = self._results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _make_row(self, cmd: str, desc: str, usage: str, highlight: bool = False) -> QWidget:
        row = QWidget()
        row.setStyleSheet(
            f"background: {'rgba(40,40,80,180)' if highlight else 'transparent'};"
            f"border-radius: 4px;"
        )
        rl = QHBoxLayout(row)
        rl.setContentsMargins(6, 3, 6, 3)

        cmd_lbl = QLabel(cmd)
        cmd_lbl.setFixedWidth(60)
        cmd_lbl.setStyleSheet(f"color: {ACCENT}; font-weight: bold; font-size: 11px; background: transparent;")
        rl.addWidget(cmd_lbl)

        desc_lbl = QLabel(desc)
        desc_lbl.setStyleSheet(f"color: {TEXT}; font-size: 11px; background: transparent;")
        rl.addWidget(desc_lbl, 1)

        usage_lbl = QLabel(usage)
        usage_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px; background: transparent;")
        rl.addWidget(usage_lbl)

        return row

    def _make_result_row(self, title: str, body: str, color: str = TEXT) -> QWidget:
        row = QWidget()
        row.setStyleSheet("background: rgba(20,20,50,160); border-radius: 4px;")
        rl = QVBoxLayout(row)
        rl.setContentsMargins(8, 4, 8, 4)
        rl.setSpacing(1)

        t_lbl = QLabel(title)
        t_lbl.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 11px; background: transparent;")
        rl.addWidget(t_lbl)

        if body:
            b_lbl = QLabel(body)
            b_lbl.setWordWrap(True)
            b_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px; background: transparent;")
            rl.addWidget(b_lbl)

        return row

    def _on_text(self, text: str):
        text = text.strip().lower()
        if not text:
            self._show_default()
            return

        parts = text.split(None, 1)
        cmd = parts[0]
        args = parts[1] if len(parts) > 1 else ""

        self._clear_results()

        # Filter commands matching the typed prefix
        matches = [(c, d, u) for c, (d, u) in _COMMANDS.items() if c.startswith(cmd)]
        for c, d, u in matches:
            self._results_layout.addWidget(
                self._make_row(c, d, u, highlight=(c == cmd))
            )

        if not matches:
            no_match = QLabel(f'No command matching "{cmd}" — try: {", ".join(_COMMANDS)}')
            no_match.setStyleSheet(f"color: {DIM}; font-size: 10px; padding: 4px;")
            self._results_layout.addWidget(no_match)

        self.adjustSize()
        self._reposition()

    def _on_enter(self):
        text = self._input.text().strip()
        if not text:
            return
        parts = text.split(None, 1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        self.command_selected.emit(cmd, args)
        self._input.clear()
        self.hide()

    def toggle(self):
        if self.isVisible():
            self.hide()
            self._input.clear()
            self._show_default()
        else:
            self._show_default()
            self._reposition()
            self.show()
            self.raise_()
            self._input.setFocus()

    def _reposition(self):
        screen = self.screen()
        if screen:
            sg = screen.geometry()
            self.move(
                sg.center().x() - self.width() // 2,
                sg.height() // 3
            )

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
            self._input.clear()
            self._show_default()
        else:
            super().keyPressEvent(event)

    def paintEvent(self, event):
        # The child widgets handle their own backgrounds; the outer container is transparent
        pass
