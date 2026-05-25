"""project_config_grid :: stage-2 config-grid for EVE multi-launch flow.

Author: RKOJ-ELENO :: 2026-05-25

Operator hard-canonical 2026-05-25T00:32Z (verbatim):
    "then the options per so once i select them and hit next we go to the next
     page that shows the projects then like a check box based system or some
     efficient system where i can pick if i want to swarm each project, loop
     each one, what i want to set the priority at. i need auto fill autos
     like all like a way to fill entire row with y/n or load defaults or load
     saved preset. then i need a way to save the preset that will have the
     saved preset for next time."

Surface:
    show_config_grid(selected_projects: list[dict]) -> list[dict]
        Takes the rows from project_picker_multiselect Stage 1 and lets the
        operator set per-project Swarm / Loop / Priority via a cell-grid UI
        with bulk auto-fill + named-preset save/load. Returns final launch
        configs:
            { key, agent_name, accent, swarm, loop, priority }

Design constraints:
  L1: stdlib only (msvcrt on Windows; line-input fallback elsewhere)
  L2: do NOT import or mutate eve.py -- sister-A owns the picker module
  L3: re-use eve_ui.py canonical header/footer/highlight primitives
  L4: cp1252-safe glyphs (no fancy box-draw); ASCII brackets [x] / [ ]
  L5: parse-clean stdlib-only; no third-party deps

Preset storage scheme:
  _shared-memory/picker-presets/<name>.json
    {
      "name": "<name>",
      "owner_email": "<default account label>",
      "created_utc": "2026-05-25T00:34:00Z",
      "configs": [
        { "key": "...", "swarm": true, "loop": true, "priority": 2 },
        ...
      ]
    }

Per-user awareness:
  The default account (from claude-accounts.json -> default name) determines
  the owner_email stamp. When operator browses saved presets we filter to
  rows where owner_email matches the current default account's label, so
  Zonia sees Zonia's presets and Leo sees Leo's. Falls back to "anonymous"
  if claude-accounts.json is missing.

Composes with:
  * project_picker_multiselect.show_multi_picker (stage-1 multi-select)
  * eve_ui.print_sub_page_header / _footer / highlight_row / clear_screen
  * automations/start-sinister-session.ps1 via SINISTER_DEFAULT_* env vars
"""
from __future__ import annotations

import json
import os
import signal
import sys
import time
from pathlib import Path
from typing import Optional

__version__ = "0.1.0"

# ---------------------------------------------------------------------------
# SIGINT -> clean exit (same as sister picker; msvcrt.kbhit loop honors it)
# ---------------------------------------------------------------------------

def _cg_sigint(*_a) -> None:
    sys.exit(0)


try:
    signal.signal(signal.SIGINT, _cg_sigint)
except (ValueError, OSError):
    pass

# ---------------------------------------------------------------------------
# Path-bootstrap so standalone python invocation finds eve_ui
# ---------------------------------------------------------------------------

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

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
PROJECTS_JSON = SANCTUM_ROOT / "automations" / "session-templates" / "projects.json"
PREFS_JSON = SANCTUM_ROOT / "_shared-memory" / "agent-prefs.json"
ACCOUNTS_JSON = SANCTUM_ROOT / "_shared-memory" / "claude-accounts.json"
PRESETS_DIR = SANCTUM_ROOT / "_shared-memory" / "picker-presets"

# Fallback ANSI palette if eve_ui import failed (no-color terminals get "")
def _ansi_on() -> bool:
    if os.environ.get("NO_COLOR", "").strip():
        return False
    term = os.environ.get("TERM", "").strip().lower()
    if term == "dumb" and os.name != "nt":
        return False
    return True


_ANSI = _ansi_on()


def _c(seq: str) -> str:
    return seq if _ANSI else ""


PURPLE = _c("\033[38;5;141m")
DARKP = _c("\033[38;5;91m")
BRIGHTP = _c("\033[38;5;177m")
WHITE = _c("\033[97m")
SOFT = _c("\033[38;5;245m")
DIM = _c("\033[38;5;240m")
OK = _c("\033[38;5;46m")
WARN = _c("\033[38;5;220m")
FAIL = _c("\033[38;5;196m")
RESET = _c("\033[0m")
BOLD = _c("\033[1m")

# Cell column indices
COL_SWARM = 0
COL_LOOP = 1
COL_PRIORITY = 2
_COLS = (COL_SWARM, COL_LOOP, COL_PRIORITY)
_COL_LABELS = {COL_SWARM: "Swarm", COL_LOOP: "Loop", COL_PRIORITY: "Priority"}

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

    Tokens: UP/DOWN/LEFT/RIGHT/ENTER/SPACE/TAB/ESC/BACKSPACE/HOME/END
    or single printable chars (lowercased). Polls kbhit() with sleeps so
    SIGINT (Ctrl-C) fires between polls -- matches sister picker behavior.
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
# Terminal helpers (delegate to eve_ui when available)
# ---------------------------------------------------------------------------

def _clear() -> None:
    if _HAS_EVE_UI:
        eve_ui.clear_screen()
        return
    if not _ANSI:
        return
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


def _header(title: str) -> None:
    if _HAS_EVE_UI:
        eve_ui.print_sub_page_header(title)
        return
    _clear()
    print()
    print(f"  {DARKP}---{RESET} {WHITE}{BOLD}{title}{RESET} {DARKP}---{RESET}")
    print()


def _footer(extra: str = "") -> None:
    if _HAS_EVE_UI:
        eve_ui.print_sub_page_footer(extra)
        return
    keys = f"{DIM}({extra}){RESET}" if extra else ""
    line = (
        f"  {DIM}---{RESET} {PURPLE}Enter){RESET} launch all   "
        f"{PURPLE}B){RESET} Back   "
        f"{PURPLE}X){RESET} Exit"
    )
    if keys:
        line = f"{line}   {keys}"
    print()
    print(line)


# ---------------------------------------------------------------------------
# Owner identity (per-user preset filtering)
# ---------------------------------------------------------------------------

def _current_owner_email() -> str:
    """Return the default account label/email so presets are owner-scoped.

    Reads claude-accounts.json -> finds account where name == default, returns
    its label (which is the "ezekielromero314@gmail.com (operator)" / "Leo
    (collaborator)" string). Falls back to "anonymous" on any failure so the
    feature degrades gracefully on a fresh checkout.
    """
    try:
        data = json.loads(ACCOUNTS_JSON.read_text(encoding="utf-8-sig"))
        default = data.get("default") or ""
        for acc in data.get("accounts", []):
            if acc.get("name") == default:
                # Prefer display_name if present (just the email), else label
                return (acc.get("display_name") or acc.get("label")
                        or default or "anonymous")
        return default or "anonymous"
    except Exception:
        return "anonymous"


# ---------------------------------------------------------------------------
# Defaults loader (from projects.json default_modes + tier)
# ---------------------------------------------------------------------------

def _load_projects_defaults() -> dict:
    """key -> { swarm: bool, loop: bool, priority: int(1-4) }."""
    out: dict[str, dict] = {}
    try:
        pj = json.loads(PROJECTS_JSON.read_text(encoding="utf-8-sig"))
        for p in pj.get("projects", []):
            k = p.get("key")
            if not k:
                continue
            dm = p.get("default_modes") or {}
            tier = int(p.get("tier", 3) or 3)
            if tier not in (1, 2, 3, 4):
                tier = 3
            out[k] = {
                "swarm": bool(dm.get("swarm", False)),
                "loop": bool(dm.get("loop", True)),
                "priority": tier,
            }
    except Exception:
        pass
    return out


# ---------------------------------------------------------------------------
# Preset I/O
# ---------------------------------------------------------------------------

def _ensure_presets_dir() -> None:
    try:
        PRESETS_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass


def _list_presets(owner_email: str) -> list[dict]:
    """Return preset summaries (dicts) filtered to the current owner.

    Each: { name, path, created_utc, owner_email, count }
    """
    _ensure_presets_dir()
    out: list[dict] = []
    try:
        for f in sorted(PRESETS_DIR.glob("*.json")):
            try:
                d = json.loads(f.read_text(encoding="utf-8-sig"))
            except Exception:
                continue
            if (d.get("owner_email") or "anonymous") != owner_email:
                continue
            out.append({
                "name": d.get("name") or f.stem,
                "path": f,
                "created_utc": d.get("created_utc") or "",
                "owner_email": d.get("owner_email") or "anonymous",
                "count": len(d.get("configs") or []),
            })
    except Exception:
        pass
    return out


def _save_preset(name: str, configs: list[dict], owner_email: str) -> Optional[Path]:
    """Atomically write a preset file. Returns the Path on success, None on fail."""
    _ensure_presets_dir()
    # Sanitize name -> filename (cp1252-safe)
    safe = "".join(c if (c.isalnum() or c in "-_") else "_" for c in name.strip())
    if not safe:
        return None
    payload = {
        "name": name,
        "owner_email": owner_email,
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "configs": [
            {
                "key": c["key"],
                "swarm": bool(c["swarm"]),
                "loop": bool(c["loop"]),
                "priority": int(c["priority"]),
            }
            for c in configs
        ],
    }
    target = PRESETS_DIR / f"{safe}.json"
    tmp = target.with_suffix(".json.tmp")
    try:
        tmp.write_text(json.dumps(payload, indent=4), encoding="utf-8")
        # Atomic-ish: replace target
        if target.exists():
            target.unlink()
        tmp.replace(target)
        return target
    except Exception:
        try:
            tmp.unlink(missing_ok=True)  # type: ignore[call-arg]
        except Exception:
            pass
        return None


def _load_preset_file(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# Inline text input (preset names)
# ---------------------------------------------------------------------------

def _read_line(prompt: str, max_len: int = 40) -> str:
    """Inline text editor. Enter confirms, ESC cancels (returns "")."""
    if not _HAS_MSVCRT:
        try:
            return input(f"  {prompt} > ").strip()
        except (EOFError, KeyboardInterrupt):
            return ""
    buf: list[str] = []
    sys.stdout.write(f"\n  {WHITE}{prompt}{RESET} > ")
    sys.stdout.flush()
    while True:
        while True:
            try:
                if msvcrt.kbhit():
                    ch = msvcrt.getwch()
                    break
                time.sleep(0.05)
            except KeyboardInterrupt:
                sys.exit(0)
        if ch == "\x03":
            sys.exit(0)
        if ch in ("\r", "\n"):
            sys.stdout.write("\n")
            sys.stdout.flush()
            return "".join(buf).strip()
        if ch == "\x1b":
            sys.stdout.write("\n")
            sys.stdout.flush()
            return ""
        if ch == "\x08":  # backspace
            if buf:
                buf.pop()
                sys.stdout.write("\b \b")
                sys.stdout.flush()
            continue
        if ch in ("\x00", "\xe0"):
            try:
                msvcrt.getwch()  # consume extended
            except KeyboardInterrupt:
                sys.exit(0)
            continue
        if ch.isprintable() and len(buf) < max_len:
            buf.append(ch)
            sys.stdout.write(ch)
            sys.stdout.flush()


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def _cell_text(c: dict, col: int) -> str:
    if col == COL_SWARM:
        return "[x]" if c["swarm"] else "[ ]"
    if col == COL_LOOP:
        return "[x]" if c["loop"] else "[ ]"
    if col == COL_PRIORITY:
        return f"{c['priority']}"
    return "?"


def _render(configs: list[dict], cur_row: int, cur_col: int,
            tick: int, msg: Optional[str] = None) -> None:
    n = len(configs)
    _header(f"Configure {n} project{'s' if n != 1 else ''}")

    # RKOJ-ELENO :: 2026-05-25T01:15Z :: operator hard-canonical *"centered
    # menu styling applied to every sub-page"* (image #61 / #62). Grid body
    # (header + rows + actions hint) now block-centers via eve_ui.center_block.
    body: list[str] = []
    body.append(f"{DIM}{'#':<3}{'Project':<24}{'Swarm':<8}{'Loop':<7}{'Priority':<10}{RESET}")
    body.append(f"{DIM}{'-' * 52}{RESET}")

    for ri, c in enumerate(configs):
        # Build the colored cell triple
        cells = []
        for col in _COLS:
            text = _cell_text(c, col)
            is_focus = (ri == cur_row and col == cur_col)
            if is_focus:
                cells.append(f"{BOLD}{BRIGHTP}{text}{RESET}")
            else:
                cells.append(f"{WHITE}{text}{RESET}")

        idx = f"{ri + 1:<3}"
        proj = c["display"][:22]
        proj_pad = proj + " " * max(0, 24 - len(proj))
        swarm_pad = 8 - 3
        loop_pad = 7 - 3
        pri_pad = 10 - len(_cell_text(c, COL_PRIORITY))

        line = (f"{DIM}{idx}{RESET}{WHITE}{proj_pad}{RESET}"
                f"{cells[0]}{' ' * swarm_pad}"
                f"{cells[1]}{' ' * loop_pad}"
                f"{cells[2]}{' ' * pri_pad}")

        if ri == cur_row and _HAS_EVE_UI:
            body.append(eve_ui.highlight_row(line, True, tick=tick, bar_width=64))
        elif ri == cur_row:
            body.append(f"{BRIGHTP}>{RESET} {line}")
        else:
            body.append(f"  {line}")

    body.append("")
    body.append(f"{WHITE}Actions:{RESET}")
    body.append(f"{PURPLE}Space{RESET}    toggle current cell")
    body.append(f"{PURPLE}Tab{RESET}      next field within row")
    body.append(f"{PURPLE}Arrows{RESET}   move cell")
    body.append(f"{PURPLE}S{RESET}        swarm-ALL  [y/n] auto-fill")
    body.append(f"{PURPLE}L{RESET}        loop-ALL   [y/n] auto-fill")
    body.append(f"{PURPLE}P 1-4{RESET}    priority-ALL  set")
    body.append(f"{PURPLE}D{RESET}        load DEFAULTS from projects.json")
    body.append(f"{PURPLE}R{RESET}        load SAVED PRESET")
    body.append(f"{PURPLE}W{RESET}        save current as PRESET (named)")

    if msg:
        body.append("")
        body.append(f"{DIM}{msg}{RESET}")

    if _HAS_EVE_UI:
        for ln in eve_ui.center_block(body, width=72):
            print(ln)
    else:
        for ln in body:
            print(f"  {ln}")

    _footer("Enter) launch all   B) Back to picker   X) Exit")


# ---------------------------------------------------------------------------
# Bulk auto-fill helpers
# ---------------------------------------------------------------------------

def _swarm_all(configs: list[dict], value: bool) -> None:
    for c in configs:
        c["swarm"] = value


def _loop_all(configs: list[dict], value: bool) -> None:
    for c in configs:
        c["loop"] = value


def _priority_all(configs: list[dict], value: int) -> None:
    if value not in (1, 2, 3, 4):
        return
    for c in configs:
        c["priority"] = value


def _apply_defaults(configs: list[dict]) -> None:
    defaults = _load_projects_defaults()
    for c in configs:
        d = defaults.get(c["key"])
        if not d:
            continue
        c["swarm"] = d["swarm"]
        c["loop"] = d["loop"]
        c["priority"] = d["priority"]


def _apply_preset(configs: list[dict], preset: dict) -> int:
    """Overlay preset's per-key swarm/loop/priority. Returns count of rows touched."""
    by_key = {entry.get("key"): entry for entry in preset.get("configs", [])}
    touched = 0
    for c in configs:
        e = by_key.get(c["key"])
        if not e:
            continue
        c["swarm"] = bool(e.get("swarm", c["swarm"]))
        c["loop"] = bool(e.get("loop", c["loop"]))
        try:
            p = int(e.get("priority", c["priority"]))
            if p in (1, 2, 3, 4):
                c["priority"] = p
        except Exception:
            pass
        touched += 1
    return touched


# ---------------------------------------------------------------------------
# Preset chooser sub-page (arrow-pick a saved preset, ESC to cancel)
# ---------------------------------------------------------------------------

def _pick_preset(owner_email: str) -> Optional[Path]:
    presets = _list_presets(owner_email)
    if not presets:
        return None
    cursor = 0
    tick = 0
    while True:
        _header(f"Load preset ({owner_email})")
        if not presets:
            print(f"  {WARN}(no presets saved for this owner){RESET}")
            _footer("B) back")
            k = _read_key()
            if k in ("b", "ESC", "ENTER", ""):
                return None
            continue
        for i, p in enumerate(presets):
            label = (f"  {WHITE}{p['name']:<24}{RESET}  "
                     f"{DIM}{p['count']} projects   {p['created_utc']}{RESET}")
            if i == cursor and _HAS_EVE_UI:
                print(eve_ui.highlight_row(label, True, tick=tick, bar_width=64))
            elif i == cursor:
                print(f"  {BRIGHTP}>{RESET} {label}")
            else:
                print(f"    {label}")
        _footer("Enter) load   B) back   X) exit")
        k = _read_key()
        tick += 1
        if k == "UP":
            cursor = (cursor - 1) % len(presets)
        elif k == "DOWN":
            cursor = (cursor + 1) % len(presets)
        elif k == "ENTER":
            return presets[cursor]["path"]
        elif k in ("b", "ESC", "BACKSPACE"):
            return None
        elif k in ("x", "q"):
            sys.exit(0)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def show_config_grid(selected_projects: list[dict]) -> list[dict]:
    """Show the config grid for the rows passed in. Returns final configs.

    Each input row should be a dict with at least:
        key, display, agent_name, accent, default_swarm, default_loop, tier
    (matches project_picker_multiselect._load_picker_rows output schema).

    Returns:
        list[dict] of launch configs:
            { key, agent_name, accent, swarm, loop, priority }
        OR [] if operator backed out / no rows.
    """
    if not selected_projects:
        return []

    # Seed configs from defaults
    configs: list[dict] = []
    for r in selected_projects:
        tier = int(r.get("tier", 3) or 3)
        if tier not in (1, 2, 3, 4):
            tier = 3
        configs.append({
            "key": r["key"],
            "display": r.get("display") or r["key"],
            "agent_name": r.get("agent_name") or r["key"],
            "accent": r.get("accent") or "purple",
            "swarm": bool(r.get("default_swarm", False)),
            "loop": bool(r.get("default_loop", True)),
            "priority": tier,
        })

    owner_email = _current_owner_email()
    cur_row = 0
    cur_col = COL_SWARM
    tick = 0
    msg: Optional[str] = None

    while True:
        _render(configs, cur_row, cur_col, tick, msg)
        msg = None
        key = _read_key()
        tick += 1

        if key == "UP":
            cur_row = (cur_row - 1) % len(configs)
        elif key == "DOWN":
            cur_row = (cur_row + 1) % len(configs)
        elif key == "LEFT":
            i = _COLS.index(cur_col)
            cur_col = _COLS[(i - 1) % len(_COLS)]
        elif key in ("RIGHT", "TAB"):
            i = _COLS.index(cur_col)
            cur_col = _COLS[(i + 1) % len(_COLS)]
        elif key == "HOME":
            cur_row = 0
        elif key == "END":
            cur_row = len(configs) - 1
        elif key == "SPACE":
            c = configs[cur_row]
            if cur_col == COL_SWARM:
                c["swarm"] = not c["swarm"]
            elif cur_col == COL_LOOP:
                c["loop"] = not c["loop"]
            elif cur_col == COL_PRIORITY:
                c["priority"] = (c["priority"] % 4) + 1
        elif key == "ENTER":
            return [
                {
                    "key": c["key"],
                    "agent_name": c["agent_name"],
                    "accent": c["accent"],
                    "swarm": bool(c["swarm"]),
                    "loop": bool(c["loop"]),
                    "priority": int(c["priority"]),
                }
                for c in configs
            ]
        elif key in ("b", "ESC"):
            return []
        elif key in ("x", "q"):
            sys.exit(0)

        # Bulk auto-fill actions
        elif key == "s":
            ans = _read_line("swarm-ALL  [y/n]", 1)
            if ans.lower().startswith("y"):
                _swarm_all(configs, True); msg = "swarm set to YES on all rows"
            elif ans.lower().startswith("n"):
                _swarm_all(configs, False); msg = "swarm set to NO on all rows"
            else:
                msg = "(cancelled)"
        elif key == "l":
            ans = _read_line("loop-ALL  [y/n]", 1)
            if ans.lower().startswith("y"):
                _loop_all(configs, True); msg = "loop set to YES on all rows"
            elif ans.lower().startswith("n"):
                _loop_all(configs, False); msg = "loop set to NO on all rows"
            else:
                msg = "(cancelled)"
        elif key == "p":
            ans = _read_line("priority-ALL  [1-4]", 1)
            try:
                v = int(ans)
                if v in (1, 2, 3, 4):
                    _priority_all(configs, v)
                    msg = f"priority set to {v} on all rows"
                else:
                    msg = "(invalid priority; expected 1-4)"
            except Exception:
                msg = "(cancelled)"
        elif key == "d":
            _apply_defaults(configs)
            msg = "defaults loaded from projects.json"
        elif key == "r":
            chosen = _pick_preset(owner_email)
            if chosen:
                preset = _load_preset_file(chosen)
                if preset:
                    touched = _apply_preset(configs, preset)
                    msg = (f"loaded preset '{preset.get('name', chosen.stem)}' "
                           f"-- applied to {touched}/{len(configs)} rows")
                else:
                    msg = "(preset failed to load)"
            else:
                msg = "(no preset selected)"
        elif key == "w":
            name = _read_line("Preset name", 32)
            if name:
                path = _save_preset(name, configs, owner_email)
                if path:
                    msg = f"saved preset -> {path.name}"
                else:
                    msg = "(save failed; check filename + permissions)"
            else:
                msg = "(save cancelled)"

        # Direct row-priority shortcuts (operator power-user)
        elif key in ("1", "2", "3", "4"):
            configs[cur_row]["priority"] = int(key)


# ---------------------------------------------------------------------------
# CLI smoke
# ---------------------------------------------------------------------------

def _smoke() -> int:
    """Render the grid with 3 sample selections, exit 0 without blocking.

    The smoke path renders ONE frame to stdout (no key reads) so CI / parse-
    check can verify the layout draws cleanly. To interact, run without
    --smoke and feed real selected_projects from the picker.
    """
    sample = [
        {
            "key": "sinister-chatbot",
            "display": "Sinister Chatbot",
            "agent_name": "leo-iter-12",
            "accent": "cyan",
            "default_swarm": True,
            "default_loop": True,
            "tier": 2,
        },
        {
            "key": "sinister-kernel-apk",
            "display": "Kernel APK",
            "agent_name": "kernel-iter-3",
            "accent": "magenta",
            "default_swarm": True,
            "default_loop": True,
            "tier": 1,
        },
        {
            "key": "sinister-panel",
            "display": "Sinister Panel",
            "agent_name": "panel-iter-7",
            "accent": "purple",
            "default_swarm": False,
            "default_loop": True,
            "tier": 3,
        },
    ]
    # Build seed configs (mirror of show_config_grid seed block)
    configs = []
    for r in sample:
        configs.append({
            "key": r["key"],
            "display": r["display"],
            "agent_name": r["agent_name"],
            "accent": r["accent"],
            "swarm": bool(r["default_swarm"]),
            "loop": bool(r["default_loop"]),
            "priority": int(r["tier"]),
        })
    _render(configs, cur_row=1, cur_col=COL_SWARM, tick=0,
            msg="smoke render -- no keys read, exiting clean")
    print()
    print(f"{OK}[smoke] project_config_grid.py OK -- "
          f"owner={_current_owner_email()}{RESET}")
    print(f"{DIM}[smoke] presets dir: {PRESETS_DIR}{RESET}")
    print(f"{DIM}[smoke] eve_ui imported: {_HAS_EVE_UI}{RESET}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--smoke":
        sys.exit(_smoke())
    print("project_config_grid.py -- import-only module. Run with --smoke to demo.")
    print("Public API: show_config_grid(selected_projects: list[dict]) -> list[dict]")
