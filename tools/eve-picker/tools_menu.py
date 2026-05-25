"""tools_menu.py :: EVE.exe T) Tools sub-page.

Author: RKOJ-ELENO :: 2026-05-25

Operator hard-canonical 2026-05-25T00:30Z (screenshot #58):
    "remove this shit from resume. place utterences, mesh status, health and
     quatum tools on the main menu page and lead to their own dedicated
     cleaned in theme pages from there."

The bottom letter-row that previously cluttered the Resume project picker
(O/G/A/N/R/H/M/Q/U/T/X) has been DELETED. Those operator-facing tools now
live on the main menu via `T) Tools` -> this module, which renders a
canonical sub-page with arrow-key highlight and dispatches each row to its
own dedicated themed page.

Sub-pages exposed:
    1) Health              -> eve._cb_tools_health -> health_tools.menu_loop
    2) Mesh status         -> eve._view_mesh_status
    3) Quantum tools       -> quantum_tools.menu_loop
    4) Queue               -> eve._view_queue
    5) Utterances          -> eve._view_utterances
    6) Sanctum Automations -> eve._sanctum_automations_menu

Each dispatched sub-page is responsible for its own clear_screen() +
canonical header/footer (per eve-ui-uniformity-doctrine-2026-05-24).
This module's render uses eve_ui.py primitives so it inherits the same
look-and-feel as every other EVE sub-page.

Smoke test: `python tools_menu.py --smoke` renders one frame and exits 0
without entering the input loop.
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Callable, Optional

__version__ = "0.1.0"

# Make eve_ui importable when this module is launched standalone (smoke test)
sys.path.insert(0, str(Path(__file__).resolve().parent))

from eve_ui import (  # type: ignore
    BRIGHTP,
    DARKP,
    DIM,
    FAIL,
    OK,
    PURPLE,
    RESET,
    SOFT,
    WARN,
    WHITE,
    center_block,
    clear_screen,
    highlight_row,
    print_sub_page_footer,
    print_sub_page_header,
    visible_len,
)


# ---------------------------------------------------------------------------
# Menu items :: (letter, label, description, callback-key)
# Callback keys map into the `callbacks` dict passed by eve.main().
# ---------------------------------------------------------------------------

_TOOLS_ITEMS: list[tuple[str, str, str, str]] = [
    ("1", "Health",              "Anthropic-throttle + fleet health",     "health"),
    ("2", "Mesh status",         "Tailscale + cross-machine mesh state",  "mesh"),
    ("3", "Quantum tools",       "QML / quantum-circuit utilities",       "quantum"),
    ("4", "Queue",               "OPERATOR-ACTION-QUEUE top rows",        "queue"),
    ("5", "Utterances",          "unresolved operator utterances",        "utterances"),
    ("6", "Sanctum Automations", "ps1 automation runner sub-menu",        "automations"),
]


_TICK = 0  # module-level monotonic for highlight breath


def _row_text(letter: str, label: str, hint: str, selected: bool) -> str:
    """Single ANSI-colored row string (same shape as main_menu rows)."""
    if selected:
        key_color = "\033[97;1;4m"
        title_color = "\033[97;1;4m"
        hint_color = "\033[38;5;253;4m"
    else:
        key_color = PURPLE
        title_color = WHITE
        hint_color = DIM
    key = f"{key_color}{letter}){RESET}"
    title = f"{title_color}{label}{RESET}"
    # 22-char title column so all rows align uniformly
    title_pad = max(1, 22 - len(label))
    hint_s = f"{hint_color}{hint}{RESET}" if hint else ""
    return f"{key}  {title}{' ' * title_pad}{hint_s}"


def _render(highlight: int) -> None:
    """Render the Tools sub-page (header + centered menu body + footer).

    RKOJ-ELENO :: 2026-05-25T01:15Z :: operator hard-canonical (image #61)
    *"centered menu styling applied to every sub-page"*. Body rows now
    block-center via eve_ui.center_block (header + footer stay full-width).
    """
    global _TICK
    print_sub_page_header("Tools")
    body: list[str] = []
    for i, (letter, label, hint, _) in enumerate(_TOOLS_ITEMS):
        selected = (i == highlight)
        row_str = _row_text(letter, label, hint, selected)
        body.append(highlight_row(row_str, selected, _TICK, bar_width=60))
    for ln in center_block(body, width=64):
        print(ln)
    print_sub_page_footer("1-6 to run / arrows + Enter")
    _TICK += 1


def _read_choice(highlight: int) -> tuple[Optional[str], int]:
    """Windows arrow-key + single-key input loop.

    Returns (action|None, new_highlight). action is either:
      - a digit "1".."6" (dispatch that row)
      - "b" / "h" / "x" (nav)
      - None (re-render only)
    """
    try:
        import msvcrt  # type: ignore
    except ImportError:
        # Non-Windows fallback :: line-input
        try:
            raw = input(f"  {PURPLE}>{RESET} ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return ("x", highlight)
        if not raw:
            return (_TOOLS_ITEMS[highlight][0], highlight)
        if raw in ("b", "h", "x", "back", "home", "exit", "quit", "q"):
            return (raw[0], highlight)
        for i, (letter, _, _, _) in enumerate(_TOOLS_ITEMS):
            if raw == letter:
                return (letter, i)
        return (None, highlight)

    while True:
        try:
            ch = msvcrt.getwch()
        except KeyboardInterrupt:
            sys.exit(0)
        if ch in ("\r", "\n"):
            return (_TOOLS_ITEMS[highlight][0], highlight)
        if ch == "\x03":  # Ctrl-C
            sys.exit(0)
        if ch in ("\xe0", "\x00"):
            try:
                ch2 = msvcrt.getwch()
            except KeyboardInterrupt:
                sys.exit(0)
            if ch2 == "H":  # up
                return (None, (highlight - 1) % len(_TOOLS_ITEMS))
            if ch2 == "P":  # down
                return (None, (highlight + 1) % len(_TOOLS_ITEMS))
            continue
        if ch == "\t":
            return (None, (highlight + 1) % len(_TOOLS_ITEMS))
        if ch.isprintable():
            low = ch.lower()
            if low in ("b", "h", "x", "q"):
                return (low, highlight)
            for i, (letter, _, _, _) in enumerate(_TOOLS_ITEMS):
                if low == letter:
                    return (letter, i)
            if low == "k":
                return (None, (highlight - 1) % len(_TOOLS_ITEMS))
            if low == "j":
                return (None, (highlight + 1) % len(_TOOLS_ITEMS))


def _default_stub(name: str) -> Callable[[], None]:
    def _f() -> None:
        clear_screen()
        print()
        print(f"  {WARN}[{name}] not wired through tools_menu yet.{RESET}")
        print(f"  {DIM}(eve.main() must inject callbacks dict for Tools sub-page.){RESET}")
        time.sleep(1.2)
    return _f


def show_tools_menu(callbacks: Optional[dict[str, Callable[[], None]]] = None) -> None:
    """Render the Tools sub-page loop.

    callbacks keys (all optional; missing keys fall back to a friendly stub):
        health        -> Health sub-page
        mesh          -> Mesh status sub-page
        quantum       -> Quantum tools sub-page
        queue         -> Queue sub-page
        utterances    -> Utterances sub-page
        automations   -> Sanctum Automations sub-menu

    Returns when operator picks B/Back. H/X route via sys.exit(0).
    """
    cb = callbacks or {}
    actions: dict[str, Callable[[], None]] = {
        "1": cb.get("health") or _default_stub("Health"),
        "2": cb.get("mesh") or _default_stub("Mesh status"),
        "3": cb.get("quantum") or _default_stub("Quantum tools"),
        "4": cb.get("queue") or _default_stub("Queue"),
        "5": cb.get("utterances") or _default_stub("Utterances"),
        "6": cb.get("automations") or _default_stub("Sanctum Automations"),
    }

    highlight = 0
    while True:
        _render(highlight)
        action, highlight = _read_choice(highlight)
        if action is None:
            continue
        if action in ("b", "back"):
            return
        if action == "h":
            # Caller (main_menu) re-paints on return; nothing else to do.
            return
        if action == "x":
            sys.exit(0)
        fn = actions.get(action)
        if fn is not None:
            try:
                fn()
            except Exception as e:
                print(f"  {FAIL}[{action}] tools sub-page failed: {e}{RESET}")
                time.sleep(1.2)
            # After sub-page returns, loop re-renders the Tools page fresh
            # (sub-page's residue is wiped by print_sub_page_header's
            # clear_screen()).
            continue


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

def _smoke() -> int:
    """Render one full Tools frame and exit 0 without the input loop."""
    try:
        _render(highlight=0)
        print(f"\n{OK}[smoke] tools_menu.py OK · _TICK={_TICK}{RESET}")
        return 0
    except Exception as e:
        print(f"{FAIL}[smoke] FAIL: {e}{RESET}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--smoke":
        sys.exit(_smoke())
    show_tools_menu()
