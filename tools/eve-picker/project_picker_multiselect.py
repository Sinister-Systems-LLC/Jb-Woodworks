"""project_picker_multiselect :: multi-select project picker for EVE.exe.

Author: RKOJ-ELENO :: 2026-05-24

Operator directive 2026-05-24T21:50Z (verbatim):
  "I need to be able to multi select with arrow keys moving throw and clicking
   enter on what projects I want to launch. Then a grid style view for me to
   easily run through and configure the things per project selected. And then
   they launch without fucking with each other or rate limiting Claude. We
   need to have the terminal windows log their position on the pc every 10
   minutes or so because I want projects to auto open and return to where
   they were closed from. And I need fucking naming and coloring to works
   and have defaults per project selected. Just log that too when you log
   position."

Surface:
  show_multi_picker() -> list[dict]
      Returns list of per-project launch configs:
        { key, agent_name, accent, swarm, loop, loop_condition, priority }

  launch_selected(configs) -> int (count launched)
      Spawns start-sinister-session.ps1 per config, 0.7s stagger.

Design constraints:
  L1: stdlib only (msvcrt on Windows; line-input fallback elsewhere)
  L2: do NOT import or mutate eve.py — sister-B owns it
  L3: re-use eve_picker_lib (build_picker_state / resolve agent/accent)
  L4: fits a 60-line terminal at every render path
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional


# RKOJ-ELENO :: 2026-05-24T22:10Z :: install SIGINT -> sys.exit(0). msvcrt.getwch()
# is a hard-block on the C runtime; Ctrl-C IS delivered as SIGINT on Windows
# Python but only between getwch calls. The poll loop below uses kbhit() so the
# handler can fire promptly. Operator: "i cannoot close eve exe. it wont close".
def _mp_sigint(*_args) -> None:
    sys.exit(0)


try:
    signal.signal(signal.SIGINT, _mp_sigint)
except (ValueError, OSError):
    pass

# Allow standalone smoke (`python project_picker_multiselect.py`) by ensuring
# our sibling eve_picker_lib is on sys.path.
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

try:
    import eve_picker_lib as lib  # type: ignore
except Exception:  # pragma: no cover — surfaces immediately to caller
    lib = None  # type: ignore

# eve_ui canonical header/footer + glow-highlight (RKOJ-ELENO :: 2026-05-25T00:32Z
# operator: "simple headers. everything else spaced out and organized.")
try:
    import eve_ui  # type: ignore
    _HAS_EVE_UI = True
except Exception:
    eve_ui = None  # type: ignore
    _HAS_EVE_UI = False

# ---------------------------------------------------------------------------
# Paths + constants
# ---------------------------------------------------------------------------

SANCTUM_ROOT = Path(os.environ.get("SINISTER_SANCTUM_ROOT", r"D:\Sinister Sanctum"))
LAUNCHER_PS1 = SANCTUM_ROOT / "automations" / "start-sinister-session.ps1"
PREFS_JSON = SANCTUM_ROOT / "automations" / "session-templates" / "agent-prefs.json"
WIN_POS_DIR = SANCTUM_ROOT / "_shared-memory" / "window-positions"

# ANSI palette (matches eve.py)
_ESC = "\x1b["
RESET = f"{_ESC}0m"
BOLD = f"{_ESC}1m"
DIM = f"{_ESC}2m"
PURPLE = f"{_ESC}38;5;141m"
BRIGHTP = f"{_ESC}38;5;177m"
WHITE = f"{_ESC}97m"
SOFT = f"{_ESC}38;5;245m"
OK = f"{_ESC}38;5;120m"
WARN = f"{_ESC}38;5;215m"
FAIL = f"{_ESC}38;5;203m"
CYAN = f"{_ESC}38;5;87m"
GREEN = f"{_ESC}38;5;120m"
YELLOW = f"{_ESC}38;5;221m"
MAGENTA = f"{_ESC}38;5;201m"

# ---------------------------------------------------------------------------
# Windows arrow-key reader (msvcrt). Falls back to line input elsewhere.
# ---------------------------------------------------------------------------

try:
    import msvcrt  # type: ignore
    _HAS_MSVCRT = True
except Exception:
    _HAS_MSVCRT = False


def _read_key(poll_ms: int = 100) -> str:
    """Poll-mode keypress reader. Returns canonical token.

    RKOJ-ELENO :: 2026-05-24T22:10Z :: switched from blocking getwch() to a
    kbhit() poll loop with 100 ms sleeps. msvcrt.getwch() blocks in C-runtime
    and refuses to surrender the GIL, so Ctrl-C (SIGINT) cannot fire until a
    real key is pressed -- which is exactly the "won't close" symptom. The
    poll loop lets the SIGINT handler (-> sys.exit) fire between polls.

    Ctrl-C also detected explicitly via getwch() returning '\\x03' on some
    Windows consoles where SIGINT isn't delivered for sub-process stdin.

    Tokens: 'UP', 'DOWN', 'LEFT', 'RIGHT', 'ENTER', 'SPACE', 'TAB',
            'ESC', 'BACKSPACE', single printable chars (lowercased).
    """
    if not _HAS_MSVCRT:
        try:
            line = input().strip()
        except EOFError:
            return "ESC"
        except KeyboardInterrupt:
            sys.exit(0)
        if not line:
            return "ENTER"
        return line[0].lower() if len(line) == 1 else line.lower()

    sleep_s = max(0.01, poll_ms / 1000.0)
    while True:
        try:
            if msvcrt.kbhit():
                ch = msvcrt.getwch()
                break
            time.sleep(sleep_s)
        except KeyboardInterrupt:
            sys.exit(0)

    # Explicit Ctrl-C glyph (some consoles deliver \x03 instead of SIGINT).
    if ch == "\x03":
        sys.exit(0)
    if ch in ("\r", "\n"):
        return "ENTER"
    if ch == " ":
        return "SPACE"
    if ch == "\t":
        return "TAB"
    if ch == "\x1b":
        return "ESC"
    if ch == "\x08":
        return "BACKSPACE"
    # Arrow keys / function keys come through as two reads: \x00 or \xe0 prefix
    if ch in ("\x00", "\xe0"):
        try:
            nxt = msvcrt.getwch()
        except KeyboardInterrupt:
            sys.exit(0)
        return {
            "H": "UP", "P": "DOWN", "K": "LEFT", "M": "RIGHT",
            "G": "HOME", "O": "END",
        }.get(nxt, "")
    return ch.lower()


# ---------------------------------------------------------------------------
# Terminal helpers
# ---------------------------------------------------------------------------

def _clear():
    # Enable ANSI on Windows; clear screen + home cursor.
    if os.name == "nt":
        try:
            os.system("")  # noqa: S605 — kicks Win10+ VT processing on
        except Exception:
            pass
    sys.stdout.write("\x1b[2J\x1b[H")
    sys.stdout.flush()


def _accent_to_ansi(accent: str) -> str:
    return {
        "purple": PURPLE,
        "magenta": MAGENTA,
        "cyan": CYAN,
        "green": GREEN,
        "yellow": YELLOW,
        "white": WHITE,
        "random": BRIGHTP,
    }.get((accent or "").lower(), PURPLE)


# ---------------------------------------------------------------------------
# Persist helpers (write-direct to agent-prefs.json with simple file lock)
# ---------------------------------------------------------------------------

def _load_prefs() -> dict:
    if not PREFS_JSON.exists():
        return {"version": 2, "default": {"agent_name": "", "accent_color": "purple"},
                "per_project": {}, "available_colors":
                ["purple", "magenta", "cyan", "green", "yellow", "white", "random"]}
    try:
        return json.loads(PREFS_JSON.read_text(encoding="utf-8-sig"))
    except Exception:
        return {"version": 2, "per_project": {}}


def _save_prefs(prefs: dict) -> bool:
    """Write prefs with a sidecar .lock so concurrent picker windows don't race."""
    lock = PREFS_JSON.with_suffix(".json.lock")
    for _ in range(30):  # ~3s total
        try:
            # Exclusive create acts as our lock
            fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            break
        except FileExistsError:
            time.sleep(0.1)
    else:
        # Couldn't obtain lock; still attempt write (best-effort)
        pass
    try:
        PREFS_JSON.write_text(
            json.dumps(prefs, indent=4, sort_keys=False),
            encoding="utf-8",
        )
        return True
    except Exception:
        return False
    finally:
        try:
            lock.unlink(missing_ok=True)  # type: ignore[call-arg]
        except Exception:
            pass


def _update_pref(key: str, agent_name: str, accent: str) -> None:
    prefs = _load_prefs()
    prefs.setdefault("per_project", {})
    prefs["per_project"][key] = {"agent_name": agent_name, "accent_color": accent}
    _save_prefs(prefs)


# ---------------------------------------------------------------------------
# Window-position metadata write (operator: "log that too when you log position")
# ---------------------------------------------------------------------------

def _annotate_position_meta(key: str, agent_name: str, accent: str) -> None:
    """Write per-project accent + agent_name into window-positions/<key>.json so
    the position monitor's next sweep can restore naming + coloring too.

    Idempotent. If the position file doesn't yet exist (first launch) we
    create a stub with no rect; the sweep will overwrite with real coords.
    """
    try:
        WIN_POS_DIR.mkdir(parents=True, exist_ok=True)
        path = WIN_POS_DIR / f"{key}.json"
        data: dict = {}
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8-sig"))
            except Exception:
                data = {}
        data["project_key"] = key
        data["agent_name"] = agent_name
        data["accent"] = accent
        data["meta_ts_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        data.setdefault("watcher", "project_picker_multiselect.py:meta")
        path.write_text(json.dumps(data, indent=4), encoding="utf-8")
    except Exception:
        pass  # non-fatal; the sweep will retry on next 10-min tick


# ---------------------------------------------------------------------------
# Picker state ingestion (fall back to direct read if lib unavailable)
# ---------------------------------------------------------------------------

def _load_picker_rows() -> list[dict]:
    """Return list of {key, display, tag, agent_name, accent, default_modes, tier}."""
    if lib is not None:
        try:
            st = lib.build_picker_state(boot_ms=0)
            prefs = lib.read_prefs() or {}
            pj = lib.read_projects()
            by_key = {p["key"]: p for p in pj.get("projects", [])}
            out = []
            for r in st.rows:
                pr = by_key.get(r.key, {})
                dm = pr.get("default_modes") or {}
                out.append({
                    "key": r.key,
                    "display": r.display,
                    "tag": r.tag,
                    "agent_name": r.agent_name,
                    "accent": r.accent,
                    "default_swarm": bool(dm.get("swarm", False)),
                    "default_loop": bool(dm.get("loop", True)),
                    "tier": r.tier,
                })
            return out
        except Exception:
            pass
    # Direct fallback if lib unavailable
    projects_path = SANCTUM_ROOT / "automations" / "session-templates" / "projects.json"
    try:
        pj = json.loads(projects_path.read_text(encoding="utf-8-sig"))
        prefs = _load_prefs()
        by_key = {p["key"]: p for p in pj.get("projects", [])}
        vis = (pj.get("picker") or {}).get("visible_keys") or list(by_key)
        out = []
        for k in vis:
            if k not in by_key:
                continue
            p = by_key[k]
            pref = (prefs.get("per_project") or {}).get(k) or {}
            dm = p.get("default_modes") or {}
            out.append({
                "key": k,
                "display": p.get("display") or k,
                "tag": (p.get("tag") or "")[:60],
                "agent_name": pref.get("agent_name") or k,
                "accent": pref.get("accent_color") or "purple",
                "default_swarm": bool(dm.get("swarm", False)),
                "default_loop": bool(dm.get("loop", True)),
                "tier": int(p.get("tier", 3) or 3),
            })
        return out
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Stage 1 — multi-select with arrow keys
# ---------------------------------------------------------------------------

# RKOJ-ELENO :: 2026-05-25T00:32Z :: operator "these projects need to have
# headers and header bars to seperate per category". Default categorization
# split by index ranges (groups of 5/5/5/5/1). Pull override from
# projects.json `picker.categories` when present:
#   "categories": [
#     {"label": "Sanctum + Core", "keys": ["sanctum", ...]},
#     ...
#   ]

_DEFAULT_CATEGORY_PLAN = [
    ("Sanctum + Core",     ["sanctum", "sinister-chatbot", "sinister-panel",
                            "kernel-apk", "sinister-emulator"]),
    ("Tooling + API",      ["rkoj", "snap-emulator-api", "tiktok-emulator-api",
                            "bumble-emulator-api", "sinister-freeze"]),
    ("Client Sites",       ["jb-woodworks", "showmasters", "letstext",
                            "eve-compliance", "sinister-generator"]),
    ("Sinister Systems",   ["jkor", "sinister-snap-api-quantum", "sinister-os",
                            "sinister-imessage-bridge", "sinister-sleight"]),
    ("Overseer",           ["sinister-overseer"]),
]


def _load_category_plan() -> list[tuple[str, list[str]]]:
    """Pull `picker.categories` from projects.json, else default plan."""
    projects_path = SANCTUM_ROOT / "automations" / "session-templates" / "projects.json"
    try:
        pj = json.loads(projects_path.read_text(encoding="utf-8-sig"))
        cats = ((pj.get("picker") or {}).get("categories")) or None
        if cats:
            return [(c.get("label", "—"), list(c.get("keys") or [])) for c in cats]
    except Exception:
        pass
    return list(_DEFAULT_CATEGORY_PLAN)


def _build_visual_list(rows: list[dict]) -> list[dict]:
    """Interleave category headers + project rows.

    Returns a list of entries:
       {"kind": "header", "label": str}              # not selectable
       {"kind": "row",    "row_index": int, "row": dict}  # selectable
    Any rows not matched by a category fall into a trailing "Other" group.
    """
    plan = _load_category_plan()
    by_key = {r["key"]: i for i, r in enumerate(rows)}
    consumed: set[int] = set()
    out: list[dict] = []
    for label, keys in plan:
        bucket = [(k, by_key[k]) for k in keys if k in by_key]
        if not bucket:
            continue
        out.append({"kind": "header", "label": label})
        for _k, idx in bucket:
            out.append({"kind": "row", "row_index": idx, "row": rows[idx]})
            consumed.add(idx)
    leftover = [i for i in range(len(rows)) if i not in consumed]
    if leftover:
        out.append({"kind": "header", "label": "Other"})
        for idx in leftover:
            out.append({"kind": "row", "row_index": idx, "row": rows[idx]})
    return out


def _row_positions(visual: list[dict]) -> list[int]:
    """Visual-index positions of the selectable rows (skip headers)."""
    return [i for i, e in enumerate(visual) if e["kind"] == "row"]


def _render_multi(rows: list[dict], visual: list[dict],
                  cursor_visual: int, selected: set[int],
                  tick: int = 0) -> None:
    # Operator: "each menu needs to go to a complete clean new menu that is
    # clean and you cannot see the menu you just came from."
    if _HAS_EVE_UI:
        eve_ui.print_sub_page_header("Pick projects")
    else:
        _clear()
        print()
        print(f"  {BRIGHTP}--- Pick projects ---{RESET}")
        print()

    # Compact account panel above the picker.
    try:
        from account_info_panel import render_account_info_block  # type: ignore
        render_account_info_block(detailed=False)
        print()
    except Exception:
        pass

    # RKOJ-ELENO :: 2026-05-25T01:15Z :: operator hard-canonical *"centered
    # menu styling like main_menu hero applied to every sub-page"*. Body
    # rows (headers + project entries) now block-center via eve_ui.center_block.
    body: list[str] = []
    for vi, entry in enumerate(visual):
        if entry["kind"] == "header":
            label = entry["label"]
            # Header bar: --- Label ------------
            bar_total = 48
            tail = max(3, bar_total - len(label) - 5)
            body.append("")
            body.append(f"{DARKP_OR_DIM()}---{RESET} "
                        f"{WHITE}{BOLD}{label}{RESET} "
                        f"{DARKP_OR_DIM()}{'-' * tail}{RESET}")
            continue
        r = entry["row"]
        ri = entry["row_index"]
        is_cursor = (vi == cursor_visual)
        mark = "x" if ri in selected else " "
        tier_badge = str(r.get("tier") or 3)
        box_color = OK if ri in selected else SOFT
        # Compact row: [x]  3  Sinister Panel
        raw = (f"{box_color}[{mark}]{RESET}  "
               f"{DIM}{tier_badge}{RESET}  "
               f"{WHITE}{r['display']}{RESET}")
        if _HAS_EVE_UI:
            body.append(eve_ui.highlight_row(raw, is_cursor, tick=tick, bar_width=52))
        else:
            prefix = ">" if is_cursor else " "
            line = f"{prefix} {raw}"
            if is_cursor:
                line = f"{BOLD}{line}{RESET}"
            body.append(line)
    if _HAS_EVE_UI:
        for ln in eve_ui.center_block(body, width=68):
            print(ln)
    else:
        for ln in body:
            print(f"  {ln}")

    print()
    # RKOJ-ELENO :: 2026-05-25T07:17Z Sub-Q :: Quick-launch (Q) hint added
    # per operator hard-canonical "quickest way to open my termionials".
    # Q = launch selected with all defaults (no grid, no Prompt-AgentModes).
    print(f"  {DIM}---{RESET} "
          f"{WHITE}Space{RESET}) toggle  "
          f"{WHITE}Enter{RESET}) configure  "
          f"{BRIGHTP}Q{RESET}) {OK}Quick-launch (skip all prompts){RESET}  "
          f"{WHITE}A{RESET}) all  "
          f"{WHITE}N{RESET}) none  "
          f"{WHITE}B{RESET}) Back  "
          f"{WHITE}X{RESET}) Exit  "
          f"{DIM}---{RESET}")
    print(f"  {DIM}selected: {len(selected)} / {len(rows)}{RESET}")


def DARKP_OR_DIM() -> str:
    """Resolve the header-bar accent: eve_ui DARKP if present, else local DIM."""
    if _HAS_EVE_UI:
        return getattr(eve_ui, "DARKP", DIM)
    return DIM


def _stage_multi_select(rows: list[dict]) -> Optional[list[int]]:
    """Return list of selected row indices, or None if user backed out.

    Cursor lands ONLY on project rows; category headers are skipped during
    navigation (operator: "Skip category headers when navigating").
    """
    if not rows:
        return None
    visual = _build_visual_list(rows)
    selectable_positions = _row_positions(visual)
    if not selectable_positions:
        return None
    cursor_idx = 0  # index into selectable_positions
    selected: set[int] = set()
    tick = 0
    while True:
        cursor_visual = selectable_positions[cursor_idx]
        _render_multi(rows, visual, cursor_visual, selected, tick=tick)
        key = _read_key()
        tick += 1
        if key == "UP":
            cursor_idx = (cursor_idx - 1) % len(selectable_positions)
        elif key == "DOWN":
            cursor_idx = (cursor_idx + 1) % len(selectable_positions)
        elif key == "HOME":
            cursor_idx = 0
        elif key == "END":
            cursor_idx = len(selectable_positions) - 1
        elif key == "SPACE":
            row_index = visual[selectable_positions[cursor_idx]]["row_index"]
            if row_index in selected:
                selected.remove(row_index)
            else:
                selected.add(row_index)
        elif key == "ENTER":
            if not selected:
                row_index = visual[selectable_positions[cursor_idx]]["row_index"]
                selected.add(row_index)
            return sorted(selected)
        elif key == "a":
            selected = set(range(len(rows)))
        elif key == "n":
            selected = set()
        # RKOJ-ELENO :: 2026-05-25T07:17Z Sub-Q :: Quick-launch (Q key).
        # Operator hard-canonical 07:17Z (Image 7+8) "quickest way to open my
        # termionials". Q at picker -> bypass grid + bypass Prompt-AgentModes
        # entirely. Sets SINISTER_QUICK_LAUNCH=1 sentinel which launch_selected
        # propagates per-spawn. Same selected set as Enter (auto-pick cursor row
        # if none selected). _read_key lowercases all keys so we match "q".
        # Note: "q" was previously a back-out alias; we now repurpose it as
        # quick-launch since b/ESC already cover back-out, and operator hard-
        # canonical promotes Q (uppercase intent) to a fleet-wide shortcut.
        elif key == "q":
            if not selected:
                row_index = visual[selectable_positions[cursor_idx]]["row_index"]
                selected.add(row_index)
            os.environ["SINISTER_QUICK_LAUNCH"] = "1"
            return sorted(selected)
        elif key in ("b", "ESC"):
            return None
        elif key == "x":
            sys.exit(0)


# ---------------------------------------------------------------------------
# Stage 2 — grid config screen
# ---------------------------------------------------------------------------

# Fields editable per row: agent / accent / swarm / loop / cond / priority
_FIELDS = ["agent", "accent", "swarm", "loop", "cond", "priority"]
_ACCENT_CYCLE = ["purple", "magenta", "cyan", "green", "yellow", "white", "random"]


def _render_grid(configs: list[dict], cursor_row: int, cursor_field: int,
                 editing_text: Optional[tuple[str, str]] = None) -> None:
    _clear()
    n = len(configs)
    print(f"  {BRIGHTP}--- Configure {n} selected projects ---{RESET}")
    print()
    header = (f"  {DIM}#  {'Project':<22} {'Agent':<18} "
              f"{'Accent':<8} {'Swarm':<6} {'Loop':<5} {'Cond':<22} {'Pri'}{RESET}")
    print(header)
    print(f"  {DIM}{'-' * 100}{RESET}")
    for ri, c in enumerate(configs):
        cells = [
            c["agent_name"][:18],
            c["accent"][:8],
            "[y]" if c["swarm"] else "[n]",
            "[y]" if c["loop"] else "[n]",
            (c["loop_condition"] or "<empty>")[:22],
            f"T{c['priority']}",
        ]
        # Colorize field under cursor
        colored = []
        for fi, val in enumerate(cells):
            is_focus = (ri == cursor_row and fi == cursor_field)
            if is_focus and editing_text and editing_text[0] in ("agent", "cond"):
                shown = editing_text[1] + "_"
                colored.append(f"{BOLD}{BRIGHTP}{shown:<{len(val) if len(val) > len(shown) else len(shown)+1}}{RESET}")
            elif is_focus:
                colored.append(f"{BOLD}{BRIGHTP}{val}{RESET}")
            else:
                colored.append(f"{WHITE}{val}{RESET}")
        accent_ansi = _accent_to_ansi(c["accent"])
        # Pad each cell to its column width
        line = (f"  {DIM}{ri+1:<2}{RESET} "
                f"{accent_ansi}{c['display'][:22]:<22}{RESET} "
                f"{colored[0]:<18} {colored[1]:<8} {colored[2]:<6} "
                f"{colored[3]:<5} {colored[4]:<22} {colored[5]}")
        if ri == cursor_row:
            print(f"{BRIGHTP}>{RESET}" + line[1:])
        else:
            print(line)
    print()
    print(f"  {BRIGHTP}---{RESET} "
          f"{WHITE}Arrows{RESET}) move  "
          f"{WHITE}Space{RESET}/{WHITE}Enter{RESET}) edit/toggle  "
          f"{WHITE}L{RESET}) launch all  "
          f"{WHITE}B{RESET}) back  {BRIGHTP}---{RESET}")
    field_name = _FIELDS[cursor_field]
    hints = {
        "agent": "type to edit agent name; Enter confirms",
        "accent": "Space cycles palette",
        "swarm": "Space toggles",
        "loop": "Space toggles",
        "cond": "type free text; Enter confirms",
        "priority": "Space cycles 1->2->3->4->1",
    }
    print(f"  {DIM}field: {WHITE}{field_name}{RESET}{DIM} — {hints[field_name]}{RESET}")


def _edit_text_field(prompt: str, initial: str, max_len: int = 40) -> str:
    """Inline text editor using msvcrt char-by-char; ESC reverts; Enter confirms.

    RKOJ-ELENO :: 2026-05-24T22:10Z :: poll-mode with 100 ms sleeps so SIGINT
    fires promptly. EOFError on the fallback path returns initial. Ctrl-C
    inside the msvcrt loop exits the entire process (not just this field).
    """
    if not _HAS_MSVCRT:
        try:
            ans = input(f"  {prompt} [{initial}] > ").strip()
        except EOFError:
            return initial
        except KeyboardInterrupt:
            sys.exit(0)
        return ans if ans else initial
    buf = list(initial)
    while True:
        sys.stdout.write("\x1b[s")  # save cursor
        sys.stdout.write(f"\x1b[1G  {prompt} > {''.join(buf)}_\x1b[K")
        sys.stdout.write("\x1b[u")  # restore cursor
        sys.stdout.flush()
        # Poll for keypress so Ctrl-C (SIGINT) is responsive between polls.
        while True:
            try:
                if msvcrt.kbhit():
                    ch = msvcrt.getwch()
                    break
                time.sleep(0.1)
            except KeyboardInterrupt:
                sys.exit(0)
        if ch == "\x03":  # Ctrl-C glyph fallback
            sys.exit(0)
        if ch in ("\r", "\n"):
            return "".join(buf)
        if ch == "\x1b":
            return initial
        if ch == "\x08":
            if buf:
                buf.pop()
        elif ch in ("\x00", "\xe0"):
            try:
                msvcrt.getwch()  # consume extended char, ignore
            except KeyboardInterrupt:
                sys.exit(0)
        elif ch.isprintable() and len(buf) < max_len:
            buf.append(ch)


def _stage_grid_config(rows: list[dict], indices: list[int]) -> Optional[list[dict]]:
    """Build per-row configs, run interactive edit loop, return final configs."""
    configs: list[dict] = []
    for i in indices:
        r = rows[i]
        configs.append({
            "key": r["key"],
            "display": r["display"],
            "agent_name": r["agent_name"],
            "accent": r["accent"],
            "swarm": r["default_swarm"],
            "loop": r["default_loop"],
            "loop_condition": "",
            "priority": int(r["tier"]) if r["tier"] in (1, 2, 3, 4) else 3,
        })
    cursor_row = 0
    cursor_field = 0
    while True:
        _render_grid(configs, cursor_row, cursor_field)
        key = _read_key()
        if key == "UP":
            cursor_row = (cursor_row - 1) % len(configs)
        elif key == "DOWN":
            cursor_row = (cursor_row + 1) % len(configs)
        elif key in ("RIGHT", "TAB"):
            cursor_field = (cursor_field + 1) % len(_FIELDS)
        elif key == "LEFT":
            cursor_field = (cursor_field - 1) % len(_FIELDS)
        elif key in ("b", "ESC"):
            return None
        elif key in ("l",):
            return configs
        elif key in ("SPACE", "ENTER"):
            fn = _FIELDS[cursor_field]
            c = configs[cursor_row]
            if fn == "agent":
                new = _edit_text_field("agent name", c["agent_name"], 32)
                if new:
                    c["agent_name"] = new
            elif fn == "accent":
                cur = c["accent"] if c["accent"] in _ACCENT_CYCLE else "purple"
                idx = _ACCENT_CYCLE.index(cur)
                c["accent"] = _ACCENT_CYCLE[(idx + 1) % len(_ACCENT_CYCLE)]
            elif fn == "swarm":
                c["swarm"] = not c["swarm"]
            elif fn == "loop":
                c["loop"] = not c["loop"]
            elif fn == "cond":
                new = _edit_text_field("loop condition", c["loop_condition"], 60)
                c["loop_condition"] = new
            elif fn == "priority":
                c["priority"] = (c["priority"] % 4) + 1
        # Letter shortcuts for power users
        elif key == "s":
            configs[cursor_row]["swarm"] = not configs[cursor_row]["swarm"]
        elif key in ("1", "2", "3", "4"):
            configs[cursor_row]["priority"] = int(key)


# ---------------------------------------------------------------------------
# Stage 3 — staggered launch
# ---------------------------------------------------------------------------

def launch_selected(configs: list[dict], stagger_seconds: float = 0.7) -> int:
    """Spawn each project via start-sinister-session.ps1 with a stagger.

    Returns count of successful launches. Sets per-spawn env vars so the
    PS1 launcher's Prompt-AgentModes branch is bypassed (uses our values).
    """
    launched = 0
    for c in configs:
        # Persist agent_name + accent BEFORE spawn (so launcher reads them too)
        _update_pref(c["key"], c["agent_name"], c["accent"])
        _annotate_position_meta(c["key"], c["agent_name"], c["accent"])

        env = os.environ.copy()
        env["SINISTER_SKIP_MODES_PROMPT"] = "1"
        env["SINISTER_DEFAULT_SWARM"] = "1" if c["swarm"] else "0"
        env["SINISTER_DEFAULT_LOOP"] = "1" if c["loop"] else "0"
        env["SINISTER_DEFAULT_PRIORITY"] = str(c["priority"])
        if c["loop_condition"]:
            env["SINISTER_DEFAULT_LOOP_CONDITION"] = c["loop_condition"]
        # RKOJ-ELENO :: 2026-05-25T07:17Z Sub-Q :: propagate quick-launch
        # sentinel so the PS1 launcher's Prompt-AgentModes early-returns w/
        # defaults (no prompts at all).
        if os.environ.get("SINISTER_QUICK_LAUNCH") == "1":
            env["SINISTER_QUICK_LAUNCH"] = "1"

        cmd = [
            "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
            "-File", str(LAUNCHER_PS1),
            "-Project", c["key"],
            "-AgentName", c["agent_name"],
            "-AccentColor", c["accent"],
        ]
        try:
            # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP so each spawn is independent
            creationflags = 0
            if os.name == "nt":
                creationflags = 0x00000008 | 0x00000200  # DETACHED + NEW_PGRP
            subprocess.Popen(
                cmd, env=env, creationflags=creationflags,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL, close_fds=True,
            )
            launched += 1
            print(f"  {OK}[launch]{RESET} {c['display']:<24} "
                  f"{DIM}agent={c['agent_name']} accent={c['accent']} "
                  f"swarm={c['swarm']} loop={c['loop']} T{c['priority']}{RESET}")
        except Exception as e:
            print(f"  {FAIL}[fail]{RESET} {c['display']}: {e}")
        time.sleep(stagger_seconds)
    return launched


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def show_multi_picker() -> list[dict]:
    """Show two-stage picker. Returns configs (also launches them).

    Returns [] if user backed out at any point.
    """
    rows = _load_picker_rows()
    if not rows:
        print(f"  {FAIL}[picker] no projects loaded (check projects.json){RESET}")
        return []
    indices = _stage_multi_select(rows)
    if not indices:
        return []
    # RKOJ-ELENO :: 2026-05-25T07:17Z Sub-Q :: quick-launch fast path. If the
    # operator pressed Q at the picker, skip the grid-config stage entirely
    # and build configs from the project's static defaults (projects.json
    # tier, agent name, accent already injected by _load_picker_rows).
    if os.environ.get("SINISTER_QUICK_LAUNCH") == "1":
        configs: list[dict] = []
        for ri in indices:
            r = rows[ri]
            configs.append({
                "key": r["key"],
                "display": r["display"],
                "agent_name": r.get("agent_name") or r.get("default_agent_name") or r["display"],
                "accent": r.get("accent") or r.get("default_accent") or "purple",
                "swarm": True,
                "loop": True,
                "loop_condition": "",
                "priority": int(r.get("tier") or 3),
            })
    else:
        configs = _stage_grid_config(rows, indices)
        if not configs:
            return []
    print()
    print(f"  {BRIGHTP}--- launching {len(configs)} sessions (staggered) ---{RESET}")
    launch_selected(configs)
    print()
    print(f"  {OK}all launched.{RESET} {DIM}returning to main menu...{RESET}")
    time.sleep(1.2)
    # Clear sentinel so next picker session starts clean.
    os.environ.pop("SINISTER_QUICK_LAUNCH", None)
    return configs


# ---------------------------------------------------------------------------
# CLI smoke
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--smoke":
        rows = _load_picker_rows()
        print(f"smoke :: loaded {len(rows)} rows")
        visual = _build_visual_list(rows)
        sel_pos = _row_positions(visual)
        print(f"smoke :: visual entries = {len(visual)} "
              f"(headers={len(visual) - len(sel_pos)}, rows={len(sel_pos)})")
        print()
        # Render the new layout once (cursor on first selectable row, none selected)
        _render_multi(rows, visual, cursor_visual=sel_pos[0] if sel_pos else 0,
                      selected=set(), tick=0)
        print()
        print("smoke :: category breakdown:")
        cur_label = None
        for e in visual:
            if e["kind"] == "header":
                cur_label = e["label"]
                print(f"  --- {cur_label}")
            else:
                r = e["row"]
                print(f"      T{r['tier']}  {r['display']}")
        sys.exit(0)
    show_multi_picker()
