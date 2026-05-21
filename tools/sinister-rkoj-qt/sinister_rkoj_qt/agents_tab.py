# Author: RKOJ-ELENO :: 2026-05-21
"""Agents tab — niri-style vertical scroll of EVE agent cards.

Each card embeds a jcode-form terminal (QPlainTextEdit + QLineEdit + QProcess
streaming claude subprocess output). EVE persona injected verbatim from
persona.py on first send.
"""

from __future__ import annotations

import shutil
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from PyQt6.QtCore import QProcess, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QTextCursor
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit, QPushButton,
    QScrollArea, QSizePolicy, QSpacerItem, QVBoxLayout, QWidget,
)

from . import state
from .persona import build_opening_prompt, eve_label


@dataclass
class AgentSession:
    pane_id: str
    project_key: str
    project_display: str
    agent_name: str
    mode: str = "claude"
    accent: str = "purple"
    status: str = "idle"
    turns: list[dict] = field(default_factory=list)
    created_at: str = ""


def _find_claude_executable() -> Optional[str]:
    """Locate the `claude` CLI on PATH. Returns None if not installed."""
    return shutil.which("claude")


class ClaudeRunner(QFrame):
    """Single agent card with embedded terminal + input line + QProcess."""

    closed = pyqtSignal(str)  # pane_id

    def __init__(self, session: AgentSession, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.session = session
        self.setObjectName("AgentCard")
        self.setMinimumHeight(360)
        self._proc: Optional[QProcess] = None
        self._first_turn = True
        self._build()

    # ── UI ─────────────────────────────────────────────────────────
    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(8)

        # Header strip
        hdr = QHBoxLayout()
        hdr.setSpacing(10)

        title = QLabel(eve_label(self.session.agent_name, self.session.project_key))
        title.setObjectName("AgentTitle")
        meta = QLabel(f"· {self.session.mode}")
        meta.setObjectName("AgentMeta")
        self.status_dot = QLabel("●")
        self.status_dot.setObjectName("StatusDot")
        self.status_dot.setProperty("state", "offline")
        self.status_dot.style().polish(self.status_dot)

        close_btn = QPushButton("×")
        close_btn.setObjectName("WinCtl")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self._on_close)

        hdr.addWidget(self.status_dot)
        hdr.addWidget(title)
        hdr.addWidget(meta)
        hdr.addStretch(1)
        hdr.addWidget(close_btn)
        root.addLayout(hdr)

        # Terminal
        self.terminal = QPlainTextEdit()
        self.terminal.setObjectName("Terminal")
        self.terminal.setReadOnly(True)
        font = QFont("Cascadia Mono", 10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.terminal.setFont(font)
        self.terminal.setMinimumHeight(240)
        root.addWidget(self.terminal, stretch=1)

        # Input row
        input_row = QHBoxLayout()
        input_row.setSpacing(8)
        self.input = QLineEdit()
        self.input.setObjectName("TerminalInput")
        self.input.setPlaceholderText(f"Talk to {eve_label(self.session.agent_name, self.session.project_key)} — Enter to send, /help for commands")
        self.input.returnPressed.connect(self._on_send)
        send_btn = QPushButton("Send")
        send_btn.setObjectName("PrimaryBtn")
        send_btn.clicked.connect(self._on_send)
        input_row.addWidget(self.input, stretch=1)
        input_row.addWidget(send_btn)
        root.addLayout(input_row)

        # Seed banner
        self._append_terminal(
            f"╔══ EVE on {self.session.project_display} ══╗\n"
            f"  pane_id: {self.session.pane_id}\n"
            f"  mode: {self.session.mode}   accent: {self.session.accent}\n"
            f"  created: {self.session.created_at}\n"
            f"  Type a message to begin. /help for slash commands.\n"
            f"╚══════════════════════════╝\n"
        )

    def _append_terminal(self, text: str) -> None:
        self.terminal.moveCursor(QTextCursor.MoveOperation.End)
        self.terminal.insertPlainText(text)
        self.terminal.moveCursor(QTextCursor.MoveOperation.End)

    def _set_status(self, state_str: str) -> None:
        self.session.status = state_str
        self.status_dot.setProperty("state", state_str)
        self.status_dot.style().unpolish(self.status_dot)
        self.status_dot.style().polish(self.status_dot)

    # ── Slash-command intercept ────────────────────────────────────
    def _maybe_intercept(self, text: str) -> bool:
        cmd = text.strip()
        if not cmd.startswith("/"):
            return False
        head = cmd.split(None, 1)[0].lower()
        if head == "/help":
            self._append_terminal(
                "[/help]\n"
                "  /help     show this list\n"
                "  /clear    clear terminal\n"
                "  /save     write resume-point to disk\n"
                "  /resume   reload last resume-point\n"
                "  /create   create a new agent (sibling card)\n"
                "  all other slashes forward to the claude subprocess.\n"
            )
            return True
        if head == "/clear":
            self.terminal.clear()
            self._append_terminal("[cleared]\n")
            return True
        if head == "/save":
            from pathlib import Path
            import json
            from .state import SHARED_MEMORY
            resume_dir = SHARED_MEMORY / "rkoj-qt" / "resume-points"
            resume_dir.mkdir(parents=True, exist_ok=True)
            fp = resume_dir / f"{self.session.pane_id}.json"
            payload = {
                "pane_id": self.session.pane_id,
                "project_key": self.session.project_key,
                "agent_name": self.session.agent_name,
                "mode": self.session.mode,
                "turns": self.session.turns,
                "saved_at": datetime.now(timezone.utc).isoformat(),
            }
            try:
                with open(fp, "w", encoding="utf-8") as fh:
                    json.dump(payload, fh, indent=2)
                self._append_terminal(f"[/save] wrote {fp}\n")
            except Exception as exc:
                self._append_terminal(f"[/save] failed: {exc}\n")
            return True
        if head == "/resume":
            self._append_terminal("[/resume] no resume-point loaded yet (stub).\n")
            return True
        if head == "/create":
            self._append_terminal("[/create] click '+ Spawn Agent' in the tab footer.\n")
            return True
        # forward to claude (return False so _on_send sends it through)
        return False

    # ── Send / process I/O ─────────────────────────────────────────
    def _on_send(self) -> None:
        text = self.input.text().strip()
        if not text:
            return
        if self._maybe_intercept(text):
            self.input.clear()
            return

        self._append_terminal(f"\n>> {text}\n")
        self.input.clear()

        # Build prompt with opening + turns + new
        if self._first_turn:
            opening = build_opening_prompt(
                project_key=self.session.project_key,
                agent_name=self.session.agent_name,
                mode=self.session.mode,
                accent=self.session.accent,
            )
            prompt = opening + "\n\nOperator says: " + text
            self._first_turn = False
        else:
            history = "\n".join(
                f"User: {t['user']}\nEVE: {t.get('assistant', '')}" for t in self.session.turns
            )
            prompt = history + f"\nUser: {text}\nEVE:"

        self.session.turns.append({"user": text, "assistant": ""})

        # Find claude
        claude = _find_claude_executable()
        if not claude:
            self._append_terminal("[error] claude CLI not on PATH. Install Claude Code first.\n")
            self._set_status("offline")
            return

        # Spawn QProcess
        if self._proc is not None and self._proc.state() != QProcess.ProcessState.NotRunning:
            self._append_terminal("[busy] previous turn still running; waiting...\n")
            return

        proc = QProcess(self)
        proc.setProgram(claude)
        proc.setArguments(["--dangerously-skip-permissions", "-p", prompt])
        proc.readyReadStandardOutput.connect(self._on_stdout)
        proc.readyReadStandardError.connect(self._on_stderr)
        proc.finished.connect(self._on_finished)
        proc.errorOccurred.connect(self._on_error)
        self._proc = proc
        self._set_status("busy")
        try:
            proc.start()
        except Exception as exc:
            self._append_terminal(f"[error] failed to start claude: {exc}\n")
            self._set_status("offline")

    def _on_stdout(self) -> None:
        if not self._proc:
            return
        data = bytes(self._proc.readAllStandardOutput()).decode("utf-8", errors="replace")
        self._append_terminal(data)
        if self.session.turns:
            self.session.turns[-1]["assistant"] += data

    def _on_stderr(self) -> None:
        if not self._proc:
            return
        data = bytes(self._proc.readAllStandardError()).decode("utf-8", errors="replace")
        self._append_terminal(data)

    def _on_finished(self, exit_code: int, exit_status: QProcess.ExitStatus) -> None:
        self._append_terminal(f"\n[exit {exit_code}]\n")
        self._set_status("online")
        self._proc = None

    def _on_error(self, err: QProcess.ProcessError) -> None:
        self._append_terminal(f"\n[process error: {err}]\n")
        self._set_status("offline")

    def _on_close(self) -> None:
        if self._proc is not None and self._proc.state() != QProcess.ProcessState.NotRunning:
            self._proc.kill()
            self._proc.waitForFinished(2000)
        self.closed.emit(self.session.pane_id)

    def shutdown(self) -> None:
        """Called from main window closeEvent — kill child cleanly."""
        if self._proc is not None and self._proc.state() != QProcess.ProcessState.NotRunning:
            self._proc.kill()
            self._proc.waitForFinished(1500)


class AgentsTab(QWidget):
    """Niri-scroll grid of EVE agent cards + project sub-tabs filter + spawn fab."""

    spawn_requested = pyqtSignal(str)  # project_key

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._cards: dict[str, ClaudeRunner] = {}
        self._project_filter: Optional[str] = None
        self._project_chips: dict[str, QPushButton] = {}
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 8, 20, 12)
        root.setSpacing(10)

        # Project sub-tab strip
        chips_scroll = QScrollArea(self)
        chips_scroll.setWidgetResizable(True)
        chips_scroll.setFrameShape(QFrame.Shape.NoFrame)
        chips_scroll.setFixedHeight(40)
        chips_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        chips_host = QWidget()
        chips_layout = QHBoxLayout(chips_host)
        chips_layout.setContentsMargins(0, 0, 0, 0)
        chips_layout.setSpacing(6)
        all_btn = QPushButton("All")
        all_btn.setObjectName("ProjectChip")
        all_btn.setProperty("active", True)
        all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        all_btn.clicked.connect(lambda: self._set_project_filter(None))
        self._project_chips["__all__"] = all_btn
        chips_layout.addWidget(all_btn)
        for proj in state.load_projects():
            chip = QPushButton(proj.display)
            chip.setObjectName("ProjectChip")
            chip.setProperty("active", False)
            chip.setCursor(Qt.CursorShape.PointingHandCursor)
            chip.clicked.connect(lambda _checked=False, k=proj.key: self._set_project_filter(k))
            self._project_chips[proj.key] = chip
            chips_layout.addWidget(chip)
        chips_layout.addStretch(1)
        chips_scroll.setWidget(chips_host)
        root.addWidget(chips_scroll)

        # Scrollable card list
        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.host = QWidget()
        self.host_layout = QVBoxLayout(self.host)
        self.host_layout.setContentsMargins(0, 0, 0, 0)
        self.host_layout.setSpacing(10)
        self.host_layout.addStretch(1)
        self.scroll.setWidget(self.host)
        root.addWidget(self.scroll, stretch=1)

        # FAB
        fab_row = QHBoxLayout()
        fab_row.addStretch(1)
        fab = QPushButton("+ Spawn Agent")
        fab.setObjectName("PrimaryBtn")
        fab.setCursor(Qt.CursorShape.PointingHandCursor)
        fab.clicked.connect(self._on_spawn_clicked)
        fab_row.addWidget(fab)
        root.addLayout(fab_row)

    def _set_project_filter(self, key: Optional[str]) -> None:
        self._project_filter = key
        for k, btn in self._project_chips.items():
            active = (k == "__all__" and key is None) or (k == key)
            btn.setProperty("active", active)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self._apply_filter()

    def _apply_filter(self) -> None:
        for pid, card in self._cards.items():
            if self._project_filter is None or card.session.project_key == self._project_filter:
                card.setVisible(True)
            else:
                card.setVisible(False)

    def _on_spawn_clicked(self) -> None:
        key = self._project_filter or "sanctum"
        self.spawn_agent(project_key=key)

    def spawn_agent(self, project_key: str, agent_name: str | None = None, mode: str = "claude") -> str:
        """Add a new card and return its pane_id."""
        projects = {p.key: p for p in state.load_projects()}
        proj = projects.get(project_key)
        display = proj.display if proj else project_key
        sess = AgentSession(
            pane_id=uuid.uuid4().hex[:12],
            project_key=project_key,
            project_display=display,
            agent_name=agent_name or display,
            mode=mode,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        card = ClaudeRunner(sess, parent=self.host)
        card.closed.connect(self._remove_card)
        # insert above the stretch
        self.host_layout.insertWidget(self.host_layout.count() - 1, card)
        self._cards[sess.pane_id] = card
        self._apply_filter()
        return sess.pane_id

    def _remove_card(self, pane_id: str) -> None:
        card = self._cards.pop(pane_id, None)
        if card:
            card.setParent(None)
            card.deleteLater()

    def shutdown_all(self) -> None:
        for card in list(self._cards.values()):
            card.shutdown()
