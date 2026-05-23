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

from term.commands import dispatch, SANCTUM_ROOT
from term.completer import SinisterCompleter
from term.keybindings import build_keybindings
from term.status import (
    detect_project_for_cwd,
    freshest_sibling_heartbeat,
    git_branch,
    pending_inbox_count,
    short_cwd_relative_to_project,
)
from term.theme import SINISTER_STYLE, BANNER


HIST_DIR = SANCTUM_ROOT / "_shared-memory" / "sinister-term-history"
HEARTBEAT = SANCTUM_ROOT / "_shared-memory" / "heartbeats" / "sinister-term.json"


def _prompt_text() -> FormattedText:
    """Multi-segment breadcrumb prompt: ◈ [project] git:branch  cwd-relative\n$ """
    project = detect_project_for_cwd()
    branch = git_branch()
    cwd_disp = short_cwd_relative_to_project()

    parts: list[tuple[str, str]] = [("class:prompt.glyph", "◈ ")]
    if project:
        parts.append(("class:prompt.project", f"[{project}] "))
    if branch:
        parts.append(("class:prompt.git", f"git:{branch} "))
    parts.append(("class:prompt.path", cwd_disp))
    parts.append(("class:prompt.dollar", "\n$ "))
    return FormattedText(parts)


def _bottom_toolbar() -> FormattedText:
    project = detect_project_for_cwd() or "no-project"
    branch = git_branch() or "no-git"
    hb = freshest_sibling_heartbeat()
    inbox = pending_inbox_count()

    parts: list[tuple[str, str]] = [
        ("class:bottom-toolbar.section", " SINISTER TERM "),
        ("class:bottom-toolbar", "  "),
        ("class:bottom-toolbar.ok", project),
        ("class:bottom-toolbar", "  "),
        ("class:bottom-toolbar.git", f"git:{branch}"),
    ]

    if hb:
        agent, age_min = hb
        hb_class = "class:bottom-toolbar.ok" if age_min < 30 else "class:bottom-toolbar.warn"
        parts.extend([
            ("class:bottom-toolbar", "  ● "),
            (hb_class, f"{agent} ({age_min}m)"),
        ])

    if inbox > 0:
        parts.extend([
            ("class:bottom-toolbar", "  "),
            ("class:bottom-toolbar.warn", f"inbox:{inbox}"),
        ])

    parts.append(("class:bottom-toolbar", "    /help · /exit"))
    return FormattedText(parts)


def _set_window_title() -> None:
    """RKOJ-ELENO :: 2026-05-23 — emit OSC-0 so host terminal title shows
    we're inside sterm. Mintty/Windows-Terminal/iTerm all honor this; no-op
    on terminals that don't (the bytes get silently swallowed)."""
    try:
        project = detect_project_for_cwd() or ""
        cwd_disp = short_cwd_relative_to_project() or str(Path.cwd())
        title = f"Sinister Term — {project + ' :: ' if project else ''}{cwd_disp}"
        # OSC 0 ; <title> BEL
        import sys as _sys
        _sys.stdout.write(f"\033]0;{title}\007")
        _sys.stdout.flush()
    except Exception:
        pass


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
    # RKOJ-ELENO :: 2026-05-23 — handle bare `cd <dir>` in-process so the
    # cwd actually persists for the next command (subprocess cd would be a
    # no-op once the shell exits). Mirrors bash/cmd muscle-memory.
    stripped = line.strip()
    if stripped == "cd" or stripped.startswith("cd "):
        target = stripped[2:].strip() or str(Path.home())
        # strip surrounding quotes a user might paste
        if len(target) >= 2 and target[0] == target[-1] and target[0] in ('"', "'"):
            target = target[1:-1]
        target = os.path.expandvars(os.path.expanduser(target))
        try:
            os.chdir(target)
        except Exception as e:
            console.print(f"[red]cd: {e}[/red]")
        return

    # RKOJ-ELENO :: 2026-05-23 — accept bare `exit`/`quit` muscle-memory
    # (also handled at caller via SystemExit-style return; we just route to
    # PowerShell which would no-op, so short-circuit here).
    if stripped in ("exit", "quit", "logout"):
        raise EOFError  # caller's loop treats EOFError as clean exit

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

    kb = build_keybindings()

    session: PromptSession[str] = PromptSession(
        history=history,
        auto_suggest=AutoSuggestFromHistory(),
        completer=SinisterCompleter(),
        complete_while_typing=True,
        bottom_toolbar=_bottom_toolbar,
        style=SINISTER_STYLE,
        key_bindings=kb,
        mouse_support=False,
        refresh_interval=2.0,  # let toolbar live-refresh heartbeat age
    )

    _write_heartbeat()
    _set_window_title()

    while True:
        _set_window_title()  # refresh on every prompt so cd changes show
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
