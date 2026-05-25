"""account_info_panel :: render Claude-account usage block (Resume + Accounts).

Author: RKOJ-ELENO :: 2026-05-24

Operator verbatim 2026-05-24T23:30Z:
    "on the resume screen and accounts menu i need to see info about the calude
     accounts and progres bar of usage. running agents per accounts etc. things
     like that."

RKOJ-ELENO :: 2026-05-25T01:36Z :: operator screenshot #67 verbatim:
    Header said "1/4 enabled" (FAKE cap; placeholder slots already removed
    from JSON), per-acct row said "100% used" (FAKE -- spawns_in_5h / soft
    cap was clamped to 100% but the soft cap is a guess, not an Anthropic
    figure), and "+ 3 disabled: Leo + 2 empty" rendered slots that don't
    exist in JSON. Operator: "review how jcode track their usage or what
    we need to do and fucking do it". Fix: prefer anthropic-usage-probe.ps1
    (jcode-style header scraping from /v1/messages); when probe fails or
    is unavailable, show raw spawn count + "(no probe)" instead of fake %.
    Header no longer includes /total cap; LINKED/UNLINKED tag per acct.

Two render modes:
  * detailed=True  -> Accounts page (5+ lines per acct): window bar + spawns
    today + running-agents list + recent rate-limit events.
  * detailed=False -> Resume page (2 lines per acct, compact): bar + agents.

Data sources:
  * _shared-memory/claude-accounts.json          (per-account state)
  * _shared-memory/spawned-windows.jsonl         (PID + account_name per spawn)
  * Get-Process claude                           (live PID set)
  * _shared-memory/rate-limit-causes.jsonl       (24h rate-limit count)

Color tokens: OK / WARN / FAIL / BRIGHTP / DIM / WHITE / SOFT / PURPLE only
(canonical-only per eve-ui-uniformity-doctrine).

Glyphs are cp1252/cp437-safe (U+2588 full block, U+2591 light shade,
U+25CF black circle). Stdout reconfigure for utf-8 mirrors main_menu.py.

Smoke:
  python -c "import sys; sys.path.insert(0, r'D:/Sinister Sanctum/tools/eve-picker');
             from account_info_panel import render_account_info_block;
             render_account_info_block(detailed=True)"
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Reconfigure stdout for utf-8 so block glyphs render on Windows cmd cp1252.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
except Exception:
    pass


# ---------------------------------------------------------------------------
# Sanctum-root probe (mirrors main_menu / account_manager / project_picker)
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
SPAWNED_JSONL = SANCTUM_ROOT / "_shared-memory" / "spawned-windows.jsonl"
RATELIM_JSONL = SANCTUM_ROOT / "_shared-memory" / "rate-limit-causes.jsonl"
USAGE_PROBE_PS1 = SANCTUM_ROOT / "automations" / "anthropic-usage-probe.ps1"


# Process-level cache so we don't re-spawn the PS1 probe every render.
_PROBE_CACHE: dict[str, dict] = {}  # slot -> {"ts": float, "live": dict|None}


def _probe_live_usage(slot: str = "default") -> dict | None:
    """Call anthropic-usage-probe.ps1 at most once per 60s/slot; return parsed
    JSON or None. 3s subprocess timeout so a slow probe never freezes render.
    Returns None when probe missing or timed out; returns dict (even with
    status=probe-failed-*) when the probe returned anything parseable so the
    caller can surface accurate state (refresh needed, offline, stale).
    """
    if not USAGE_PROBE_PS1.exists():
        return None
    now_ts = time.time()
    cached = _PROBE_CACHE.get(slot, {})
    cache_ts = float(cached.get("ts", 0.0))
    if (now_ts - cache_ts) < 60.0 and cache_ts > 0:
        return cached.get("live")
    live: dict | None = None
    try:
        r = subprocess.run(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
             "-File", str(USAGE_PROBE_PS1), "-Mode", "Json",
             "-Slot", slot, "-CacheSec", "60"],
            capture_output=True, text=True, timeout=3, errors="replace",
        )
        if r.stdout:
            try:
                live = json.loads(r.stdout)
            except Exception:
                live = None
    except Exception:
        live = None  # includes TimeoutExpired
    _PROBE_CACHE[slot] = {"ts": now_ts, "live": live}
    return live


# ---------------------------------------------------------------------------
# Color tokens (canonical only; NO_COLOR / dumb-term aware)
# ---------------------------------------------------------------------------

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
BRIGHTP = _c("\033[38;5;177m")
DARKP = _c("\033[38;5;91m")
WHITE = _c("\033[97m")
SOFT = _c("\033[38;5;245m")
DIM = _c("\033[38;5;240m")
OK = _c("\033[38;5;46m")
WARN = _c("\033[38;5;220m")
FAIL = _c("\033[38;5;196m")
RESET = _c("\033[0m")


# ---------------------------------------------------------------------------
# Data probes
# ---------------------------------------------------------------------------

def _load_accounts() -> dict | None:
    if not ACCOUNTS_JSON.exists():
        return None
    try:
        return json.loads(ACCOUNTS_JSON.read_text(encoding="utf-8-sig", errors="replace"))
    except Exception:
        return None


def _live_claude_pids() -> set[int]:
    """Set of currently-running claude.exe PIDs (via Get-Process)."""
    if os.name != "nt":
        # POSIX fallback: pgrep claude
        try:
            r = subprocess.run(
                ["pgrep", "-f", "claude"], capture_output=True, text=True, timeout=5,
            )
            return {int(x) for x in r.stdout.split() if x.isdigit()}
        except Exception:
            return set()
    try:
        r = subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command",
             "Get-Process claude -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id"],
            capture_output=True, text=True, timeout=6, errors="replace",
        )
        return {int(x) for x in r.stdout.split() if x.strip().isdigit()}
    except Exception:
        return set()


def _spawned_rows() -> list[dict]:
    """Read spawned-windows.jsonl (newest-first, capped at 500 most-recent)."""
    if not SPAWNED_JSONL.exists():
        return []
    try:
        with SPAWNED_JSONL.open("r", encoding="utf-8", errors="replace") as fp:
            lines = fp.readlines()[-500:]
    except Exception:
        return []
    out: list[dict] = []
    for ln in lines:
        ln = ln.strip()
        if not ln:
            continue
        try:
            out.append(json.loads(ln))
        except Exception:
            continue
    return out


# ---------------------------------------------------------------------------
# 5h-window spawn-count math (REAL data source, replaces bad transcript-msg
# fallback that produced "999% used (8490/500 msgs 5h)" -- screenshot #57).
# RKOJ-ELENO :: 2026-05-25 :: operator visual showed nonsense numbers because
# claude-usage-meter.ps1 summed every transcript record (8490) and divided by
# a hardcoded 500-msg guess. The numerator was a different time window than
# the denominator and the denominator didn't reflect any real Anthropic cap.
# Per `_shared-memory/knowledge/best-agent-count-per-claude-plan-study-2026-05-24.md`
# the SAFE concurrent agent count is 4, MAX is 6 for Max 20x. Treating spawn
# count in a rolling 5h window vs a tier-aware soft cap gives a sensible
# "how close am I to my burst budget" number.
# ---------------------------------------------------------------------------

WINDOW_CAP_BY_TIER: dict[str, int] = {
    "max": 50,        # Max 20x (operator's plan in screenshot)
    "max20": 50,
    "max_20x": 50,
    "max_5x": 20,
    "max5": 20,
    "pro": 12,
    "team": 80,
    "enterprise": 200,
}
WINDOW_CAP_DEFAULT = 30  # unknown tier fallback


def _window_cap_for(tier: str | None) -> int:
    key = (tier or "").strip().lower()
    return WINDOW_CAP_BY_TIER.get(key, WINDOW_CAP_DEFAULT)


def _spawns_in_5h(account_name: str, spawn_rows: list[dict], now: datetime) -> int:
    """Count spawns for `account_name` whose `started` is within last 5 hours."""
    if not account_name:
        return 0
    cutoff = now - timedelta(hours=5)
    n = 0
    for row in spawn_rows:
        if (row.get("account_name") or "").strip() != account_name:
            continue
        ts = row.get("started") or ""
        started = _parse_utc(ts)
        if started is None:
            continue
        # `started` may be local-tz offset (e.g. -04:00); convert to UTC for compare.
        try:
            started_utc = started.astimezone(timezone.utc)
        except Exception:
            started_utc = started
        if started_utc >= cutoff:
            n += 1
    return n


def _running_per_account(live_pids: set[int], spawn_rows: list[dict]) -> dict[str, list[str]]:
    """Map account_name -> list of (agent or project) display strings still alive."""
    out: dict[str, list[str]] = {}
    seen_pids: set[int] = set()
    # Iterate newest-first so most recent spawn-record wins per PID (rare PID reuse).
    for row in reversed(spawn_rows):
        try:
            pid = int(row.get("pid", -1))
        except Exception:
            continue
        if pid in seen_pids:
            continue
        seen_pids.add(pid)
        if pid not in live_pids:
            continue
        acct = (row.get("account_name") or "").strip() or "(unknown)"
        agent = row.get("agent") or row.get("project") or "?"
        out.setdefault(acct, []).append(str(agent))
    return out


def _rate_limit_24h(account_name: str) -> int:
    """Count rate-limit events in last 24h for `account_name`."""
    if not RATELIM_JSONL.exists():
        return 0
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    n = 0
    try:
        with RATELIM_JSONL.open("r", encoding="utf-8", errors="replace") as fp:
            for ln in fp:
                ln = ln.strip()
                if not ln or account_name not in ln:
                    continue
                try:
                    rec = json.loads(ln)
                except Exception:
                    continue
                if rec.get("account_name") != account_name:
                    continue
                ts = rec.get("ts_utc") or ""
                try:
                    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                except Exception:
                    continue
                if dt >= cutoff:
                    n += 1
    except Exception:
        return 0
    return n


# ---------------------------------------------------------------------------
# Usage-percentage computation (5h rolling window)
# ---------------------------------------------------------------------------

def _parse_utc(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00") if s.endswith("Z") else s)
    except Exception:
        return None


def _fmt_dur(td: timedelta | None) -> str:
    if td is None:
        return "-"
    secs = int(td.total_seconds())
    if secs <= 0:
        return "0m"
    h, rem = divmod(secs, 3600)
    m, _ = divmod(rem, 60)
    return f"{h}h{m:02d}m" if h else f"{m}m"


def _usage_pct(
    acct: dict,
    now: datetime,
    spawn_rows: list[dict] | None = None,
) -> tuple[int, str, int, int, bool]:
    """Return (pct_used, remaining_str, spawns_in_window, cap, over_limit).

    Replaces the prior elapsed-time-since-last-spawn proxy. We now count
    REAL spawns from `spawned-windows.jsonl` whose `account_name` matches
    AND whose `started` falls inside the rolling 5-hour window. Divide by
    a tier-aware soft cap (WINDOW_CAP_BY_TIER) to get the "burst budget"
    percentage. Bounded at 100% for display; `over_limit=True` when the
    raw count exceeds the cap (caller surfaces an OVER LIMIT badge).

    "Remaining" is the time until the OLDEST spawn-in-window ages out of
    the 5h window (when the budget starts refilling). If no spawns in
    window, returns "5h00m budget" idle hint.
    """
    if spawn_rows is None:
        spawn_rows = _spawned_rows()
    name = acct.get("name") or ""
    cap = _window_cap_for(acct.get("plan_tier"))
    spawns = _spawns_in_5h(name, spawn_rows, now)
    over_limit = spawns > cap
    pct_raw = int(round(100.0 * spawns / cap)) if cap > 0 else 0
    pct = min(100, max(0, pct_raw))

    # Determine remaining "until budget partially refills" by finding the
    # oldest spawn inside the 5h window for this account.
    cutoff = now - timedelta(hours=5)
    oldest: datetime | None = None
    for row in spawn_rows:
        if (row.get("account_name") or "").strip() != name:
            continue
        s = _parse_utc(row.get("started"))
        if s is None:
            continue
        try:
            s_utc = s.astimezone(timezone.utc)
        except Exception:
            s_utc = s
        if s_utc < cutoff:
            continue
        if oldest is None or s_utc < oldest:
            oldest = s_utc
    if oldest is None:
        remaining_str = "5h00m budget"
    else:
        refills_at = oldest + timedelta(hours=5)
        delta = refills_at - now
        if delta.total_seconds() <= 0:
            remaining_str = "refilling now"
        else:
            remaining_str = _fmt_dur(delta) + " to refill"
    return (pct, remaining_str, spawns, cap, over_limit)


def _bar(pct: int, width: int = 20) -> str:
    """Block-bar: GREEN <60%, YELLOW 60-85%, RED >85%."""
    pct = max(0, min(100, pct))
    filled = int(round(width * pct / 100))
    empty = width - filled
    if pct < 60:
        col = OK
    elif pct < 85:
        col = WARN
    else:
        col = FAIL
    # U+2588 full block (used), U+2591 light shade (unused) -- cp437-safe.
    return f"{col}{'█' * filled}{DIM}{'░' * empty}{RESET}"


# ---------------------------------------------------------------------------
# Public renderer
# ---------------------------------------------------------------------------

def render_account_info_block(detailed: bool = False) -> None:
    """Render per-account usage info block.

    detailed=True   ->  Accounts page format (5 lines + spacer per enabled acct).
    detailed=False  ->  Resume page format (2 lines per enabled acct, compact).

    RKOJ-ELENO :: 2026-05-25T12:00Z :: sub-agent B :: every line buffers into
    `_buf` and renders via eve_ui.center_block per eve-ui-uniformity-doctrine
    "centered menu each page" (operator image #61). The fallback (no eve_ui
    available) preserves the previous 2-sp indent.
    """
    _buf: list[str] = []

    def _emit(line: str = "") -> None:
        _buf.append(line)

    def _flush() -> None:
        if not _buf:
            return
        try:
            import sys as _sys
            from pathlib import Path as _P
            _here = _P(__file__).resolve().parent
            if str(_here) not in _sys.path:
                _sys.path.insert(0, str(_here))
            from eve_ui import center_block as _cb  # type: ignore
            for ln in _cb(_buf, width=72):
                print(ln)
        except Exception:
            for ln in _buf:
                print(f"  {ln}")
        _buf.clear()

    data = _load_accounts()
    if not data:
        _emit(f"{DIM}(no claude-accounts.json){RESET}")
        _flush()
        return
    accts = data.get("accounts", [])
    if not accts:
        _emit(f"{DIM}(no accounts configured){RESET}")
        _flush()
        return

    now = datetime.now(timezone.utc)
    live_pids = _live_claude_pids()
    spawn_rows = _spawned_rows()
    running_map = _running_per_account(live_pids, spawn_rows)

    enabled = [a for a in accts if a.get("enabled", False)]
    disabled = [a for a in accts if not a.get("enabled", False)]
    empty_slots = sum(
        1 for a in disabled
        if str(a.get("label", "")).startswith("(unconfigured")
    )
    disabled_named = [a for a in disabled if not str(a.get("label", "")).startswith("(unconfigured")]
    # RKOJ-ELENO :: 2026-05-25 :: operator hard-canonical "stop having account
    # capped at 4 and just have it be per account. like show when its unlinked
    # things like that." `linked` is auto-computed by claude-accounts.ps1
    # Test-AccountLinked. Default False if field absent -- operator wants the
    # actionable UNLINKED tag to surface for any acct that hasn't been verified
    # linked, never optimistically green.
    linked = [a for a in enabled if a.get("linked", False)]
    unlinked = [a for a in enabled if not a.get("linked", False)]

    title = "Claude accounts" if detailed else "Accounts"
    _emit()
    # No-cap header: count of accounts, breakdown of enabled / linked /
    # unlinked. The old "N/M enabled" implied a fixed M-slot cap.
    _emit(f"{BRIGHTP}{title}{RESET}  "
          f"{WHITE}{len(accts)} accounts{RESET}  "
          f"{DIM}({len(enabled)} enabled, {len(linked)} linked, "
          f"{len(unlinked)} unlinked){RESET}  "
          f"{DIM}{data.get('rotation_strategy', '?')}{RESET}")
    _emit()

    # U+25CF black circle (cp1252/WGL4 safe).
    bullet = "●"

    for acct in enabled:
        name = acct.get("name", "?")
        label = acct.get("label", name)
        tier = (acct.get("plan_tier") or "?").strip() or "?"
        today = int(acct.get("successful_spawns_today", 0) or 0)
        rate_lim = _parse_utc(acct.get("rate_limited_until_utc"))
        is_linked = bool(acct.get("linked", False))

        # Resolve probe for this slot (default acct probes the live OAuth cred;
        # others probe their own credentials.<slot>.json). Probe regardless of
        # `linked` flag -- the probe IS our truth source for whether the OAuth
        # token works. linked flag may lag the probe by minutes.
        probe_slot = name if name and name != "operator" else "default"
        live = _probe_live_usage(probe_slot)
        probe_ok = bool(live and live.get("status") == "ok")
        # Probe returns nested session/weekly_all objects (verified live
        # 2026-05-25T02:19Z). 5h util = session.utilization, 7d util =
        # weekly_all.utilization. Tolerate flat unified_*_utilization too.
        probe_5h = None
        probe_7d = None
        if probe_ok and live:
            sess = live.get("session") or {}
            wk = live.get("weekly_all") or {}
            probe_5h = sess.get("utilization") if sess else live.get("unified_5h_utilization")
            probe_7d = wk.get("utilization") if wk else live.get("unified_7d_utilization")

        # Status dot color: probe-ok wins; then rate-limit; then unlinked;
        # NEVER use fake spawn-count percent for dot color.
        if rate_lim and rate_lim > now:
            dot_col = FAIL
        elif probe_ok and isinstance(probe_5h, (int, float)):
            p = float(probe_5h) * 100.0
            dot_col = OK if p < 60 else (WARN if p < 85 else FAIL)
        elif not is_linked:
            dot_col = WARN  # unlinked = yellow (actionable)
        else:
            dot_col = SOFT  # probe unavailable, no fake dot

        # Header line (both modes) -- LINKED / UNLINKED tag.
        link_tag = (f"{OK}LINKED{RESET}" if is_linked
                    else f"{WARN}UNLINKED{RESET}")
        _emit(f"{dot_col}{bullet}{RESET} {WHITE}{label}{RESET} "
              f"{DIM}[{RESET}{PURPLE}{tier}{RESET}{DIM}]{RESET}  "
              f"{DIM}[{RESET}{link_tag}{DIM}]{RESET}")

        # Window bar -- probe-first, never fake. Probe ok beats `linked` flag
        # (probe IS the truth source; linked flag may lag).
        if rate_lim and rate_lim > now:
            bar_line = (f"  {SOFT}5h Window:{RESET} "
                        f"{FAIL}[rate-limited {_fmt_dur(rate_lim - now)} left]{RESET}")
        elif probe_ok and isinstance(probe_5h, (int, float)):
            p_int = int(round(float(probe_5h) * 100.0))
            extras = []
            if isinstance(probe_7d, (int, float)):
                extras.append(f"{DIM}7d {int(round(float(probe_7d)*100))}%{RESET}")
            sess = (live or {}).get("session") or {}
            reset_unix = sess.get("reset_unix")
            if reset_unix:
                try:
                    delta = float(reset_unix) - time.time()
                    if delta > 0:
                        h = int(delta // 3600); m = int((delta % 3600) // 60)
                        rstr = f"{h}h{m:02d}m" if h else f"{m}m"
                        extras.append(f"{DIM}resets in {rstr}{RESET}")
                except Exception:
                    pass
            extras_str = ("  " + "  ".join(extras)) if extras else ""
            bar_line = (f"  {SOFT}5h Window:{RESET} {_bar(p_int, 20)} "
                        f"{WHITE}{p_int}% used{RESET} {OK}[MEASURED]{RESET}{extras_str}")
        elif live and live.get("status", "").startswith("probe-failed"):
            why = "refresh needed" if live.get("refresh_needed") else live.get("status", "probe-failed")
            spawns_in_win = _spawns_in_5h(name, spawn_rows, now)
            bar_line = (f"  {SOFT}5h Window:{RESET} "
                        f"{DIM}spawns {spawns_in_win} in last 5h (raw){RESET}  "
                        f"{WARN}[probe: {why}]{RESET}")
        elif not is_linked:
            bar_line = (f"  {SOFT}5h Window:{RESET} "
                        f"{WARN}not logged in -- run claude login to enable probe{RESET}")
        else:
            spawns_in_win = _spawns_in_5h(name, spawn_rows, now)
            bar_line = (f"  {SOFT}5h Window:{RESET} "
                        f"{DIM}spawns {spawns_in_win} in last 5h (raw){RESET}  "
                        f"{DIM}(no probe){RESET}")
        _emit(bar_line)

        running = running_map.get(name, [])
        running_count = len(running)
        running_disp = ", ".join(running[:4])
        if running_count > 4:
            running_disp += f", +{running_count - 4}"

        if detailed:
            _emit(f"  {SOFT}Today:{RESET}   {WHITE}{today}{RESET} spawns")
            if running_count:
                _emit(f"  {SOFT}Running:{RESET} {OK}{running_count}{RESET} "
                      f"{('agent' if running_count == 1 else 'agents')}  "
                      f"{DIM}({running_disp}){RESET}")
            else:
                _emit(f"  {SOFT}Running:{RESET} {DIM}0 agents{RESET}")
            rl_24 = _rate_limit_24h(name)
            if rl_24:
                _emit(f"  {SOFT}Recent:{RESET}  {WARN}{rl_24} rate-limit event"
                      f"{'s' if rl_24 != 1 else ''} in last 24h{RESET}")
            else:
                _emit(f"  {SOFT}Recent:{RESET}  {DIM}no rate-limit events in last 24h{RESET}")
            _emit()
        else:
            # Compact: one extra info line combining today + running
            today_str = f"{WHITE}{today}{RESET} {DIM}today{RESET}"
            if running_count:
                run_str = (f"{OK}{running_count}{RESET} "
                           f"{DIM}running ({running_disp}){RESET}")
            else:
                run_str = f"{DIM}0 running{RESET}"
            _emit(f"  {SOFT}Today:{RESET}   {today_str}  {SOFT}{bullet}{RESET}  {run_str}")

    # Disabled / empty slot summary
    if disabled_named:
        names = ", ".join(str(a.get("label") or a.get("name")) for a in disabled_named)
        _emit(f"{DIM}{bullet} {len(disabled_named)} disabled: {names}{RESET}")
    if empty_slots:
        _emit(f"{DIM}+ {empty_slots} empty slot{'s' if empty_slots != 1 else ''} "
              f"{bullet} press {RESET}{PURPLE}O{RESET}{DIM} to onboard{RESET}")
    _emit()
    _flush()


# ---------------------------------------------------------------------------
# CLI smoke entry
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mode = "detailed"
    if len(sys.argv) > 1 and sys.argv[1] in ("compact", "resume", "--compact"):
        mode = "compact"
    render_account_info_block(detailed=(mode == "detailed"))
    print(f"  {OK}[smoke] OK (mode={mode}){RESET}")
