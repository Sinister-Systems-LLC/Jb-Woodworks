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

from term.aliases import expand_line, load_aliases
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

# RKOJ-ELENO :: 2026-05-25 :: integration — name pill + jcode popup +
# concise logger + crash recovery. Best-effort imports so older installs
# without the new modules still boot.
try:
    from term.name_pill import default_style as _pill_style, write_pill as _write_pill
    _HAVE_PILL = True
except Exception:
    _HAVE_PILL = False
try:
    from term.jcode_popup import build_snapshot as _popup_snapshot, write_popup as _write_popup
    _HAVE_POPUP = True
except Exception:
    _HAVE_POPUP = False
try:
    from term.concise_log import default as _log_default
    _LOG = _log_default()
except Exception:
    _LOG = None
try:
    from term.crash_recovery import install_atexit_reset as _install_atexit, log_crash as _log_crash
    _install_atexit()
except Exception:
    _log_crash = None

# RKOJ-ELENO :: 2026-05-25 :: paste robustness + double-Ctrl+C tolerance
# (ported from jcode src/tui/app/input.rs + ui_overlays.rs). Best-effort
# imports so older installs still boot.
try:
    from term.paste_handler import (
        PasteBuffer as _PasteBuffer,
        install_paste_handler as _install_paste_handler,
        expand_placeholders as _expand_placeholders,
    )
    _PASTE_BUFFER = _PasteBuffer()
    _HAVE_PASTE = True
except Exception:
    _HAVE_PASTE = False
    _PASTE_BUFFER = None
    _expand_placeholders = lambda line, _buf: line  # noqa: E731

try:
    from term.hardened_input import InputLoopHardener as _Hardener
    _HARDENER = _Hardener()
    _HAVE_HARDENER = True
except Exception:
    _HAVE_HARDENER = False

# RKOJ-ELENO :: 2026-05-25 :: cmux-spec event bus (iter-44). Publish boot /
# dispatch / exit events so future Feed panel + crash replay can consume
# without coupling to app.py internals. Best-effort import — if event_bus
# isn't on the path, the publish_event no-op keeps app.py running.
try:
    from term.event_bus import publish as _publish_event
    _HAVE_EVENT_BUS = True
except Exception:
    _HAVE_EVENT_BUS = False
    def _publish_event(name: str, category: str, payload=None):  # noqa: E501
        return None
    _HARDENER = None


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
        # RKOJ-ELENO :: 2026-05-23 :: OSC-12 purple cursor matches Sanctum theme
        _sys.stdout.write("\033]12;#A06EFF\007")
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


def _emit_pill_and_popup_if_enabled() -> None:
    """Best-effort: render the name pill + jcode popup overlay if enabled.

    Operator feedback 2026-05-25T12:02:58Z: "this looks like shit and its
    super laggy". Overlay is now default-OFF; set SINISTER_TERM_OVERLAY=on
    to opt in. The minimal liquid-glass replacement lives in glass_overlay.py
    and is invoked separately if SINISTER_TERM_GLASS=on.
    """
    if os.environ.get("SINISTER_TERM_OVERLAY", "off").lower() not in ("on", "1", "true"):
        return
    try:
        project = detect_project_for_cwd() or "sinister-term"
        project_key_map = {
            "Sinister Sanctum": "sinister-sanctum",
            "Sinister Term":    "sinister-term",
            "Sinister Forge":   "sinister-forge",
            "Sinister Mind":    "sinister-mind",
            "Sinister Overseer": "sinister-overseer",
            "Sinister Chatbot": "sinister-chatbot",
            "Sinister Vault":   "sinister-vault",
            "Sinister Memory":  "sinister-memory",
            "Sinister Kernel APK": "sinister-kernel-apk",
            "Sinister Panel":   "sinister-panel",
            "Sinister Link":    "sinister-link",
            "Sinister OS":      "sinister-os",
            "Eve EXE":          "eve-exe",
        }
        pk = project_key_map.get(project, project if project.startswith("sinister-") else "sinister-term")
        if _HAVE_PILL:
            _write_pill(_pill_style(pk, mode="resume", loop=True, swarm=True, status="alive"))
        if _HAVE_POPUP:
            br = git_branch() or ""
            _write_popup(_popup_snapshot(
                current_task="active",
                session_name=br or "sterm",
                cwd=str(Path.cwd()),
            ), corner="br", width=38)
    except Exception as e:
        if _log_crash is not None:
            _log_crash("term.app._emit_pill_and_popup", e)


def _confirm_exit(console: Console) -> bool:
    """RKOJ-ELENO :: 2026-05-25 :: extra popup before close.

    Operator hard-canonical 2026-05-25T~14:14Z: *"make the x button have a
    extra popup before just closing"*. Returns True if the operator
    confirms exit; False to stay in the shell.

    Bypass via env: SINISTER_TERM_FAST_EXIT=1 skips the prompt so scripted
    shutdowns + auto-restart watchers don't hang on stdin.

    Robust to TTY-less environments: if stdin isn't a TTY (piped scripts,
    CI), default to confirming exit so the process actually terminates.
    """
    if os.environ.get("SINISTER_TERM_FAST_EXIT", "").lower() in ("1", "true", "on"):
        return True
    try:
        import sys as _sys
        if not _sys.stdin.isatty():
            return True
    except Exception:
        pass
    try:
        console.print(
            "[#A06EFF]┌─ Exit Sinister Term? ─────────────────[/#A06EFF]\n"
            "[#A06EFF]│[/#A06EFF] [#FFFFFF]Press [bold]y[/bold] to exit, "
            "anything else to stay.[/#FFFFFF]\n"
            "[#A06EFF]└────────────────────────────────────────[/#A06EFF]"
        )
        # Use a plain input() — prompt_toolkit's session is in an awkward
        # state at EOF/exit-dispatch, but bare input() always works.
        try:
            ans = input("> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            # If they Ctrl+D again at the confirmation prompt, they really
            # want to leave.
            return True
        return ans in ("y", "yes")
    except Exception:
        # Never block exit on a broken console — fall through to confirm.
        return True


def run() -> None:
    console = Console()
    console.print(BANNER)
    if _LOG is not None:
        try:
            _LOG.info("STERM_BOOT", cwd=str(Path.cwd()))
        except Exception:
            pass
    try:
        _publish_event(
            "sterm_boot", "lifecycle",
            payload={"cwd": str(Path.cwd())},
        )
    except Exception:
        pass

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

    # RKOJ-ELENO :: 2026-05-25 :: install paste handler so multi-line pastes
    # get the [pasted N lines] placeholder treatment (jcode parity).
    if _HAVE_PASTE and _PASTE_BUFFER is not None:
        try:
            def _on_placeholder(result):
                if _LOG is not None:
                    try:
                        _LOG.info("STERM_PASTE_PLACEHOLDER",
                                  lines=result.line_count,
                                  has_url=result.image_url is not None)
                    except Exception:
                        pass
            _install_paste_handler(session, _PASTE_BUFFER, on_placeholder=_on_placeholder)
        except Exception:
            pass

    while True:
        _set_window_title()  # refresh on every prompt so cd changes show
        _emit_pill_and_popup_if_enabled()  # name pill + jcode popup overlay
        try:
            line = session.prompt(_prompt_text())
        except KeyboardInterrupt:
            # RKOJ-ELENO :: 2026-05-25 :: double-Ctrl+C exit pattern (jcode
            # ui_overlays.rs:367 "press twice to confirm"). First press → hint
            # only; second within window → clean exit.
            if _HAVE_HARDENER and _HARDENER is not None and _HARDENER.on_ctrl_c():
                console.print("[#A06EFF]> sterm out (^C^C)[/#A06EFF]")
                break
            console.print("[dim](^C — press again or type /exit to quit)[/dim]")
            continue
        except EOFError:
            # RKOJ-ELENO :: 2026-05-25 :: X-button popup confirmation
            # (operator-bind 2026-05-25T~14:14Z: "make the x button have a
            # extra popup before just closing"). Window-X via SIGHUP / Ctrl+D
            # both surface as EOFError on prompt_toolkit. Confirm-on-exit
            # avoids the accidental-close foot-gun.
            if not _confirm_exit(console):
                continue
            console.print("[#A06EFF]> sterm out[/#A06EFF]")
            break

        # Reset Ctrl+C tracker on any successful prompt — operator did
        # something, they're not trying to exit.
        if _HAVE_HARDENER and _HARDENER is not None:
            _HARDENER.reset_ctrl_c()

        # RKOJ-ELENO :: 2026-05-25 :: expand [pasted N lines] placeholders
        # BEFORE strip/dispatch so the underlying shell/command sees the
        # full text the operator originally pasted.
        if _HAVE_PASTE and _PASTE_BUFFER is not None and len(_PASTE_BUFFER) > 0:
            line = _expand_placeholders(line, _PASTE_BUFFER)
            _PASTE_BUFFER.clear()  # one-shot per submit

        line = line.strip()
        if not line:
            continue

        _write_heartbeat()

        # RKOJ-ELENO :: 2026-05-23 :: alias substitution on first token. Re-load
        # every prompt so /alias edits take effect without restart.
        line = expand_line(line, load_aliases())

        result = dispatch(line)
        try:
            _publish_event(
                "dispatch", "agent",
                payload={"line": line[:200], "handled": bool(result.handled)},
            )
        except Exception:
            pass
        if result.handled:
            if result.output:
                console.print(result.output)
            if result.exit_term:
                # RKOJ-ELENO :: 2026-05-25 :: confirm /exit too — same popup
                # as the window-X path. Skippable via SINISTER_TERM_FAST_EXIT=1
                # env for scripted shutdowns.
                if not _confirm_exit(console):
                    continue
                break
            continue

        _run_shell_command(line, console)

    try:
        _publish_event("sterm_exit", "lifecycle", payload={})
    except Exception:
        pass
    console.print("[dim]◈ Sinister Term exited.[/dim]")


if __name__ == "__main__":
    run()
