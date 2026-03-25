"""
Divination Card Tracker panel.

Scans DivinationStash tabs via OAuth to show card stack completion progress
and poe.ninja value for each card. Sorted by completion % descending.

Requires OAuth (account:stashes scope). Scan is user-triggered.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QScrollArea,
)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot

ACCENT = "#e2b96f"
TEXT   = "#d4c5a9"
DIM    = "#8a7a65"
GREEN  = "#5cba6e"
RED    = "#e05050"
TEAL   = "#4ae8c8"


class DivPanel(QWidget):
    _scan_done = pyqtSignal(bool, str)   # (success, error_msg)
    _updated   = pyqtSignal(object)      # list of card dicts

    def __init__(self, div_tracker, oauth_manager=None, stash_api=None, league="Standard"):
        super().__init__()
        self._tracker   = div_tracker
        self._oauth     = oauth_manager
        self._stash_api = stash_api
        self._league    = league
        self._build_ui()

        self._scan_done.connect(self._on_scan_done)
        self._updated.connect(self._on_update)
        div_tracker.on_update(lambda cards: self._updated.emit(cards))

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # Auth status
        if self._oauth and self._oauth.is_configured:
            self._auth_label = QLabel("")
            self._auth_label.setStyleSheet(f"color: {DIM}; font-size: 11px;")
            layout.addWidget(self._auth_label)
        else:
            no_oauth = QLabel(
                "Divination card tracking requires a PoE OAuth connection.\n"
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

        # Summary row
        self._summary_label = QLabel("No scan yet.")
        self._summary_label.setStyleSheet(f"color: {ACCENT}; font-weight: bold;")
        layout.addWidget(self._summary_label)

        # Scrollable card list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        self._card_container = QWidget()
        self._card_layout    = QVBoxLayout(self._card_container)
        self._card_layout.setContentsMargins(0, 0, 0, 0)
        self._card_layout.setSpacing(3)
        self._card_layout.addStretch()
        scroll.setWidget(self._card_container)
        layout.addWidget(scroll)

        note = QLabel("Sorted by completion % · Only cards in your DivinationStash tab are shown.")
        note.setStyleSheet(f"color: {DIM}; font-size: 10px;")
        note.setWordWrap(True)
        layout.addWidget(note)

        # Scan button
        self._scan_btn = QPushButton("Scan Divination Stash")
        self._scan_btn.setStyleSheet(
            f"QPushButton {{ background: {ACCENT}; color: #1a1a2e; font-weight: bold; padding: 5px 14px; }}"
            f"QPushButton:hover {{ background: #c8a84b; }}"
        )
        self._scan_btn.clicked.connect(self._start_scan)
        layout.addWidget(self._scan_btn)

        self._status = QLabel("")
        self._status.setStyleSheet(f"color: {DIM}; font-size: 10px;")
        layout.addWidget(self._status)

        self._refresh_auth_ui()

    def _start_scan(self):
        self._scan_btn.setEnabled(False)
        self._scan_btn.setText("Scanning…")
        self._status.setText("")
        self._tracker.scan(
            self._league,
            on_done=lambda ok, err: self._scan_done.emit(ok, err),
        )

    @pyqtSlot(bool, str)
    def _on_scan_done(self, ok: bool, err: str):
        self._scan_btn.setEnabled(True)
        self._scan_btn.setText("Scan Divination Stash")
        if not ok:
            self._status.setStyleSheet(f"color: {RED}; font-size: 10px;")
            self._status.setText(f"Error: {err}")

    @pyqtSlot(object)
    def _on_update(self, cards: list):
        self._refresh_auth_ui()

        # Clear existing card rows (except the trailing stretch)
        while self._card_layout.count() > 1:
            item = self._card_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not cards:
            empty = QLabel("No divination cards found in stash.")
            empty.setStyleSheet(f"color: {DIM}; font-size: 11px;")
            self._card_layout.insertWidget(0, empty)
            self._summary_label.setText("0 cards found.")
            self._status.setStyleSheet(f"color: {GREEN}; font-size: 10px;")
            self._status.setText("Scan complete.")
            return

        # Group: near-complete (≥75%), in-progress (<75%), singles (current=1, full>1)
        near     = [c for c in cards if c["pct"] >= 75]
        progress = [c for c in cards if 1 < c["pct"] < 75]
        singles  = [c for c in cards if c["pct"] < 1 and c["current"] == 1]

        insert_idx = 0
        for group_label, group in (("Near Complete (≥75%)", near),
                                   ("In Progress", progress),
                                   ("Singles", singles)):
            if not group:
                continue
            hdr = QLabel(group_label)
            hdr.setStyleSheet(f"color: {TEAL}; font-size: 10px; font-weight: bold;")
            self._card_layout.insertWidget(insert_idx, hdr)
            insert_idx += 1
            for card in group:
                row = self._make_card_row(card)
                self._card_layout.insertWidget(insert_idx, row)
                insert_idx += 1

        total_chaos = sum(c["chaos"] * (c["current"] // max(c["full_stack"], 1)) for c in cards)
        complete    = sum(1 for c in cards if c["current"] >= c["full_stack"])
        self._summary_label.setText(
            f"{len(cards)} card type(s) found  •  {complete} complete set(s)  •  ~{total_chaos:.0f}c total"
        )
        self._status.setStyleSheet(f"color: {GREEN}; font-size: 10px;")
        self._status.setText("Scan complete.")

    def _make_card_row(self, card: dict) -> QWidget:
        row = QWidget()
        row.setStyleSheet("background: #0f0f23; border-radius: 3px;")
        hl = QHBoxLayout(row)
        hl.setContentsMargins(6, 3, 6, 3)
        hl.setSpacing(6)

        name_lbl = QLabel(card["name"])
        name_lbl.setStyleSheet(f"color: {TEXT}; font-size: 11px;")
        hl.addWidget(name_lbl, stretch=1)

        stack_lbl = QLabel(f"{card['current']}/{card['full_stack']}")
        pct = card["pct"]
        color = GREEN if pct >= 100 else (TEAL if pct >= 75 else TEXT)
        stack_lbl.setStyleSheet(f"color: {color}; font-size: 11px;")
        stack_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        hl.addWidget(stack_lbl)

        if card["chaos"] > 0:
            chaos_lbl = QLabel(f"{card['chaos']:.1f}c")
            chaos_lbl.setStyleSheet(f"color: {ACCENT}; font-size: 10px;")
            chaos_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            hl.addWidget(chaos_lbl)

        return row

    def _refresh_auth_ui(self):
        if self._auth_label is None:
            return
        if self._oauth and self._oauth.is_authenticated:
            name = self._oauth.account_name or "account"
            self._auth_label.setText(f"Connected: {name}")
            self._auth_label.setStyleSheet(f"color: {GREEN}; font-size: 11px;")
            self._scan_btn.setEnabled(True)
        else:
            self._auth_label.setText("Not connected — use the Currency tab to connect your PoE account")
            self._auth_label.setStyleSheet(f"color: {DIM}; font-size: 11px;")
            self._scan_btn.setEnabled(False)
