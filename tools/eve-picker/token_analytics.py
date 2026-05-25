"""EVE :: Token Analytics sub-page (Accounts tab option 7).

Author: RKOJ-ELENO :: 2026-05-24

Operator verbatim 2026-05-24 ~23:30Z:
    "in parrallel add to teh account tab a token menu so that we can track
     all token use and see places where we can improve our token use and
     make better systems to become more token efficent"

Companion to eve.py + account_manager.py -- thin Python wrapper that shells
out to automations/token-analytics.ps1 (the canonical token sampler that
reuses claude-usage-meter.ps1's transcript-parse strategy and extends it
with per-project / per-session / per-model / cache / waste / recommendations
breakouts).

The Python module exists so the picker-side codepath (and any future
PyInstaller bundle) can call show_token_analytics() without re-implementing
the sub-menu UX. eve.py wraps the same .ps1 calls inline via
_token_analytics_submenu() (sister-A wiring) -- both code paths converge on
the .ps1 as the single token-data source-of-truth.

Layout (per eve-ui-uniformity-doctrine-2026-05-24):

      --- Token Analytics ---

      Action picker:
        1) Summary           (1h / 5h / 24h / 7d windows)
        2) By project        (per-project totals + cache hit + cost)
        3) Cache report      (per-project cache efficiency)
        4) Waste report      (abandoned cache / context bloat / tool loops)
        5) Recommendations   (5-10 prioritized actions)
        6) By session        (top 10 sessions by billable-eq)
        7) By model          (Opus vs Sonnet vs Haiku mix)

      --- B) Back   X) Exit   (R refresh) ---
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path


# ---------------------------------------------------------------------------
# Color tokens -- try to inherit from eve.py; else ANSI fallback (same xterm
# codes used by every other Sanctum-themed surface).
# ---------------------------------------------------------------------------

def _resolve_colors():
    try:
        import eve  # noqa: WPS433 -- sibling when imported from picker
        return {
            "PURPLE": eve.PURPLE, "BRIGHTP": eve.BRIGHTP, "DARKP": eve.DARKP,
            "WHITE": eve.WHITE, "SOFT": eve.SOFT, "DIM": eve.DIM,
            "OK": eve.OK, "WARN": eve.WARN, "FAIL": eve.FAIL,
            "RESET": eve.RESET, "BOLD": eve.BOLD,
        }
    except Exception:
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
# without eve.py on sys.path -- needed for the smoke test contract).
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
        if (p / "automations" / "token-analytics.ps1").exists():
            return p
    return None


SANCTUM_ROOT = _probe_sanctum_root()
TOKEN_PS1 = (SANCTUM_ROOT / "automations" / "token-analytics.ps1") if SANCTUM_ROOT else None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Menu action -> ps1 -Action arg.
_ACTIONS = [
    ("1", "Summary",         "Summary",         "1h / 5h / 24h / 7d windows"),
    ("2", "By project",      "ByProject",       "per-project totals + cache hit + cost"),
    ("3", "Cache report",    "CacheReport",     "per-project cache efficiency"),
    ("4", "Waste report",    "WasteReport",     "abandoned cache / context bloat / tool loops"),
    ("5", "Recommendations", "Recommendations", "5-10 prioritized actions"),
    ("6", "By session",      "BySession",       "top 10 sessions by billable-eq"),
    ("7", "By model",        "ByModel",         "Opus vs Sonnet vs Haiku mix"),
]


def _run_action(action: str, *, top_n: int = 10) -> int:
    """Shell to token-analytics.ps1 -Action <action>. Returns exit code.

    Stdio passes through so the .ps1's colorized output renders inline. We
    add a 60s timeout to match worst-case scan over ~1GB of transcripts.
    """
    if not TOKEN_PS1 or not TOKEN_PS1.exists():
        print(f"  {C['FAIL']}[!] token-analytics.ps1 not found (SANCTUM_ROOT={SANCTUM_ROOT}){C['RESET']}")
        return 127
    args = [
        "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", str(TOKEN_PS1), "-Action", action,
    ]
    if action == "BySession":
        args += ["-TopN", str(top_n)]
    try:
        r = subprocess.run(args, timeout=120)
        return r.returncode
    except subprocess.TimeoutExpired:
        print(f"  {C['FAIL']}[!] timed out scanning transcripts (>120s){C['RESET']}")
        return 124
    except Exception as e:
        print(f"  {C['FAIL']}[!] exception: {e}{C['RESET']}")
        return 1


def _render_header() -> None:
    print()
    print(f"  {C['DARKP']}---{C['RESET']} {C['WHITE']}{C['BOLD']}Token Analytics{C['RESET']} "
          f"{C['DARKP']}---{C['RESET']}")
    print()


def _render_menu() -> None:
    print(f"  {C['SOFT']}Pick a report -- all reports scan ~/.claude/projects/**/*.jsonl in real-time.{C['RESET']}")
    print()
    for key, title, _action, hint in _ACTIONS:
        print(f"    {C['PURPLE']}{key}){C['RESET']} {C['WHITE']}{title:<18}{C['RESET']} "
              f"{C['DIM']}{hint}{C['RESET']}")
    # RKOJ-ELENO :: 2026-05-25T07:17Z Sub-Q :: B4 footer migration -- canonical
    # eve_ui.print_sub_page_footer (now also surfaces Home key for consistency
    # with rest of EVE; previously this page omitted H).
    print()
    try:
        import sys as _sys
        from pathlib import Path as _P
        _here = _P(__file__).resolve().parent
        if str(_here) not in _sys.path:
            _sys.path.insert(0, str(_here))
        from eve_ui import print_sub_page_footer as _psf  # type: ignore
        _psf("R refresh")
    except Exception:
        print(f"  {C['DIM']}---{C['RESET']} "
              f"{C['PURPLE']}B){C['RESET']} Back   "
              f"{C['PURPLE']}H){C['RESET']} Home   "
              f"{C['PURPLE']}X){C['RESET']} Exit   "
              f"{C['DIM']}(R refresh){C['RESET']}")


def _wait_for_enter(prompt: str = "(Enter to return)") -> None:
    try:
        input(f"  {C['DIM']}{prompt}{C['RESET']} ")
    except (EOFError, KeyboardInterrupt):
        pass


def show_token_analytics() -> None:
    """Main loop. Caller from eve.py / account_manager / picker."""
    if not SANCTUM_ROOT or not TOKEN_PS1:
        print(f"  {C['FAIL']}[token-analytics] SANCTUM_ROOT not resolved or token-analytics.ps1 missing.{C['RESET']}")
        time.sleep(1.5)
        return

    while True:
        _render_header()
        _render_menu()
        try:
            resp = input(f"  {C['WHITE']}> [1]:{C['RESET']} ").strip().lower() or "1"
        except (EOFError, KeyboardInterrupt):
            print()
            return

        if resp in ("b", "back", ""):
            return
        if resp in ("x", "exit", "quit"):
            sys.exit(0)
        if resp == "r":
            continue  # re-render

        action = None
        for key, _title, ps_action, _hint in _ACTIONS:
            if resp == key:
                action = ps_action
                break
        if not action:
            print(f"  {C['WARN']}unknown key '{resp}' -- pick 1-7 or B/X.{C['RESET']}")
            time.sleep(0.8)
            continue

        rc = _run_action(action)
        if rc != 0:
            print(f"  {C['WARN']}[!] action '{action}' exited {rc}.{C['RESET']}")
        _wait_for_enter()


# ---------------------------------------------------------------------------
# Smoke test entry -- `python token_analytics.py --smoke` parses + dry-renders.
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if "--smoke" in sys.argv:
        print(f"[smoke] SANCTUM_ROOT={SANCTUM_ROOT}")
        print(f"[smoke] TOKEN_PS1={TOKEN_PS1}")
        print(f"[smoke] TOKEN_PS1 exists: {bool(TOKEN_PS1 and TOKEN_PS1.exists())}")
        print(f"[smoke] _ACTIONS count: {len(_ACTIONS)}")
        # Dry-render the menu (no input prompt).
        _render_header()
        _render_menu()
        print()
        print("[smoke] OK -- module imports + renders without errors")
        sys.exit(0)
    show_token_analytics()
