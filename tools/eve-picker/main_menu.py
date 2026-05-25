"""main_menu.py :: EVE.exe top-level menu (centered, two-column layout).

Author: RKOJ-ELENO :: 2026-05-24

Operator directive 2026-05-24T22:25Z: *"yo wtf this looks like shit and this
is the second menu. fix all this up"*. Prior layout was misaligned: hero OK
but menu rows had inconsistent indents, inline parenthetical hints scattered,
'K) Kill Fleet' floated, footer was duplicated. This rewrite enforces:

  * Hero centered per line (term-width aware via os.get_terminal_size)
  * Animation band centered + tick-driven (jcode rainbow shimmer)
  * Menu rows in strict two-column layout:
        KEY)  Title              description
    title-start col = 6, description-start col = 28 (visible-width).
  * Highlighted row uses BRIGHTP/WHITE inversion (no '>' arrow prefix)
  * Single DIM footer line (Ctrl-C / shortcut help merged)

Per `_shared-memory/knowledge/eve-ui-uniformity-doctrine-2026-05-24.md`:
HEADER (---title---) + BODY + FOOTER (---shortcuts---) canonical layout.
Only canonical color tokens (PURPLE / WHITE / DIM / DARKP / BRIGHTP / SOFT
/ OK / WARN). No new tokens introduced.

Composes with:
  * eve_picker_lib.count_mcp / count_bots
  * jcode_animation.render_animation_frame (sister-B owns the module)
  * eve.py main() injects callbacks={resume,auto_resume,...} via
    show_main_menu(callbacks=...). Defaults are friendly no-op stubs.

Smoke test: `python main_menu.py --smoke` renders one full frame (header +
animation tick 0 + menu + footer) and exits 0 without any input loop.
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Callable, Optional

__version__ = "0.3.0"

# RKOJ-ELENO :: 2026-05-24T22:10Z :: operator "i cannoot close eve exe. it wont close".
# RKOJ-ELENO :: 2026-05-25T02:15Z :: operator "and now it wont fucking close" — escalate.
# Two-strike rule: 1st Ctrl-C tries clean sys.exit; 2nd within 2s does os._exit(0)
# (nuclear — bypasses any hung daemon thread, blocked subprocess, atexit handler).
# X-key from menu also routes to os._exit(0) per operator hard-canonical.
_LAST_SIGINT_AT: list[float] = [0.0]

def _eve_sigint(*_args) -> None:
    try:
        sys.stdout.write("\n  [EVE] Ctrl-C received - exiting cleanly. (press Ctrl-C again to force-kill)\n")
        sys.stdout.flush()
    except Exception:
        pass
    now = time.time()
    if (now - _LAST_SIGINT_AT[0]) < 2.0:
        # Double-tap within 2s -> nuke
        os._exit(0)
    _LAST_SIGINT_AT[0] = now
    sys.exit(0)

try:
    signal.signal(signal.SIGINT, _eve_sigint)
except (ValueError, OSError):
    pass

# RKOJ-ELENO :: 2026-05-25T02:15Z :: cross-page navigation letters. Sub-pages
# (account_manager / tools_menu / etc) check this set and on receiving any of
# these letters set os.environ["_EVE_NAV_TO"] + return; main_menu loop pops the
# env var after fn() returns and re-dispatches that letter immediately.
# Operator: "i need allow flows to allow for unlimited use. meaning i can keep
# doing thigns here going to all pages etc". Now any sub-page lets operator
# jump straight to another top-level surface without bouncing through main.
NAV_LETTERS = {"r", "a", "g", "t", "n", "m", "w", "l"}

# RKOJ-ELENO :: 2026-05-24T22:30Z :: Windows cp1252 console choked on the
# middle-dot (U+00B7) and bullet-operator (U+2219) glyphs the animation +
# divider strings use. Force stdout to UTF-8 best-effort so the renderer
# never crashes mid-frame. Falls back silently on platforms that don't
# expose reconfigure() (Python <3.7) or non-TextIOWrapper stdout (piped).
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
except Exception:
    pass

# ---------------------------------------------------------------------------
# Path probe (mirrors eve.py SANCTUM_ROOT logic; standalone-importable)
# ---------------------------------------------------------------------------

def _sanctum_root() -> Path:
    env = os.environ.get("SINISTER_SANCTUM_ROOT") or os.environ.get("SANCTUM_ROOT")
    if env and Path(env).exists():
        return Path(env)
    for cand in (r"D:\Sinister Sanctum", r"C:\Sinister Sanctum"):
        p = Path(cand)
        if p.exists():
            return p
    return Path.cwd()


SANCTUM_ROOT = _sanctum_root()
ACCOUNTS_JSON = SANCTUM_ROOT / "_shared-memory" / "claude-accounts.json"
HEARTBEAT_DIR = SANCTUM_ROOT / "_shared-memory" / "heartbeats"
# Sinister LINK :: cross-machine pairing state file. Read on every main-menu
# render so the header reflects unlinked/linked/STALE in real time. The file
# is committed via sanctum-auto-push so both peers converge to the same view.
LINK_STATE_JSON = SANCTUM_ROOT / "_shared-memory" / "sinister-link-state.json"
LINK_HEALTH_JSON = SANCTUM_ROOT / "_shared-memory" / "sinister-link-health.json"

# RKOJ-ELENO :: 2026-05-24T23:20Z :: operator "its flickering stop it. and why
# do i have like to home pages." Module-level selected index drives arrow-key
# nav (replaces ad-hoc highlight param). Render uses cursor-home (no full
# clear-screen flush) to eliminate flicker + duplicate-render artifacts.
_SELECTED_IDX = 0
_FIRST_RENDER = True  # first paint clears whole screen; subsequent paints home-only


# ---------------------------------------------------------------------------
# ANSI palette (canonical tokens only; NO_COLOR / TERM=dumb aware)
# ---------------------------------------------------------------------------

def _ansi_on() -> bool:
    if os.environ.get("NO_COLOR", "").strip():
        return False
    term = os.environ.get("TERM", "").strip().lower()
    if term in ("dumb",) and os.name != "nt":
        return False
    return True


_ANSI = _ansi_on()


def _c(seq: str) -> str:
    return seq if _ANSI else ""


# Canonical tokens (matches eve-ui-uniformity-doctrine table)
PURPLE = _c("\033[38;5;141m")   # shortcut keys, accent
DARKP = _c("\033[38;5;91m")     # divider rules
BRIGHTP = _c("\033[38;5;177m")  # active / highlighted row
WHITE = _c("\033[97m")          # primary content + titles
SOFT = _c("\033[38;5;245m")     # labels
DIM = _c("\033[38;5;240m")      # metadata, less-important
OK = _c("\033[38;5;46m")        # success
WARN = _c("\033[38;5;220m")     # mid / warning
RESET = _c("\033[0m")


# ---------------------------------------------------------------------------
# Term-width helpers (ANSI-aware centering)
# ---------------------------------------------------------------------------

def _term_cols() -> int:
    try:
        return max(60, os.get_terminal_size().columns)
    except (OSError, ValueError):
        return 80


def _strip_ansi(s: str) -> str:
    out = []
    i = 0
    while i < len(s):
        if s[i] == "\033" and i + 1 < len(s) and s[i + 1] == "[":
            j = i + 2
            while j < len(s) and s[j] not in "ABCDEFGHJKSTfmnsulh":
                j += 1
            i = j + 1
            continue
        out.append(s[i])
        i += 1
    return "".join(out)


def _visible_len(s: str) -> int:
    return len(_strip_ansi(s))


def _center(line: str, width: int) -> str:
    pad = max(0, (width - _visible_len(line)) // 2)
    return " " * pad + line


# ---------------------------------------------------------------------------
# Account + count probes (cheap, swallow failures)
# ---------------------------------------------------------------------------

def _active_account_label() -> str:
    try:
        data = json.loads(ACCOUNTS_JSON.read_text(encoding="utf-8-sig"))
        default = data.get("default") or "operator"
        for acct in data.get("accounts", []):
            if acct.get("name") == default:
                return acct.get("label") or default
        return default
    except Exception:
        return "operator"


def _count_live_agents(window_s: int = 300) -> int:
    if not HEARTBEAT_DIR.exists():
        return 0
    now = time.time()
    n = 0
    try:
        for p in HEARTBEAT_DIR.iterdir():
            if p.suffix.lower() not in (".json", ".beat"):
                continue
            try:
                if (now - p.stat().st_mtime) < window_s:
                    n += 1
            except OSError:
                continue
    except OSError:
        return 0
    return n


def _eve_version() -> str:
    try:
        sys.path.insert(0, str(SANCTUM_ROOT / "automations" / "eve-launcher"))
        import eve  # type: ignore
        return getattr(eve, "EVE_VERSION", "0.4.6")
    except Exception:
        return "0.4.6"


def _counts() -> tuple[int, int]:
    try:
        sys.path.insert(0, str(SANCTUM_ROOT / "tools" / "eve-picker"))
        from eve_picker_lib import count_mcp, count_bots  # type: ignore
        return count_mcp(), count_bots()
    except Exception:
        return 0, 0


# ---------------------------------------------------------------------------
# Hero block (centered, one line each)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# ASCII-art EVE title (5-row block letters, cp1252-safe via box-drawing chars)
# RKOJ-ELENO :: 2026-05-24T23:30Z :: operator "i want in biger letters EVE."
# Box-drawing chars U+2588 / U+2554..U+255D are all cp437/cp1252-safe and
# render cleanly in Windows cmd + git-bash + Windows Terminal.
# ---------------------------------------------------------------------------

_EVE_ASCII = [
    "███████╗ ██╗   ██╗ ███████╗",
    "██╔════╝ ██║   ██║ ██╔════╝",
    "█████╗   ██║   ██║ █████╗  ",
    "██╔══╝   ╚██╗ ██╔╝ ██╔══╝  ",
    "███████╗  ╚████╔╝  ███████╗",
    "╚══════╝   ╚═══╝   ╚══════╝",
]


def _eve_ascii_colored() -> list[str]:
    """Render the EVE ASCII title with a PURPLE -> BRIGHTP gradient per row."""
    # Top-to-bottom gradient: deep -> bright -> deep again for shimmer feel
    palette = [DARKP, PURPLE, BRIGHTP, BRIGHTP, PURPLE, DARKP]
    return [f"{palette[i]}{row}{RESET}" for i, row in enumerate(_EVE_ASCII)]


# ---------------------------------------------------------------------------
# Glowing orb line — connected-account-count visualization.
# RKOJ-ELENO :: 2026-05-24T23:30Z :: operator "include the connected account
# count with like a glowing orb system that looks cool."
# ---------------------------------------------------------------------------

# Pulse palette (cycled per tick) — bright purple -> white-hot -> green -> back
_ORB_PULSE = [BRIGHTP, WHITE, OK, BRIGHTP, PURPLE, DARKP]


def _connected_account_count() -> int:
    """Count accounts with enabled=True in claude-accounts.json (cheap, swallows errors)."""
    try:
        a = json.loads(ACCOUNTS_JSON.read_text(encoding="utf-8-sig", errors="replace"))
        return sum(1 for x in a.get("accounts", []) if x.get("enabled", False))
    except Exception:
        return 0


def _orb_line(connected: int, tick: int) -> str:
    """Render N glowing orbs (one per connected account), each phase-offset.

    The pulse moves through the orb row left-to-right for a 'flowing' effect.
    Single orb falls back to a simple pulse. Cp1252-safe: orb glyph is U+25CF
    (BLACK CIRCLE, in WGL4 / standard Windows fonts).
    """
    if connected <= 0:
        return f"{DIM}{chr(0x25CB)}  no accounts connected{RESET}"
    orbs: list[str] = []
    for i in range(connected):
        phase = (tick // 2 + i) % len(_ORB_PULSE)
        color = _ORB_PULSE[phase]
        orbs.append(f"{color}{chr(0x25CF)}{RESET}")
    label = "account" if connected == 1 else "accounts"
    return f"  {' '.join(orbs)}  {WHITE}{connected}{RESET} {SOFT}{label} connected{RESET}"


def _link_header_line() -> str:
    """Render the 'Sinister LINK :: <state>' header line.

    RKOJ-ELENO :: 2026-05-25 :: operator hard-canonical *"place iut in even
    anmd have it in the main header in ready saying sinister LINK unlinked
    to eleno"*. 4 visual states (color-coded):
      unlinked              -> WARN (orange) + '(L to link)'
      linked to <peer>      -> OK (green) with last-sync age
      linked to <peer> STALE-> FAIL (red) when peer unreachable >10min
      linking               -> PURPLE (transient; not currently produced)

    Reads sinister-link-state.json (cheap; <1 KB). Falls through silently
    on parse error -> shows 'unlinked' so the menu never blocks on a corrupt
    state file.
    """
    try:
        if not LINK_STATE_JSON.exists():
            return (f"{WARN}Sinister LINK :: unlinked{RESET}  "
                    f"{DIM}(press {RESET}{PURPLE}L{RESET}{DIM} to pair with peer){RESET}")
        s = json.loads(LINK_STATE_JSON.read_text(encoding="utf-8-sig", errors="replace"))
        peer = (s.get("peer") or {}).get("display") or (s.get("peer") or {}).get("name") or "?"
        # 'invited' is the post-GenerateInvite, pre-AcceptInvite stub state.
        # Operator hard-canonical 2026-05-25T07:08:40Z UX fix.
        state_val = s.get("state") or ""
        if state_val == "invited":
            peer_label = peer if peer != "?" else "peer"
            return (f"{PURPLE}Sinister LINK :: invited{RESET}  "
                    f"{DIM}(awaiting acceptance from {peer_label}; press {RESET}{PURPLE}L{RESET}{DIM} for status){RESET}")
        last = s.get("last_sync_utc") or ""
        if not last:
            return (f"{PURPLE}Sinister LINK :: linked to {peer}{RESET}  "
                    f"{DIM}(no sync yet){RESET}")
        # Parse age and color-code
        from datetime import datetime, timezone
        try:
            dt = datetime.fromisoformat(last.replace("Z", "+00:00"))
            age_s = int((datetime.now(timezone.utc) - dt).total_seconds())
        except Exception:
            age_s = 99999
        if age_s < 60:
            word = f"{age_s}s"
        elif age_s < 3600:
            word = f"{age_s // 60}m"
        else:
            word = f"{age_s // 3600}h"
        if age_s > 600:
            return (f"{WARN}Sinister LINK :: linked to {peer} "
                    f"({WARN}STALE {word}{RESET}{WARN}){RESET}  "
                    f"{DIM}(L for diagnostics){RESET}")
        return (f"{OK}Sinister LINK :: linked to {peer}{RESET}  "
                f"{DIM}(last sync {word} ago){RESET}")
    except Exception:
        return f"{WARN}Sinister LINK :: unlinked{RESET}"


def _hero_lines() -> list[str]:
    mcp, bots = _counts()
    acct = _active_account_label()
    live = _count_live_agents()
    ver = _eve_version()
    today = time.strftime("%Y-%m-%d")
    live_word = "agent" if live == 1 else "agents"
    connected = _connected_account_count()
    lines: list[str] = []
    # Big ASCII EVE title (6 rows, gradient-colored)
    lines.extend(_eve_ascii_colored())
    lines.append("")
    # Sinister LINK header (operator hard-canonical 2026-05-25): rendered
    # FIRST after the EVE banner so it's the most-visible status indicator.
    lines.append(_link_header_line())
    # Server / client / version / path / acct (no 'acct:' label per operator 2026-05-24T23:30Z)
    lines.extend([
        f"{SOFT}server:{RESET} {WHITE}Sanctum{RESET}    {SOFT}client:{RESET} {WHITE}EVE{RESET}",
        f"{PURPLE}EVE-OPUS-4.7{RESET}  {DIM}·{RESET}  {DIM}v{ver}{RESET}",
        f"{SOFT}{SANCTUM_ROOT}{RESET}",
        f"{WHITE}{acct}{RESET}",
        f"{SOFT}mcp:{RESET} {OK}{mcp}{RESET}   "
        f"{SOFT}bots:{RESET} {OK}{bots}{RESET}   "
        f"{SOFT}live:{RESET} {OK}{live} {live_word}{RESET}",
        _orb_line(connected, _TICK),
    ])
    return lines


# ---------------------------------------------------------------------------
# Accounts panel (ported from eve.py _render_accounts_panel)
# RKOJ-ELENO :: 2026-05-24T23:20Z :: operator "i need acocunts tab here as well".
# Ported (not imported) because eve.py is the entry-point and importing it
# would cause a circular import. Reads claude-accounts.json directly. Shows
# strategy + cursor + next-up account + per-account ON rows + collapsed
# disabled summary. Compact 4-6 line block.
#
# RKOJ-ELENO :: 2026-05-25T01:36Z :: operator screenshot #67 verbatim header
# said "1/4 enabled" (FAKE cap; placeholder slots already removed from JSON),
# per-acct row said "100% used" (FAKE; today/50 hardcoded math overflowed to
# 100% with 62 spawns), and "+ 3 disabled: Leo + 2 empty" rendered slots that
# don't exist in JSON. Operator: "review how jcode track their usage or what
# we need to do and fucking do it". Fix: drop the /total denominator (no
# cap), drop the today/50 fake percent, prefer real headers from
# anthropic-usage-probe.ps1 when available, show LINKED/UNLINKED tags, and
# don't synthesize "__slot__" entries. Mirrors the corrected eve.py renderer.
# ---------------------------------------------------------------------------

# Process-level cache so we don't re-spawn the PS1 probe every render.
_ACCT_PROBE_CACHE: dict[str, object] = {"ts": 0.0, "live": None}


def _probe_live_usage_cached() -> dict | None:
    """Call anthropic-usage-probe.ps1 at most once per 60s; return parsed JSON
    or None. Bounded 3s subprocess timeout so a slow probe never freezes the
    main menu render (matches the eve.py P0 freeze fix 2026-05-25T00:15Z).
    """
    probe = SANCTUM_ROOT / "automations" / "anthropic-usage-probe.ps1"
    if not probe.exists():
        return None
    now_ts = time.time()
    cache_ts = float(_ACCT_PROBE_CACHE.get("ts", 0.0))  # type: ignore[arg-type]
    if (now_ts - cache_ts) < 60.0 and cache_ts > 0:
        return _ACCT_PROBE_CACHE.get("live")  # type: ignore[return-value]
    live: dict | None = None
    try:
        r = subprocess.run(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
             "-File", str(probe), "-Mode", "Json",
             "-Slot", "default", "-CacheSec", "60"],
            capture_output=True, text=True, timeout=3, errors="replace",
        )
        if r.returncode == 0 and r.stdout:
            try:
                live = json.loads(r.stdout)
            except Exception:
                live = None
    except Exception:
        live = None  # includes TimeoutExpired
    _ACCT_PROBE_CACHE["ts"] = now_ts
    _ACCT_PROBE_CACHE["live"] = live
    return live


def _accounts_inline_lines() -> list[str]:
    """Return rendered account-panel lines (or empty list if file missing).

    Returns lines (not print()) so main _render() can center the block.
    No /total cap. No today/50 fake percent. LINKED/UNLINKED tag per acct.
    Real % only when anthropic-usage-probe returns headers; otherwise show
    raw `spawns N today` with `(no probe)` so operator can't be misled.
    """
    out: list[str] = []
    if not ACCOUNTS_JSON.exists():
        return out
    try:
        a = json.loads(ACCOUNTS_JSON.read_text(encoding="utf-8-sig", errors="replace"))
    except Exception as e:
        return [f"{WARN}claude accounts (unreadable: {e}){RESET}"]
    strategy = a.get("rotation_strategy", "?")
    cursor = a.get("last_rotation_index", 0)
    accts = a.get("accounts", [])
    default_name = a.get("default", "")
    enabled_accts = [x for x in accts if x.get("enabled", False)]
    linked_accts = [x for x in enabled_accts if x.get("linked", False)]
    unlinked_accts = [x for x in enabled_accts if not x.get("linked", False)]

    # Compute next-up account for round-robin-strict
    next_name = ""
    if strategy == "round-robin-strict" and accts:
        n = len(accts)
        for i in range(n):
            idx = (cursor + i) % n
            cand = accts[idx]
            if cand.get("enabled", False) and not cand.get("rate_limited_until_utc"):
                next_name = cand.get("label", cand.get("name", "?"))
                break
    elif strategy == "burn-first":
        anchor = next((x for x in accts if x.get("name") == default_name and x.get("enabled", False)), None)
        if anchor:
            next_name = anchor.get("label", anchor.get("name", "?"))

    # No-cap header: total count of real accounts + breakdown chip. Format:
    #   Claude accounts (N)  M enabled (K linked, U unlinked)  strategy  next -> ...
    next_tag = f"{OK}{next_name}{RESET}" if next_name else f"{DIM}none{RESET}"
    cursor_tag = f" {DIM}c{cursor}{RESET}" if strategy == "round-robin-strict" else ""
    out.append(
        f"{WHITE}Claude accounts{RESET} {DIM}({len(accts)}){RESET}  "
        f"{BRIGHTP}{len(enabled_accts)} enabled{RESET} "
        f"{DIM}({len(linked_accts)} linked, {len(unlinked_accts)} unlinked){RESET}  "
        f"{DIM}{strategy}{RESET}{cursor_tag}  "
        f"{DIM}next ->{RESET} {next_tag}  "
        f"{DIM}[{RESET}{PURPLE}O{RESET}{DIM}]nboard{RESET}"
    )

    # Resolve one live-probe call (cached) for the default acct -- the only
    # slot anthropic-usage-probe can speak for (it reads the live OAuth cred).
    live = _probe_live_usage_cached()

    disabled_named: list[str] = []
    for acct in accts:
        name = acct.get("name", "?")
        enabled = acct.get("enabled", False)
        plan_tier = (acct.get("plan_tier") or "?").strip() or "?"
        label = acct.get("label", name)
        linked = bool(acct.get("linked", False))

        if not enabled:
            # Only render REAL disabled accounts (no synthesized empty slots).
            if label and not str(label).startswith("(unconfigured"):
                disabled_named.append(str(label))
            continue

        today = int(acct.get("successful_spawns_today", 0) or 0)
        is_default = (name == default_name)
        marker = f"{BRIGHTP}*{RESET}" if is_default else " "
        is_next = (label == next_name) if next_name else False
        arrow = f" {OK}<-NEXT{RESET}" if is_next else ""

        # LINKED/UNLINKED tag (operator hard-canonical 2026-05-25).
        if linked:
            status_tag = f"{OK}ON LINKED{RESET}"
        else:
            status_tag = f"{WARN}ON UNLINKED{RESET}"

        # Usage column -- NEVER show a fake percent. Cases (probe-first):
        # 1) default + probe ok: show REAL "5h 76%  7d 80% [MEASURED]"
        # 2) probe failed: "probe: refresh needed" or other status
        # 3) unlinked + no probe: "not logged in"
        # 4) fallback: raw spawns_today + "(no probe)"
        if is_default and live and live.get("status") == "ok":
            sess = live.get("session") or {}
            wk = live.get("weekly_all") or {}
            p5 = sess.get("pct")
            p7 = wk.get("pct")
            parts = []
            if isinstance(p5, (int, float)):
                parts.append(f"{WHITE}5h {int(p5)}%{RESET}")
            if isinstance(p7, (int, float)):
                parts.append(f"{DIM}7d {int(p7)}%{RESET}")
            measured_tag = f" {OK}[MEASURED]{RESET}" if parts else f" {OK}[MEASURED]{RESET} {DIM}headers ok{RESET}"
            usage_str = ("  ".join(parts) + measured_tag) if parts else measured_tag.lstrip()
        elif is_default and live and str(live.get("status", "")).startswith("probe-failed"):
            why = "refresh needed" if live.get("refresh_needed") else live.get("status")
            usage_str = f"{WARN}[probe: {why}]{RESET} {DIM}spawns {today} today{RESET}"
        elif not linked:
            usage_str = f"{DIM}not logged in{RESET}"
        else:
            usage_str = f"{DIM}spawns {today} today{RESET} {DIM}(no probe){RESET}"

        label_inline = f"{WHITE}{label}{RESET} {DIM}[{RESET}{PURPLE}{plan_tier}{RESET}{DIM}]{RESET}"
        out.append(
            f"{marker} {status_tag}  {label_inline}  "
            f"{usage_str}{arrow}"
        )

    if disabled_named:
        names = ", ".join(disabled_named)
        out.append(
            f"{DIM}+ {len(disabled_named)} disabled: {names} "
            f"(press {RESET}{PURPLE}O{RESET}{DIM} to onboard){RESET}"
        )
    return out


# ---------------------------------------------------------------------------
# Animation band (jcode rainbow shimmer, full-width centered, 6 rows)
# ---------------------------------------------------------------------------

_ANIM_ERR: str | None = None  # captured on first failure for visible reporting


def _animation_lines(tick: int, width: int, height: int = 6) -> list[str]:
    """Return `height` rendered animation rows.

    Calls jcode_animation.render_animation_frame(tick, width, height) which
    returns pre-rendered ANSI-colored lines exactly `width` glyphs wide.
    On failure: surfaces a visible WARN line so the operator sees WHY the
    animation is missing (was silently swallowed pre-2026-05-24 RKOJ-ELENO fix).
    """
    global _ANIM_ERR
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import jcode_animation  # type: ignore
        # Constrain to ~80% of terminal width so the band has breathing room
        anim_w = max(40, min(width - 8, 100))
        return jcode_animation.render_animation_frame(tick, width=anim_w, height=height)
    except Exception as e:
        _ANIM_ERR = f"{type(e).__name__}: {e}"
        return [f"{WARN}[animation disabled: {_ANIM_ERR}]{RESET}"]


# ---------------------------------------------------------------------------
# Two-column menu (KEY)  Title              description)
# ---------------------------------------------------------------------------

# RKOJ-ELENO :: 2026-05-25T00:20Z :: operator menu order + naming spec.
# RKOJ-ELENO :: 2026-05-25T00:30Z :: operator verbatim *"change the kill fleet
# selection here to agents"* -- restored K=Agents (singular short label) per
# the literal directive. Sister B's full sub-page (project-grouped multi-select
# manager) wires through eve.py callback key 'agents_working_with' for
# back-compat with mid-turn rename, falls back to 'agents'/'kill_fleet'.
_MENU_ITEMS: list[tuple[str, str, str]] = [
    ("R", "Resume Project",            "pick a project + spawn"),
    ("A", "Auto Resume",               "last project + last agent"),
    ("G", "General Agent",             "no project scope"),
    ("T", "Tools",                     "automations / health / mesh"),
    ("N", "New Project",               "scaffold a new lane"),
    ("M", "Account Manager",           "add / login / logout / usage"),
    ("W", "Agents I'm Working With",   "project-grouped multi-select fleet manager"),
    # RKOJ-ELENO :: 2026-05-25T06:30Z :: Sub-agent G iter22 UI audit -- L key was
    # orphaned (eve.py wired `sinister_link` callback but no menu row). Surfaced.
    ("L", "Sinister LINK",             "cross-machine pairing (leo + operator)"),
    ("X", "Exit",                      ""),
]

# Column geometry (visible-character widths, ANSI-strip aware)
# 2026-05-25T00:20Z :: bumped 18 -> 26 to fit "Agents I'm Working With" (22 chars)
# plus 4-char gap before description column. Selected-bar width also bumped.
_TITLE_WIDTH = 26  # title-start to description-start gap

# RKOJ-ELENO :: 2026-05-25T00:05Z :: operator "when we scroll through the
# selections on the eve exe i want it to have a glowing purple bar that is
# suttle that is like making it glow and i want it to like enlarge when i
# scroll through them make it all legit looking. clean in theme and speedy."
#
# Glow palette: 256-color background indices that look subtle-purple in
# mintty / windows-terminal. Pulse cycles slowly (every 4 ticks) through
# three near-shades so the bar "breathes" without flickering.
#   53 = #5f005f  deep magenta-purple (dimmest)
#   54 = #5f0087  mid Sinister purple
#   60 = #5f5f87  cool slate-purple (lightest, accent shimmer)
# RKOJ-ELENO :: 2026-05-25T00:15Z :: operator screenshot #55 -- *"no the
# highlights needs to highlight the entire thing and have a cooler effect
# to it than that shit"*. Prior impl wrapped the row text in bg but because
# each row segment carried its own SGR + final RESET, the bg only painted
# the FIRST segment (key cell). Fix: build the row as ONE concatenated
# string and wrap once -- bg now extends edge-to-edge.
# Cooler effects: (1) edge-glow vertical bars at row edges (U+258C/U+2590
# in BRIGHTP), (2) slow 2-shade pulse 53<->54 every 6 ticks, (3) bold+
# bright-white text on selected row, (4) underline for "bar" feel.
_GLOW_BG_PALETTE = (53, 54)
_EDGE_GLOW_FG = "\033[38;5;177m"  # BRIGHTP for edge bar glyphs
_EDGE_GLYPH_L = "▌"  # LEFT HALF BLOCK -- left-edge accent
_EDGE_GLYPH_R = "▐"  # RIGHT HALF BLOCK -- right-edge accent
# Width of the selected bar fill (excludes the 1-char edge glyphs each side).
# Sized to hold the longest row.
_BAR_WIDTH = 64


def _row_text(letter: str, label: str, hint: str, selected: bool) -> str:
    """Build a menu row as a SINGLE ANSI-colored string.

    Layout (visible widths): [2sp][KEY)][2sp][TITLE padded to _TITLE_WIDTH][HINT]
    All segments concatenated -> single bg wrapper paints edge-to-edge.
    """
    if selected:
        # bold + underline bright-white on selected text (pops on purple bg)
        key_color = "\033[97;1;4m"
        title_color = "\033[97;1;4m"
        hint_color = "\033[38;5;253;4m"  # light grey + underline
    else:
        key_color = PURPLE
        title_color = WHITE
        hint_color = DIM
    key = f"{key_color}{letter}){RESET}"
    title = f"{title_color}{label}{RESET}"
    title_pad = max(1, _TITLE_WIDTH - len(label))
    hint_s = f"{hint_color}{hint}{RESET}" if hint else ""
    # 2sp left indent inside the bar
    return f"  {key}  {title}{' ' * title_pad}{hint_s}"


def _highlight_row(text: str, is_selected: bool, tick: int = 0) -> str:
    """Render a menu row, wrapping the WHOLE string in bg edge-to-edge.

    Unselected rows: padded to (_BAR_WIDTH + 2) so they occupy the same
    column width as selected rows (prevents nav shift).

    Selected rows: bg-wrapped row + edge-glow glyphs in BRIGHTP. Bg pulses
    palette 53 <-> 54 every 6 ticks (slow breath, NOT strobe).
    """
    visible = _visible_len(text)
    if not is_selected:
        pad_total = max(0, _BAR_WIDTH - visible)
        # 1sp left + 1sp right matches the 1-char edge-glyph footprint
        return " " + text + " " * pad_total + " "
    if not _ANSI:
        pad_total = max(0, _BAR_WIDTH - visible)
        return f">{text}" + " " * pad_total + "<"
    bg_idx = _GLOW_BG_PALETTE[(tick // 6) % len(_GLOW_BG_PALETTE)]
    bg_code = f"\033[48;5;{bg_idx}m"
    pad_total = max(0, _BAR_WIDTH - visible)
    edge_l = f"{_EDGE_GLOW_FG}{_EDGE_GLYPH_L}{RESET}"
    edge_r = f"{_EDGE_GLOW_FG}{_EDGE_GLYPH_R}{RESET}"
    bg_block = f"{bg_code}{text}{' ' * pad_total}{RESET}"
    return f"{edge_l}{bg_block}{edge_r}"


def _menu_lines(highlight: int) -> list[str]:
    out = [
        "",
        f"{DARKP}---{RESET} {BRIGHTP}Menu{RESET} {DARKP}---{RESET}",
        "",
    ]
    for i, (letter, label, hint) in enumerate(_MENU_ITEMS):
        selected = (i == highlight)
        row_str = _row_text(letter, label, hint, selected)
        out.append(_highlight_row(row_str, selected, _TICK))
    out.append("")
    return out


def _prompt_line() -> str:
    return f"{WHITE}> pick a letter:{RESET}"


def _footer_line() -> str:
    return (
        f"{DIM}--- arrow keys + Enter, or single-letter shortcut "
        f"· Ctrl-C anywhere to quit ---{RESET}"
    )


# ---------------------------------------------------------------------------
# Render loop (clears screen, redraws hero + animation + menu + prompt + footer)
# ---------------------------------------------------------------------------

_TICK = 0  # module-level monotonic counter so the animation visibly advances

# RKOJ-ELENO :: 2026-05-25T01:36Z :: operator screenshot #66 *"more animation
# and live here"*. The render-on-event model only advances _TICK on keypress
# so the band feels static. Live partial-redraw mode rewrites JUST the
# animation band + accounts panel rows in-place (no full-screen repaint) so
# operator gets a visibly moving "river of stars" without flicker.
#
# These row trackers are updated by _render() each frame so the partial
# redraw helper knows where to position the cursor.
_ANIM_ROW_START: int = 0     # 1-based terminal row where animation band starts
_ANIM_ROW_HEIGHT: int = 6    # number of animation rows
_ACCT_ROW_START: int = 0     # 1-based terminal row where accounts panel starts
_ACCT_ROW_HEIGHT: int = 0    # number of account-panel rows
_ANIM_BAND_WIDTH: int = 0    # animation band visible width (matches _animation_lines)


def _render(highlight: int) -> None:
    """Build the entire frame in a buffer, then write it in ONE syscall.

    RKOJ-ELENO :: 2026-05-24T23:20Z :: operator "its flickering stop it. and
    why do i have like to home pages". Root cause: `\\033[2J` (clear-entire-
    screen) followed by individual print() lines caused visible white-flash
    flicker on each frame AND on slow terminals the clear + redraw could be
    interleaved with the next paint producing a "two home pages" stacking
    artifact (the previous frame's content scrolling visible below the new
    one).

    Fix: cursor-home (\\033[H) + clear-from-cursor-to-end (\\033[J), build
    the WHOLE frame in a single string buffer, write/flush ONCE. No clear-
    entire-screen, no per-line flush. First paint clears the screen one time
    to wipe the launching shell's prior output.
    """
    global _TICK, _FIRST_RENDER
    global _ANIM_ROW_START, _ANIM_ROW_HEIGHT, _ACCT_ROW_START, _ACCT_ROW_HEIGHT
    global _ANIM_BAND_WIDTH
    cols = _term_cols()
    buf: list[str] = []
    if _ANSI:
        if _FIRST_RENDER:
            # One-time full-screen clear to wipe whatever the spawning shell left
            buf.append("\033[2J\033[H")
            _FIRST_RENDER = False
        else:
            # Cursor home + clear-to-end (overwrites previous frame in place)
            buf.append("\033[H\033[J")
    # Row tracker: count terminal rows we've written so far (1-based, top=1).
    # After the initial cursor-home there's a leading "\n" newline (row 1 blank).
    row_cursor = 1
    buf.append("\n"); row_cursor += 1
    # Hero (centered per-line)
    for line in _hero_lines():
        buf.append(_center(line, cols) + "\n"); row_cursor += 1
    buf.append("\n"); row_cursor += 1
    # Animation band (each row is its own pre-centered string)
    anim = _animation_lines(_TICK, cols, height=6)
    _ANIM_ROW_START = row_cursor
    _ANIM_ROW_HEIGHT = len(anim)
    # Cache the visible band width so partial redraws keep same geometry
    _ANIM_BAND_WIDTH = max(40, min(cols - 8, 100))
    for line in anim:
        buf.append(_center(line, cols) + "\n"); row_cursor += 1
    if anim:
        buf.append("\n"); row_cursor += 1
    # Accounts panel (operator 2026-05-24T23:20Z "i need acocunts tab here")
    acct_lines = _accounts_inline_lines()
    _ACCT_ROW_START = row_cursor if acct_lines else 0
    _ACCT_ROW_HEIGHT = len(acct_lines)
    if acct_lines:
        a_max_w = max((_visible_len(ln) for ln in acct_lines), default=0)
        a_pad = " " * max(0, (cols - a_max_w) // 2)
        for ln in acct_lines:
            buf.append(a_pad + ln + "\n"); row_cursor += 1
        buf.append("\n"); row_cursor += 1
    # Menu (two-column rows, BLOCK-centered: compute widest row's visible width,
    # derive ONE left-pad, apply that same pad to every row so columns align)
    menu = _menu_lines(highlight)
    max_w = max((_visible_len(ln) for ln in menu), default=0)
    block_pad = max(0, (cols - max_w) // 2)
    pad_str = " " * block_pad
    for line in menu:
        if line == "":
            buf.append("\n")
        else:
            buf.append(pad_str + line + "\n")
    # Prompt + footer
    buf.append(_center(_prompt_line(), cols) + "\n")
    buf.append("\n")
    buf.append(_center(_footer_line(), cols) + "\n")
    buf.append("\n")
    sys.stdout.write("".join(buf))
    sys.stdout.flush()
    _TICK += 1


def _partial_animation_redraw() -> None:
    """Repaint JUST the animation band + accounts panel rows in place.

    RKOJ-ELENO :: 2026-05-25T01:36Z :: operator screenshot #66 *"more
    animation and live here"*. The live-tick loop calls this at ~5fps so
    the band visibly moves without redrawing the whole screen (which would
    flicker the hero block + menu + prompt each tick).

    Uses ANSI cursor-positioning (\\033[<row>;1H) + line-clear (\\033[2K)
    to overwrite ONLY the target rows. Saves + restores cursor with
    \\033[s / \\033[u so the operator's input cursor stays put.

    No-ops if _ANIM_ROW_START is 0 (full _render() hasn't fired yet).
    """
    global _TICK
    if not _ANSI or _ANIM_ROW_START <= 0:
        return
    cols = _term_cols()
    buf: list[str] = []
    # Save cursor so the input prompt position is preserved
    buf.append("\033[s")
    # Repaint animation band
    anim = _animation_lines(_TICK, cols, height=_ANIM_ROW_HEIGHT or 6)
    for i, line in enumerate(anim):
        # \033[<row>;1H = move to absolute row, col 1; \033[2K = clear entire line
        buf.append(f"\033[{_ANIM_ROW_START + i};1H\033[2K")
        buf.append(_center(line, cols))
    # Repaint accounts panel (has time-changing usage / counter data)
    if _ACCT_ROW_START > 0 and _ACCT_ROW_HEIGHT > 0:
        acct_lines = _accounts_inline_lines()
        # Only redraw if line count matches (otherwise geometry shifted; let
        # next full _render() reconcile).
        if len(acct_lines) == _ACCT_ROW_HEIGHT:
            a_max_w = max((_visible_len(ln) for ln in acct_lines), default=0)
            a_pad = " " * max(0, (cols - a_max_w) // 2)
            for i, ln in enumerate(acct_lines):
                buf.append(f"\033[{_ACCT_ROW_START + i};1H\033[2K")
                buf.append(a_pad + ln)
    # Restore cursor so operator's typing prompt isn't displaced
    buf.append("\033[u")
    sys.stdout.write("".join(buf))
    sys.stdout.flush()
    _TICK += 1


# ---------------------------------------------------------------------------
# Input loop (single-letter shortcut + arrow-key + Enter)
# ---------------------------------------------------------------------------

def _read_choice(highlight: int) -> tuple[Optional[str], int]:
    """Return (letter|None, new_highlight). letter=None means re-render only.

    KeyboardInterrupt routes to sys.exit(0); EOF routes to graceful X-exit.
    """
    try:
        raw = input(f"  {PURPLE}>{RESET} ").strip().lower()
    except EOFError:
        return ("x", highlight)
    except KeyboardInterrupt:
        sys.exit(0)

    if not raw:
        letter = _MENU_ITEMS[highlight][0].lower()
        return (letter, highlight)

    # Arrow-key escape sequences (rare on Windows cmd; included for parity)
    if raw in ("\x1b[a", "k", "up"):
        return (None, (highlight - 1) % len(_MENU_ITEMS))
    if raw in ("\x1b[b", "j", "down"):
        return (None, (highlight + 1) % len(_MENU_ITEMS))

    # Single-letter match
    for i, (letter, _, _) in enumerate(_MENU_ITEMS):
        if raw == letter.lower():
            return (letter.lower(), i)

    return (None, highlight)


def _read_choice_animated(highlight: int) -> tuple[Optional[str], int]:
    """Windows blocking-keystroke input loop. ONE render per operator action.

    RKOJ-ELENO :: 2026-05-24T23:55Z :: operator screenshot #48 — "in current
    scope i cannot type here and its flickering". Prior implementation polled
    msvcrt.kbhit() at 3 FPS while re-rendering on every tick; this:
      1) FLICKERED (cursor-home repaint redrew the entire frame each tick)
      2) BROKE INPUT (msvcrt.kbhit() polling could miss keystrokes between
         sleeps; the prompt cursor was wiped mid-keystroke by the redraw)

    New model (render-on-event):
      * Render the full frame ONCE.
      * Block on msvcrt.getwch() (single keystroke, no polling, no timeout).
      * Process the key (arrow / Enter / shortcut).
      * If it changed highlight: _render() once more.
      * If it dispatches: return.

    NO POLLING. NO FLICKER. INPUT ALWAYS RECEIVED.

    Animation: _TICK advances on every _render() call so the animation
    visibly moves between operator actions (not continuously). For
    continuous live animation EVE_LIVE_ANIM defaults to ON; set
    EVE_LIVE_ANIM=0 to fall back to render-on-event mode.

    RKOJ-ELENO :: 2026-05-25T01:36Z :: operator screenshot #66 "more
    animation and live here" -- flipped default polarity so the band feels
    alive without operator setting an env var. Partial-redraw mitigation
    (only animation rows + accounts panel repaint; full hero/menu/prompt
    rows are not touched) prevents the original flicker that motivated
    the render-on-event mode.
    """
    try:
        import msvcrt  # Windows-only
    except ImportError:
        return _read_choice(highlight)

    # RKOJ-ELENO :: 2026-05-25T02:30Z :: operator P0 "i cannot scroll and select things"
    # + "it wont close". Live-anim 5fps polling DROPPED keystrokes (msvcrt.kbhit + partial
    # redraw race) AND blocked Ctrl-C handler. Flipped default OFF: render-on-event blocking
    # msvcrt.getwch() never misses keystrokes and propagates Ctrl-C cleanly. Live mode is
    # opt-in via EVE_LIVE_ANIM=1 for operators who can tolerate the input lag.
    if os.environ.get("EVE_LIVE_ANIM", "0") == "1":
        return _read_choice_animated_live(highlight)

    # Render-on-event: paint once, then BLOCK on next keystroke.
    _render(highlight)
    while True:
        try:
            ch = msvcrt.getwch()
        except KeyboardInterrupt:
            sys.exit(0)

        if ch in ("\r", "\n"):
            # Enter on the highlighted row dispatches that row.
            return (_MENU_ITEMS[highlight][0].lower(), highlight)
        if ch == "\x03":  # Ctrl-C
            sys.exit(0)
        if ch == "\xe0" or ch == "\x00":
            # arrow-key prefix on Windows (xE0 standard, x00 for some keypads)
            try:
                ch2 = msvcrt.getwch()
            except KeyboardInterrupt:
                sys.exit(0)
            if ch2 == "H":  # up
                highlight = (highlight - 1) % len(_MENU_ITEMS)
                _render(highlight)
                continue
            if ch2 == "P":  # down
                highlight = (highlight + 1) % len(_MENU_ITEMS)
                _render(highlight)
                continue
            # Other escape suffix -- ignore, loop blocks on next getwch
            continue
        if ch == "\t":  # Tab also moves down
            highlight = (highlight + 1) % len(_MENU_ITEMS)
            _render(highlight)
            continue
        if ch.isprintable():
            low = ch.lower()
            # Single-letter immediate dispatch for menu shortcuts
            for i, (letter, _, _) in enumerate(_MENU_ITEMS):
                if low == letter.lower():
                    return (low, i)
            # j/k vim-style nav
            if low == "k":
                highlight = (highlight - 1) % len(_MENU_ITEMS)
                _render(highlight)
                continue
            if low == "j":
                highlight = (highlight + 1) % len(_MENU_ITEMS)
                _render(highlight)
                continue
            # Unknown printable -- ignore, loop blocks on next getwch


def _read_choice_animated_live(highlight: int) -> tuple[Optional[str], int]:
    """Live-animation variant. Default since 2026-05-25T01:36Z (operator
    screenshot #66 "more animation and live here"). Polls msvcrt.kbhit()
    at ~5 FPS so the Sinister shimmer + sparkle accents visibly drift
    between keystrokes.

    Flicker mitigation: full _render() runs ONCE on entry + only on
    highlight change. Per-tick animation updates go through
    _partial_animation_redraw() which uses cursor-positioning to repaint
    JUST the animation rows + accounts panel (the menu / hero / prompt
    rows are left untouched, so the cursor doesn't flash and the menu
    bar doesn't flicker).

    Fallback: EVE_LIVE_ANIM=0 routes back to render-on-event mode.
    Live tick rate is EVE_LIVE_ANIM_FPS (default 5; set to 2 if the
    operator's terminal still shows perceptible flicker).
    """
    try:
        import msvcrt
    except ImportError:
        return _read_choice(highlight)

    # Live tick rate: default 5fps (200 ms). Operator can drop to 2fps via
    # EVE_LIVE_ANIM_FPS=2 if their terminal still flickers.
    try:
        fps = int(os.environ.get("EVE_LIVE_ANIM_FPS", "5"))
    except ValueError:
        fps = 5
    fps = max(1, min(10, fps))
    tick_interval = 1.0 / fps

    _render(highlight)
    last_render = time.time()
    while True:
        now = time.time()
        if now - last_render >= tick_interval:
            # Partial redraw: only animation rows + accounts panel repaint.
            # Cursor saved + restored so input prompt stays in place.
            _partial_animation_redraw()
            last_render = now
        if msvcrt.kbhit():
            ch = msvcrt.getwch()
            if ch in ("\r", "\n"):
                return (_MENU_ITEMS[highlight][0].lower(), highlight)
            if ch == "\x03":
                sys.exit(0)
            if ch == "\xe0" or ch == "\x00":
                ch2 = msvcrt.getwch() if msvcrt.kbhit() else ""
                if ch2 == "H":
                    highlight = (highlight - 1) % len(_MENU_ITEMS)
                    _render(highlight); last_render = time.time(); continue
                if ch2 == "P":
                    highlight = (highlight + 1) % len(_MENU_ITEMS)
                    _render(highlight); last_render = time.time(); continue
                continue
            if ch == "\t":
                highlight = (highlight + 1) % len(_MENU_ITEMS)
                _render(highlight); last_render = time.time(); continue
            if ch.isprintable():
                low = ch.lower()
                for i, (letter, _, _) in enumerate(_MENU_ITEMS):
                    if low == letter.lower():
                        return (low, i)
                if low == "k":
                    highlight = (highlight - 1) % len(_MENU_ITEMS)
                    _render(highlight); last_render = time.time(); continue
                if low == "j":
                    highlight = (highlight + 1) % len(_MENU_ITEMS)
                    _render(highlight); last_render = time.time(); continue
        else:
            # Sleep up to tick_interval/4 so kbhit response stays snappy
            # (50ms max sleep keeps keystroke latency under one tick).
            time.sleep(min(0.05, tick_interval / 4))


# ---------------------------------------------------------------------------
# Action stubs (eve.py supplies real callables via show_main_menu(callbacks=...))
# ---------------------------------------------------------------------------

def _default_resume() -> None:
    print(f"  {WARN}[R] show_project_picker not wired - eve.py main() needs to inject it.{RESET}")
    time.sleep(1.0)


def _default_stub(name: str) -> Callable[[], None]:
    def _f() -> None:
        print(f"  {WARN}[{name}] not wired through main_menu yet.{RESET}")
        time.sleep(0.8)
    return _f


def _kill_fleet_action() -> None:
    """RKOJ-ELENO :: 2026-05-24T22:10Z :: dispatches kill-fleet.ps1 -Mode Hard.

    NOTE 2026-05-25T00:20Z :: no longer bound to a top-level menu key. Kept
    available for sister-B's "Agents I'm Working With" sub-page (bottom-of-
    list "Kill All" action). External callers may still pass it through the
    callbacks dict (key 'kill_fleet') for back-compat.
    """
    ps1 = SANCTUM_ROOT / "automations" / "kill-fleet.ps1"
    if not ps1.exists():
        print(f"  {WARN}[K] kill-fleet.ps1 missing at {ps1}{RESET}")
        time.sleep(1.2)
        return
    print(f"  {WARN}[K] Force-closing all EVE-spawned windows in 1s ...{RESET}")
    print(f"  {DIM}(this window will also exit; use Ctrl-C to abort){RESET}")
    time.sleep(1.0)
    try:
        subprocess.run(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
             "-File", str(ps1), "-Mode", "Hard"],
            timeout=10,
            check=False,
        )
    except subprocess.TimeoutExpired:
        print(f"  {WARN}[K] kill-fleet.ps1 timed out after 10s; exiting EVE anyway.{RESET}")
    except Exception as e:
        print(f"  {WARN}[K] kill-fleet.ps1 failed: {e}{RESET}")
    sys.exit(0)


def _agents_working_with_action() -> None:
    """RKOJ-ELENO :: 2026-05-25T00:20Z :: W-key stub for "Agents I'm Working With".

    Sister B (sister-sanctum lane) owns the full sub-page: live PID list,
    per-row K/R/M actions, bottom "Kill All". For now we ship a useful preview
    by running `kill-fleet.ps1 -Mode Soft -WhatIf` which LISTS live agents
    without killing -- operator-actionable visibility while sister wires the
    full interactive sub-page.

    Coord note: _shared-memory/cross-agent/2026-05-25T0020Z-sanctum-to-
    sanctum-B-agents-im-working-with-spec.md
    """
    print(f"  {WARN}[W] agents-im-working-with: NOT YET IMPLEMENTED -- sister B owns;{RESET}")
    print(f"  {WARN}    for now showing kill-fleet preview (-WhatIf, no kills){RESET}")
    print()
    ps1 = SANCTUM_ROOT / "automations" / "kill-fleet.ps1"
    if not ps1.exists():
        print(f"  {WARN}[W] kill-fleet.ps1 missing at {ps1}{RESET}")
        time.sleep(1.5)
        return
    try:
        subprocess.run(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
             "-File", str(ps1), "-Mode", "Soft", "-WhatIf"],
            timeout=15,
            check=False,
        )
    except subprocess.TimeoutExpired:
        print(f"  {WARN}[W] kill-fleet.ps1 -WhatIf timed out after 15s.{RESET}")
    except Exception as e:
        print(f"  {WARN}[W] kill-fleet.ps1 -WhatIf failed: {e}{RESET}")
    print()
    print(f"  {DIM}press Enter to return to menu...{RESET}")
    try:
        input()
    except (EOFError, KeyboardInterrupt):
        pass


# ---------------------------------------------------------------------------
# Public entrypoint
# ---------------------------------------------------------------------------

def show_main_menu(callbacks: Optional[dict[str, Callable[[], None]]] = None) -> str:
    """Render the centered jcode-hero main menu loop.

    callbacks keys (all optional; falls back to a friendly stub if missing):
        resume                  - R action (call existing project picker)
        auto_resume             - A action
        general                 - G action
        tools                   - T action (Quantum + Health combined)
        new_project             - N action
        account_mgr             - M action (was Onboarding)
        agents_working_with     - W action (sub-page: live agents + per-row
                                  K/R/M actions + Kill All; sister-B owns).
                                  Default = stub preview via -WhatIf.
        agents / kill_fleet     - back-compat keys; both route to W.

    Returns the letter the operator last picked (lowercase). X / Ctrl-C / EOF
    return "x" and the caller is expected to sys.exit cleanly.
    """
    cb = callbacks or {}
    actions: dict[str, Callable[[], None]] = {
        "r": cb.get("resume") or _default_resume,
        "a": cb.get("auto_resume") or _default_stub("Auto-Resume"),
        "g": cb.get("general") or _default_stub("General"),
        "t": cb.get("tools") or _default_stub("Tools"),
        "n": cb.get("new_project") or _default_stub("New Project"),
        "m": cb.get("account_mgr") or _default_stub("Account Manager"),
        # W = Agents I'm Working With (operator hard-canonical 2026-05-25
        # spec final 8-item menu). Accept multiple callback keys for
        # back-compat: 'agents' / 'agents_working_with' / 'kill_fleet' all
        # point at the same project-grouped multi-select page.
        "w": (
            cb.get("agents_working_with")
            or cb.get("agents")
            or cb.get("kill_fleet")
            or _agents_working_with_action
        ),
        # RKOJ-ELENO :: 2026-05-25T06:30Z :: Sub-agent G iter22 -- L) Sinister LINK
        # was wired in eve.py but unreachable. Now dispatched here so callbacks
        # injection from eve.main() actually fires the page.
        "l": cb.get("sinister_link") or _default_stub("Sinister LINK"),
    }

    highlight = 0
    # Prefer the animated (non-blocking) loop on Windows so the jcode shimmer
    # actually moves frame-to-frame. Falls back to blocking input on platforms
    # without msvcrt (RKOJ-ELENO :: 2026-05-24 fix).
    use_animated = (os.name == "nt") and _ANSI
    # RKOJ-ELENO :: 2026-05-25T02:15Z :: cross-page nav. If a sub-page sets
    # _EVE_NAV_TO, dispatch that letter immediately without redrawing main.
    pending_nav = os.environ.pop("_EVE_NAV_TO", "")
    while True:
        if pending_nav:
            letter = pending_nav
            pending_nav = ""
            # Sync highlight cursor to the dispatched letter so the next
            # main-menu paint (if we return here) shows the right row selected.
            for i, (l, _, _) in enumerate(_MENU_ITEMS):
                if l.lower() == letter:
                    highlight = i
                    break
        elif use_animated:
            letter, highlight = _read_choice_animated(highlight)
        else:
            _render(highlight)
            letter, highlight = _read_choice(highlight)
        if letter is None:
            continue
        if letter == "x":
            # Operator hard-canonical: X must ALWAYS exit. os._exit bypasses
            # any hung daemon thread / blocked subprocess / atexit handler.
            try:
                sys.stdout.write("\n  [EVE] goodbye.\n"); sys.stdout.flush()
            except Exception:
                pass
            os._exit(0)
        fn = actions.get(letter)
        if fn is not None:
            fn()
            # After a sub-page (Account Manager / Tools / Onboarding) returns,
            # the screen has the sub-page's residue. Reset _FIRST_RENDER so the
            # next main-menu paint does a full clear-screen and lands clean.
            global _FIRST_RENDER
            _FIRST_RENDER = True
            # Check if sub-page requested cross-page navigation.
            pending_nav = os.environ.pop("_EVE_NAV_TO", "")
            continue
        # Unknown letter; loop redraws.


# ---------------------------------------------------------------------------
# Smoke test entrypoint (--smoke renders one frame and exits 0)
# ---------------------------------------------------------------------------

def _smoke() -> int:
    """Render one full frame (header + animation tick 0 + menu + footer) and exit."""
    try:
        _render(highlight=0)
        # Verify the animation ticked at least once
        assert _TICK == 1, f"expected _TICK == 1 after one render, got {_TICK}"
        print(f"{OK}[smoke] OK · _TICK={_TICK} · cols={_term_cols()}{RESET}")
        return 0
    except Exception as e:
        print(f"{WARN}[smoke] FAIL: {e}{RESET}", file=sys.stderr)
        return 1


def _demo_highlight() -> int:
    """RKOJ-ELENO :: 2026-05-25T00:15Z :: print all menu rows with row 3
    selected so operator can visually confirm the bg-fills-entire-row +
    edge-glow effect statically. No screen clear, no input loop."""
    global _TICK
    try:
        print()
        print(f"{DARKP}--- {BRIGHTP}menu highlight demo{RESET} {DARKP}(row 3 selected){RESET} ---")
        print()
        for line in _menu_lines(highlight=3):
            print(line)
        _TICK += 1
        # Pulse-shift demo: same rows at tick=7 to show 2nd palette shade
        print()
        print(f"{DARKP}--- {BRIGHTP}pulse +6 ticks{RESET} ---")
        print()
        _TICK = 7
        for line in _menu_lines(highlight=3):
            print(line)
        print()
        print(f"{OK}[demo-highlight] OK{RESET}")
        return 0
    except Exception as e:
        print(f"{WARN}[demo-highlight] FAIL: {e}{RESET}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--smoke":
        sys.exit(_smoke())
    if len(sys.argv) > 1 and sys.argv[1] == "--demo-highlight":
        sys.exit(_demo_highlight())
    show_main_menu()
