"""EVE :: Sinister Sanctum session launcher (jcode-style, single entry point)

Author: RKOJ-ELENO :: 2026-05-24

v2 — operator directive 2026-05-24:
    "i want eve exe to work like the jcode exe all features similar system in
     our braning and colors but i want it to be combined in a sense with session
     start and everythinng we have been working on"

This file is now THE single entry point for a Sanctum session. The bat shim
("Sinister Start.bat") is a ~20-line probe that just locates the repo and
hands off to EVE.exe with all argv flags forwarded. Everything that used to
live in the bat (autonomy bootstrap, plugin background install, shell preflight,
account / swarm / loop flags, --diagnose, --setup-autonomy) now lives here.

Architecture:

    eve_picker_lib (D:\\Sinister Sanctum\\tools\\eve-picker\\)
        - render-agnostic picker logic
        - read_projects / read_prefs / visible_projects
        - build_picker_state / resolve_pick / parse_multi
        - banner_text / picker_text_rows

This file (eve.py):
    - SANCTUM_ROOT probe (env -> D:\\Sinister Sanctum -> C:\\... -> %USERPROFILE%)
    - First-run autonomy bootstrap (~/.sanctum-autonomy-granted marker)
    - Background plugin check (DETACHED_PROCESS, non-blocking)
    - Spawn-shell preflight (mintty/git-bash/bash warning)
    - CLI flags: --diagnose / --setup-autonomy / --account / --account-status
                 --swarm / --loop / --both / --no-swarm / --no-loop
                 --version / --help / --profile
    - Animated jcode-style ASCII "C" banner (~8 frames, ~0.07s/frame, ~0.6s total)
    - Polished jcode-feel picker UI with Sanctum purple accents
    - Status line: [account: X] [swarm: on/off] [loop: on/off]
    - "Recent ship" line showing last commit subject
    - subprocess.call(PS1) dispatch for spawn / sub-flows

Profile mode: `EVE.exe --profile` prints `boot=<N>ms` and exits 0.
Honors SINISTER_SKIP_BANNER=1 (skip the animated banner).
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path


# ---------------------------------------------------------------------------
# Sanctum root probe (must run BEFORE any lib import that reads SANCTUM_ROOT)
# ---------------------------------------------------------------------------

def _probe_sanctum_root() -> Path | None:
    """Try env var, then conventional locations. Set SINISTER_SANCTUM_ROOT for children."""
    candidates: list[str] = []
    env = os.environ.get("SINISTER_SANCTUM_ROOT")
    if env:
        candidates.append(env)
    candidates += [
        r"D:\Sinister Sanctum",
        r"C:\Sinister Sanctum",
        os.path.join(os.environ.get("USERPROFILE", ""), "Sinister Sanctum"),
    ]
    for cand in candidates:
        if not cand:
            continue
        p = Path(cand)
        if (p / "automations" / "start-sinister-session.ps1").exists():
            os.environ["SINISTER_SANCTUM_ROOT"] = str(p)
            os.environ["SANCTUM_ROOT"] = str(p)
            return p
    return None


SANCTUM_ROOT_PATH = _probe_sanctum_root()


def _setup_lib_path() -> None:
    """Add tools/eve-picker to sys.path before importing eve_picker_lib."""
    here = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
    candidates: list[Path] = []
    if SANCTUM_ROOT_PATH is not None:
        candidates.append(SANCTUM_ROOT_PATH / "tools" / "eve-picker")
    candidates.append(here.parent.parent / "tools" / "eve-picker")
    for cand in candidates:
        if cand.exists() and str(cand) not in sys.path:
            sys.path.insert(0, str(cand))


_setup_lib_path()
try:
    import eve_picker_lib as lib  # noqa: E402
except ImportError:
    lib = None  # noqa: E402 -- handled at runtime; some flags don't need the lib

try:
    import quantum_tools  # noqa: E402  -- stdlib-only quantum sub-menu (RKOJ-ELENO 2026-05-24)
except ImportError:
    quantum_tools = None  # noqa: E402  -- T sub-menu disabled if module missing

try:
    import health_tools  # noqa: E402  -- stdlib-only Anthropic-throttle health (RKOJ-ELENO 2026-05-24)
except ImportError:
    health_tools = None  # noqa: E402  -- H sub-menu disabled if module missing

try:
    import eve_logger  # noqa: E402  -- structured jsonl logger (RKOJ-ELENO 2026-05-24)
except ImportError:
    eve_logger = None  # noqa: E402  -- logger silently disabled if missing


PS1_LAUNCHER = (SANCTUM_ROOT_PATH / "automations" / "start-sinister-session.ps1") if SANCTUM_ROOT_PATH else None


# ---------------------------------------------------------------------------
# ANSI 256-color palette (Sanctum purple-everything)
# Color-capability detect: NO_COLOR / TERM=dumb / EVE_QUIET disable escapes.
# (RKOJ-ELENO :: 2026-05-24 — jcode color_support.rs parity)
# ---------------------------------------------------------------------------

def _ansi_enabled() -> bool:
    """True iff we should emit ANSI escapes. Honors NO_COLOR + TERM=dumb."""
    if os.environ.get("NO_COLOR", "").strip():
        return False
    if os.environ.get("TERM", "").strip().lower() in ("dumb", ""):
        # Windows console without TERM set still wants color; allow on Win.
        if os.name != "nt":
            return False
    return True


_ANSI_ON = _ansi_enabled()


def _C(seq: str) -> str:
    """Return seq if color enabled, else empty string."""
    return seq if _ANSI_ON else ""


PURPLE = _C("\033[38;5;141m")     # Sanctum purple #A06EFF-ish (xterm 141)
DARKP = _C("\033[38;5;91m")
BRIGHTP = _C("\033[38;5;177m")
WHITE = _C("\033[97m")
SOFT = _C("\033[38;5;245m")
DIM = _C("\033[38;5;240m")
OK = _C("\033[38;5;46m")
WARN = _C("\033[38;5;220m")
FAIL = _C("\033[38;5;196m")
RESET = _C("\033[0m")
BOLD = _C("\033[1m")

PILL_G = _C("\033[48;5;22;38;5;15;1m")
PILL_B = _C("\033[48;5;19;38;5;15;1m")
PILL_R = _C("\033[48;5;52;38;5;15;1m")
PILL_P = _C("\033[48;5;91;38;5;15;1m")
PILL_Z = _C("\033[0m")


def enable_vt_on_windows() -> None:
    """Enable ANSI escape interpretation in the Windows console."""
    if os.name != "nt":
        return
    try:
        import ctypes
        k32 = ctypes.windll.kernel32
        STD_OUTPUT_HANDLE = -11
        ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
        h = k32.GetStdHandle(STD_OUTPUT_HANDLE)
        mode = ctypes.c_ulong()
        if k32.GetConsoleMode(h, ctypes.byref(mode)):
            k32.SetConsoleMode(h, mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Animated jcode-style ASCII banner (~0.6s total)
# ---------------------------------------------------------------------------

# Lifted from automations/sinister-banner.sh (image #3 jcode reference).
_LOGO_LINES = [
    "        =,,@@@@#,==",
    "     ,@@@@@@@@@@@@-",
    "   .@@@@@@@@@@@##@@@@@-",
    "   .@@@@@@@.    -@@@@@-",
    "   |@@@@@@@      @@@@@|",
    "   .@@@@@@@%     @@@@@|",
    "   @@@@@@@@@     @@@@@@-",
    "   .@@@@@@@@@@,,@@@@@@@-",
    "   -@@@@@@@@@@@@@@@@@@@-",
    "    *@@@@@@@@@@@@@@@@@@@%",
    "      ^@@@@@@@@@@@@@@@@%",
    "         ^=@@@@@@@-",
]

# Sanctum-purple-leaning gradient (red->orange->pink->magenta->purple->indigo).
_BANNER_COLORS = [196, 202, 208, 209, 210, 211, 212, 213, 207, 201, 200, 199, 198, 197, 165, 129, 93, 99]


def play_banner(frames: int = 8, delay: float = 0.07) -> None:
    """Render an animated color-cycling ASCII C glyph. Total ~frames*delay seconds.

    Honors SINISTER_SKIP_BANNER=1 to bypass entirely.
    Cursor is hidden during animation and restored at exit.
    """
    if os.environ.get("SINISTER_SKIP_BANNER", "").strip() == "1":
        return
    # Reserve vertical space, then redraw in place each frame.
    sys.stdout.write("\033[?25l")  # hide cursor
    for _ in _LOGO_LINES:
        sys.stdout.write("\n")
    sys.stdout.flush()
    try:
        for f in range(frames):
            # Move cursor up over the reserved rows
            sys.stdout.write(f"\033[{len(_LOGO_LINES)}A")
            for i, line in enumerate(_LOGO_LINES):
                cidx = (i + f) % len(_BANNER_COLORS)
                color = _BANNER_COLORS[cidx]
                sys.stdout.write(f"\033[2K\033[38;5;{color}m{line}\033[0m\n")
            sys.stdout.flush()
            time.sleep(delay)
    finally:
        sys.stdout.write("\033[?25h")  # restore cursor
        sys.stdout.flush()


# ---------------------------------------------------------------------------
# First-run autonomy bootstrap
# ---------------------------------------------------------------------------

def _autonomy_marker() -> Path:
    return Path(os.environ.get("USERPROFILE", str(Path.home()))) / ".sanctum-autonomy-granted"


def run_autonomy_bootstrap(force: bool = False) -> int:
    """Invoke grant-claude-autonomy.ps1 if marker missing (or force=True)."""
    if SANCTUM_ROOT_PATH is None:
        print(f"  {FAIL}[FAIL] Sanctum root not found — cannot run autonomy bootstrap{RESET}")
        return 1
    script = SANCTUM_ROOT_PATH / "automations" / "grant-claude-autonomy.ps1"
    if not script.exists():
        print(f"  {WARN}[warn] grant-claude-autonomy.ps1 not found at {script}{RESET}")
        return 1
    marker = _autonomy_marker()
    if marker.exists() and not force:
        return 0
    print()
    print(f"  {DARKP}{'=' * 68}{RESET}")
    print(f"  {WHITE}{BOLD} Sinister Sanctum :: First-run autonomy bootstrap {RESET}")
    print(f"  {DARKP}{'=' * 68}{RESET}")
    print(f"  {SOFT}Running grant-claude-autonomy.ps1 once before launching.{RESET}")
    print(f"  {SOFT}Re-run any time: EVE --setup-autonomy{RESET}")
    print()
    return subprocess.call([
        "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", str(script),
    ])


# ---------------------------------------------------------------------------
# Background plugin check (DETACHED_PROCESS, non-blocking)
# ---------------------------------------------------------------------------

def fire_plugin_check_background() -> None:
    """Fire-and-forget plugin install check. Returns immediately."""
    if SANCTUM_ROOT_PATH is None:
        return
    script = SANCTUM_ROOT_PATH / "automations" / "check-required-plugins.ps1"
    if not script.exists():
        return
    cmd = [
        "powershell.exe", "-WindowStyle", "Hidden",
        "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", str(script),
        "-AutoInstall", "-Silent",
    ]
    creationflags = 0
    if os.name == "nt":
        # DETACHED_PROCESS (0x00000008) | CREATE_NEW_PROCESS_GROUP (0x00000200)
        creationflags = 0x00000008 | 0x00000200
    try:
        subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creationflags,
            close_fds=True,
        )
    except Exception:
        pass  # fire-and-forget; never block the launcher


# ---------------------------------------------------------------------------
# Spawn-shell preflight (warn only)
# ---------------------------------------------------------------------------

_SHELL_CANDIDATES = [
    r"C:\Program Files\Git\usr\bin\mintty.exe",
    r"C:\Program Files\Git\git-bash.exe",
    r"C:\Program Files\Git\bin\bash.exe",
]


def spawn_shell_preflight(verbose: bool = False) -> bool:
    """Return True if any spawn-capable shell exists. Warn (but don't block) otherwise."""
    found = [p for p in _SHELL_CANDIDATES if Path(p).exists()]
    if found:
        if verbose:
            print(f"  {OK}[OK]{RESET}    spawn shell: {found[0]}")
        return True
    print()
    print(f"  {WARN}[WARN]{RESET} no spawn-capable shell found.")
    for c in _SHELL_CANDIDATES:
        print(f"         tried: {c}")
    print(f"         install Git for Windows: https://gitforwindows.org")
    print(f"  {WARN}[WARN]{RESET} picker will still open but spawn may fail. Ctrl+C to abort.")
    print()
    time.sleep(2)
    return False


# ---------------------------------------------------------------------------
# Diagnose flag (probe everything, exit)
# ---------------------------------------------------------------------------

def run_diagnose() -> int:
    """Probe every prerequisite + report. No spawn."""
    print()
    print(f"  {DARKP}{'=' * 68}{RESET}")
    print(f"  {WHITE}{BOLD} EVE :: --diagnose {RESET}")
    print(f"  {DARKP}{'=' * 68}{RESET}")
    print()

    def row(ok: bool, label: str, detail: str = "") -> None:
        tag = f"{OK}[OK]   {RESET}" if ok else f"{FAIL}[FAIL] {RESET}"
        print(f"  {tag} {label}" + (f"  {SOFT}{detail}{RESET}" if detail else ""))

    def info(label: str, detail: str = "") -> None:
        print(f"  {DIM}[info] {RESET} {label}" + (f"  {SOFT}{detail}{RESET}" if detail else ""))

    if SANCTUM_ROOT_PATH:
        row(True, "SANCTUM_ROOT", str(SANCTUM_ROOT_PATH))
    else:
        row(False, "SANCTUM_ROOT not found in any known location")

    for c in _SHELL_CANDIDATES:
        row(Path(c).exists(), Path(c).name, c)

    if SANCTUM_ROOT_PATH:
        ps1 = SANCTUM_ROOT_PATH / "automations" / "start-sinister-session.ps1"
        row(ps1.exists(), "start-sinister-session.ps1", str(ps1))
        auto = SANCTUM_ROOT_PATH / "automations" / "grant-claude-autonomy.ps1"
        row(auto.exists(), "grant-claude-autonomy.ps1", str(auto))
        plug = SANCTUM_ROOT_PATH / "automations" / "check-required-plugins.ps1"
        row(plug.exists(), "check-required-plugins.ps1", str(plug))

    marker = _autonomy_marker()
    if marker.exists():
        row(True, "autonomy marker present", str(marker))
    else:
        info("no autonomy marker (will bootstrap on next normal launch)", str(marker))

    eve_exe_paths = []
    if SANCTUM_ROOT_PATH:
        eve_exe_paths += [
            SANCTUM_ROOT_PATH / "automations" / "eve-launcher" / "dist" / "EVE" / "EVE.exe",
            SANCTUM_ROOT_PATH / "automations" / "eve-launcher" / "dist" / "EVE.exe",
        ]
    for ep in eve_exe_paths:
        if ep.exists():
            row(True, f"EVE.exe present", f"{ep} ({ep.stat().st_size} bytes)")
        else:
            info(f"EVE.exe NOT present at {ep}")

    # Account / swarm / loop env
    print()
    print(f"  {SOFT}Environment:{RESET}")
    for var in ("SINISTER_ACCOUNT", "SINISTER_DEFAULT_SWARM", "SINISTER_DEFAULT_LOOP",
                "SINISTER_SKIP_MODES_PROMPT", "SINISTER_SKIP_BANNER",
                "SINISTER_EVE_SWARM", "SINISTER_EVE_LOOP"):
        val = os.environ.get(var, "")
        if val:
            print(f"    {DIM}{var}={RESET}{val}")
        else:
            print(f"    {DIM}{var}=(unset){RESET}")

    if lib is not None:
        print()
        try:
            t0 = time.monotonic()
            state = lib.build_picker_state(boot_ms=0)
            elapsed = int((time.monotonic() - t0) * 1000)
            print(f"  {OK}[OK]{RESET}    picker assembly: {elapsed} ms, {len(state.rows)} rows, "
                  f"mcp={state.mcp}, bots={state.bots}")
        except Exception as e:
            print(f"  {FAIL}[FAIL]{RESET} picker assembly failed: {e}")
    else:
        print(f"  {FAIL}[FAIL]{RESET} eve_picker_lib not importable")

    if quantum_tools is not None:
        try:
            qout = quantum_tools._quantum_outputs_dir()
            if qout is not None:
                qcount = len(list(qout.glob("*.json")))
                print(f"  {OK}[OK]{RESET}    quantum_tools: {qcount} JSON output files at {qout}")
            else:
                print(f"  {WARN}[warn]{RESET} quantum_tools: outputs/ dir not located")
        except Exception as e:
            print(f"  {WARN}[warn]{RESET} quantum_tools probe error: {e}")
    else:
        print(f"  {WARN}[warn]{RESET} quantum_tools not importable (T sub-menu will be disabled)")

    # Fleet heartbeat probe
    fleet = _fleet_heartbeat_summary()
    if fleet:
        print(f"  {OK}[OK]{RESET}    fleet heartbeat: {fleet}")
    else:
        print(f"  {WARN}[warn]{RESET} no fleet heartbeats found")

    print()
    print(f"  {SOFT}Done. Run EVE.exe with no args to launch.{RESET}")
    print()
    return 0


# ---------------------------------------------------------------------------
# Recent ship / git helpers
# ---------------------------------------------------------------------------

def _fleet_heartbeat_summary() -> str:
    """jcode-style ticker: count fleet heartbeats fresh in last 5 minutes.

    Returns ANSI-rendered "fleet 3/7 live" string. Reads JSON from
    _shared-memory/heartbeats/<slug>.json; an agent counts as "live" if
    file mtime is within the freshness window. Empty string on probe failure.
    """
    if SANCTUM_ROOT_PATH is None:
        return ""
    hb_dir = SANCTUM_ROOT_PATH / "_shared-memory" / "heartbeats"
    if not hb_dir.exists():
        return ""
    try:
        hbs = list(hb_dir.glob("*.json"))
    except OSError:
        return ""
    if not hbs:
        return ""
    fresh_window = 300  # 5 minutes
    now = time.time()
    live = sum(1 for p in hbs if (now - p.stat().st_mtime) <= fresh_window)
    total = len(hbs)
    color = OK if live >= 1 else DIM
    return f"{color}{live}/{total} live{RESET}"


def _recent_commit_subject() -> str:
    """Best-effort one-line `git log -1 --format=%s`. Empty string on failure."""
    if SANCTUM_ROOT_PATH is None:
        return ""
    try:
        out = subprocess.check_output(
            ["git", "log", "-1", "--format=%s"],
            cwd=str(SANCTUM_ROOT_PATH),
            stderr=subprocess.DEVNULL,
            timeout=2,
        ).decode("utf-8", errors="replace").strip()
        return out
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Prefs read/write — fleet-default loop_mode toggled via L picker key
# (RKOJ-ELENO :: 2026-05-24)
# ---------------------------------------------------------------------------

def _prefs_path() -> Path | None:
    if SANCTUM_ROOT_PATH is None:
        return None
    return SANCTUM_ROOT_PATH / "automations" / "session-templates" / "agent-prefs.json"


def _read_prefs_defaults() -> dict:
    """Return {swarm,loop,skip_modes_prompt} from agent-prefs.json defaults block.

    Silent fallback to all-False on any read/parse failure. Loop fleet-default is
    True per operator hard-canonical 2026-05-24.
    """
    out = {"swarm_mode": False, "loop_mode": False, "skip_modes_prompt": False}
    p = _prefs_path()
    if p is None or not p.exists():
        return out
    try:
        import json as _json
        data = _json.loads(p.read_text(encoding="utf-8"))
        d = data.get("defaults") or {}
        out["swarm_mode"] = bool(d.get("swarm_mode", False))
        out["loop_mode"] = bool(d.get("loop_mode", False))
        out["skip_modes_prompt"] = bool(d.get("skip_modes_prompt", False))
    except Exception:
        pass
    return out


def _toggle_prefs_loop() -> bool | None:
    """Flip defaults.loop_mode in agent-prefs.json. Return new state, or None on failure."""
    p = _prefs_path()
    if p is None or not p.exists():
        return None
    try:
        import json as _json
        data = _json.loads(p.read_text(encoding="utf-8"))
        if "defaults" not in data or not isinstance(data["defaults"], dict):
            data["defaults"] = {"swarm_mode": False, "loop_mode": False, "skip_modes_prompt": True}
        cur = bool(data["defaults"].get("loop_mode", False))
        new = not cur
        data["defaults"]["loop_mode"] = new
        # Pretty-print preserving 4-space indent so the file still diffs cleanly.
        p.write_text(_json.dumps(data, indent=4) + "\n", encoding="utf-8")
        return new
    except Exception:
        return None


def _queue_top_rows(n: int = 3) -> list[str]:
    """Return up to N most-recent open queue rows (## headers) from OPERATOR-ACTION-QUEUE.md."""
    if SANCTUM_ROOT_PATH is None:
        return []
    q = SANCTUM_ROOT_PATH / "_shared-memory" / "OPERATOR-ACTION-QUEUE.md"
    if not q.exists():
        return []
    try:
        lines = q.read_text(encoding="utf-8", errors="replace").splitlines()
        rows = [ln.lstrip("#").strip() for ln in lines if ln.startswith("## ")]
        return rows[:n]
    except Exception:
        return []


def _unresolved_utterances(n: int = 5) -> list[dict]:
    """Return up to N most-recent unresolved operator-utterances (status != 'resolved')."""
    if SANCTUM_ROOT_PATH is None:
        return []
    u = SANCTUM_ROOT_PATH / "_shared-memory" / "operator-utterances.jsonl"
    if not u.exists():
        return []
    try:
        import json as _json
        out: list[dict] = []
        for ln in u.read_text(encoding="utf-8", errors="replace").splitlines():
            ln = ln.strip()
            if not ln:
                continue
            try:
                rec = _json.loads(ln)
            except Exception:
                continue
            if rec.get("status") and rec["status"] != "resolved":
                out.append(rec)
        return out[-n:][::-1]  # last N, newest-first
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Mesh dashboard (RKOJ-ELENO 2026-05-24 — v0.4.4)
# Operator: "make sure all ai agents work together in a mesh network in a sense
# in the ba fil and exe"
# Shows: fleet heartbeats (live/idle/stale), per-lane inbox unread, multi-account
# rotation status, last 8 cross-lane commits.
# ---------------------------------------------------------------------------

def _view_mesh_status() -> None:
    """One-shot mesh-network snapshot. Returns control to picker on Enter."""
    import json as _json
    if SANCTUM_ROOT_PATH is None:
        print(f"  {FAIL}[mesh] SANCTUM_ROOT not resolved{RESET}")
        return
    print()
    print(f"  {WHITE}{BOLD}MESH STATUS{RESET}  {DIM}// fleet at-a-glance{RESET}")
    print(f"  {DARKP}{'-' * 88}{RESET}")

    # 1) Fleet heartbeats — live (≤5m) / idle (5m-1h) / stale (>1h)
    hb_dir = SANCTUM_ROOT_PATH / "_shared-memory" / "heartbeats"
    live = idle = stale = total = 0
    hb_rows: list[tuple[str, int, str]] = []
    if hb_dir.exists():
        now_t = time.time()
        for p in hb_dir.rglob("*.json"):
            total += 1
            age_sec = int(now_t - p.stat().st_mtime)
            if age_sec <= 300:
                live += 1; tag = "live"
            elif age_sec <= 3600:
                idle += 1; tag = "idle"
            else:
                stale += 1; tag = "stale"
            hb_rows.append((p.stem, age_sec, tag))
    print(f"  {SOFT}heartbeats{RESET}  total={WHITE}{total}{RESET}   "
          f"{OK}live={live}{RESET}   {WARN}idle={idle}{RESET}   {DIM}stale={stale}{RESET}")
    hb_rows.sort(key=lambda r: r[1])
    for slug, age, tag in hb_rows[:5]:
        color = OK if tag == "live" else (WARN if tag == "idle" else DIM)
        age_str = f"{age}s" if age < 60 else (f"{age // 60}m" if age < 3600 else f"{age // 3600}h")
        print(f"    {color}*{RESET} {WHITE}{slug:<32}{RESET}  {color}{tag:<5}{RESET}  {DIM}{age_str} ago{RESET}")

    # 2) Inbox unread per lane (top 5)
    print()
    print(f"  {SOFT}inbox{RESET}  per-lane unread (top 5)")
    manifest = SANCTUM_ROOT_PATH / "_shared-memory" / "inbox" / "_manifest.json"
    if manifest.exists():
        try:
            m = _json.loads(manifest.read_text(encoding="utf-8-sig", errors="replace"))
            total_u = m.get("total_unread", 0)
            per_lane = m.get("per_lane", {})
            print(f"    {DIM}total unread fleet-wide:{RESET} {WHITE}{total_u}{RESET}")
            top = sorted(per_lane.items(), key=lambda kv: -kv[1])[:5]
            for slug, n in top:
                color = WARN if n > 5 else SOFT
                print(f"    {color}*{RESET} {WHITE}{slug:<32}{RESET}  {color}{n} unread{RESET}")
        except Exception as e:
            print(f"    {WARN}(manifest unreadable: {e}){RESET}")
    else:
        print(f"    {DIM}(no manifest — run automations/inbox-manifest-build.ps1){RESET}")

    # 3) Account rotation status
    print()
    print(f"  {SOFT}accounts{RESET}  multi-claude rotation")
    accts_f = SANCTUM_ROOT_PATH / "_shared-memory" / "claude-accounts.json"
    if accts_f.exists():
        try:
            a = _json.loads(accts_f.read_text(encoding="utf-8-sig", errors="replace"))
            print(f"    {DIM}strategy={RESET}{a.get('rotation_strategy','?')}  "
                  f"{DIM}max_concurrent_global={RESET}{a.get('max_concurrent_global','?')}")
            for acct in a.get("accounts", []):
                enabled = acct.get("enabled", False)
                state_tag = f"{OK}enabled{RESET}" if enabled else f"{DIM}disabled{RESET}"
                rate_lim = acct.get("rate_limited_until_utc")
                rate_tag = f"  {FAIL}rate-limited until {rate_lim}{RESET}" if rate_lim else ""
                cur = acct.get("current_sessions", 0)
                cap = acct.get("max_sessions_concurrent", "?")
                today = acct.get("successful_spawns_today", 0)
                label = acct.get("label", acct.get("name", "?"))
                print(f"    {BRIGHTP}*{RESET} {WHITE}{label:<32}{RESET}  "
                      f"{state_tag}  sessions={cur}/{cap}  today={today}{rate_tag}")
        except Exception as e:
            print(f"    {WARN}(accounts file unreadable: {e}){RESET}")
    else:
        print(f"    {DIM}(claude-accounts.json not present){RESET}")

    # 4) Recent cross-lane git activity (last 8 commits)
    print()
    print(f"  {SOFT}recent activity{RESET}  last 8 commits on this branch")
    try:
        log = subprocess.check_output(
            ["git", "log", "--oneline", "-8", "--no-color"],
            cwd=str(SANCTUM_ROOT_PATH), stderr=subprocess.DEVNULL, timeout=3
        ).decode("utf-8", errors="replace").strip().splitlines()
        for ln in log:
            trunc = ln if len(ln) <= 84 else ln[:81] + "..."
            print(f"    {DIM}*{RESET} {SOFT}{trunc}{RESET}")
    except Exception as e:
        print(f"    {WARN}(git log failed: {e}){RESET}")

    print()
    print(f"  {DARKP}{'-' * 88}{RESET}")
    print(f"  {DIM}// fleet broadcast: `sinister-swarm broadcast --message \"<text>\"`{RESET}")
    print(f"  {DIM}// DM a lane:        `sinister-swarm dm --to <slug> --message \"<text>\"`{RESET}")
    print(f"  {DIM}// watch live:       `sinister-swarm watch`{RESET}")
    print()
    try:
        input(f"  {DIM}> press Enter to return to picker:{RESET} ")
    except (EOFError, KeyboardInterrupt):
        pass


# ---------------------------------------------------------------------------
# Picker UI (jcode-feel polish)
# ---------------------------------------------------------------------------

def banner(state) -> None:
    """ANSI-render the picker banner using fields from PickerState + status line."""
    now = time.strftime("%Y-%m-%d %H:%M")
    account = os.environ.get("SINISTER_ACCOUNT", "operator")
    # RKOJ-ELENO 2026-05-24: precedence env-var > prefs defaults. So when no CLI/env
    # override is set, the status line reflects what the spawn will actually use.
    prefs_def = _read_prefs_defaults()
    swarm_env = os.environ.get("SINISTER_DEFAULT_SWARM", "").strip()
    loop_env = os.environ.get("SINISTER_DEFAULT_LOOP", "").strip()
    swarm_on = (swarm_env == "1") if swarm_env in ("0", "1") else prefs_def["swarm_mode"]
    loop_on = (loop_env == "1") if loop_env in ("0", "1") else prefs_def["loop_mode"]
    swarm_tag = f"{OK}on{RESET}" if swarm_on else f"{DIM}off{RESET}"
    loop_tag = f"{OK}on{RESET}" if loop_on else f"{DIM}off{RESET}"

    print()
    print(f"  {PURPLE}{BOLD}     E V E     {RESET}{DIM}// jcode-speed launcher :: Sinister Sanctum{RESET}")
    print(f"  {DARKP}{'-' * 68}{RESET}")
    print(f"  {SOFT}server{RESET} Sanctum    {SOFT}client{RESET} EVE    {DIM}{now}{RESET}")
    print(f"  {SOFT}model{RESET}  claude-opus-4-7[1m]   {SOFT}speed{RESET} turbo   {SOFT}token{RESET} compact")
    print(f"  {SOFT}boot{RESET}   {OK}{state.boot_ms} ms{RESET}   "
          f"{PILL_G} mcp:{state.mcp} {PILL_Z}  {PILL_B} bots:{state.bots} {PILL_Z}  "
          f"{PILL_R} --skip-perms {PILL_Z}")
    print(f"  {DARKP}{'-' * 68}{RESET}")
    # Status line + jcode-style fleet heartbeat ticker
    fleet = _fleet_heartbeat_summary()
    fleet_seg = f"  {DIM}[{RESET}fleet: {fleet}{DIM}]{RESET}" if fleet else ""
    print(f"  {DIM}[{RESET}account: {BRIGHTP}{account}{RESET} {DIM}]{RESET}  "
          f"{DIM}[{RESET}swarm: {swarm_tag}{DIM}]{RESET}  "
          f"{DIM}[{RESET}loop: {loop_tag}{DIM}]{RESET}"
          f"{fleet_seg}")
    recent = _recent_commit_subject()
    if recent:
        if len(recent) > 64:
            recent = recent[:61] + "..."
        print(f"  {DIM}ship  {RESET}{SOFT}{recent}{RESET}")
    print(f"  {DARKP}{'-' * 68}{RESET}")
    print()


def render_picker(state) -> None:
    """ANSI-render the picker rows using fields from PickerState.

    v3 spacing (RKOJ-ELENO :: 2026-05-24): widened to 88 cols, display column
    bumped to 28, tag truncated to 46 with ellipsis, blank divider every 5 rows
    for visual grouping. Picker is the operator's most-used surface — readability
    matters more than terminal economy.
    """
    print()
    print(f"  {WHITE}{BOLD}Pick a project{RESET}")
    print(f"  {DARKP}{'-' * 88}{RESET}")
    # RKOJ-ELENO 2026-05-24: fleet-default hint line. Loop is ON for the whole fleet;
    # per-session override via --no-loop, fleet-wide via agent-prefs.json defaults.loop_mode.
    prefs_def = _read_prefs_defaults()
    loop_word = f"{OK}ON{RESET}" if prefs_def["loop_mode"] else f"{DIM}OFF{RESET}"
    print(f"  {DIM}fleet-default loop: {loop_word}{DIM}   override per-session: --no-loop  |  "
          f"toggle this session: press {RESET}{PURPLE}L{RESET}{DIM}  |  "
          f"persist: edit agent-prefs.json defaults.loop_mode{RESET}")
    print()
    for i, r in enumerate(state.rows):
        marker = f"{BRIGHTP}*{RESET}" if r.is_default else " "
        # Truncate tag with ellipsis if too long; keeps row to one terminal line.
        tag = r.tag if len(r.tag) <= 46 else r.tag[:43] + "..."
        line = (f"  {marker} {PURPLE}{r.index:2}){RESET}  "
                f"{WHITE}{r.display:<28}{RESET}  "
                f"{SOFT}{tag:<46}{RESET}")
        if r.customized:
            line += f"  {DIM}[{r.agent_name} / {r.accent}]{RESET}"
        print(line)
        # Visual grouping: blank line every 5 rows so the eye can scan.
        if (i + 1) % 5 == 0 and (i + 1) < len(state.rows):
            print()
    print()
    print(f"  {DARKP}{'-' * 88}{RESET}")
    print()
    print(f"  {PURPLE}G){RESET}  General         "
          f"{PURPLE}A){RESET}  Auto-Resume     "
          f"{PURPLE}N){RESET}  New Project     "
          f"{PURPLE}R){RESET}  Rename + Color")
    print()
    print(f"  {PURPLE}K){RESET}  Clear ctx       "
          f"{PURPLE}S){RESET}  Autonomy        "
          f"{PURPLE}F){RESET}  Full picker     "
          f"{PURPLE}X){RESET}  Exit")
    print()
    print(f"  {PURPLE}T){RESET}  Quantum tools     "
          f"{DIM}// PSTF / QDDD / TLPC / qbc-recall / summary{RESET}")
    print(f"  {PURPLE}H){RESET}  Health            "
          f"{DIM}// Anthropic throttle status :: plan-quota vs server-throttle{RESET}")
    print(f"  {PURPLE}L){RESET}  Loop toggle       "
          f"{DIM}// flip fleet-default loop_mode in agent-prefs.json{RESET}")
    print(f"  {PURPLE}Q){RESET}  Queue (top 3)     "
          f"{DIM}// peek OPERATOR-ACTION-QUEUE.md{RESET}")
    print(f"  {PURPLE}U){RESET}  Utterances (5)    "
          f"{DIM}// last 5 unresolved operator messages{RESET}")
    print(f"  {PURPLE}M){RESET}  Mesh status       "
          f"{DIM}// fleet heartbeats + inbox + accounts + recent activity{RESET}")
    print()
    print(f"  {DIM}     multi-select: 1,3,5 or 1-3     |     "
          f"loop/swarm modes prompted after pick{RESET}")
    print(f"  {DARKP}{'-' * 88}{RESET}")
    print()


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

def dispatch_project(key: str) -> int:
    if PS1_LAUNCHER is None or not PS1_LAUNCHER.exists():
        print(f"  {FAIL}[FAIL] PS1 launcher not found{RESET}")
        return 2
    cmd = [
        "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", str(PS1_LAUNCHER),
        "-Project", key,
    ]
    return subprocess.call(cmd)


def dispatch_interactive() -> int:
    if PS1_LAUNCHER is None or not PS1_LAUNCHER.exists():
        print(f"  {FAIL}[FAIL] PS1 launcher not found{RESET}")
        return 2
    cmd = [
        "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", str(PS1_LAUNCHER),
    ]
    return subprocess.call(cmd)


def dispatch_multi(keys: list[str]) -> int:
    rc = 0
    for k in keys:
        print(f"  {SOFT}[multi] spawning {WHITE}{k}{RESET}")
        rc = dispatch_project(k) or rc
        time.sleep(0.4)
    return rc


# ---------------------------------------------------------------------------
# Account status
# ---------------------------------------------------------------------------

def run_account_status() -> int:
    if SANCTUM_ROOT_PATH is None:
        print(f"  {FAIL}[FAIL] Sanctum root not found{RESET}")
        return 1
    accounts_ps = SANCTUM_ROOT_PATH / "automations" / "claude-accounts.ps1"
    if not accounts_ps.exists():
        print(f"  {FAIL}[FAIL] claude-accounts.ps1 not found at {accounts_ps}{RESET}")
        return 1
    print()
    print(f"  {DARKP}{'=' * 68}{RESET}")
    print(f"  {WHITE}{BOLD} EVE :: Multi-account status {RESET}")
    print(f"  {DARKP}{'=' * 68}{RESET}")
    cmd = [
        "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-Command",
        f". '{accounts_ps}'; "
        "$cfg = Get-AccountsConfig; "
        'Write-Host \"Default: $($cfg.default)\"; '
        'Write-Host \"Strategy: $($cfg.rotation_strategy)\"; '
        'Write-Host \"Accounts:\"; '
        '$cfg.accounts | ForEach-Object { '
        "$rl = if ($_.rate_limited_until_utc) { 'RATE-LIMITED until ' + $_.rate_limited_until_utc } else { 'available' }; "
        'Write-Host \"  - $($_.name) [$($_.plan_tier)] sessions=$($_.current_sessions)/$($_.max_sessions_concurrent) $rl\" }',
    ]
    return subprocess.call(cmd)


# ---------------------------------------------------------------------------
# Arg parsing (must run BEFORE banner + picker so probe flags exit fast)
# ---------------------------------------------------------------------------

EVE_VERSION = "0.4.5"  # v0.4.5 :: jcode-parity logs/log-tail/log-level/trace/cwd/quiet/json-version/fuzzy/color-detect (RKOJ-ELENO 2026-05-24)
EVE_BUILD_CHANNEL = "release"  # parity with jcode telemetry build_channel field


def _print_help() -> None:
    """jcode-style structured table of every flag + env var (operator directive 2026-05-24)."""
    H = WHITE + BOLD
    R = RESET
    print(f"{H}EVE.exe {EVE_VERSION}{R}  {SOFT}Sinister Sanctum session launcher (jcode-parity){R}")
    print()
    print(f"{H}USAGE{R}")
    print(f"  EVE.exe [flags]                 # interactive picker")
    print(f"  EVE.exe --diagnose              # probe-only, no spawn")
    print(f"  Sinister Start.bat [flags]      # bat shim forwards all flags")
    print()
    print(f"{H}PROBE FLAGS{R}  {DIM}(exit immediately, no picker){R}")
    print(f"  {PURPLE}--version, -v{R}          Print version + exit 0")
    print(f"  {PURPLE}--version --json{R}       Print JSON {{version,build,os,python,sanctum_root}}")
    print(f"  {PURPLE}--help, -h{R}             Print this help table + exit 0")
    print(f"  {PURPLE}--profile{R}              Print 'boot=Nms rows=N mcp=N bots=N' + exit 0")
    print(f"  {PURPLE}--diagnose{R}             Probe every prerequisite + exit 0")
    print(f"  {PURPLE}--account-status{R}       Print multi-account state + exit 0")
    print(f"  {PURPLE}--quantum-summary{R}      Print one-screen quantum status + exit 0")
    print(f"  {PURPLE}--quantum-tools{R}        Open quantum tools sub-menu (PSTF/QDDD/TLPC/recall)")
    print(f"  {PURPLE}--log-tail [N]{R}         Print last N events from today's log (default 20) + exit 0")
    print(f"  {PURPLE}--log-path{R}             Print today's log file path + exit 0")
    print()
    print(f"{H}SETUP FLAGS{R}")
    print(f"  {PURPLE}--setup-autonomy{R}       Re-run grant-claude-autonomy.ps1 + exit 0")
    print()
    print(f"{H}SESSION FLAGS{R}  {DIM}(applied before picker dispatch){R}")
    print(f"  {PURPLE}--account <name>{R}       Pin account (sets SINISTER_ACCOUNT)")
    print(f"  {PURPLE}--swarm{R}                Pre-enable swarm mode")
    print(f"  {PURPLE}--loop{R}                 Pre-enable loop mode")
    print(f"  {PURPLE}--both{R}                 Enable swarm + loop")
    print(f"  {PURPLE}--no-swarm{R}             Disable swarm")
    print(f"  {PURPLE}--no-loop{R}              Disable loop")
    print(f"  {PURPLE}--cwd <path>{R}           Pin Sanctum root for this invocation (jcode -C parity)")
    print()
    print(f"{H}OBSERVABILITY FLAGS{R}  {DIM}(jcode --trace / --quiet parity){R}")
    print(f"  {PURPLE}--trace{R}                Mirror log events to stderr (sets EVE_TRACE=1)")
    print(f"  {PURPLE}--log-level <lvl>{R}      debug | info | warn | error  (default: info)")
    print(f"  {PURPLE}--quiet{R}                Suppress banner + status line (sets EVE_QUIET=1)")
    print()
    print(f"{H}ENVIRONMENT VARIABLES{R}")
    print(f"  {SOFT}SINISTER_SANCTUM_ROOT{R}      Path to Sanctum repo (default: D:\\Sinister Sanctum)")
    print(f"  {SOFT}SINISTER_ACCOUNT{R}           Pinned account name")
    print(f"  {SOFT}SINISTER_DEFAULT_SWARM{R}     '1' / '0' :: pre-set swarm")
    print(f"  {SOFT}SINISTER_DEFAULT_LOOP{R}      '1' / '0' :: pre-set loop")
    print(f"  {SOFT}SINISTER_SKIP_MODES_PROMPT{R} '1' to skip post-pick swarm/loop prompt")
    print(f"  {SOFT}SINISTER_SKIP_BANNER{R}       '1' to skip animated banner")
    print(f"  {SOFT}EVE_LOG_LEVEL{R}              debug | info | warn | error (default: info)")
    print(f"  {SOFT}EVE_TRACE{R}                  '1' to mirror logs to stderr")
    print(f"  {SOFT}EVE_QUIET{R}                  '1' to suppress non-error output")
    print(f"  {SOFT}NO_COLOR{R}                   Set (any value) to disable ANSI escapes")
    print(f"  {SOFT}TERM=dumb{R}                  Disables ANSI escapes (non-Windows)")
    print(f"  {SOFT}SINISTER_NO_TELEMETRY{R}      '1' to disable local jsonl logging")
    print(f"  {SOFT}DO_NOT_TRACK{R}               '1' to disable local jsonl logging")
    print(f"  {SOFT}JCODE_NO_TELEMETRY{R}         '1' to disable local jsonl logging (alias)")
    print()
    print(f"{H}LOG FILES{R}")
    print(f"  ~/.sinister/logs/eve-YYYY-MM-DD.jsonl  (UTC date, auto-rotated, 7-day retention)")
    print()
    print(f"{H}PICKER KEYS{R}  {DIM}(at the picker prompt){R}")
    print(f"  {PURPLE}1..N{R}  pick project       {PURPLE}1,3,5{R}  multi-select       {PURPLE}1-3{R}  range")
    print(f"  {PURPLE}/<q>{R}  fuzzy filter rows  {PURPLE}G/A/N/R/K/S/F{R}  verbs           {PURPLE}T/H/L/M{R}  sub-menus")
    print(f"  {PURPLE}Q{R}     queue              {PURPLE}U{R}  utterances             {PURPLE}X{R}  exit")
    print()


def _print_version_json() -> int:
    """JSON version output (jcode `version --json` parity)."""
    import json as _json
    payload = {
        "version": EVE_VERSION,
        "build": EVE_BUILD_CHANNEL,
        "os": os.name,
        "platform": sys.platform,
        "python": sys.version.split()[0],
        "sanctum_root": str(SANCTUM_ROOT_PATH) if SANCTUM_ROOT_PATH else None,
        "color": _ANSI_ON,
    }
    print(_json.dumps(payload, indent=2))
    return 0


def _parse_session_flags(argv: list[str]) -> list[str]:
    """Mutate os.environ based on swarm/loop/account flags. Return remaining argv."""
    out: list[str] = []
    i = 0
    while i < len(argv):
        a = argv[i]
        al = a.lower()
        if al == "--account":
            if i + 1 < len(argv):
                os.environ["SINISTER_ACCOUNT"] = argv[i + 1]
                i += 2
                continue
            i += 1
            continue
        if al == "--swarm":
            os.environ["SINISTER_DEFAULT_SWARM"] = "1"
            os.environ["SINISTER_SKIP_MODES_PROMPT"] = "1"
            i += 1
            continue
        if al == "--loop":
            os.environ["SINISTER_DEFAULT_LOOP"] = "1"
            os.environ["SINISTER_SKIP_MODES_PROMPT"] = "1"
            i += 1
            continue
        if al == "--both":
            os.environ["SINISTER_DEFAULT_SWARM"] = "1"
            os.environ["SINISTER_DEFAULT_LOOP"] = "1"
            os.environ["SINISTER_SKIP_MODES_PROMPT"] = "1"
            i += 1
            continue
        if al == "--no-swarm":
            os.environ["SINISTER_DEFAULT_SWARM"] = "0"
            os.environ["SINISTER_SKIP_MODES_PROMPT"] = "1"
            i += 1
            continue
        if al == "--no-loop":
            os.environ["SINISTER_DEFAULT_LOOP"] = "0"
            os.environ["SINISTER_SKIP_MODES_PROMPT"] = "1"
            i += 1
            continue
        # Observability flags (RKOJ-ELENO 2026-05-24, jcode parity)
        if al == "--trace":
            os.environ["EVE_TRACE"] = "1"
            i += 1
            continue
        if al == "--quiet":
            os.environ["EVE_QUIET"] = "1"
            i += 1
            continue
        if al == "--log-level":
            if i + 1 < len(argv):
                lvl = argv[i + 1].lower()
                if lvl in ("debug", "info", "warn", "error"):
                    os.environ["EVE_LOG_LEVEL"] = lvl
                i += 2
                continue
            i += 1
            continue
        if al == "--cwd" or al == "-c":
            if i + 1 < len(argv):
                # Pin Sanctum root for downstream PS1
                os.environ["SINISTER_SANCTUM_ROOT"] = argv[i + 1]
                os.environ["SANCTUM_ROOT"] = argv[i + 1]
                i += 2
                continue
            i += 1
            continue
        out.append(a)
        i += 1
    return out


def _profile_and_exit() -> int:
    if lib is None:
        print("boot=0ms rows=0 mcp=0 bots=0 (lib_missing)")
        return 1
    t0 = time.monotonic()
    state = lib.build_picker_state(boot_ms=0)
    boot_ms = int((time.monotonic() - t0) * 1000)
    print(f"boot={boot_ms}ms rows={len(state.rows)} mcp={state.mcp} bots={state.bots}")
    return 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]

    # Probe flags first — these must exit fast without rendering anything heavy.
    # --version supports optional --json (jcode parity)
    if argv:
        arg0 = argv[0].lower()
        if arg0 in ("--version", "-v", "/version"):
            if "--json" in argv:
                return _print_version_json()
            print(f"EVE.exe {EVE_VERSION} :: Sinister Sanctum session launcher")
            return 0
        if arg0 in ("--help", "-h", "/help", "/?"):
            _print_help()
            return 0

    # Log-tail / log-path probe flags (jcode-parity, RKOJ-ELENO 2026-05-24)
    if any(a.lower() in ("--log-tail", "/log-tail") for a in argv):
        enable_vt_on_windows()
        if eve_logger is None:
            print("  [FAIL] eve_logger module not importable")
            return 1
        # Find optional N argument right after --log-tail
        n = 20
        for idx, a in enumerate(argv):
            if a.lower() in ("--log-tail", "/log-tail") and idx + 1 < len(argv):
                try:
                    n = int(argv[idx + 1])
                except ValueError:
                    n = 20
                break
        return eve_logger.tail_log(n)

    if any(a.lower() in ("--log-path", "/log-path") for a in argv):
        if eve_logger is None:
            print("  [FAIL] eve_logger module not importable")
            return 1
        print(str(eve_logger.log_path()))
        return 0

    if "--profile" in argv:
        return _profile_and_exit()
    if any(a.lower() in ("--diagnose", "-diagnose", "/diagnose") for a in argv):
        enable_vt_on_windows()
        return run_diagnose()
    if any(a.lower() in ("--setup-autonomy", "-setup-autonomy", "/setup-autonomy") for a in argv):
        enable_vt_on_windows()
        return run_autonomy_bootstrap(force=True)
    if any(a.lower() in ("--account-status", "-account-status", "/account-status") for a in argv):
        enable_vt_on_windows()
        return run_account_status()
    if any(a.lower() in ("--quantum-summary", "-quantum-summary", "/quantum-summary") for a in argv):
        enable_vt_on_windows()
        if quantum_tools is None:
            print("  [FAIL] quantum_tools module not importable")
            return 1
        return quantum_tools.quantum_summary()
    if any(a.lower() in ("--quantum-tools", "-quantum-tools", "/quantum-tools") for a in argv):
        enable_vt_on_windows()
        if quantum_tools is None:
            print("  [FAIL] quantum_tools module not importable")
            return 1
        return quantum_tools.menu_loop()

    # Parse session-config flags (mutate env for child PS1)
    argv = _parse_session_flags(argv)

    # Bail early if Sanctum root never resolved.
    if SANCTUM_ROOT_PATH is None or lib is None:
        enable_vt_on_windows()
        print()
        print(f"  {FAIL}[FAIL] Sinister Sanctum repo not found.{RESET}")
        print(f"  {SOFT}Set SINISTER_SANCTUM_ROOT or place repo at D:\\Sinister Sanctum{RESET}")
        print()
        try:
            input("  press Enter to exit ")
        except (EOFError, KeyboardInterrupt):
            pass
        return 1

    # Prereq flow (skip banner + shell warn under --quiet)
    enable_vt_on_windows()
    _quiet = os.environ.get("EVE_QUIET", "").strip() == "1"
    if not _quiet:
        play_banner()
    run_autonomy_bootstrap(force=False)
    fire_plugin_check_background()
    spawn_shell_preflight(verbose=False)

    # Build picker state
    t0 = time.monotonic()
    state = lib.build_picker_state(boot_ms=0)
    state.boot_ms = int((time.monotonic() - t0) * 1000)

    # session_start event (jcode-parity local jsonl logging, RKOJ-ELENO 2026-05-24)
    if eve_logger is not None:
        try:
            eve_logger.info(
                "session_start",
                version=EVE_VERSION,
                build=EVE_BUILD_CHANNEL,
                boot_ms=state.boot_ms,
                rows=len(state.rows),
                mcp=state.mcp,
                bots=state.bots,
                account=os.environ.get("SINISTER_ACCOUNT", "operator"),
                swarm=os.environ.get("SINISTER_DEFAULT_SWARM", ""),
                loop=os.environ.get("SINISTER_DEFAULT_LOOP", ""),
                quiet=_quiet,
            )
        except Exception:
            pass

    # Local helper :: log session_end events (jcode-parity, RKOJ-ELENO 2026-05-24)
    def _log_session_end(end_reason: str, **fields):
        if eve_logger is None:
            return
        try:
            eve_logger.info("session_end", end_reason=end_reason,
                            version=EVE_VERSION, **fields)
        except Exception:
            pass

    # Fuzzy filter state (jcode session_picker/filter.rs parity)
    _filter_query: str = ""
    _full_rows = list(state.rows)

    while True:
        banner(state)
        # Apply fuzzy filter to rows if active (preserve original full list)
        if _filter_query:
            try:
                state.rows = lib.filter_rows(_full_rows, _filter_query)
            except AttributeError:
                # lib upgrade incomplete; ignore filter
                state.rows = _full_rows
            if not state.rows:
                print(f"  {WARN}[filter]{RESET} no rows match {DIM}'{_filter_query}'{RESET} — clearing filter")
                _filter_query = ""
                state.rows = list(_full_rows)
            else:
                print(f"  {DIM}[filter]{RESET} {SOFT}'{_filter_query}'{RESET} matches {OK}{len(state.rows)}{RESET} of {len(_full_rows)} rows  {DIM}(/ alone to clear){RESET}")
        render_picker(state)
        try:
            raw = input(
                f"  {WHITE}Selection [1-{len(state.rows)} / G / A / N / R / K / S / F / T / H / L / Q / U / M / X / /q, "
                f"default={state.default_key}] {PURPLE}>{RESET} "
            ).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            _log_session_end("interrupt")
            return 0

        # Fuzzy filter :: type '/' alone to clear, '/q' to filter on q (jcode parity)
        if raw.startswith("/"):
            q = raw[1:].strip()
            _filter_query = q
            if not q:
                state.rows = list(_full_rows)
                print(f"  {DIM}[filter]{RESET} cleared")
            continue

        # T shortcut :: quantum tools sub-menu (intercept before resolve_pick)
        if raw.lower() in ("t", "quantum", "tools"):
            if quantum_tools is None:
                print(f"  {WARN}quantum_tools module not importable.{RESET}")
                time.sleep(1)
            else:
                quantum_tools.menu_loop()
            state = lib.build_picker_state(boot_ms=state.boot_ms)
            continue

        # H shortcut :: health sub-menu (Anthropic throttle status :: RKOJ-ELENO 2026-05-24)
        if raw.lower() in ("h", "health"):
            if health_tools is None:
                print(f"  {WARN}health_tools module not importable.{RESET}")
                time.sleep(1)
            else:
                health_tools.menu_loop()
            state = lib.build_picker_state(boot_ms=state.boot_ms)
            continue

        # L shortcut :: toggle fleet-default loop_mode (RKOJ-ELENO 2026-05-24)
        if raw.lower() in ("l", "loop"):
            new_state = _toggle_prefs_loop()
            if new_state is None:
                print(f"  {WARN}[L] failed to toggle (agent-prefs.json missing/unwritable){RESET}")
            else:
                tag = f"{OK}on{RESET}" if new_state else f"{DIM}off{RESET}"
                print(f"  {BRIGHTP}[L]{RESET} loop_mode toggled to {tag} for next spawn")
            time.sleep(0.8)
            state = lib.build_picker_state(boot_ms=state.boot_ms)
            continue

        # X (exit) :: explicit exit alias since Q is rebound to Queue (RKOJ-ELENO 2026-05-24)
        if raw.lower() in ("x", "exit"):
            print(f"  {SOFT}bye.{RESET}")
            _log_session_end("normal_exit")
            return 0

        # Q (queue) :: show top 3 open OPERATOR-ACTION-QUEUE rows (RKOJ-ELENO 2026-05-24)
        # Operator directive 2026-05-24: Q is Queue. X is the new exit key.
        if raw.lower() in ("q", "queue", "qq"):
            rows = _queue_top_rows(3)
            print()
            print(f"  {WHITE}{BOLD}Top 3 open queue rows:{RESET}")
            if not rows:
                print(f"  {DIM}(no ## headers found in OPERATOR-ACTION-QUEUE.md){RESET}")
            for r in rows:
                trunc = r if len(r) <= 96 else r[:93] + "..."
                print(f"  {PURPLE}*{RESET} {SOFT}{trunc}{RESET}")
            print()
            try:
                input(f"  {DIM}> press Enter to return:{RESET} ")
            except (EOFError, KeyboardInterrupt):
                return 0
            state = lib.build_picker_state(boot_ms=state.boot_ms)
            continue

        # U (utterances) :: show last 5 unresolved operator-utterances (RKOJ-ELENO 2026-05-24)
        if raw.lower() in ("u", "utterances"):
            recs = _unresolved_utterances(5)
            print()
            print(f"  {WHITE}{BOLD}Last 5 unresolved operator-utterances:{RESET}")
            if not recs:
                print(f"  {DIM}(none — operator-utterances.jsonl is clean){RESET}")
            for r in recs:
                ts = r.get("ts_utc", "?")
                slug = r.get("session_slug", "?")
                preview = r.get("preview") or r.get("message_full", "")
                preview = preview if len(preview) <= 78 else preview[:75] + "..."
                status = r.get("status", "new")
                print(f"  {PURPLE}*{RESET} {DIM}{ts}{RESET} "
                      f"{BRIGHTP}{slug}{RESET} {SOFT}({status}){RESET}: {WHITE}{preview}{RESET}")
            print()
            try:
                input(f"  {DIM}> press Enter to return:{RESET} ")
            except (EOFError, KeyboardInterrupt):
                return 0
            state = lib.build_picker_state(boot_ms=state.boot_ms)
            continue

        # M (mesh) :: fleet network at-a-glance (RKOJ-ELENO 2026-05-24 v0.4.4)
        if raw.lower() in ("m", "mesh", "fleet"):
            _view_mesh_status()
            state = lib.build_picker_state(boot_ms=state.boot_ms)
            continue

        result = lib.resolve_pick(raw, state)

        if result.verb == "quit":
            print(f"  {SOFT}bye.{RESET}")
            _log_session_end("normal_exit")
            return 0
        elif result.verb == "multi":
            if eve_logger is not None:
                try: eve_logger.info("project_dispatch", verb="multi", keys=",".join(result.keys))
                except Exception: pass
            dispatch_multi(result.keys)
        elif result.verb in ("numeric", "default"):
            if eve_logger is not None:
                try: eve_logger.info("project_dispatch", verb=result.verb, key=result.keys[0])
                except Exception: pass
            dispatch_project(result.keys[0])
        elif result.verb == "general":
            if eve_logger is not None:
                try: eve_logger.info("project_dispatch", verb="general")
                except Exception: pass
            dispatch_project("general")
        elif result.verb in ("auto-resume", "new", "rename", "clear", "autonomy", "full"):
            _log_session_end("interactive_handoff", verb=result.verb)
            return dispatch_interactive()
        else:
            print(f"  {WARN}unknown selection: {raw}{RESET}")
            time.sleep(1)
            continue

        # Refresh state so prefs changes via R) show on next iteration
        state = lib.build_picker_state(boot_ms=state.boot_ms)
        _full_rows = list(state.rows)
        _filter_query = ""
        try:
            ans = input(f"  {DIM}> press Enter for picker, X to exit:{RESET} ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            _log_session_end("interrupt")
            return 0
        if ans in ("x", "quit", "exit"):
            _log_session_end("normal_exit")
            return 0


if __name__ == "__main__":
    sys.exit(main())
