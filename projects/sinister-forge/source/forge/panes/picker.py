# Sinister Forge :: panes/picker.py
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later

from __future__ import annotations
from dataclasses import dataclass

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Select, Static

from forge.projects import load_projects
from forge.theme import AGENT_ACCENTS


OBJECTIVES = [
    ("resume", "Resume", "Continue exactly where last session left off"),
    ("coaudit", "Coaudit", "CO-AUDIT a running project"),
    ("dev", "Dev", "Active development / coding"),
    ("audit", "Audit", "Review state / push-readiness"),
    ("expand", "Expand", "EXPAND 7-step contract"),
    ("smoketest", "SmokeTest", "Loop API endpoints + auto-fix"),
    ("securityaudit", "SecAudit", "Loop security surface + auto-fix"),
    ("forge", "Forge", "Sinister Forge harness work"),
]

TOKEN_MODES = [
    ("compact", "Compact  (saves ~3000 tokens)"),
    ("full", "Full  (inline all contracts)"),
]

SPEEDS = [
    ("max", "Max  (6-10 parallel)"),
    ("turbo", "Turbo  (3-5 parallel, default)"),
    ("fast", "Fast  (2 parallel)"),
    ("normal", "Normal  (sequential)"),
]

HOSTS = [
    ("claude", "Claude  (default)"),
    ("codex", "Codex  (needs OPENAI_API_KEY)"),
]


@dataclass
class PickerResult:
    project_key: str
    objective: str
    token_mode: str
    speed: str
    host: str
    agent_name: str
    accent: str
    focus: str


class AgentPicker(ModalScreen[PickerResult | None]):
    BINDINGS = [Binding("escape", "dismiss(None)", "Cancel")]

    CSS = """
    AgentPicker { align: center middle; }
    AgentPicker > Vertical { background: #15131A; border: round #A06EFF; width: 80; height: auto; padding: 1 2; }
    AgentPicker Label { color: #E8D6FF; text-style: bold; margin-top: 1; }
    AgentPicker Select, AgentPicker Input { width: 100%; margin-bottom: 1; }
    AgentPicker .picker-actions { align-horizontal: right; margin-top: 1; }
    """

    def compose(self) -> ComposeResult:
        projects = load_projects()
        project_options = [(p.display, p.key) for p in projects] or [("Sanctum", "sanctum")]
        default_project = projects[0].key if projects else "sanctum"

        with Vertical():
            yield Static("[b]NEW AGENT[/]  ::  fill the picks + Submit", markup=True)
            yield Label("Project")
            yield Select(project_options, id="picker-project", value=default_project, allow_blank=False)
            yield Label("Objective")
            yield Select(
                [(f"{label}  -  {desc[:40]}", key) for key, label, desc in OBJECTIVES],
                id="picker-objective", value="resume", allow_blank=False,
            )
            yield Label("Token Mode")
            yield Select([(label, key) for key, label in TOKEN_MODES],
                         id="picker-tokmode", value="compact", allow_blank=False)
            yield Label("Speed")
            yield Select([(label, key) for key, label in SPEEDS],
                         id="picker-speed", value="turbo", allow_blank=False)
            yield Label("Agent Host")
            yield Select([(label, key) for key, label in HOSTS],
                         id="picker-host", value="claude", allow_blank=False)
            yield Label("Agent Name")
            yield Input(value=default_project, id="picker-name")
            yield Label("Accent")
            yield Select([(name, name) for name in AGENT_ACCENTS],
                         id="picker-accent", value="purple", allow_blank=False)
            yield Label("Focus (optional)")
            yield Input(value="", id="picker-focus")
            with Horizontal(classes="picker-actions"):
                yield Button("Cancel", id="picker-cancel")
                yield Button("Submit", id="picker-submit", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "picker-cancel":
            self.dismiss(None)
        elif event.button.id == "picker-submit":
            self.dismiss(self._collect())

    def _val(self, sid: str) -> str:
        try:
            v = self.query_one(f"#{sid}").value
            return "" if v is None else str(v)
        except Exception:
            return ""

    def _collect(self) -> PickerResult:
        return PickerResult(
            project_key=self._val("picker-project"),
            objective=self._val("picker-objective"),
            token_mode=self._val("picker-tokmode"),
            speed=self._val("picker-speed"),
            host=self._val("picker-host"),
            agent_name=self._val("picker-name") or self._val("picker-project"),
            accent=self._val("picker-accent") or "purple",
            focus=self._val("picker-focus"),
        )
