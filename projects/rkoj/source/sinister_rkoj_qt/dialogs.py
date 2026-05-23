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


def _humanize_age(saved_at: str) -> str:
    """Return a compact "N min ago" / "N hr ago" / "N day ago" label for
    an ISO8601 saved_at string. Falls back to the raw string if parsing
    fails so the operator can still see what's there.
    """
    if not saved_at:
        return "(no timestamp)"
    try:
        from datetime import datetime, timezone as _tz
        s = saved_at.rstrip("Z").replace(" ", "T")
        # Strip microseconds + timezone — accept either YYYY-MM-DDTHH:MM:SS
        # or YYYY-MM-DDTHH:MM:SS.ffffff[+TZ].
        for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S",
                    "%Y-%m-%dT%H:%M"):
            try:
                dt = datetime.strptime(s[:26], fmt)
                break
            except ValueError:
                continue
        else:
            return saved_at[:19].replace("T", " ")
        dt = dt.replace(tzinfo=_tz.utc)
        delta = datetime.now(_tz.utc) - dt
        secs = int(delta.total_seconds())
        if secs < 60:
            return f"{secs}s ago"
        mins = secs // 60
        if mins < 60:
            return f"{mins} min ago"
        hrs = mins // 60
        if hrs < 24:
            return f"{hrs} hr ago"
        days = hrs // 24
        if days < 30:
            return f"{days} day{'s' if days != 1 else ''} ago"
        return saved_at[:10]  # YYYY-MM-DD fallback for old saves
    except Exception:
        return saved_at[:19].replace("T", " ")


class SavedSessionsPicker(QDialog):
    """List saved resume-points and let operator pick one to resume.

    Scans `_shared-memory/resume-points/EVE on <project>/*.json` written by
    the agent's `/save` slash command (or by AgentWindow.closeEvent
    autoclose path). Each entry shows the project, turn count, when it was
    saved, save reason chip (autoclose / manual), mode, and short
    session_uuid. Double-click or Resume button accepts. Delete button
    (or Del key) removes the selected saved session from disk.

    v1.6.9 — picker UX overhaul:
      - Wording fixed: "Open in new window" → "Resume inline" (v1.6.8
        reverted floating-window flow so the picker UI was lying).
      - "Delete selected" button + `Del` key shortcut for housekeeping.
      - `save_reason` surfaced as a chip on each row.
      - Tighter row labels (relative time + mode chip + short uuid).

    Result on accept (`result_data` attribute):
      dict with keys: project_key, project_display, agent_name, mode,
                      session_uuid, saved_at, turns, save_reason
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("NewAgentDialog")  # reuse the dialog styling
        self.setModal(True)
        self.setWindowTitle("Resume Saved Session")
        self.setMinimumWidth(640)
        self.setMinimumHeight(500)
        self.setStyleSheet(_DIALOG_QSS)
        self.result_data: Optional[dict] = None
        self._sessions = self._scan_sessions()
        self._build()
        QShortcut(QKeySequence("Escape"), self, activated=self.reject)
        QShortcut(QKeySequence("Delete"), self, activated=self._on_delete)

    def _scan_sessions(self) -> list[dict]:
        """v1.6.87 — combined list: every project from projects.json
        (the Sinister Start.bat fleet roster) + every saved resume-point.
        Each entry is either kind='project' (start fresh) or
        kind='saved' (resume existing session). Sorted: projects with
        saves first (most-recent-save first), then projects with no
        saves alphabetically. Within a project the saved sessions
        appear newest-first."""
        # 1. Load saved sessions
        saved: list[dict] = []
        rp_root = state.SHARED_MEMORY / "resume-points"
        if rp_root.exists():
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
                            continue
                        saved.append({
                            "kind": "saved",
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
                            "save_reason": data.get("save_reason", "manual"),
                            "_fp": str(fp),
                        })
            except Exception:
                pass
        # 2. Load all projects from projects.json (Sinister Start.bat roster)
        projects: list[dict] = []
        try:
            for p in state.load_projects():
                projects.append({
                    "kind": "project",
                    "project_key": p.key,
                    "project_display": p.display,
                    "mode": "claude",
                    "saved_count": 0,
                    "newest_save_ts": "",
                })
        except Exception:
            pass
        # 3. Annotate each project with its saved-count + newest-save ts
        by_key: dict[str, dict] = {p["project_key"]: p for p in projects}
        for s in saved:
            pk = s["project_key"]
            if pk in by_key:
                by_key[pk]["saved_count"] += 1
                ts = s.get("saved_at", "")
                if ts > by_key[pk]["newest_save_ts"]:
                    by_key[pk]["newest_save_ts"] = ts
        # 4. Merge: each project header followed by its saves
        projects.sort(key=lambda p: (
            p["newest_save_ts"] == "",   # projects with saves first
            -1 if p["newest_save_ts"] else 0,
            p["project_display"].lower(),
        ))
        out: list[dict] = []
        saved_by_key: dict[str, list[dict]] = {}
        for s in saved:
            saved_by_key.setdefault(s["project_key"], []).append(s)
        for proj in projects:
            out.append(proj)
            proj_saves = saved_by_key.get(proj["project_key"], [])
            proj_saves.sort(key=lambda s: s.get("saved_at", ""), reverse=True)
            out.extend(proj_saves)
        return out

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
                "Inside any agent card, type /save to write a resume-point,\n"
                "or just close the card — v1.6.7+ writes an autoclose save\n"
                "to _shared-memory/resume-points/ on the way out."
            )
            empty.setObjectName("DialogSubtitle")
            empty.setWordWrap(True)
            root.addWidget(empty)
        else:
            self.subtitle_label = QLabel()
            self.subtitle_label.setObjectName("DialogSubtitle")
            self.subtitle_label.setWordWrap(True)
            root.addWidget(self.subtitle_label)

            self._list = QListWidget()
            self._list.setObjectName("SavedSessionsList")
            self._populate_list()
            self._list.itemDoubleClicked.connect(self._on_double_click)
            if self._list.count() > 0:
                self._list.setCurrentRow(0)
            root.addWidget(self._list, stretch=1)

            self._refresh_subtitle()

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        if self._sessions:
            self.delete_btn = QPushButton("Delete selected")
            self.delete_btn.setObjectName("DialogSecondary")
            self.delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.delete_btn.setToolTip(
                "Remove the selected saved session from disk (Del key)"
            )
            self.delete_btn.clicked.connect(self._on_delete)
            btn_row.addWidget(self.delete_btn)
        btn_row.addStretch(1)
        cancel = QPushButton("Cancel")
        cancel.setObjectName("DialogSecondary")
        cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel.clicked.connect(self.reject)
        btn_row.addWidget(cancel)
        if self._sessions:
            self.open_btn = QPushButton("Resume inline")
            self.open_btn.setObjectName("DialogPrimary")
            self.open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.open_btn.setDefault(True)
            self.open_btn.setToolTip(
                "Open this saved session as a card inside the Agents tab"
            )
            self.open_btn.clicked.connect(self._on_accept)
            btn_row.addWidget(self.open_btn)
        root.addLayout(btn_row)

    def _populate_list(self) -> None:
        """v1.6.87 — render two kinds:
          kind='project'  ► [+] Project Name        N saved · Start fresh
          kind='saved'    ►    └─ <turns> · <ts> · uuid <8> · [reason]
        """
        self._list.clear()
        for s in self._sessions:
            if s.get("kind") == "project":
                n = s.get("saved_count", 0)
                save_str = (
                    f"{n} saved · click to resume newest" if n
                    else "no saves yet · click to start fresh"
                )
                label = (
                    f"[+] {s['project_display']:30s}    {save_str}"
                )
            else:
                ts = _humanize_age(s.get("saved_at", ""))
                reason = (s.get("save_reason") or "manual").lower()
                reason_chip = (
                    "[autoclose]" if reason == "autoclose" else f"[{reason}]"
                )
                label = (
                    f"    └─ {s['turns']:2d} turn(s) · {ts:10s} · "
                    f"uuid {s['session_uuid'][:8]} {reason_chip}"
                )
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, s)
            self._list.addItem(item)

    def _refresh_subtitle(self) -> None:
        n_proj = sum(1 for s in self._sessions if s.get("kind") == "project")
        n_saved = sum(1 for s in self._sessions if s.get("kind") == "saved")
        self.subtitle_label.setText(
            f"{n_proj} project(s) · {n_saved} saved session(s) — "
            f"click a project to start fresh, or click a saved session "
            f"to resume. Del key removes a save."
        )

    def _on_double_click(self, item: QListWidgetItem) -> None:
        self._accept_item(item)

    def _on_accept(self) -> None:
        if not getattr(self, "_list", None):
            self.reject()
            return
        item = self._list.currentItem()
        if not item:
            self.reject()
            return
        self._accept_item(item)

    def _accept_item(self, item: QListWidgetItem) -> None:
        """v1.6.87 — when project row picked: emit fresh-spawn payload
        (no session_uuid). When saved row picked: emit resume payload."""
        data = item.data(Qt.ItemDataRole.UserRole)
        if data.get("kind") == "project":
            self.result_data = {
                "project_key": data["project_key"],
                "project_display": data["project_display"],
                "agent_name": data["project_display"],
                "mode": data.get("mode", "claude"),
                "session_uuid": None,   # fresh spawn — no resume
            }
        else:
            self.result_data = data
        self.accept()

    def _on_delete(self) -> None:
        """Delete the selected saved session's JSON file from disk +
        refresh the picker. Reversible: file is renamed `_FN.json.deleted`
        (operator can `ren` back if it was a mistake)."""
        if not getattr(self, "_list", None):
            return
        item = self._list.currentItem()
        if not item:
            return
        sess = item.data(Qt.ItemDataRole.UserRole) or {}
        fp = sess.get("_fp")
        if not fp:
            return
        try:
            p = Path(fp)
            if p.exists():
                # Rename-not-delete — easy operator rollback.
                p.rename(p.with_suffix(p.suffix + ".deleted"))
        except Exception:
            # Surface the failure quietly — keep the row so operator can
            # retry; harmless if file is in use briefly.
            return
        # Drop from in-memory list + rebuild rows.
        self._sessions = [s for s in self._sessions if s.get("_fp") != fp]
        self._populate_list()
        self._refresh_subtitle()
        if self._sessions:
            self._list.setCurrentRow(0)
        else:
            # No sessions left — disable Resume to avoid a no-op confirm.
            if hasattr(self, "open_btn"):
                self.open_btn.setEnabled(False)
            if hasattr(self, "delete_btn"):
                self.delete_btn.setEnabled(False)
