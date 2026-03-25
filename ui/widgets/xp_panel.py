"""
XP Rate Tracker panel.

Polls the GGG Character API to track XP/hr for the current session.
Requires OAuth connection with account:characters scope.
Polling: every 5 minutes via QTimer, plus on zone_change events (via XPTracker).
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
)
from PyQt6.QtCore import QTimer, pyqtSignal, pyqtSlot

ACCENT = "#e2b96f"
TEXT   = "#d4c5a9"
DIM    = "#8a7a65"
GREEN  = "#5cba6e"
RED    = "#e05050"

_AUTO_POLL_INTERVAL_MS = 5 * 60 * 1000   # 5 minutes


def _fmt_duration(minutes: float) -> str:
    """Format a duration in minutes as a human-readable string (e.g. '2h 15m', '45m')."""
    if minutes >= 60:
        hours = int(minutes // 60)
        mins  = int(minutes % 60)
        return f"{hours}h {mins}m" if mins else f"{hours}h"
    return f"{int(minutes)}m"


def _fmt_xp(xp: int) -> str:
    """Format an XP value with M/K suffix for readability."""
    if xp >= 1_000_000_000:
        return f"{xp / 1_000_000_000:.3f}B"
    if xp >= 1_000_000:
        return f"{xp / 1_000_000:.2f}M"
    if xp >= 1_000:
        return f"{xp / 1_000:.1f}K"
    return str(xp)


class XPPanel(QWidget):
    # Signals for thread-safe UI updates from background thread callbacks
    _started = pyqtSignal(bool, str)   # (success, char_name_or_error_msg)
    _updated = pyqtSignal(object)      # dict from XPTracker.get_display_data()

    def __init__(self, xp_tracker, oauth_manager=None, league="Standard"):
        super().__init__()
        self._tracker = xp_tracker
        self._oauth   = oauth_manager
        self._league  = league
        self._build_ui()

        self._started.connect(self._on_started)
        self._updated.connect(self._on_update)
        xp_tracker.on_update(lambda d: self._updated.emit(d))

        # Periodic auto-poll (fires only when a session is active)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._auto_poll)
        self._timer.start(_AUTO_POLL_INTERVAL_MS)

        # Populate display from persisted state (if a session was running before restart)
        self._on_update(xp_tracker.get_display_data())

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # OAuth status row
        if self._oauth and self._oauth.is_configured:
            self._auth_label = QLabel("")
            self._auth_label.setStyleSheet(f"color: {DIM}; font-size: 11px;")
            layout.addWidget(self._auth_label)
        else:
            no_oauth = QLabel(
                "XP tracking requires a PoE OAuth connection.\n"
                "Set oauth_client_id in the Settings tab to enable."
            )
            no_oauth.setStyleSheet(f"color: {DIM}; font-size: 11px;")
            no_oauth.setWordWrap(True)
            layout.addWidget(no_oauth)
            self._auth_label = None

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #2a2a4a;")
        layout.addWidget(sep)

        # Character and level display
        self._char_label = QLabel("")
        self._char_label.setStyleSheet(f"color: {ACCENT}; font-weight: bold; font-size: 13px;")
        layout.addWidget(self._char_label)

        self._level_label = QLabel("")
        self._level_label.setStyleSheet(f"color: {TEXT}; font-size: 12px;")
        layout.addWidget(self._level_label)

        # XP rate display
        self._rate_label = QLabel("Start a session to track XP/hr.")
        self._rate_label.setStyleSheet(f"color: {ACCENT}; font-weight: bold;")
        self._rate_label.setWordWrap(True)
        layout.addWidget(self._rate_label)

        self._elapsed_label = QLabel("")
        self._elapsed_label.setStyleSheet(f"color: {DIM}; font-size: 11px;")
        layout.addWidget(self._elapsed_label)

        layout.addStretch()

        # Buttons
        btn_row = QHBoxLayout()
        self._start_btn = QPushButton("Start Tracking")
        self._start_btn.clicked.connect(self._start_session)

        self._poll_btn = QPushButton("Refresh XP")
        self._poll_btn.clicked.connect(self._manual_poll)
        self._poll_btn.setEnabled(False)

        btn_row.addWidget(self._start_btn)
        btn_row.addWidget(self._poll_btn)
        layout.addLayout(btn_row)

        self._status = QLabel("")
        self._status.setStyleSheet(f"color: {DIM}; font-size: 10px;")
        layout.addWidget(self._status)

        self._refresh_auth_ui()

    # ------------------------------------------------------------------
    # Session controls
    # ------------------------------------------------------------------

    def _start_session(self):
        self._start_btn.setEnabled(False)
        self._start_btn.setText("Fetching...")
        self._status.setText("")
        self._tracker.start_session(
            self._league,
            on_started=lambda ok, msg: self._started.emit(ok, msg),
        )

    @pyqtSlot(bool, str)
    def _on_started(self, ok: bool, msg: str):
        self._start_btn.setText("Start Tracking")
        self._start_btn.setEnabled(True)
        if ok:
            self._poll_btn.setEnabled(True)
            self._status.setStyleSheet(f"color: {GREEN}; font-size: 10px;")
            self._status.setText(f"Tracking: {msg}")
        else:
            self._status.setStyleSheet(f"color: {RED}; font-size: 10px;")
            self._status.setText(f"Error: {msg}")

    def _manual_poll(self):
        self._poll_btn.setEnabled(False)
        self._poll_btn.setText("Polling...")
        # Re-enable button after 3s (poll result fires _updated which also updates display)
        QTimer.singleShot(3000, lambda: (
            self._poll_btn.setEnabled(True),
            self._poll_btn.setText("Refresh XP"),
        ))
        self._tracker.poll()

    def _auto_poll(self):
        """Fires every 5 minutes; only polls if a session is active and OAuth is connected."""
        if self._tracker.get_display_data().get("started") and self._is_authenticated():
            self._tracker.poll()

    # ------------------------------------------------------------------
    # Display update
    # ------------------------------------------------------------------

    @pyqtSlot(object)
    def _on_update(self, data: dict):
        self._refresh_auth_ui()
        if not data.get("started"):
            self._char_label.setText("")
            self._level_label.setText("")
            self._elapsed_label.setText("")
            return

        char           = data.get("char_name", "")
        level          = data.get("level", 0)
        base_level     = data.get("baseline_level", 0)
        xp_gained      = data.get("xp_this_session", 0)
        xp_hr          = data.get("xp_per_hr", 0)
        elapsed        = data.get("elapsed_minutes", 0)
        time_to_level  = data.get("time_to_level")   # minutes or None

        self._char_label.setText(char)
        if level != base_level and base_level > 0:
            self._level_label.setText(f"Level {base_level} → {level}  (leveled up!)")
            self._level_label.setStyleSheet(f"color: {GREEN}; font-size: 12px;")
        else:
            self._level_label.setText(f"Level {level}")
            self._level_label.setStyleSheet(f"color: {TEXT}; font-size: 12px;")

        if xp_hr > 0:
            self._rate_label.setText(
                f"{_fmt_xp(xp_hr)} XP/hr  •  {_fmt_xp(xp_gained)} gained this session"
            )
        elif xp_gained > 0:
            self._rate_label.setText(f"{_fmt_xp(xp_gained)} XP gained this session")
        else:
            self._rate_label.setText("Session active — click Refresh XP to update")

        if time_to_level is not None and level < 100:
            ttl_str = _fmt_duration(time_to_level)
            self._elapsed_label.setText(f"{elapsed:.0f} min elapsed  •  ~{ttl_str} to level {level + 1}")
        else:
            self._elapsed_label.setText(f"{elapsed:.0f} min elapsed")
        self._poll_btn.setEnabled(True)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _is_authenticated(self) -> bool:
        return bool(self._oauth and self._oauth.is_authenticated)

    def _refresh_auth_ui(self):
        if self._auth_label is None:
            return
        if self._is_authenticated():
            name = self._oauth.account_name or "account"
            self._auth_label.setText(f"Connected: {name}")
            self._auth_label.setStyleSheet(f"color: {GREEN}; font-size: 11px;")
            self._start_btn.setEnabled(True)
        else:
            self._auth_label.setText("Not connected — use the Currency tab to connect your PoE account")
            self._auth_label.setStyleSheet(f"color: {DIM}; font-size: 11px;")
            self._start_btn.setEnabled(False)
            self._poll_btn.setEnabled(False)
