"""
Heist Blueprint Organizer panel.

Scans stash tabs via OAuth to show Heist Contracts grouped by rogue job type
and Blueprints with wing unlock status.

Requires OAuth (account:stashes scope). Scan is user-triggered.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QScrollArea, QTabWidget,
)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot

from modules.heist_planner import ROGUE_JOBS

ACCENT = "#e2b96f"
TEXT   = "#d4c5a9"
DIM    = "#8a7a65"
GREEN  = "#5cba6e"
RED    = "#e05050"
TEAL   = "#4ae8c8"


class HeistPanel(QWidget):
    _scan_done = pyqtSignal(bool, str)   # (success, error_msg)
    _updated   = pyqtSignal(object)      # result dict from HeistPlanner

    def __init__(self, heist_planner, oauth_manager=None, stash_api=None, league="Standard"):
        super().__init__()
        self._planner  = heist_planner
        self._oauth    = oauth_manager
        self._stash_api = stash_api
        self._league   = league
        self._build_ui()

        self._scan_done.connect(self._on_scan_done)
        self._updated.connect(self._on_update)
        heist_planner.on_update(lambda result: self._updated.emit(result))

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
                "Heist tracking requires a PoE OAuth connection.\n"
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

        # Sub-tabs: Contracts / Blueprints
        self._sub_tabs = QTabWidget()
        self._sub_tabs.setStyleSheet(
            "QTabBar::tab { padding: 4px 10px; font-size: 11px; }"
        )

        # Contracts tab
        self._contracts_widget = QWidget()
        contracts_layout = QVBoxLayout(self._contracts_widget)
        contracts_layout.setContentsMargins(0, 4, 0, 0)
        contracts_layout.setSpacing(4)
        self._contracts_scroll = _make_scroll_area()
        self._contracts_container = self._contracts_scroll.widget()
        self._contracts_layout   = self._contracts_container.layout()
        contracts_layout.addWidget(self._contracts_scroll)

        # Blueprints tab
        self._blueprints_widget = QWidget()
        blueprints_layout = QVBoxLayout(self._blueprints_widget)
        blueprints_layout.setContentsMargins(0, 4, 0, 0)
        blueprints_layout.setSpacing(4)
        self._blueprints_scroll = _make_scroll_area()
        self._blueprints_container = self._blueprints_scroll.widget()
        self._blueprints_layout    = self._blueprints_container.layout()
        blueprints_layout.addWidget(self._blueprints_scroll)

        self._sub_tabs.addTab(self._contracts_widget,  "Contracts")
        self._sub_tabs.addTab(self._blueprints_widget, "Blueprints")
        layout.addWidget(self._sub_tabs)

        note = QLabel("Scan reads all stash tabs · 1s per tab · large stashes may take a moment")
        note.setStyleSheet(f"color: {DIM}; font-size: 10px;")
        note.setWordWrap(True)
        layout.addWidget(note)

        # Scan button
        self._scan_btn = QPushButton("Scan Stash for Heist Items")
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
        self._planner.scan(
            self._league,
            on_done=lambda ok, err: self._scan_done.emit(ok, err),
        )

    @pyqtSlot(bool, str)
    def _on_scan_done(self, ok: bool, err: str):
        self._scan_btn.setEnabled(True)
        self._scan_btn.setText("Scan Stash for Heist Items")
        if not ok:
            self._status.setStyleSheet(f"color: {RED}; font-size: 10px;")
            self._status.setText(f"Error: {err}")

    @pyqtSlot(object)
    def _on_update(self, result: dict):
        self._refresh_auth_ui()

        total_c = result.get("total_contracts", 0)
        total_b = result.get("total_blueprints", 0)
        self._summary_label.setText(
            f"{total_c} contract(s)  •  {total_b} blueprint(s)"
        )

        self._render_contracts(result.get("contracts_by_job", {}))
        self._render_blueprints(result.get("blueprints", []))

        self._status.setStyleSheet(f"color: {GREEN}; font-size: 10px;")
        self._status.setText("Scan complete.")

    def _render_contracts(self, contracts_by_job: dict):
        _clear_layout(self._contracts_layout)

        if not contracts_by_job:
            empty = QLabel("No contracts found in stash.")
            empty.setStyleSheet(f"color: {DIM}; font-size: 11px;")
            self._contracts_layout.insertWidget(0, empty)
            return

        insert_idx = 0
        # Render in canonical job order; Unknown at the end
        ordered_jobs = [j for j in ROGUE_JOBS if j in contracts_by_job]
        if "Unknown" in contracts_by_job:
            ordered_jobs.append("Unknown")

        for job in ordered_jobs:
            items = contracts_by_job[job]
            hdr = QLabel(f"{job}  ({len(items)})")
            hdr.setStyleSheet(f"color: {TEAL}; font-size: 10px; font-weight: bold;")
            self._contracts_layout.insertWidget(insert_idx, hdr)
            insert_idx += 1

            for contract in items:
                row = _make_contract_row(contract)
                self._contracts_layout.insertWidget(insert_idx, row)
                insert_idx += 1

    def _render_blueprints(self, blueprints: list):
        _clear_layout(self._blueprints_layout)

        if not blueprints:
            empty = QLabel("No blueprints found in stash.")
            empty.setStyleSheet(f"color: {DIM}; font-size: 11px;")
            self._blueprints_layout.insertWidget(0, empty)
            return

        for idx, bp in enumerate(blueprints):
            row = _make_blueprint_row(bp)
            self._blueprints_layout.insertWidget(idx, row)

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


# ------------------------------------------------------------------
# Row builders (module-level for clarity)
# ------------------------------------------------------------------

def _make_contract_row(contract: dict) -> QWidget:
    row = QWidget()
    row.setStyleSheet("background: #0f0f23; border-radius: 3px;")
    hl = QHBoxLayout(row)
    hl.setContentsMargins(6, 3, 6, 3)
    hl.setSpacing(8)

    name_lbl = QLabel(contract["name"])
    name_lbl.setStyleSheet(f"color: {TEXT}; font-size: 11px;")
    hl.addWidget(name_lbl, stretch=1)

    job_level = contract.get("job_level", 0)
    if job_level:
        lvl_lbl = QLabel(f"Lv {job_level}")
        lvl_lbl.setStyleSheet(f"color: {TEAL}; font-size: 10px;")
        lvl_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        hl.addWidget(lvl_lbl)

    ilvl_lbl = QLabel(f"ilvl {contract['ilvl']}")
    ilvl_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px;")
    ilvl_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    hl.addWidget(ilvl_lbl)

    return row


def _make_blueprint_row(bp: dict) -> QWidget:
    row = QWidget()
    row.setStyleSheet("background: #0f0f23; border-radius: 3px;")
    vl = QVBoxLayout(row)
    vl.setContentsMargins(6, 4, 6, 4)
    vl.setSpacing(2)

    # Top row: name | ilvl
    hl = QHBoxLayout()
    hl.setContentsMargins(0, 0, 0, 0)
    hl.setSpacing(8)

    name_lbl = QLabel(bp["name"])
    name_lbl.setStyleSheet(f"color: {ACCENT}; font-size: 11px; font-weight: bold;")
    hl.addWidget(name_lbl, stretch=1)

    ilvl_lbl = QLabel(f"ilvl {bp['ilvl']}")
    ilvl_lbl.setStyleSheet(f"color: {DIM}; font-size: 10px;")
    ilvl_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    hl.addWidget(ilvl_lbl)
    vl.addLayout(hl)

    # Details row: job | wings
    details_parts = []
    job = bp.get("job", "")
    if job and job != "Unknown":
        job_level = bp.get("job_level", 0)
        details_parts.append(f"{job} Lv {job_level}" if job_level else job)

    unlocked = bp.get("wings_unlocked", 0)
    total    = bp.get("wings_total", 0)
    if total > 0:
        wing_color = GREEN if unlocked >= total else (TEAL if unlocked > 0 else DIM)
        details_parts.append(f"Wings: {unlocked}/{total}")
    else:
        wing_color = DIM

    if details_parts:
        detail_lbl = QLabel("  •  ".join(details_parts))
        detail_lbl.setStyleSheet(f"color: {wing_color}; font-size: 10px;")
        vl.addWidget(detail_lbl)

    return row


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _make_scroll_area() -> QScrollArea:
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setStyleSheet("QScrollArea { border: none; }")
    container = QWidget()
    layout    = QVBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(3)
    layout.addStretch()
    scroll.setWidget(container)
    return scroll


def _clear_layout(layout):
    """Remove all items from a layout except the trailing stretch."""
    while layout.count() > 1:
        item = layout.takeAt(0)
        if item.widget():
            item.widget().deleteLater()
