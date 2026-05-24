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


PS1_LAUNCHER = (SANCTUM_ROOT_PATH / "automations" / "start-sinister-session.ps1") if SANCTUM_ROOT_PATH else None


# ---------------------------------------------------------------------------
# ANSI 256-color palette (Sanctum purple-everything)
# ---------------------------------------------------------------------------

PURPLE = "\033[38;5;141m"     # Sanctum purple #A06EFF-ish (xterm 141)
DARKP = "\033[38;5;91m"
BRIGHTP = "\033[38;5;177m"
WHITE = "\033[97m"
SOFT = "\033[38;5;245m"
DIM = "\033[38;5;240m"
OK = "\033[38;5;46m"
WARN = "\033[38;5;220m"
FAIL = "\033[38;5;196m"
RESET = "\033[0m"
BOLD = "\033[1m"

PILL_G = "\033[48;5;22;38;5;15;1m"
PILL_B = "\033[48;5;19;38;5;15;1m"
PILL_R = "\033[48;5;52;38;5;15;1m"
PILL_P = "\033[48;5;91;38;5;15;1m"
PILL_Z = "\033[0m"


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
# Picker UI (jcode-feel polish)
# ---------------------------------------------------------------------------

def banner(state) -> None:
    """ANSI-render the picker banner using fields from PickerState + status line."""
    now = time.strftime("%Y-%m-%d %H:%M")
    account = os.environ.get("SINISTER_ACCOUNT", "operator")
    swarm_on = os.environ.get("SINISTER_DEFAULT_SWARM", "").strip() == "1"
    loop_on = os.environ.get("SINISTER_DEFAULT_LOOP", "").strip() == "1"
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
          f"{PURPLE}Q){RESET}  Quit")
    print()
    print(f"  {PURPLE}T){RESET}  Quantum tools     "
          f"{DIM}// PSTF / QDDD / TLPC / qbc-recall / summary{RESET}")
    print(f"  {PURPLE}H){RESET}  Health            "
          f"{DIM}// Anthropic throttle status :: plan-quota vs server-throttle{RESET}")
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

EVE_VERSION = "0.4.2"  # v0.4.2 :: picker spacing v3 (88-col layout, blank-line groups) + sinister-os row + loop/swarm hint


def _print_help() -> None:
    print(f"EVE.exe {EVE_VERSION} - Sinister Sanctum session launcher (jcode-style)")
    print()
    print("Usage: EVE.exe [flags]")
    print()
    print("Probe flags (exit immediately, no picker):")
    print("  --version, -v        Print version + exit 0.")
    print("  --help, -h           Print this help + exit 0.")
    print("  --profile            Print 'boot=<N>ms rows=N mcp=N bots=N' + exit 0.")
    print("  --diagnose           Probe every prerequisite + exit 0.")
    print("  --account-status     Print multi-account state + exit 0.")
    print("  --quantum-summary    Print one-screen quantum status + exit 0.")
    print("  --quantum-tools      Open quantum tools sub-menu (PSTF/QDDD/TLPC/recall).")
    print()
    print("Setup flags:")
    print("  --setup-autonomy     Re-run grant-claude-autonomy.ps1 + exit 0.")
    print()
    print("Session flags (forwarded to picker via env):")
    print("  --account <name>     Pin a specific account (sets SINISTER_ACCOUNT).")
    print("  --swarm              Pre-enable swarm mode.")
    print("  --loop               Pre-enable loop mode.")
    print("  --both               Enable both swarm + loop.")
    print("  --no-swarm           Disable swarm.")
    print("  --no-loop            Disable loop.")
    print()
    print("Env:")
    print("  SINISTER_SANCTUM_ROOT   Path to Sanctum repo (defaults to D:\\Sinister Sanctum).")
    print("  SINISTER_SKIP_BANNER=1  Skip the animated banner intro.")
    print()


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
    if argv:
        arg0 = argv[0].lower()
        if arg0 in ("--version", "-v", "/version"):
            print(f"EVE.exe {EVE_VERSION} :: Sinister Sanctum session launcher")
            return 0
        if arg0 in ("--help", "-h", "/help", "/?"):
            _print_help()
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

    # Prereq flow
    enable_vt_on_windows()
    play_banner()
    run_autonomy_bootstrap(force=False)
    fire_plugin_check_background()
    spawn_shell_preflight(verbose=False)

    # Build picker state
    t0 = time.monotonic()
    state = lib.build_picker_state(boot_ms=0)
    state.boot_ms = int((time.monotonic() - t0) * 1000)

    while True:
        banner(state)
        render_picker(state)
        try:
            raw = input(
                f"  {WHITE}Selection [1-{len(state.rows)} / G / A / N / R / K / S / F / T / H / Q, "
                f"default={state.default_key}] {PURPLE}>{RESET} "
            ).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0

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

        result = lib.resolve_pick(raw, state)

        if result.verb == "quit":
            print(f"  {SOFT}bye.{RESET}")
            return 0
        elif result.verb == "multi":
            dispatch_multi(result.keys)
        elif result.verb in ("numeric", "default"):
            dispatch_project(result.keys[0])
        elif result.verb == "general":
            dispatch_project("general")
        elif result.verb in ("auto-resume", "new", "rename", "clear", "autonomy", "full"):
            return dispatch_interactive()
        else:
            print(f"  {WARN}unknown selection: {raw}{RESET}")
            time.sleep(1)
            continue

        # Refresh state so prefs changes via R) show on next iteration
        state = lib.build_picker_state(boot_ms=state.boot_ms)
        try:
            ans = input(f"  {DIM}> press Enter for picker, Q to quit:{RESET} ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if ans in ("q", "quit", "exit"):
            return 0


if __name__ == "__main__":
    sys.exit(main())
