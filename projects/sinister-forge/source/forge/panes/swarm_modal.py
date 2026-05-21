# Sinister Forge :: panes/swarm_modal.py
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
#
# PH16 modal for :dm and :broadcast palette actions. Operator picks a
# recipient (DM only) + subject + body; submit writes the inbox JSON via
# forge.swarm helpers.

from __future__ import annotations

from dataclasses import dataclass

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Select, Static, TextArea

from forge.swarm import known_slugs


@dataclass(slots=True)
class SwarmModalResult:
    kind: str  # "dm" or "broadcast"
    to_slug: str  # ignored for broadcast (set to "*" by convention)
    subject: str
    body: str


class SwarmModal(ModalScreen[SwarmModalResult | None]):
    """Pop-up for :dm and :broadcast.

    For :dm the recipient Select is shown. For :broadcast it's hidden
    and the result.to_slug is "*".
    """

    BINDINGS = [
        Binding("escape", "dismiss(None)", "Close", show=False),
    ]

    DEFAULT_CSS = """
    SwarmModal {
        align: center middle;
        background: rgba(7, 7, 11, 0.85);
    }
    #swarm-card {
        width: 84;
        max-width: 92%;
        height: auto;
        background: $surface;
        border: round $primary;
        padding: 1 2;
    }
    #swarm-title {
        color: $primary-lighten-2;
        text-style: bold;
        padding: 0 0 1 0;
    }
    .swarm-row {
        height: auto;
        margin: 0 0 1 0;
    }
    .swarm-label {
        color: $primary-lighten-2;
        text-style: bold;
        width: 12;
    }
    .swarm-input {
        height: 3;
        width: 1fr;
    }
    #swarm-body {
        height: 8;
        width: 1fr;
    }
    #swarm-buttons {
        height: 3;
        align-horizontal: right;
        padding-top: 1;
    }
    #swarm-buttons Button {
        margin-left: 1;
    }
    """

    def __init__(self, *, kind: str) -> None:
        super().__init__()
        if kind not in ("dm", "broadcast"):
            raise ValueError(f"SwarmModal kind must be dm|broadcast, got {kind!r}")
        self.kind = kind
        # Build the options once - Select doesn't accept generators
        self._options = [(s, s) for s in known_slugs()]

    def compose(self) -> ComposeResult:
        with Vertical(id="swarm-card"):
            title = "◈ DIRECT MESSAGE" if self.kind == "dm" else "◈ BROADCAST"
            yield Static(title, id="swarm-title")
            if self.kind == "dm":
                with Horizontal(classes="swarm-row"):
                    yield Static("To", classes="swarm-label")
                    initial = self._options[0][1] if self._options else None
                    self._to: Select[str] = Select(
                        options=self._options,
                        id="swarm-to",
                        classes="swarm-input",
                        value=initial,
                        allow_blank=False,
                    )
                    yield self._to
            else:
                self._to = None  # type: ignore[assignment]
            with Horizontal(classes="swarm-row"):
                yield Static("Subject", classes="swarm-label")
                self._subject = Input(
                    placeholder="one-liner subject",
                    id="swarm-subject",
                    classes="swarm-input",
                )
                yield self._subject
            with Horizontal(classes="swarm-row"):
                yield Static("Body", classes="swarm-label")
                self._body = TextArea(text="", id="swarm-body")
                yield self._body
            with Horizontal(id="swarm-buttons"):
                yield Button("Cancel", id="swarm-cancel")
                send_label = "Send DM" if self.kind == "dm" else "Send Broadcast"
                yield Button(send_label, id="swarm-send", variant="primary")

    def on_mount(self) -> None:
        self._subject.focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "swarm-cancel":
            self.dismiss(None)
            return
        if event.button.id == "swarm-send":
            subj = (self._subject.value or "").strip() or "(no subject)"
            body = (self._body.text or "").strip()
            if self.kind == "dm":
                to_slug = str(self._to.value) if self._to and self._to.value else ""
                if not to_slug:
                    return
            else:
                to_slug = "*"
            self.dismiss(SwarmModalResult(
                kind=self.kind,
                to_slug=to_slug,
                subject=subj,
                body=body,
            ))
