# Author: RKOJ-ELENO :: 2026-05-21
"""Modal dialogs — Panel-styled QDialog popups.

NewAgentDialog: project picker + agent name + mode picker → returns dict
on accept, None on cancel. Wired to header's `+ Create Agent` button.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QFormLayout, QFrame,
    QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QPushButton, QVBoxLayout, QWidget,
)

from . import state
from .theme import (
    BORDER, ELEVATED, FG, MUTED_FG, PANEL_BG, PURPLE_HALO, PURPLE_PRIMARY,
)


_DIALOG_QSS = f"""
QDialog#NewAgentDialog {{
    background-color: {PANEL_BG};
    border: 1px solid {BORDER};
    border-radius: 14px;
}}
QLabel#DialogTitle {{
    color: {PURPLE_PRIMARY};
    font-size: 18px;
    font-weight: 700;
    background: transparent;
}}
QLabel#DialogSubtitle {{
    color: {MUTED_FG};
    font-size: 12px;
    background: transparent;
}}
QLabel#FieldLabel {{
    color: {MUTED_FG};
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1px;
    background: transparent;
}}
QComboBox#DialogCombo, QLineEdit#DialogInput {{
    background-color: {ELEVATED};
    color: {FG};
    border: 1px solid {BORDER};
    border-radius: 7px;
    padding: 7px 10px;
    font-size: 13px;
    min-height: 22px;
}}
QComboBox#DialogCombo:hover, QLineEdit#DialogInput:hover {{
    border-color: {PURPLE_PRIMARY};
}}
QComboBox#DialogCombo:focus, QLineEdit#DialogInput:focus {{
    border-color: {PURPLE_PRIMARY};
}}
QComboBox#DialogCombo::drop-down {{
    border: none;
    width: 28px;
}}
QComboBox#DialogCombo QAbstractItemView {{
    background-color: {ELEVATED};
    color: {FG};
    border: 1px solid {BORDER};
    selection-background-color: rgba(191,90,242,56);
    selection-color: white;
}}
QPushButton#DialogPrimary {{
    background-color: {PURPLE_PRIMARY};
    color: white;
    border: none;
    border-radius: 7px;
    padding: 8px 18px;
    font-size: 12px;
    font-weight: 600;
    min-height: 30px;
}}
QPushButton#DialogPrimary:hover {{
    background-color: {PURPLE_HALO};
}}
QPushButton#DialogSecondary {{
    background-color: transparent;
    color: {MUTED_FG};
    border: 1px solid {BORDER};
    border-radius: 7px;
    padding: 8px 18px;
    font-size: 12px;
    font-weight: 500;
    min-height: 30px;
}}
QPushButton#DialogSecondary:hover {{
    color: {FG};
    border-color: {PURPLE_PRIMARY};
}}
QListWidget#SavedSessionsList {{
    background-color: {ELEVATED};
    color: {FG};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 4px;
    font-size: 12px;
    outline: none;
}}
QListWidget#SavedSessionsList::item {{
    background-color: transparent;
    color: {FG};
    border-radius: 6px;
    padding: 9px 10px;
}}
QListWidget#SavedSessionsList::item:hover {{
    background-color: rgba(191,90,242,30);
}}
QListWidget#SavedSessionsList::item:selected {{
    background-color: rgba(191,90,242,71);
    color: white;
}}
"""


class NewAgentDialog(QDialog):
    """Project + name + mode picker for a new EVE agent.

    Result on accept (`result_dict` attribute):
      {"project_key": str, "agent_name": str, "mode": str}
    """

    # Mode picker — claude (default model), claude-haiku (fast), claude-opus
    # (deep). All three pass through `claude -p`; only the --model alias
    # differs. "anthropic-sdk" is still Phase-2 (needs API key + SDK path).
    _MODES: list[tuple[str, str, bool]] = [
        ("claude",        "claude  (default Claude Code model)",            True),
        ("claude-haiku",  "claude --model haiku  (fast)",                   True),
        ("claude-opus",   "claude --model opus  (deep, slower)",            True),
        ("anthropic-sdk", "Anthropic SDK direct  (Phase-2, needs API key)", False),
    ]

    def __init__(self, parent: QWidget | None = None,
                 default_project_key: str = "sanctum") -> None:
        super().__init__(parent)
        self.setObjectName("NewAgentDialog")
        self.setModal(True)
        self.setWindowTitle("New Agent")
        self.setMinimumWidth(440)
        self.setStyleSheet(_DIALOG_QSS)
        self.result_dict: Optional[dict] = None
        self._build(default_project_key)
        # Esc closes; Enter accepts.
        QShortcut(QKeySequence("Escape"), self, activated=self.reject)

    def _build(self, default_project_key: str) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(22, 20, 22, 20)
        root.setSpacing(14)

        # ── Title block ────────────────────────────────────────────────
        title = QLabel("Spawn new EVE agent")
        title.setObjectName("DialogTitle")
        root.addWidget(title)
        subtitle = QLabel(
            "Pick the project context. Each agent gets its own card, "
            "session UUID, heartbeat, and PROGRESS file."
        )
        subtitle.setObjectName("DialogSubtitle")
        subtitle.setWordWrap(True)
        root.addWidget(subtitle)

        # ── Form ──────────────────────────────────────────────────────
        form_frame = QFrame()
        form = QFormLayout(form_frame)
        form.setContentsMargins(0, 6, 0, 6)
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        # Project picker — populated from projects.json.
        proj_label = QLabel("PROJECT")
        proj_label.setObjectName("FieldLabel")
        self.project_combo = QComboBox()
        self.project_combo.setObjectName("DialogCombo")
        projects = state.load_projects()
        if not projects:
            # Fallback when projects.json is missing — at least let the
            # operator spawn into sanctum.
            projects = [state.Project(key="sanctum", display="Sanctum",
                                      tag="", root="")]
        default_index = 0
        for i, p in enumerate(projects):
            label = f"{p.display}   ·   {p.tag[:60]}" if p.tag else p.display
            self.project_combo.addItem(label, userData=p.key)
            if p.key == default_project_key:
                default_index = i
        self.project_combo.setCurrentIndex(default_index)
        self.project_combo.currentIndexChanged.connect(self._on_project_changed)
        form.addRow(proj_label, self.project_combo)

        # Agent name — defaults to project display.
        name_label = QLabel("AGENT NAME")
        name_label.setObjectName("FieldLabel")
        self.name_input = QLineEdit()
        self.name_input.setObjectName("DialogInput")
        self.name_input.setPlaceholderText(
            "leave blank to use project display name"
        )
        form.addRow(name_label, self.name_input)

        # Mode picker.
        mode_label = QLabel("MODE")
        mode_label.setObjectName("FieldLabel")
        self.mode_combo = QComboBox()
        self.mode_combo.setObjectName("DialogCombo")
        for i, (key, label, enabled) in enumerate(self._MODES):
            self.mode_combo.addItem(label, userData=key)
            if not enabled:
                # Mark disabled-but-visible so operator sees what's coming.
                item = self.mode_combo.model().item(i)
                if item is not None:
                    item.setEnabled(False)
        self.mode_combo.setCurrentIndex(0)
        form.addRow(mode_label, self.mode_combo)

        root.addWidget(form_frame)

        # ── Buttons ────────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        # Resume-saved button on the left so it's visually distinct from
        # the Cancel/Spawn cluster on the right.
        self.resume_btn = QPushButton("Resume saved session…")
        self.resume_btn.setObjectName("DialogSecondary")
        self.resume_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.resume_btn.clicked.connect(self._on_resume_clicked)
        btn_row.addWidget(self.resume_btn)
        btn_row.addStretch(1)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("DialogSecondary")
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(self.cancel_btn)
        self.spawn_btn = QPushButton("Spawn")
        self.spawn_btn.setObjectName("DialogPrimary")
        self.spawn_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.spawn_btn.setDefault(True)
        self.spawn_btn.clicked.connect(self._on_accept)
        btn_row.addWidget(self.spawn_btn)
        root.addLayout(btn_row)

    def _on_resume_clicked(self) -> None:
        """Pop the SavedSessionsPicker. If operator picks one, set our
        result_dict so the caller can open an AgentWindow in resume mode."""
        picker = SavedSessionsPicker(self)
        if picker.exec() == QDialog.DialogCode.Accepted and picker.result_data:
            self.result_dict = {
                "project_key": picker.result_data.get("project_key", "sanctum"),
                "agent_name": picker.result_data.get("agent_name"),
                "mode": picker.result_data.get("mode", "claude"),
                "session_uuid": picker.result_data.get("session_uuid"),
                "resume": True,
            }
            self.accept()

    def _on_project_changed(self, _index: int) -> None:
        # No-op for now — name input is intentionally left as the operator
        # types it. We could auto-fill but that's annoying if they typed
        # already.
        pass

    def _on_accept(self) -> None:
        project_key = self.project_combo.currentData() or "sanctum"
        agent_name = self.name_input.text().strip() or None
        mode = self.mode_combo.currentData() or "claude"
        self.result_dict = {
            "project_key": project_key,
            "agent_name": agent_name,
            "mode": mode,
            "session_uuid": None,
            "resume": False,
        }
        self.accept()


class SavedSessionsPicker(QDialog):
    """List saved resume-points and let operator pick one to resume.

    Scans `_shared-memory/resume-points/EVE on <project>/*.json` written by
    the agent's `/save` slash command. Each entry shows the project, turn
    count, saved timestamp, and short session_uuid. Double-click or Open
    button accepts.

    Result on accept (`result_data` attribute):
      dict with keys: project_key, project_display, agent_name, mode,
                      session_uuid, saved_at, turns
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("NewAgentDialog")  # reuse the dialog styling
        self.setModal(True)
        self.setWindowTitle("Resume Saved Session")
        self.setMinimumWidth(620)
        self.setMinimumHeight(480)
        self.setStyleSheet(_DIALOG_QSS)
        self.result_data: Optional[dict] = None
        self._sessions = self._scan_sessions()
        self._build()
        QShortcut(QKeySequence("Escape"), self, activated=self.reject)

    def _scan_sessions(self) -> list[dict]:
        """Walk `_shared-memory/resume-points/<display>/*.json` and parse
        each into a flat dict. Newest first."""
        sessions: list[dict] = []
        rp_root = state.SHARED_MEMORY / "resume-points"
        if not rp_root.exists():
            return sessions
        try:
            for proj_dir in rp_root.iterdir():
                if not proj_dir.is_dir():
                    continue
                for fp in proj_dir.glob("*.json"):
                    try:
                        with open(fp, "r", encoding="utf-8") as fh:
                            data = json.load(fh)
                    except Exception:
                        continue
                    suid = data.get("session_uuid") or ""
                    if not suid:
                        continue  # pre-v1.6.3 saves without session_uuid
                    sessions.append({
                        "project_display": (
                            data.get("agent_display", "").replace("EVE on ", "")
                            or proj_dir.name.replace("EVE on ", "")
                        ),
                        "project_key": data.get("project_key", "sanctum"),
                        "agent_name": data.get("agent_name", ""),
                        "mode": data.get("mode", "claude"),
                        "session_uuid": suid,
                        "saved_at": data.get("saved_at", ""),
                        "turns": len(data.get("turns", [])),
                        "_fp": str(fp),
                    })
        except Exception:
            pass
        sessions.sort(key=lambda s: s.get("saved_at", ""), reverse=True)
        return sessions

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(22, 20, 22, 20)
        root.setSpacing(14)

        title = QLabel("Resume saved session")
        title.setObjectName("DialogTitle")
        root.addWidget(title)

        if not self._sessions:
            empty = QLabel(
                "No saved sessions found.\n\n"
                "Inside any agent window, type /save to write a resume-point.\n"
                "Saved sessions appear under _shared-memory/resume-points/."
            )
            empty.setObjectName("DialogSubtitle")
            empty.setWordWrap(True)
            root.addWidget(empty)
        else:
            subtitle = QLabel(
                f"{len(self._sessions)} saved session(s)   ·   "
                f"double-click or pick + Open to resume in a new window:"
            )
            subtitle.setObjectName("DialogSubtitle")
            subtitle.setWordWrap(True)
            root.addWidget(subtitle)

            self._list = QListWidget()
            self._list.setObjectName("SavedSessionsList")
            for s in self._sessions:
                ts = (s.get("saved_at") or "")[:19].replace("T", " ")
                label = (
                    f"{s['project_display']}    ·    "
                    f"{s['turns']} turn(s)    ·    {ts or '(no timestamp)'}\n"
                    f"   uuid {s['session_uuid'][:36]}   ·   mode {s.get('mode', 'claude')}"
                )
                item = QListWidgetItem(label)
                item.setData(Qt.ItemDataRole.UserRole, s)
                self._list.addItem(item)
            self._list.itemDoubleClicked.connect(self._on_double_click)
            if self._list.count() > 0:
                self._list.setCurrentRow(0)
            root.addWidget(self._list, stretch=1)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_row.addStretch(1)
        cancel = QPushButton("Cancel")
        cancel.setObjectName("DialogSecondary")
        cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel.clicked.connect(self.reject)
        btn_row.addWidget(cancel)
        if self._sessions:
            self.open_btn = QPushButton("Open in new window")
            self.open_btn.setObjectName("DialogPrimary")
            self.open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.open_btn.setDefault(True)
            self.open_btn.clicked.connect(self._on_accept)
            btn_row.addWidget(self.open_btn)
        root.addLayout(btn_row)

    def _on_double_click(self, item: QListWidgetItem) -> None:
        self.result_data = item.data(Qt.ItemDataRole.UserRole)
        self.accept()

    def _on_accept(self) -> None:
        if not getattr(self, "_list", None):
            self.reject()
            return
        item = self._list.currentItem()
        if not item:
            self.reject()
            return
        self.result_data = item.data(Qt.ItemDataRole.UserRole)
        self.accept()
