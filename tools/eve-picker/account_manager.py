"""EVE :: Account Manager sub-page (replaces Onboarding)

Author: RKOJ-ELENO :: 2026-05-24

Operator verbatim 2026-05-24T21:50Z:
    "change onboarding to account manager and have account managment to set
     name, login logout. still keep this here tho the accounts status. and
     switch to a status bar to show usage like jcode. I want the jcode usage
     popups as well."

Companion module to eve.py — keep account-management surface area out of the
1300-line main file. Sister-B (`eve.py`) owns the menu wiring (renames
`O) Onboarding` -> `M) Account Manager` and calls show_account_manager()).

Layout (per eve-ui-uniformity-doctrine-2026-05-24):

      --- Account Manager ---

      Connected Claude accounts                  <- _render_accounts_panel() from eve.py
      <existing accounts status block>

      Usage status bar (jcode-style)             <- _render_usage_status_bar()
      ezekielromero314@gmail.com [max]   [...]  80% window  42 today
      leo (Leo collaborator)    [max]   [disabled]
      ...

      Actions:
        A) Add account     L) Login (web)    O) Logout
        R) Rename slot     E) Enable/Disable D) Delete slot
        U) Usage popup (jcode-style)

      --- B) Back   X) Exit   (arrow keys / number to select slot) ---

Sub-flows shell out to claude-accounts.ps1 (Add / SetKey / Enable / Disable /
Remove / Status / ResolveEmails) — never reimplements the JSON edit logic.
The Rename sub-flow uses a small in-place JSON rewrite because PS1 has no
SetLabel action yet (queued sister-B follow-up).
"""
from __future__ import annotations

import getpass
import json
import os
import re
import signal
import subprocess
import sys
import time
import webbrowser
from datetime import datetime, timezone, timedelta
from pathlib import Path


# RKOJ-ELENO :: 2026-05-24T22:10Z :: install SIGINT -> sys.exit(0) so Ctrl-C
# inside any input()/getpass()/subprocess wait is escapable instead of
# silently swallowed. Operator: "i cannoot close eve exe. it wont close".
def _acct_sigint(*_args) -> None:
    sys.exit(0)


try:
    signal.signal(signal.SIGINT, _acct_sigint)
except (ValueError, OSError):
    pass


# ---------------------------------------------------------------------------
# Color tokens — inherit from eve.py at runtime if importable, else best-effort
# stdout printing. Keeps this module self-contained for smoke-test importing.
# ---------------------------------------------------------------------------

def _resolve_colors():
    """Return a dict of color escape strings. Tries eve.py first."""
    try:
        import eve  # noqa: WPS433 -- sibling module when called from picker
        return {
            "PURPLE": eve.PURPLE, "BRIGHTP": eve.BRIGHTP, "DARKP": eve.DARKP,
            "WHITE": eve.WHITE, "SOFT": eve.SOFT, "DIM": eve.DIM,
            "OK": eve.OK, "WARN": eve.WARN, "FAIL": eve.FAIL,
            "RESET": eve.RESET, "BOLD": eve.BOLD,
        }
    except Exception:
        # Direct ANSI fallbacks (same xterm codes used in eve.py).
        no_color = "NO_COLOR" in os.environ or os.environ.get("TERM") == "dumb"
        def c(code: str) -> str:
            return "" if no_color else code
        return {
            "PURPLE":  c("\033[38;5;141m"),
            "BRIGHTP": c("\033[38;5;177m"),
            "DARKP":   c("\033[38;5;91m"),
            "WHITE":   c("\033[97m"),
            "SOFT":    c("\033[38;5;245m"),
            "DIM":     c("\033[38;5;240m"),
            "OK":      c("\033[38;5;46m"),
            "WARN":    c("\033[38;5;220m"),
            "FAIL":    c("\033[38;5;196m"),
            "RESET":   c("\033[0m"),
            "BOLD":    c("\033[1m"),
        }


C = _resolve_colors()


# ---------------------------------------------------------------------------
# Sanctum root probe (re-implemented locally so module imports cleanly even
# without eve.py on sys.path — needed for smoke-test contract).
# ---------------------------------------------------------------------------

def _probe_sanctum_root() -> Path | None:
    env = os.environ.get("SINISTER_SANCTUM_ROOT") or os.environ.get("SANCTUM_ROOT")
    candidates = [env] if env else []
    candidates += [
        r"D:\Sinister Sanctum",
        r"C:\Sinister Sanctum",
        os.path.join(os.environ.get("USERPROFILE", ""), "Sinister Sanctum"),
    ]
    for cand in candidates:
        if not cand:
            continue
        p = Path(cand)
        if (p / "automations" / "claude-accounts.ps1").exists():
            return p
    return None


SANCTUM_ROOT = _probe_sanctum_root()
ACCOUNTS_JSON = (SANCTUM_ROOT / "_shared-memory" / "claude-accounts.json") if SANCTUM_ROOT else None
ACCOUNTS_PS1 = (SANCTUM_ROOT / "automations" / "claude-accounts.ps1") if SANCTUM_ROOT else None
ACCOUNTS_LOG = (SANCTUM_ROOT / "_shared-memory" / "claude-accounts.log") if SANCTUM_ROOT else None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_accounts() -> dict | None:
    if not ACCOUNTS_JSON or not ACCOUNTS_JSON.exists():
        return None
    try:
        return json.loads(ACCOUNTS_JSON.read_text(encoding="utf-8-sig", errors="replace"))
    except Exception as e:
        print(f"  {C['FAIL']}[accounts] unreadable: {e}{C['RESET']}")
        return None


def _save_accounts(data: dict) -> bool:
    if not ACCOUNTS_JSON:
        return False
    try:
        ACCOUNTS_JSON.write_text(
            json.dumps(data, indent=4, ensure_ascii=False),
            encoding="utf-8",
        )
        return True
    except Exception as e:
        print(f"  {C['FAIL']}[accounts] write failed: {e}{C['RESET']}")
        return False


def _ps1(action: str, *extra: str, timeout: int = 20) -> tuple[int, str, str]:
    """Shell out to claude-accounts.ps1 with the given -Action + extra args."""
    if not ACCOUNTS_PS1 or not ACCOUNTS_PS1.exists():
        return (127, "", "claude-accounts.ps1 missing")
    cmd = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
           "-File", str(ACCOUNTS_PS1), "-Action", action, *extra]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=timeout, errors="replace")
        return (r.returncode, r.stdout or "", r.stderr or "")
    except Exception as e:
        return (1, "", str(e))


# RKOJ-ELENO :: 2026-05-24T22:50Z :: OAuth-pivot bridge. claude-oauth-accounts.ps1
# handles login/use/active/list/logoutslot/rotate for Max-plan slots.
OAUTH_PS1 = (SANCTUM_ROOT / "automations" / "claude-oauth-accounts.ps1") if SANCTUM_ROOT else None


def _ps1_oauth(action: str, *extra: str, timeout: int = 300) -> tuple[int, str, str]:
    """Shell out to claude-oauth-accounts.ps1 with the given -Action + extra args.
    Longer default timeout because Login is interactive (operator clicks OAuth in
    browser, then presses Enter -- can take a minute or two).
    """
    if not OAUTH_PS1 or not OAUTH_PS1.exists():
        return (127, "", "claude-oauth-accounts.ps1 missing")
    cmd = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
           "-File", str(OAUTH_PS1), "-Action", action, *extra]
    try:
        # Login is interactive -- inherit stdio so operator can interact with the prompt.
        if action == "Login":
            r = subprocess.run(cmd, timeout=timeout)
            return (r.returncode, "", "")
        r = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=timeout, errors="replace")
        return (r.returncode, r.stdout or "", r.stderr or "")
    except Exception as e:
        return (1, "", str(e))


def _parse_utc(s):
    if not s:
        return None
    try:
        s2 = s.replace("Z", "+00:00") if s.endswith("Z") else s
        return datetime.fromisoformat(s2)
    except Exception:
        return None


def _fmt_dur(td):
    if td is None:
        return "-"
    secs = int(td.total_seconds())
    if secs < 0:
        return "0m"
    h, rem = divmod(secs, 3600)
    m, _ = divmod(rem, 60)
    return f"{h}h{m:02d}m" if h > 0 else f"{m}m"


def _bar(pct: int, width: int = 20, semantic: str = "used") -> str:
    """Return a colored block-bar of fixed width with pct fill (0-100).

    semantic:
      "used"      high % = consumed quota = FAIL color (default; new usage bar)
      "remaining" high % = headroom = OK color (modal popup historical use)
    """
    filled = max(0, min(width, int(round(width * pct / 100))))
    empty = width - filled
    if semantic == "remaining":
        col = C["OK"] if pct > 60 else (C["WARN"] if pct > 25 else C["FAIL"])
    else:
        col = C["OK"] if pct < 60 else (C["WARN"] if pct < 90 else C["FAIL"])
    # ASCII-safe block characters (avoid PowerShell unicode-blockdraw parse fails).
    return f"{col}{'#' * filled}{C['DIM']}{'-' * empty}{C['RESET']}"


# ---------------------------------------------------------------------------
# Accounts status block (call _render_accounts_panel from eve.py when present).
# ---------------------------------------------------------------------------

def _render_status_block() -> None:
    """Render the accounts status block. Prefers eve.py's _render_accounts_panel."""
    try:
        import eve  # noqa: WPS433
        if hasattr(eve, "_render_accounts_panel"):
            eve._render_accounts_panel()
            return
    except Exception:
        pass
    # Fallback: render an inline compact panel.
    # RKOJ-ELENO :: 2026-05-25 :: operator hard-canonical "stop having account
    # capped at 4 and just have it be per account. like show when its unlinked
    # things like that." Dropped the "N/M" denominator (implied a cap); added
    # an explicit unlinked count so the operator sees enabled-but-missing-creds
    # slots in the fallback render path too.
    data = _load_accounts()
    if not data:
        print(f"  {C['DIM']}(no accounts.json){C['RESET']}")
        return
    accts = data.get("accounts", [])
    enabled = sum(1 for a in accts if a.get("enabled"))
    unlinked = sum(1 for a in accts if a.get("enabled") and not a.get("linked", True))
    unlinked_tag = (f"  {C['WARN']}{unlinked} UNLINKED{C['RESET']}"
                    if unlinked > 0 else "")
    print(f"  {C['WHITE']}{C['BOLD']}Claude accounts{C['RESET']} "
          f"{C['BRIGHTP']}{enabled} enabled{C['RESET']}{unlinked_tag}  "
          f"{C['DIM']}{data.get('rotation_strategy', '?')}{C['RESET']}")


# ---------------------------------------------------------------------------
# Usage status bar -- PROXY (5h rolling spawn count vs. tier soft cap).
# Operator 2026-05-25 (image #67): "leave out wrong info. like saying its
# 100%. its fucking not. review how jcode track their usaage". This panel
# does NOT pull real Anthropic-side usage; it counts spawns from
# _shared-memory/spawned-windows.jsonl in the last 5h and divides by a
# tier-aware soft cap (Max 20x = 50, Pro = 12, etc). For the REAL Anthropic
# /oauth/usage utilization (matches the claude.ai/usage dashboard) see the
# 4-bar live readout in eve.py _render_accounts_panel (default OAuth slot
# only). jcode pattern documented in
# _shared-memory/knowledge/jcode-usage-tracking-pattern-2026-05-25.md.
# Every spawn-count row is rendered with a [PROXY] badge so the operator
# cannot mistake it for measured data.
# ---------------------------------------------------------------------------

def _probe_real_usage(plan_tier: str = "max", window_hours: int = 5) -> dict | None:
    """Shell out to claude-usage-meter.ps1 for transcript-summed token + msg counts.

    NOTE (RKOJ-ELENO 2026-05-25): the name "_probe_real_usage" is HISTORICAL
    only. The underlying claude-usage-meter.ps1 is a transcript-sum estimate,
    NOT a real Anthropic-side measurement. DEPRECATED for primary display --
    the meter summed every transcript record (e.g. 8490) and divided by a
    hardcoded 500-msg guess, producing nonsense "999% used" rows (screenshot
    #57, 2026-05-25). Use _spawn_window_usage() below for the per-account
    5h-window proxy instead. The only MEASURED source is the Anthropic
    /oauth/usage endpoint, called via anthropic-usage-probe.ps1 and rendered
    as the 4-bar live readout in eve.py.
    """
    if not SANCTUM_ROOT:
        return None
    meter = SANCTUM_ROOT / "automations" / "claude-usage-meter.ps1"
    if not meter.exists():
        return None
    try:
        r = subprocess.run(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
             "-File", str(meter), "-Mode", "Json",
             "-PlanTier", plan_tier, "-WindowHours", str(window_hours)],
            capture_output=True, text=True, timeout=30, errors="replace",
        )
        if r.returncode != 0:
            return None
        return json.loads(r.stdout)
    except Exception:
        return None


# RKOJ-ELENO :: 2026-05-25 :: spawn-window usage replaces the bad
# transcript-msg fallback. Counts spawns from spawned-windows.jsonl whose
# `account_name` matches AND `started` is within last 5h. Divides by a
# tier-aware soft cap. See account_info_panel._usage_pct for shared math.
_WINDOW_CAP_BY_TIER: dict[str, int] = {
    "max": 50, "max20": 50, "max_20x": 50,
    "max_5x": 20, "max5": 20,
    "pro": 12, "team": 80, "enterprise": 200,
}
_WINDOW_CAP_DEFAULT = 30


def _spawn_window_usage(account_name: str, plan_tier: str) -> dict:
    """Return {pct, spawns, cap, over_limit} for a 5h rolling window."""
    if not SANCTUM_ROOT:
        return {"pct": 0, "spawns": 0, "cap": _WINDOW_CAP_DEFAULT, "over_limit": False}
    jsonl = SANCTUM_ROOT / "_shared-memory" / "spawned-windows.jsonl"
    cap = _WINDOW_CAP_BY_TIER.get((plan_tier or "").strip().lower(), _WINDOW_CAP_DEFAULT)
    if not jsonl.exists() or not account_name:
        return {"pct": 0, "spawns": 0, "cap": cap, "over_limit": False}
    cutoff = datetime.now(timezone.utc) - timedelta(hours=5)
    spawns = 0
    try:
        with jsonl.open("r", encoding="utf-8", errors="replace") as fp:
            for ln in fp.readlines()[-500:]:
                ln = ln.strip()
                if not ln or account_name not in ln:
                    continue
                try:
                    row = json.loads(ln)
                except Exception:
                    continue
                if (row.get("account_name") or "").strip() != account_name:
                    continue
                ts = row.get("started") or ""
                try:
                    s = datetime.fromisoformat(ts.replace("Z", "+00:00") if ts.endswith("Z") else ts)
                    s_utc = s.astimezone(timezone.utc)
                except Exception:
                    continue
                if s_utc >= cutoff:
                    spawns += 1
    except Exception:
        pass
    over_limit = spawns > cap
    pct = min(100, int(round(100.0 * spawns / cap))) if cap > 0 else 0
    return {"pct": pct, "spawns": spawns, "cap": cap, "over_limit": over_limit}


def _render_usage_status_bar(data: dict) -> None:
    """One color-coded line per account showing PROXY usage + status icon.

    Every active row carries a [PROXY] badge -- this panel does not pull
    real Anthropic-side utilization. The MEASURED 4-bar readout (session /
    weekly / sonnet / design from /oauth/usage) renders in
    eve._render_accounts_panel for the default OAuth slot only.
    """
    accts = data.get("accounts", [])
    if not accts:
        return
    now = datetime.now(timezone.utc)
    default_name = data.get("default", "")

    # RKOJ-ELENO :: 2026-05-25 :: operator hard-canonical "leave out wrong info.
    # like saying its 100%. its fucking not". Header explicitly calls out PROXY
    # so the operator never confuses spawn-count math with real Anthropic-side
    # quota burn. See jcode-usage-tracking-pattern-2026-05-25.md for the real-
    # data path we want to migrate to.
    print()
    print(f"  {C['SOFT']}Usage status bar{C['RESET']}  "
          f"{C['WARN']}[PROXY]{C['RESET']}  "
          f"{C['DIM']}(5h spawn-count vs tier soft cap -- NOT Anthropic-side %){C['RESET']}")

    for i, a in enumerate(accts):
        name = a.get("name", "?")
        label = a.get("label", name)
        tier = (a.get("plan_tier") or "?").strip() or "?"
        enabled = a.get("enabled", False)
        # RKOJ-ELENO :: 2026-05-25 :: surface unlinked accounts so they don't
        # masquerade as healthy. Operator hard-canonical: show when its unlinked.
        is_linked = bool(a.get("linked", True))
        today = a.get("successful_spawns_today", 0)
        rate_lim = _parse_utc(a.get("rate_limited_until_utc"))

        # Determine usage % per slot using REAL spawn-window data.
        if not enabled:
            icon = f"{C['DIM']}o{C['RESET']}"
            bar = f"{C['DIM']}[disabled]{C['RESET']}"
            tail = ""
        elif not is_linked:
            icon = f"{C['WARN']}?{C['RESET']}"
            bar = f"{C['WARN']}[unlinked - run Login/SetKey]{C['RESET']}"
            tail = f"  {C['DIM']}today {today}{C['RESET']}"
        elif rate_lim and rate_lim > now:
            icon = f"{C['FAIL']}x{C['RESET']}"
            bar = f"{C['FAIL']}[rate-limited {_fmt_dur(rate_lim - now)}]{C['RESET']}"
            tail = f"  {C['DIM']}today {today}{C['RESET']}"
        else:
            usage = _spawn_window_usage(name, tier)
            pct = usage["pct"]
            spawns = usage["spawns"]
            cap = usage["cap"]
            over = usage["over_limit"]
            if over:
                icon = f"{C['FAIL']}!{C['RESET']}"
            elif pct < 60:
                icon = f"{C['OK']}*{C['RESET']}"
            elif pct < 85:
                icon = f"{C['WARN']}^{C['RESET']}"
            else:
                icon = f"{C['FAIL']}!{C['RESET']}"
            bar = _bar(pct)
            over_tag = f"  {C['FAIL']}OVER LIMIT{C['RESET']}" if over else ""
            # RKOJ-ELENO :: 2026-05-25 :: operator hard-canonical "saying its
            # 100% its fucking not". Always prefix the [PROXY] badge and the
            # tilde so the operator cannot read this as measured truth.
            tail = (f"  {C['WARN']}[PROXY]{C['RESET']}  "
                    f"{C['WHITE']}~{pct}% of soft cap{C['RESET']}  "
                    f"{C['DIM']}({spawns}/{cap} spawns this 5h){C['RESET']}  "
                    f"{C['DIM']}today {today}{C['RESET']}{over_tag}")

        idx_tag = f"{C['BRIGHTP']}{i+1:>2}.{C['RESET']}"
        label_inline = f"{C['WHITE']}{label}{C['RESET']} {C['DIM']}[{C['RESET']}{C['PURPLE']}{tier}{C['RESET']}{C['DIM']}]{C['RESET']}"
        print(f"  {idx_tag} {icon}  {label_inline}  {bar}{tail}")


# ---------------------------------------------------------------------------
# Action sub-flows
# ---------------------------------------------------------------------------

_SLOT_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,30}$")


def _slugify_slot(raw: str) -> str:
    """Auto-slug operator input. 'Sinister Gmail' -> 'sinister-gmail'.
    Operator 2026-05-24T22:50Z: typed 'Sinister Gmail' and got rejected by
    the strict regex. We now ACCEPT arbitrary input + auto-normalize to a
    lowercase dash-joined slug that fits the underlying storage rules.
    Returns '' if input is empty after normalization.
    """
    s = (raw or "").strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-_")
    if len(s) > 31:
        s = s[:31].rstrip("-_")
    if not s or not _SLOT_RE.match(s):
        return ""
    return s


def _prompt_slot(data: dict, action_label: str) -> dict | None:
    """Prompt operator to pick a slot by index (returns the account dict)."""
    accts = data.get("accounts", [])
    if not accts:
        print(f"  {C['WARN']}no accounts to {action_label}{C['RESET']}")
        return None
    try:
        raw = input(f"  {C['WHITE']}> slot # to {action_label}:{C['RESET']} ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return None
    if not raw.isdigit():
        print(f"  {C['WARN']}not a number{C['RESET']}")
        return None
    idx = int(raw) - 1
    if idx < 0 or idx >= len(accts):
        print(f"  {C['WARN']}out of range (1-{len(accts)}){C['RESET']}")
        return None
    return accts[idx]


# RKOJ-ELENO :: 2026-05-25T01:15Z :: operator "reduce this to jsut have login,
# logout ... remove api key". The menu now only surfaces L) Login and O) Logout.
# The functions below are DEPRECATED and no longer wired into the menu — kept
# only as documentation of removed surface area. Future cleanup may delete them
# outright once no external callers reference them.
#
# Removed from menu:
#   _action_add            (chooser between OAuth/API-key)
#   _action_add_apikey     (legacy API key flow)
#   _action_bulk_setup     (P) bulk OAuth wizard)
#   _action_mark_limited   (M) mark limited)
#   _action_active_slot    (V) show active OAuth slot)
#   _action_rename         (R) rename slot)
#   _action_enable_disable (E) toggle enabled flag)
#   _action_delete         (D) delete slot)
#   _action_usage_popup    (U) jcode-style usage overlay) — token analytics
#
# Status refresh: no longer a discrete action. _load_accounts() runs at the top
# of every show_account_manager() loop iteration, so the panel auto-refreshes
# on every keystroke (Enter included).


def _action_oauth_login() -> None:
    """Walk operator through OAuth scaffold: slot name -> Login (interactive)."""
    try:
        raw = input(f"  {C['WHITE']}> slot name (any text -- 'Sinister Gmail' -> 'sinister-gmail'):{C['RESET']} ").strip()
    except (EOFError, KeyboardInterrupt):
        return
    slot = _slugify_slot(raw)
    if not slot:
        print(f"  {C['WARN']}could not slugify '{raw}' (need at least one alphanumeric char){C['RESET']}")
        return
    if slot != raw.lower():
        print(f"  {C['DIM']}(normalized to slot='{slot}'){C['RESET']}")
    try:
        display = input(f"  {C['WHITE']}> display name (e.g. 'Sinister Gmail', Enter to derive from email):{C['RESET']} ").strip()
    except (EOFError, KeyboardInterrupt):
        return
    extra = ["-Name", slot]
    if display:
        extra += ["-DisplayName", display]
    print(f"  {C['SOFT']}> Login -Name {slot} (interactive -- follow prompts){C['RESET']}")
    rc, _out, _err = _ps1_oauth("Login", *extra, timeout=600)
    if rc == 0:
        print(f"  {C['OK']}[+] OAuth slot '{slot}' captured & enabled.{C['RESET']}")
    else:
        print(f"  {C['FAIL']}[!] OAuth Login failed/aborted (exit {rc}).{C['RESET']}")


def _action_add_apikey(open_browser: bool = False) -> None:
    """Legacy API-key add path. Uses Console pay-as-you-go billing (NOT Max plan)."""
    if open_browser:
        print(f"  {C['SOFT']}> opening console.anthropic.com keys page in browser ...{C['RESET']}")
        try:
            webbrowser.open("https://console.anthropic.com/settings/keys")
        except Exception as e:
            print(f"  {C['WARN']}(browser open failed: {e} -- open manually){C['RESET']}")
        print(f"  {C['DIM']}Steps: Settings -> API Keys -> Create Key -> copy sk-ant-...{C['RESET']}")
    try:
        raw = input(f"  {C['WHITE']}> slot name (any text -- 'Sinister Gmail' -> 'sinister-gmail'):{C['RESET']} ").strip()
    except (EOFError, KeyboardInterrupt):
        return
    slot = _slugify_slot(raw)
    if not slot:
        print(f"  {C['WARN']}could not slugify '{raw}' (need at least one alphanumeric char){C['RESET']}")
        return
    if slot != raw.lower():
        print(f"  {C['DIM']}(normalized to slot='{slot}'){C['RESET']}")
    try:
        label = input(f"  {C['WHITE']}> label (e.g. 'me@x.com (work)', Enter to skip):{C['RESET']} ").strip()
        api_key = getpass.getpass(f"  {C['WHITE']}> API key (sk-ant-... HIDDEN):{C['RESET']} ").strip()
    except (EOFError, KeyboardInterrupt):
        return
    if not api_key.startswith("sk-ant-"):
        print(f"  {C['WARN']}API key must start with 'sk-ant-' (got '{api_key[:8]}...'){C['RESET']}")
        return
    extra = ["-Name", slot, "-ApiKey", api_key]
    if label:
        extra += ["-Label", label]
    print(f"  {C['SOFT']}> SetKey -Name {slot} -ApiKey sk-ant-***{C['RESET']}")
    rc, out, err = _ps1("SetKey", *extra, timeout=20)
    for line in out.splitlines():
        print(f"    {line}")
    if rc == 0:
        print(f"  {C['OK']}[+] Slot '{slot}' added & enabled (api_key mode).{C['RESET']}")
        print(f"  {C['SOFT']}> ResolveEmails (auto-detect email from profile API){C['RESET']}")
        _ps1("ResolveEmails", timeout=30)
    else:
        print(f"  {C['FAIL']}[!] SetKey failed (exit {rc}): {err[:200]}{C['RESET']}")


def _action_bulk_setup() -> None:
    """Bulk setup: delegate to automations/eve-bulk-oauth-login.ps1.

    Operator hard-canonical 2026-05-24 ~23:10Z: "do all this for me and in
    built it all into eve ... this entire round robin needs to be auto."

    The canonical bulk-setup flow now lives in PowerShell (eve-bulk-oauth-
    login.ps1) so the Desktop BAT and EVE.exe both use the same code path.
    We shell out to it in a NEW console window via `start /WAIT` so the
    interactive prompts work cleanly and EVE.exe stays responsive in the
    background. When the wizard exits the operator returns here.
    """
    if not SANCTUM_ROOT:
        print(f"  {C['FAIL']}[bulk] SANCTUM_ROOT not resolved -- cannot launch wizard.{C['RESET']}")
        return
    wizard = SANCTUM_ROOT / "automations" / "eve-bulk-oauth-login.ps1"
    if not wizard.exists():
        print(f"  {C['FAIL']}[bulk] wizard missing: {wizard}{C['RESET']}")
        return
    print()
    print(f"  {C['WHITE']}{C['BOLD']}Launching bulk OAuth login wizard...{C['RESET']}")
    print(f"  {C['DIM']}  (Account Manager will resume when wizard exits; no extra window){C['RESET']}")
    print()
    try:
        # RKOJ-ELENO :: 2026-05-25T01:35Z :: operator "enter here doesnt work i
        # need allow flows to allow for unlimited use ... and now it wont
        # fucking close". Previous impl used `cmd /c start /WAIT "Title" ps1`
        # which spawned an EXTRA `start` cmd window that lingered after the
        # inner powershell exited -- operator perceived "stuck". Switched to
        # direct subprocess.run on powershell.exe (inherits this console, no
        # extra window, exits cleanly so control snaps back to the manager
        # menu loop). The wizard itself uses Start-Sleep auto-close at end.
        cmd = [
            "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
            "-File", str(wizard),
        ]
        subprocess.run(cmd, check=False)
        print()
        print(f"  {C['OK']}[bulk] wizard exited -- returning to Account Manager.{C['RESET']}")
        # Brief pause so the operator sees the "returning" msg before the
        # manager loop re-renders the header on the next iteration.
        time.sleep(0.6)
    except Exception as e:
        print(f"  {C['FAIL']}[bulk] launch failed: {e}{C['RESET']}")
        time.sleep(1.0)


def _action_mark_limited(data: dict) -> None:
    """Operator-set 'limited til <date>' for a slot.

    Operator hard-canonical 2026-05-24T22:50Z: "limited til monday" is a common
    operator override when an account is known to be capped past the rolling 5h.
    """
    acct = _prompt_slot(data, "mark as rate-limited")
    if not acct:
        return
    name = acct.get("name")
    print(f"  {C['DIM']}Examples: '2026-05-30T00:00:00Z' (Monday 00:00 UTC){C['RESET']}")
    try:
        until = input(f"  {C['WHITE']}> rate-limited until (ISO-8601 UTC):{C['RESET']} ").strip()
    except (EOFError, KeyboardInterrupt):
        return
    if not until:
        print(f"  {C['DIM']}(no change){C['RESET']}")
        return
    try:
        weekly_in = input(f"  {C['WHITE']}> weekly cap reset? [y/N]:{C['RESET']} ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        return
    extra = ["-Name", name, "-Until", until]
    if weekly_in in ("y", "yes"):
        extra.append("-Weekly")
    rc, out, err = _ps1_oauth("MarkLimited", *extra, timeout=15)
    for line in out.splitlines():
        print(f"    {line}")
    if rc == 0:
        print(f"  {C['OK']}[+] '{name}' marked limited until {until}.{C['RESET']}")
    else:
        print(f"  {C['FAIL']}[!] MarkLimited failed (exit {rc}): {err[:200]}{C['RESET']}")


def _action_active_slot() -> None:
    """Show which OAuth slot is currently active (matches ~/.claude/.credentials.json)."""
    print(f"  {C['SOFT']}> Active (compare ~/.claude/.credentials.json hash to known slots){C['RESET']}")
    rc, out, err = _ps1_oauth("Active", timeout=10)
    for line in out.splitlines():
        print(f"    {line}")
    if rc != 0 and err:
        print(f"  {C['WARN']}(stderr: {err[:200]}){C['RESET']}")


def _action_logout(data: dict) -> None:
    """Logout: disable the slot + remove credentials_file if Sanctum-owned.

    For OAuth slots, routes through claude-oauth-accounts.ps1 LogoutSlot (which
    also clears active .credentials.json if it was the active slot).
    """
    acct = _prompt_slot(data, "logout")
    if not acct:
        return
    name = acct.get("name")
    creds_file = acct.get("credentials_file")
    auth_mode = acct.get("auth_mode", "api_key")
    if auth_mode == "oauth":
        print(f"  {C['SOFT']}> OAuth LogoutSlot -Name {name}{C['RESET']}")
        rc, out, err = _ps1_oauth("LogoutSlot", "-Name", name, timeout=15)
        for line in out.splitlines():
            print(f"    {line}")
        if rc == 0:
            print(f"  {C['OK']}[+] OAuth slot '{name}' logged out.{C['RESET']}")
        else:
            print(f"  {C['FAIL']}[!] OAuth LogoutSlot failed (exit {rc}): {err[:200]}{C['RESET']}")
        return
    print(f"  {C['SOFT']}> Disable -Name {name}{C['RESET']}")
    rc, out, err = _ps1("Disable", "-Name", name)
    for line in out.splitlines():
        print(f"    {line}")
    if rc != 0:
        print(f"  {C['FAIL']}[!] Disable failed (exit {rc}): {err[:200]}{C['RESET']}")
        return
    # Remove credentials file if it lives under the standard Sanctum-owned path.
    if creds_file:
        cp = Path(creds_file)
        if cp.exists() and "\\.claude\\credentials." in str(cp).lower():
            try:
                cp.unlink()
                print(f"  {C['OK']}[-] removed {cp.name}{C['RESET']}")
            except Exception as e:
                print(f"  {C['WARN']}could not remove credentials file: {e}{C['RESET']}")
    print(f"  {C['OK']}[+] Slot '{name}' logged out.{C['RESET']}")


def _action_rename(data: dict) -> None:
    """Rename: change the `label` field in-place via JSON edit (no SetLabel in PS1 yet)."""
    acct = _prompt_slot(data, "rename")
    if not acct:
        return
    name = acct.get("name")
    cur = acct.get("label", "")
    try:
        new = input(f"  {C['WHITE']}> new label for '{name}' (current: '{cur}'):{C['RESET']} ").strip()
    except (EOFError, KeyboardInterrupt):
        return
    if not new:
        print(f"  {C['DIM']}(no change){C['RESET']}")
        return
    # Re-read to avoid losing concurrent edits, then patch + save.
    fresh = _load_accounts()
    if not fresh:
        return
    for a in fresh.get("accounts", []):
        if a.get("name") == name:
            a["label"] = new
            break
    if _save_accounts(fresh):
        print(f"  {C['OK']}[+] '{name}' label -> '{new}'{C['RESET']}")


def _action_enable_disable(data: dict) -> None:
    """Toggle enabled flag for selected slot."""
    acct = _prompt_slot(data, "enable/disable")
    if not acct:
        return
    name = acct.get("name")
    action = "Disable" if acct.get("enabled") else "Enable"
    print(f"  {C['SOFT']}> {action} -Name {name}{C['RESET']}")
    rc, out, err = _ps1(action, "-Name", name)
    for line in out.splitlines():
        print(f"    {line}")
    if rc == 0:
        print(f"  {C['OK']}[+] {name} -> {action.lower()}d{C['RESET']}")
    else:
        print(f"  {C['FAIL']}[!] {action} failed (exit {rc}){C['RESET']}")


def _action_delete(data: dict) -> None:
    """Delete: prompt slot, require type-to-confirm, call Remove."""
    acct = _prompt_slot(data, "delete")
    if not acct:
        return
    name = acct.get("name")
    print(f"  {C['WARN']}This will REMOVE slot '{name}' permanently.{C['RESET']}")
    try:
        confirm = input(f"  {C['WHITE']}> type '{name}' to confirm:{C['RESET']} ").strip()
    except (EOFError, KeyboardInterrupt):
        return
    if confirm != name:
        print(f"  {C['DIM']}(confirmation did not match — aborted){C['RESET']}")
        return
    rc, out, err = _ps1("Remove", "-Name", name)
    for line in out.splitlines():
        print(f"    {line}")
    if rc == 0:
        print(f"  {C['OK']}[+] '{name}' removed{C['RESET']}")
    else:
        print(f"  {C['FAIL']}[!] Remove failed (exit {rc}): {err[:200]}{C['RESET']}")


# ---------------------------------------------------------------------------
# Usage popup (jcode-style overlay) — modal showing detail_lines for one slot.
# ---------------------------------------------------------------------------

def _recent_log_lines(name: str, limit: int = 5) -> list[str]:
    """Tail recent log lines that mention this account name."""
    if not ACCOUNTS_LOG or not ACCOUNTS_LOG.exists():
        return []
    try:
        with ACCOUNTS_LOG.open("r", encoding="utf-8", errors="replace") as fp:
            tail = fp.readlines()[-400:]
    except Exception:
        return []
    hits = [ln.rstrip() for ln in tail if name in ln]
    return hits[-limit:]


def _action_usage_popup(data: dict) -> None:
    """jcode-style usage overlay for one slot. Modal — Enter returns to manager."""
    acct = _prompt_slot(data, "show usage popup for")
    if not acct:
        return
    name = acct.get("name")
    label = acct.get("label", name)
    tier = acct.get("plan_tier", "?")
    enabled = acct.get("enabled", False)
    today = acct.get("successful_spawns_today", 0)
    sess = acct.get("current_sessions", 0)
    cap = acct.get("max_sessions_concurrent", 0)
    rate_lim = _parse_utc(acct.get("rate_limited_until_utc"))
    last_429 = _parse_utc(acct.get("last_429_at_utc"))
    last_spawn = _parse_utc(acct.get("last_spawn_at_utc"))
    creds_file = acct.get("credentials_file", "?")
    now = datetime.now(timezone.utc)
    window_secs = 5 * 3600

    # Status classification (jcode UsageOverlayStatus parity).
    if not enabled:
        status_label, status_col, icon = "disabled", C["DIM"], "o"
    elif rate_lim and rate_lim > now:
        status_label, status_col, icon = "rate-limited", C["FAIL"], "x"
    elif last_spawn:
        elapsed = (now - last_spawn).total_seconds()
        if elapsed >= window_secs:
            status_label, status_col, icon = "healthy (fresh)", C["OK"], "*"
        else:
            pct = 100 - int(100 * elapsed / window_secs)
            if pct > 60:
                status_label, status_col, icon = "healthy", C["OK"], "*"
            elif pct > 25:
                status_label, status_col, icon = "watch", C["WARN"], "^"
            else:
                status_label, status_col, icon = "high", C["FAIL"], "!"
    else:
        status_label, status_col, icon = "healthy (no spawns yet)", C["OK"], "*"

    # Render the modal box.
    print()
    print(f"  {C['DARKP']}{'=' * 70}{C['RESET']}")
    print(f"  {C['WHITE']}{C['BOLD']}Usage popup{C['RESET']}  "
          f"{status_col}{icon} {status_label}{C['RESET']}  "
          f"{C['DIM']}(jcode-style overlay){C['RESET']}")
    print(f"  {C['DARKP']}{'-' * 70}{C['RESET']}")
    print(f"  {C['SOFT']}slot{C['RESET']}        {C['WHITE']}{name}{C['RESET']}")
    print(f"  {C['SOFT']}label{C['RESET']}       {C['WHITE']}{label}{C['RESET']}")
    print(f"  {C['SOFT']}plan tier{C['RESET']}   {C['PURPLE']}{tier}{C['RESET']}")
    print(f"  {C['SOFT']}enabled{C['RESET']}     "
          f"{(C['OK'] + 'ON') if enabled else (C['DIM'] + 'OFF')}{C['RESET']}")
    print(f"  {C['SOFT']}sessions{C['RESET']}    {C['WHITE']}{sess}/{cap}{C['RESET']}")
    print(f"  {C['SOFT']}today{C['RESET']}       {C['WHITE']}{today}{C['RESET']} spawns")

    # 5h-window state
    if last_spawn is None:
        win_str = f"{C['DIM']}fresh{C['RESET']}"
    else:
        elapsed = (now - last_spawn).total_seconds()
        if elapsed >= window_secs:
            win_str = f"{C['DIM']}fresh (last spawn > 5h ago){C['RESET']}"
        else:
            pct = 100 - int(100 * elapsed / window_secs)
            remaining = window_secs - elapsed
            col = C["OK"] if pct > 60 else (C["WARN"] if pct > 25 else C["FAIL"])
            win_str = f"{col}{pct}% remaining  ({_fmt_dur(timedelta(seconds=remaining))}){C['RESET']}"
    print(f"  {C['SOFT']}5h window{C['RESET']}   {win_str}")

    # Rate-limit state
    if rate_lim and rate_lim > now:
        print(f"  {C['SOFT']}rate-lim{C['RESET']}    {C['FAIL']}ACTIVE until {rate_lim.isoformat()} "
              f"({_fmt_dur(rate_lim - now)} left){C['RESET']}")
    elif last_429:
        print(f"  {C['SOFT']}rate-lim{C['RESET']}    {C['DIM']}cleared (last 429: {last_429.isoformat()}){C['RESET']}")
    else:
        print(f"  {C['SOFT']}rate-lim{C['RESET']}    {C['OK']}clean (no 429s){C['RESET']}")

    print(f"  {C['SOFT']}creds file{C['RESET']}  {C['DIM']}{creds_file}{C['RESET']}")

    # Recent log events
    hits = _recent_log_lines(name, limit=5)
    if hits:
        print(f"  {C['DARKP']}{'-' * 70}{C['RESET']}")
        print(f"  {C['SOFT']}recent events:{C['RESET']}")
        for ln in hits:
            print(f"    {C['DIM']}{ln}{C['RESET']}")

    print(f"  {C['DARKP']}{'=' * 70}{C['RESET']}")
    try:
        input(f"  {C['DIM']}> press Enter to return:{C['RESET']} ")
    except (EOFError, KeyboardInterrupt):
        pass


# ---------------------------------------------------------------------------
# Main entry — show_account_manager()
# ---------------------------------------------------------------------------

def _clear_screen() -> None:
    """Wipe terminal + cursor home so a fresh sub-page renders on blank surface.

    RKOJ-ELENO :: 2026-05-25T00:15Z :: operator "each menu needs to go to a
    complete clean new menu that is clean and you cannot see the menu you
    just came from". No-op when NO_COLOR / TERM=dumb on POSIX.
    """
    if "NO_COLOR" in os.environ:
        return
    if os.environ.get("TERM", "").lower() == "dumb" and os.name != "nt":
        return
    try:
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()
    except Exception:
        pass


def _render_header() -> None:
    _clear_screen()
    print()
    print(f"  {C['DARKP']}---{C['RESET']} {C['WHITE']}{C['BOLD']}Account Manager{C['RESET']} "
          f"{C['DARKP']}---{C['RESET']}")
    print()


def _render_actions_menu() -> None:
    # RKOJ-ELENO :: 2026-05-25T01:15Z :: operator "reduce this to jsut have
    # login, logout (select account on it) status refresh needs to happen auto.
    # remove api key". Menu pared down to 2 actions; status auto-refreshes on
    # every loop iteration via _load_accounts() at the top of show_account_manager.
    #
    # RKOJ-ELENO :: 2026-05-25T01:15Z :: operator hard-canonical (image #62)
    # *"centered menu styling like main_menu hero applied to every sub-page"*.
    # Actions block now block-centers via eve_ui.center_block.
    body: list[str] = []
    body.append(f"{C['SOFT']}Actions:{C['RESET']}")
    body.append(f"  {C['PURPLE']}L){C['RESET']} {C['OK']}Login{C['RESET']}   "
                f"{C['DIM']}add a Claude account via OAuth{C['RESET']}")
    body.append(f"  {C['PURPLE']}O){C['RESET']} {C['OK']}Logout{C['RESET']}  "
                f"{C['DIM']}select an account to log out{C['RESET']}")
    print()
    try:
        import sys as _sys
        from pathlib import Path as _P
        _here = _P(__file__).resolve().parent
        if str(_here) not in _sys.path:
            _sys.path.insert(0, str(_here))
        from eve_ui import center_block  # type: ignore
        for ln in center_block(body, width=64):
            print(ln)
    except Exception:
        for ln in body:
            print(f"  {ln}")
    print()
    print(f"  {C['DIM']}---{C['RESET']} "
          f"{C['PURPLE']}L){C['RESET']} Login   "
          f"{C['PURPLE']}O){C['RESET']} Logout   "
          f"{C['PURPLE']}B){C['RESET']} Back   "
          f"{C['PURPLE']}X){C['RESET']} Exit   "
          f"{C['DIM']}(status auto-refreshes){C['RESET']}")


def _route_home() -> None:
    """Dispatch to main menu. Best-effort import (sibling module)."""
    try:
        from main_menu import show_main_menu  # type: ignore
        show_main_menu()
    except Exception:
        pass


def show_account_manager() -> None:
    """Main loop. Sister-B wires `M) Account Manager` in eve.py to this."""
    if not SANCTUM_ROOT or not ACCOUNTS_JSON or not ACCOUNTS_PS1:
        print(f"  {C['FAIL']}[account-manager] SANCTUM_ROOT not resolved — cannot run.{C['RESET']}")
        time.sleep(1.5)
        return

    while True:
        _render_header()
        # 0. RKOJ-ELENO :: 2026-05-24T23:30Z :: operator "i need to see info about
        #    the calude accounts and progres bar of usage. running agents per
        #    accounts etc. things like that." Per-account usage panel with
        #    5h-window progress bar + live-PID running-agents list.
        try:
            from account_info_panel import render_account_info_block  # type: ignore
            render_account_info_block(detailed=True)
        except Exception as e:
            print(f"  {C['WARN']}[acct-info] panel unavailable: {e}{C['RESET']}")
        # 1. Existing accounts status panel (preserved per operator).
        _render_status_block()
        # 2. jcode-style usage status bar (REPLACES the sessions cur/cap row).
        data = _load_accounts()
        if data:
            _render_usage_status_bar(data)
        # 3. Actions menu + footer.
        _render_actions_menu()

        try:
            resp = input(f"  {C['DIM']}> {C['RESET']}").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return

        # RKOJ-ELENO :: 2026-05-25T01:15Z :: operator "reduce this to jsut have
        # login, logout (select account on it) status refresh needs to happen
        # auto. remove api key". Dispatch trimmed to L/O + chrome (B/H/X).
        # Any other key falls through to a re-render (auto status refresh).
        if resp in ("b", "back", ""):
            return
        if resp in ("h", "home"):
            _route_home()
            return
        if resp in ("x", "exit", "quit"):
            # RKOJ-ELENO :: 2026-05-25T02:15Z :: hard-exit per operator "wont
            # fucking close" — os._exit bypasses any hung daemon/subprocess.
            try:
                sys.stdout.write("\n  [EVE] goodbye.\n"); sys.stdout.flush()
            except Exception:
                pass
            os._exit(0)
        # RKOJ-ELENO :: 2026-05-25T02:15Z :: cross-page navigation. Operator:
        # "enter here doesnt work i need allow flows to allow for unlimited
        # use. meaning i can keep doing thigns here going to all pages etc".
        # Main-menu shortcut letters from this sub-page route straight to that
        # top-level surface (no bounce through main first). main_menu loop
        # pops _EVE_NAV_TO after this returns and re-dispatches the letter.
        if resp in {"r", "a", "g", "t", "n", "w", "l"}:
            os.environ["_EVE_NAV_TO"] = resp
            return
        # 't' could route to main Tools but operator may also mean "stay here";
        # we treat it as nav since account_manager doesn't have its own 't' action.
        if resp == "t":
            os.environ["_EVE_NAV_TO"] = resp
            return
        if resp == "l":
            # OAuth login (Max-plan slot capture). Parallel agent is fixing the
            # underlying wizard at automations/claude-oauth-accounts.ps1.
            _action_oauth_login()
        elif resp == "o":
            if data:
                _action_logout(data)
        else:
            # Unknown / orphan keys (a/k/r/e/d/u/m/v/p/s) -> silent re-render.
            # The loop already re-reads claude-accounts.json each iteration, so
            # any keystroke effectively triggers a status refresh.
            pass


# ---------------------------------------------------------------------------
# Smoke test entry — `python account_manager.py --smoke` parses + dry-renders.
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if "--smoke" in sys.argv:
        data = _load_accounts()
        if data:
            _render_status_block()
            _render_usage_status_bar(data)
            print(f"  {C['OK']}[smoke] OK — {len(data.get('accounts', []))} accounts loaded{C['RESET']}")
        else:
            print("[smoke] could not load accounts.json (still importable)")
        sys.exit(0)
    show_account_manager()
