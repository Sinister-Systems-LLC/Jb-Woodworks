"""eve_picker_lib :: shared picker logic for EVE.exe + RKOJ.exe.

Author: RKOJ-ELENO :: 2026-05-23

Source-of-truth for project enumeration, agent-name / accent resolution,
multi-select parsing, and verb dispatch. Both surfaces import this module:

  * EVE.exe (standalone, ANSI-rendered console) -- automations/eve-launcher/eve.py
  * RKOJ.exe (PyQt6 in-panel overlay)             -- projects/rkoj/source/sinister_rkoj_qt/picker_overlay.py

Constraints (per plan eve-into-rkoj-integration-2026-05-23T1330Z, Section 4.4):
  L5: zero non-stdlib imports
  L6: import time < 20 ms
  L7: EVE.exe still < 300 ms cold-start after lift-shift
  L8: RKOJ picker overlay opens within 60 ms

This module is render-agnostic. Callers wrap `picker_text_rows()` / `banner_text()`
with whatever color / widget surface they own (ANSI escapes for the console,
QLabel rows for Qt, etc.).
"""
from __future__ import annotations

import colorsys
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

__version__ = "0.1.0"

SANCTUM_ROOT = Path(os.environ.get("SINISTER_SANCTUM_ROOT", r"D:\Sinister Sanctum"))
PROJECTS_JSON = SANCTUM_ROOT / "automations" / "session-templates" / "projects.json"
PREFS_JSON = SANCTUM_ROOT / "automations" / "session-templates" / "agent-prefs.json"

# Curated palette mirrors projects/rkoj/source/sinister_rkoj_qt/agents_tab.py::_PROJECT_COLORS.
# Lifted here so EVE.exe can render swatches without depending on Qt.
_PROJECT_COLORS: dict[str, str] = {
    "sanctum":             "#BF5AF2",
    "sinister-panel":      "#30D158",
    "kernel-apk":          "#FF9F0A",
    "sinister-emulator":   "#0A84FF",
    "snap-emulator-api":   "#FFCC00",
    "tiktok-emulator-api": "#FF453A",
    "bumble-emulator-api": "#FFD60A",
    "sinister-forge":      "#C39DFF",
    "sinister-mind":       "#A78BFA",
    "rkoj-workstation":    "#BF5AF2",
    "sinister-jokr":       "#5AC8FA",
    "sinister-letstext":   "#FF2D55",
    "sinister-eve":        "#BF5AF2",
    "letstext":            "#FF2D55",
    "sinister-freeze":     "#64D2FF",
    "jb-woodworks":        "#A2845E",
    "showmasters":         "#FF6482",
    "sinister-generator":  "#5E5CE6",
    "jkor":                "#FF9500",
    "sinister-snap-api-quantum": "#64D2FF",
    "rkoj":                "#BF5AF2",
}


@dataclass
class PickerRow:
    index: int
    key: str
    display: str
    tag: str
    agent_name: str
    accent: str
    is_default: bool
    customized: bool
    project_color: str


@dataclass
class PickerState:
    rows: list[PickerRow]
    default_key: str
    mcp: int
    bots: int
    boot_ms: int


@dataclass
class PickResult:
    verb: str
    keys: list[str] = field(default_factory=list)
    raw: str = ""


@dataclass
class AgentModes:
    swarm: bool = False
    loop: bool = False
    loop_interval_s: int = 0


# ---------------------------------------------------------------------------
# Filesystem readers (utf-8-sig handles both BOM + non-BOM transparently)
# ---------------------------------------------------------------------------

def read_projects() -> dict:
    """Read projects.json. Raises FileNotFoundError if missing, JSONDecodeError if malformed."""
    return json.loads(PROJECTS_JSON.read_text(encoding="utf-8-sig"))


def read_prefs() -> Optional[dict]:
    """Read agent-prefs.json; return None if missing or malformed (non-fatal)."""
    if not PREFS_JSON.exists():
        return None
    try:
        return json.loads(PREFS_JSON.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def visible_projects(projects_json: dict) -> list[dict]:
    """Honor the picker.visible_keys ordering. Falls back to all projects if not set."""
    by_key = {p["key"]: p for p in projects_json.get("projects", [])}
    visible_keys = (projects_json.get("picker") or {}).get("visible_keys") or list(by_key)
    return [by_key[k] for k in visible_keys if k in by_key]


# ---------------------------------------------------------------------------
# Per-project agent / accent / color
# ---------------------------------------------------------------------------

def get_agent_name(key: str, prefs: Optional[dict]) -> str:
    if prefs and (entry := (prefs.get("per_project") or {}).get(key)):
        return entry.get("agent_name") or key
    return key


def get_accent(key: str, prefs: Optional[dict]) -> str:
    if prefs and (entry := (prefs.get("per_project") or {}).get(key)):
        return entry.get("accent_color") or "purple"
    return "purple"


def project_color(key: str) -> str:
    """Stable hex color per project. Curated palette + deterministic HSV-from-hash fallback."""
    if key in _PROJECT_COLORS:
        return _PROJECT_COLORS[key]
    h = (abs(hash(key)) % 360) / 360.0
    r, g, b = colorsys.hsv_to_rgb(h, 0.55, 0.95)
    return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"


# ---------------------------------------------------------------------------
# Environment counts (MCP servers + bot definitions)
# ---------------------------------------------------------------------------

def count_mcp() -> int:
    for cand in (Path.home() / ".claude" / ".mcp.json", Path.home() / ".claude.json"):
        if not cand.exists():
            continue
        try:
            data = json.loads(cand.read_text(encoding="utf-8"))
            n = len(data.get("mcpServers") or {})
            if n:
                return n
        except Exception:
            continue
    return 0


def count_bots() -> int:
    bot_dir = Path(r"D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\agents")
    if not bot_dir.exists():
        return 0
    return sum(1 for _ in bot_dir.iterdir() if _.is_dir())


# ---------------------------------------------------------------------------
# Picker state assembly
# ---------------------------------------------------------------------------

def build_picker_state(boot_ms: int = 0,
                       projects_json: Optional[dict] = None,
                       prefs: Optional[dict] = None) -> PickerState:
    """Assemble PickerState from disk (or from caller-injected JSON for tests)."""
    pj = projects_json if projects_json is not None else read_projects()
    pf = prefs if prefs is not None else read_prefs()
    raw_rows = visible_projects(pj)
    default_key = pj.get("default") or "sanctum"
    rows: list[PickerRow] = []
    for i, p in enumerate(raw_rows, 1):
        key = p["key"]
        agent = get_agent_name(key, pf)
        accent = get_accent(key, pf)
        rows.append(PickerRow(
            index=i,
            key=key,
            display=p.get("display") or key,
            tag=(p.get("tag") or "")[:60],
            agent_name=agent,
            accent=accent,
            is_default=(key == default_key),
            customized=(agent != key) or (accent != "purple"),
            project_color=project_color(key),
        ))
    return PickerState(
        rows=rows,
        default_key=default_key,
        mcp=count_mcp(),
        bots=count_bots(),
        boot_ms=boot_ms,
    )


# ---------------------------------------------------------------------------
# Multi-select + verb resolution
# ---------------------------------------------------------------------------

def parse_multi(pick: str, max_n: int) -> list[int]:
    """Parse '1,3,5' or '1-3' or '1,3-5,7' -> sorted unique 1-based indices.

    Returns [] when input is not multi-select (single token, empty, malformed).
    """
    pick = pick.strip()
    if "," not in pick and "-" not in pick:
        return []
    out: set[int] = set()
    for part in pick.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            try:
                a, b = (int(x.strip()) for x in part.split("-", 1))
            except ValueError:
                return []
            if a > b:
                a, b = b, a
            for i in range(a, b + 1):
                if 1 <= i <= max_n:
                    out.add(i)
        else:
            try:
                i = int(part)
            except ValueError:
                return []
            if 1 <= i <= max_n:
                out.add(i)
    return sorted(out)


_VERB_LETTERS: dict[str, str] = {
    "g": "general",
    "a": "auto-resume",
    "n": "new",
    "r": "rename",
    "k": "clear",
    "s": "autonomy",
    "f": "full",
    "q": "quit",
}


def resolve_pick(raw: str, state: PickerState) -> PickResult:
    """Resolve a raw user selection into a PickResult.

    Verbs:
        numeric       - single 1-based index into state.rows
        multi         - 1,3,5 or 1-3 (>=2 indices)
        default       - empty input -> state.default_key
        general / auto-resume / new / rename / clear / autonomy / full / quit
        unknown       - anything else
    """
    t = (raw or "").strip().lower()
    max_n = len(state.rows)

    if not t:
        return PickResult(verb="default", keys=[state.default_key], raw=raw)

    multi = parse_multi(t, max_n)
    if len(multi) >= 2:
        return PickResult(
            verb="multi",
            keys=[state.rows[i - 1].key for i in multi],
            raw=raw,
        )

    if t in _VERB_LETTERS:
        verb = _VERB_LETTERS[t]
        keys = ["general"] if verb == "general" else []
        return PickResult(verb=verb, keys=keys, raw=raw)

    # Long-form aliases the EVE picker honored historically
    aliases = {"quit": "quit", "exit": "quit", "rename": "rename",
               "clear": "clear", "setup": "autonomy", "autonomy": "autonomy"}
    if t in aliases:
        return PickResult(verb=aliases[t], keys=[], raw=raw)

    if t.isdigit():
        idx = int(t)
        if 1 <= idx <= max_n:
            return PickResult(verb="numeric", keys=[state.rows[idx - 1].key], raw=raw)
        return PickResult(verb="unknown", keys=[], raw=raw)

    return PickResult(verb="unknown", keys=[], raw=raw)


# ---------------------------------------------------------------------------
# Render helpers (return plain text rows; callers add ANSI / Qt formatting)
# ---------------------------------------------------------------------------

def banner_text(state: PickerState) -> list[str]:
    """Return the banner block as a list of plain-text lines.

    Callers (eve.py / picker_overlay.py) wrap each line with the appropriate
    color escape codes or QLabel styling.
    """
    return [
        "     E V E       // jcode-speed launcher",
        "-" * 60,
        f"server Sanctum    client EVE",
        f"model  claude-opus-4-7[1m]   speed turbo   token compact",
        f"boot   {state.boot_ms} ms     mcp:{state.mcp}   bots:{state.bots}   --skip-perms",
        "-" * 60,
    ]


def picker_text_rows(state: PickerState) -> list[str]:
    """Plain-text picker rows. Caller adds color + layout."""
    out: list[str] = ["Pick a project", "-" * 60]
    for r in state.rows:
        marker = "*" if r.is_default else " "
        line = f"{marker} {r.index:2}) {r.display:<22} {r.tag:<36}"
        if r.customized:
            line += f"  [{r.agent_name} / {r.accent}]"
        out.append(line)
    out.append("-" * 60)
    out.append("G) General      A) Auto-Resume   N) New Project   R) Rename + Color")
    out.append("K) Clear ctx    S) Autonomy      F) Full picker   Q) Quit")
    out.append("    multi-select: 1,3,5 or 1-3")
    out.append("-" * 60)
    return out


# ---------------------------------------------------------------------------
# Agent-mode env-var read (mirrors EVE.exe's SINISTER_EVE_SWARM / _LOOP)
# ---------------------------------------------------------------------------

def prompt_agent_modes_from_env() -> AgentModes:
    """Read swarm/loop intent from the environment. RKOJ chips read the same vars."""
    swarm = os.environ.get("SINISTER_EVE_SWARM", "").strip() == "1"
    loop = os.environ.get("SINISTER_EVE_LOOP", "").strip() == "1"
    try:
        loop_interval_s = int(os.environ.get("SINISTER_EVE_LOOP_INTERVAL_S", "0").strip() or "0")
    except ValueError:
        loop_interval_s = 0
    return AgentModes(swarm=swarm, loop=loop, loop_interval_s=loop_interval_s)
