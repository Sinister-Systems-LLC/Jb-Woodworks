# Sinister Term :: app.py
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
#
# v0 main loop. prompt_toolkit-based shell with Sinister theme + slash
# commands + history. Falls through to the underlying shell on non-slash
# input.

from __future__ import annotations

import json
import os
import platform
import subprocess
import time
from pathlib import Path

try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.formatted_text import FormattedText
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
    from prompt_toolkit.key_binding import KeyBindings
except ImportError as e:
    raise ImportError(
        "Sinister Term requires prompt_toolkit. Install with: pip install -e ."
    ) from e

from rich.console import Console

from term.commands import dispatch, load_projects, SANCTUM_ROOT
from term.completer import SinisterCompleter
from term.theme import SINISTER_STYLE, BANNER


HIST_DIR = SANCTUM_ROOT / "_shared-memory" / "sinister-term-history"
HEARTBEAT = SANCTUM_ROOT / "_shared-memory" / "heartbeats" / "sinister-term.json"


def _detect_project_for_cwd() -> str | None:
    cwd = Path.cwd().resolve()
    for p in load_projects():
        root = p.get("root")
        if not root:
            continue
        try:
            if cwd.is_relative_to(Path(root).resolve()):
                return p.get("display") or p.get("key")
        except Exception:
            continue
    return None


def _prompt_text() -> FormattedText:
    cwd = Path.cwd()
    short_cwd = str(cwd)
    if len(short_cwd) > 40:
        short_cwd = "..." + short_cwd[-37:]
    project = _detect_project_for_cwd()
    parts = [("class:prompt.glyph", "◈ ")]
    if project:
        parts.append(("class:prompt.project", f"[{project}] "))
    parts.append(("class:prompt.path", short_cwd))
    parts.append(("class:prompt.dollar", "\n$ "))
    return FormattedText(parts)


def _bottom_toolbar() -> FormattedText:
    project = _detect_project_for_cwd() or "no-project"
    return FormattedText([
        ("class:bottom-toolbar.section", " SINISTER TERM "),
        ("class:bottom-toolbar", "  "),
        ("class:bottom-toolbar.ok", project),
        ("class:bottom-toolbar", "    /help for commands  ·  /exit to quit"),
    ])


def _write_heartbeat() -> None:
    try:
        HEARTBEAT.parent.mkdir(parents=True, exist_ok=True)
        HEARTBEAT.write_text(json.dumps({
            "agent": "sinister-term",
            "ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "alive": True,
            "cwd": str(Path.cwd()),
        }, indent=2), encoding="utf-8")
    except Exception:
        pass


def _run_shell_command(line: str, console: Console) -> None:
    """Fall-through: run the line in the underlying shell."""
    if platform.system() == "Windows":
        cmd = ["powershell.exe", "-NoProfile", "-Command", line]
    else:
        cmd = ["/bin/sh", "-c", line]
    try:
        subprocess.run(cmd, check=False)
    except Exception as e:
        console.print(f"[red]shell exec failed: {e}[/red]")


def run() -> None:
    console = Console()
    console.print(BANNER)

    HIST_DIR.mkdir(parents=True, exist_ok=True)
    hist_path = HIST_DIR / "history.jsonl"
    history = FileHistory(str(hist_path))

    kb = KeyBindings()

    @kb.add("c-l")
    def _(event):
        event.app.renderer.clear()

    session: PromptSession[str] = PromptSession(
        history=history,
        auto_suggest=AutoSuggestFromHistory(),
        completer=SinisterCompleter(),
        complete_while_typing=True,
        bottom_toolbar=_bottom_toolbar,
        style=SINISTER_STYLE,
        key_bindings=kb,
        mouse_support=False,
    )

    _write_heartbeat()

    while True:
        try:
            line = session.prompt(_prompt_text())
        except KeyboardInterrupt:
            console.print("[dim](^C — type /exit to quit)[/dim]")
            continue
        except EOFError:
            break

        line = line.strip()
        if not line:
            continue

        _write_heartbeat()

        result = dispatch(line)
        if result.handled:
            if result.output:
                console.print(result.output)
            if result.exit_term:
                break
            continue

        _run_shell_command(line, console)

    console.print("[dim]◈ Sinister Term exited.[/dim]")


if __name__ == "__main__":
    run()
