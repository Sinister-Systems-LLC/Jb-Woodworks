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

try:
    import animations  # noqa: E402  -- jcode-style HSV+donut+orbit_rings (RKOJ-ELENO 2026-05-24)
except ImportError:
    animations = None  # noqa: E402  -- main menu falls back to plain banner if missing


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
    """Enable ANSI escape interpretation in the Windows console.
    Also force stdout/stderr to UTF-8 with replace-error-handler so emoji in queue/
    utterance rows never crash the picker with UnicodeEncodeError on cp1252 hosts.
    (RKOJ-ELENO 2026-05-24 — operator screenshot iter 34 showed crash on Q-queue
    when an OPERATOR-ACTION-QUEUE row contained 'orange-circle' emoji.)"""
    # Force UTF-8 encoding on stdout/stderr FIRST so any subsequent print() call
    # tolerates emoji + non-ascii regardless of console code page.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
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
        # Also set the active console code page to UTF-8 (65001) so cp1252
        # default doesn't reject emoji at the OS layer.
        try:
            k32.SetConsoleOutputCP(65001)
        except Exception:
            pass
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Legacy pumpkin banner DELETED (RKOJ-ELENO :: 2026-05-24T23:40Z)
# ---------------------------------------------------------------------------
# Operator screenshot #50 (2026-05-24T23:35Z) called out the red ASCII pumpkin
# (_LOGO_LINES + play_banner() above main_menu) and the legacy R/G/T/O/N/X
# letter menu as unwanted. Both were removed. main_menu.show_main_menu() in
# tools/eve-picker/main_menu.py now owns the entire entry surface with its
# own EVE block letters + hero + animation band. No replacement banner here.


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
    """Return {swarm,loop,loop_relentless,skip_modes_prompt} from agent-prefs.json defaults.

    RKOJ-ELENO :: 2026-05-25T06:35Z :: per operator hard-canonical 06:30Z 'make sure loop
    and swarm mode come on by deafult for each agent', fleet defaults are now swarm=True +
    loop=True + loop_relentless=True. Read precedence:
      1. defaults.modes.{swarm,loop}  (new schema; loop may be 'relentless'/'on'/'off' string)
      2. defaults.{swarm_mode,loop_mode,loop_relentless}  (legacy boolean schema)
      3. fallback (swarm=True, loop=True, loop_relentless=True)
    """
    out = {"swarm_mode": True, "loop_mode": True, "loop_relentless": True, "skip_modes_prompt": False}
    p = _prefs_path()
    if p is None or not p.exists():
        return out
    try:
        import json as _json
        data = _json.loads(p.read_text(encoding="utf-8"))
        d = data.get("defaults") or {}
        if "swarm_mode" in d:
            out["swarm_mode"] = bool(d.get("swarm_mode", True))
        if "loop_mode" in d:
            out["loop_mode"] = bool(d.get("loop_mode", True))
        if "loop_relentless" in d:
            out["loop_relentless"] = bool(d.get("loop_relentless", True))
        out["skip_modes_prompt"] = bool(d.get("skip_modes_prompt", False))
        m = d.get("modes") or {}
        if "swarm" in m:
            out["swarm_mode"] = bool(m.get("swarm", True))
        if "loop" in m:
            lv = m.get("loop", "relentless")
            if isinstance(lv, str):
                lvs = lv.strip().lower()
                if lvs in ("off", "false", "0", "no", "n"):
                    out["loop_mode"] = False
                    out["loop_relentless"] = False
                elif lvs == "relentless":
                    out["loop_mode"] = True
                    out["loop_relentless"] = True
                else:
                    out["loop_mode"] = True
                    out["loop_relentless"] = False
            else:
                out["loop_mode"] = bool(lv)
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
            # RKOJ-ELENO :: 2026-05-25T06:35Z :: default-create loop+swarm ON.
            data["defaults"] = {
                "swarm_mode": True,
                "loop_mode": True,
                "loop_relentless": True,
                "skip_modes_prompt": False,
                "modes": {"swarm": True, "loop": "relentless"},
            }
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
# First-run gate (RKOJ-ELENO 2026-05-24 — operator 21:24Z setup-helper directive).
# On first-run EVE auto-runs the wizard which (a) calls grant-claude-autonomy,
# (b) initializes _shared-memory, (c) drops marker file, (d) spawns a setup-helper
# Claude session (general project + SINISTER_SETUP_HELPER=1 env). Idempotent —
# does nothing after marker file ~/.sanctum-autonomy-granted exists.
# ---------------------------------------------------------------------------

def _maybe_run_first_run_wizard(force: bool = False) -> None:
    """Probe + (if first-run OR forced) run the wizard before showing the picker.

    RKOJ-ELENO 2026-05-25 :: --force-setup-wizard support + EVE-specific marker
    file at ~/.eve/first_run_marker.lock so subsequent EVE launches skip the
    wizard even if the global ~/.sanctum-autonomy-granted marker drifts.
    """
    import subprocess as _subprocess
    import datetime as _datetime
    if SANCTUM_ROOT_PATH is None:
        return

    # EVE-specific marker: if present + not forced, skip detector entirely.
    eve_marker = Path(os.path.expanduser("~/.eve/first_run_marker.lock"))
    if eve_marker.exists() and not force:
        return

    detector = SANCTUM_ROOT_PATH / "automations" / "eve-first-run-check.ps1"
    wizard = SANCTUM_ROOT_PATH / "automations" / "eve-first-run-wizard.ps1"
    if not detector.exists():
        return
    # Detector exit codes: 0=ready, 1=hard-block first-run, 2=soft-warn.
    try:
        r = _subprocess.run(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
             "-File", str(detector), "-Format", "json"],
            capture_output=True, text=True, timeout=15, errors="replace"
        )
    except Exception:
        return
    if r.returncode == 0 and not force:
        # Drop EVE marker so we skip the detector on next launch.
        try:
            eve_marker.parent.mkdir(parents=True, exist_ok=True)
            eve_marker.write_text(
                _datetime.datetime.utcnow().isoformat() + "Z",
                encoding="utf-8",
            )
        except Exception:
            pass
        return  # already set up; skip wizard
    # First-run OR forced: surface banner + invoke wizard interactively
    print()
    if force:
        print(f"  {WARN}[FORCED SETUP WIZARD]{RESET} Re-running setup at operator request.")
    else:
        print(f"  {WARN}[FIRST-RUN DETECTED]{RESET} EVE has not been set up on this PC yet.")
    print(f"  {DIM}Launching setup wizard - this is one-time + idempotent.{RESET}")
    print()
    if wizard.exists():
        try:
            _subprocess.call(
                ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                 "-File", str(wizard)],
                timeout=900
            )
            # Wizard creates marker on success; double-check + drop EVE marker too.
            try:
                eve_marker.parent.mkdir(parents=True, exist_ok=True)
                if not eve_marker.exists():
                    eve_marker.write_text(
                        _datetime.datetime.utcnow().isoformat() + "Z",
                        encoding="utf-8",
                    )
            except Exception:
                pass
        except Exception as e:
            print(f"  {FAIL}[wizard failed: {e}]{RESET}")
    else:
        print(f"  {FAIL}[wizard script missing at {wizard}]{RESET}")
        print(f"  Manual fallback: {SOFT}{SANCTUM_ROOT_PATH}/docs/LEO-SETUP.md{RESET}")


# ---------------------------------------------------------------------------
# Accounts panel — between picker rows and bottom menu (RKOJ-ELENO 2026-05-24).
# Operator 20:10Z: "i want to see connected claude accounts and there stats
# in betweenm project picker and the bottom settings."
# Compact 4-line block (header + per-account row + strategy footer). Reads
# claude-accounts.json directly. Tier-aware MAIN USAGE = current_sessions.
# ---------------------------------------------------------------------------

def _render_accounts_panel() -> None:
    """Connected-accounts panel with round-robin status bar (RKOJ-ELENO 2026-05-24).
    Operator 21:08Z 'i still dont see the claude acocunt logins. status bar round
    robin system.' Renders a visually distinct bordered block with:
      - Title row (so it pops between projects + bottom menu)
      - Round-robin STATUS BAR (strategy + cursor + next-up account)
      - One row per account (ON/OFF + label + sessions/cap + today + RL state)
      - Footer hint pointing at O key for onboarding.
    """
    if SANCTUM_ROOT_PATH is None:
        return
    accts_f = SANCTUM_ROOT_PATH / "_shared-memory" / "claude-accounts.json"
    if not accts_f.exists():
        return
    import json as _json
    try:
        a = _json.loads(accts_f.read_text(encoding="utf-8-sig", errors="replace"))
    except Exception as e:
        print(f"  {WARN}claude accounts (unreadable: {e}){RESET}")
        return
    strategy = a.get("rotation_strategy", "?")
    cursor = a.get("last_rotation_index", 0)
    accts = a.get("accounts", [])
    enabled_count = sum(1 for x in accts if x.get("enabled", False))
    total = len(accts)
    default_name = a.get("default", "")

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

    # RKOJ-ELENO :: 2026-05-25 :: operator hard-canonical "clean up all shit
    # like this. like all this needs to be clean and in theme" (image #8).
    # Canonical sub-section header treatment per eve-ui-uniformity-doctrine:
    # DARKP --- WHITE BOLD title DIM meta DARKP ---. Debug noise dropped
    # (round-robin-strict cursor + next->none + bracketed [O]nboard cue).
    # Unlinked count surfaces in the meta strip so operator sees it at a
    # glance without the "(0 linked, 1 unlinked)" parenthetical clutter.
    unlinked_total = sum(1 for x in accts if x.get("enabled", False) and not x.get("linked", True))
    meta_parts = [f"{total} slots", f"{enabled_count} enabled"]
    if unlinked_total:
        meta_parts.append(f"{unlinked_total} unlinked")
    # Strategy chip: collapse "round-robin-strict" -> "round-robin"; drop the
    # cursor index (operator: internal debug noise).
    strategy_chip = "round-robin" if strategy.startswith("round-robin") else strategy
    meta_parts.append(strategy_chip)
    # Only show next-up when there IS a next slot -- "next -> none" was debug.
    if next_name:
        meta_parts.append(f"next: {next_name}")
    meta = " · ".join(meta_parts)
    print(f"  {DARKP}---{RESET} {WHITE}{BOLD}Accounts{RESET} "
          f"{DIM}{meta}{RESET} {DARKP}---{RESET}")
    # RKOJ-ELENO :: 2026-05-24T22:05Z :: operator "make sure clauyde accounts and
    # account manager section are usiong valid usage progress bars and shwo the real
    # amount of usage". Previously this used time-since-last-spawn as a proxy --
    # NOT real usage. Now we shell out to automations/claude-usage-meter.ps1 which
    # sums actual billable token spend + msg count from Claude Code transcripts in
    # the 5h rolling window. Default account gets the FLEET meter; other slots use
    # spawn-count proxy (api-key spawns lack transcript correlation).
    from datetime import datetime as _dt, timezone as _tz, timedelta as _td
    _now = _dt.now(_tz.utc)

    # RKOJ-ELENO :: 2026-05-25T00:00Z :: operator "this cap is wrong you need to
    # make sure we are constantly updating it live in eve. it says 100 but its
    # this: [screenshot claude.ai/usage: session 8%, weekly 69%, sonnet 0%,
    # design 0%]". PRIMARY source is now anthropic-usage-probe.ps1 which scrapes
    # the live ratelimit headers from /v1/messages. Those numbers MATCH the
    # claude.ai/usage dashboard exactly. The old claude-usage-meter.ps1 (which
    # summed transcript tokens with a HARD-CODED msg_cap guess) is kept as
    # fallback only -- transcript scraping is noisy and the caps were fake.
    _default_tier = "max"
    for _a in accts:
        if _a.get("name") == default_name:
            _default_tier = (_a.get("plan_tier") or "max").strip() or "max"
            break
    # RKOJ-ELENO :: 2026-05-25T00:15Z :: operator P0 freeze fix.
    # Prior implementation made TWO synchronous PS1 subprocess.run calls
    # (anthropic-usage-probe 20s + claude-usage-meter 30s) on EVERY picker
    # re-render. When operator pressed Enter on Resume, render_picker fired
    # immediately, locking the UI thread for up to 50s while PowerShell
    # spawned + scraped network headers. EVE.exe window appeared frozen
    # ("clicking enter on resume forze the eve window and i cannot close").
    # Fix: (1) tight 3s timeout per probe (was 20s/30s); (2) process-level
    # cache keyed by ts so re-renders within 60s skip the subprocess entirely.
    _live_usage = None   # primary: real Anthropic ratelimit headers
    _real_usage = None   # fallback: transcript-summed meter
    if SANCTUM_ROOT_PATH is not None:
        global _USAGE_CACHE
        try:
            _USAGE_CACHE  # type: ignore[has-type]
        except NameError:
            _USAGE_CACHE = {"ts": 0.0, "live": None, "real": None}
        _now_ts = time.time()
        _cache_age = _now_ts - _USAGE_CACHE.get("ts", 0.0)
        _CACHE_TTL = 60.0  # render-from-cache for 60s before re-probing
        if _cache_age < _CACHE_TTL and _USAGE_CACHE.get("ts", 0.0) > 0:
            _live_usage = _USAGE_CACHE.get("live")
            _real_usage = _USAGE_CACHE.get("real")
        else:
            _probe = SANCTUM_ROOT_PATH / "automations" / "anthropic-usage-probe.ps1"
            if _probe.exists():
                import os as _os
                _refresh = _os.environ.get("SINISTER_USAGE_PROBE_REFRESH", "60")
                try:
                    _refresh_i = int(_refresh)
                except Exception:
                    _refresh_i = 60
                try:
                    import subprocess as _subprocess
                    _r = _subprocess.run(
                        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                         "-File", str(_probe), "-Mode", "Json",
                         "-Slot", "default", "-CacheSec", str(_refresh_i)],
                        capture_output=True, text=True, timeout=3, errors="replace",
                    )
                    if _r.returncode == 0 and _r.stdout:
                        _live_usage = _json.loads(_r.stdout)
                except Exception:
                    _live_usage = None  # includes TimeoutExpired -- bounded; UI thread continues
            # Fallback meter only if the live probe didn't return useful data.
            if _live_usage is None or _live_usage.get("status") != "ok":
                _meter = SANCTUM_ROOT_PATH / "automations" / "claude-usage-meter.ps1"
                if _meter.exists():
                    try:
                        import subprocess as _subprocess
                        _r = _subprocess.run(
                            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                             "-File", str(_meter), "-Mode", "Json",
                             "-PlanTier", _default_tier, "-WindowHours", "5"],
                            capture_output=True, text=True, timeout=3, errors="replace",
                        )
                        if _r.returncode == 0 and _r.stdout:
                            _real_usage = _json.loads(_r.stdout)
                    except Exception:
                        _real_usage = None
            # Persist whatever we got (or None) so we don't re-spawn until TTL.
            _USAGE_CACHE = {"ts": _now_ts, "live": _live_usage, "real": _real_usage}

    def _parse_utc(s):
        if not s:
            return None
        try:
            s2 = s.replace("Z", "+00:00") if s.endswith("Z") else s
            return _dt.fromisoformat(s2)
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

    # RKOJ-ELENO :: 2026-05-24T23:55Z :: operator "i want the usage to be progress
    # bar based". Inline visual bar for the per-account usage display. ASCII-safe
    # (#/-) to avoid PowerShell unicode-blockdraw parse fails.
    def _usage_bar(pct, width=14):
        clamped = max(0, min(int(pct), 100))
        filled = int(round(width * clamped / 100))
        empty = width - filled
        col = OK if clamped < 60 else (WARN if clamped < 90 else FAIL)
        return f"{col}[{'#' * filled}{DIM}{'-' * empty}{col}]{RESET}"

    disabled_labels = []
    unlinked_labels = []
    for acct in accts:
        name = acct.get("name", "?")
        enabled = acct.get("enabled", False)
        # RKOJ-ELENO :: 2026-05-25 :: operator hard-canonical "show when its
        # unlinked things like that". `linked` is computed by claude-accounts.ps1
        # Test-AccountLinked; True iff credentials_file holds a real (non-FAKE)
        # token. Missing field defaults True for back-compat (older configs).
        linked = acct.get("linked", True)
        plan_tier = (acct.get("plan_tier") or "?").strip() or "?"
        label = acct.get("label", name)

        if not enabled:
            # Collect for collapsed footer; tag unconfigured slots separately.
            if label and not label.startswith("(unconfigured"):
                disabled_labels.append(label)
            else:
                disabled_labels.append("__slot__")
            continue

        today = acct.get("successful_spawns_today", 0)
        rate_lim_s = acct.get("rate_limited_until_utc")
        last_spawn_s = acct.get("last_spawn_at_utc")
        is_default = (name == default_name)
        marker = f"{BRIGHTP}*{RESET}" if is_default else " "
        is_next = (label == next_name) if next_name else False
        arrow = f" {OK}<-NEXT{RESET}" if is_next else ""

        # REAL usage display with VISUAL PROGRESS BAR (operator 23:55Z "i want
        # the usage to be progress bar based"). Default account: 4-bar live
        # readout from anthropic-usage-probe.ps1 (session/weekly/sonnet/design).
        # API-key slots: spawn-count proxy (no transcript correlation yet).
        last_spawn = _parse_utc(last_spawn_s)
        rate_lim = _parse_utc(rate_lim_s)
        if rate_lim and rate_lim > _now:
            window_str = f"{FAIL}RL {_fmt_dur(rate_lim - _now)}{RESET}"
        elif is_default and _live_usage and _live_usage.get("status") == "ok":
            # Override label tier with measured subscription_type from the OAuth
            # credentials (e.g. "max" + tier "default_claude_max_20x" => max20).
            _sub = (_live_usage.get("subscription_type") or "").strip()
            _tier = (_live_usage.get("rate_limit_tier") or "").strip()
            if "max_20x" in _tier or "max20" in _tier:
                plan_tier = "max20"
            elif _sub:
                plan_tier = _sub
            # RKOJ-ELENO :: 2026-05-25 :: operator hard-canonical "leave out wrong
            # info. like saying its 100%. its fucking not". Label this slot
            # [MEASURED] only because it pulls live Anthropic ratelimit headers.
            # The 4-bar readout below is the actual data.
            window_str = f"{OK}[MEASURED]{RESET}  {DIM}headers ok{RESET}"
        else:
            # RKOJ-ELENO :: 2026-05-25 :: spawn-window math replaces the broken
            # transcript-msg fallback that produced "999% used (8490/500 msgs 5h
            # (fallback))" in screenshot #57. Numerator was transcript record
            # count (all-time, all-projects); denominator was a 500-msg HARDCODED
            # guess that didn't match any real Anthropic cap. Now: count spawns
            # from spawned-windows.jsonl where account_name == name AND
            # started >= now - 5h; divide by tier-aware soft cap (max 20x = 50
            # per best-agent-count-per-claude-plan-study-2026-05-24.md). Bounded
            # 0-100% display, OVER LIMIT badge when raw count > cap.
            _WINDOW_CAP = {
                "max": 50, "max20": 50, "max_20x": 50,
                "max_5x": 20, "max5": 20,
                "pro": 12, "team": 80, "enterprise": 200,
            }
            _cap = _WINDOW_CAP.get((plan_tier or "").strip().lower(), 30)
            _spawn_jsonl = SANCTUM_ROOT_PATH / "_shared-memory" / "spawned-windows.jsonl"
            _cutoff = _now - _td(hours=5)
            _spawns_in_5h = 0
            if _spawn_jsonl.exists():
                try:
                    with _spawn_jsonl.open("r", encoding="utf-8", errors="replace") as _fp:
                        for _ln in _fp.readlines()[-500:]:
                            _ln = _ln.strip()
                            if not _ln or name not in _ln:
                                continue
                            try:
                                _row = _json.loads(_ln)
                            except Exception:
                                continue
                            if (_row.get("account_name") or "").strip() != name:
                                continue
                            _ts = _row.get("started") or ""
                            try:
                                _s = _dt.fromisoformat(
                                    _ts.replace("Z", "+00:00") if _ts.endswith("Z") else _ts
                                )
                                _s_utc = _s.astimezone(_tz.utc)
                            except Exception:
                                continue
                            if _s_utc >= _cutoff:
                                _spawns_in_5h += 1
                except Exception:
                    pass
            _over = _spawns_in_5h > _cap
            _spawn_pct = min(100, int(round(100.0 * _spawns_in_5h / _cap))) if _cap > 0 else 0
            _over_tag = f"  {FAIL}OVER LIMIT{RESET}" if _over else ""
            # RKOJ-ELENO :: 2026-05-25 :: operator hard-canonical "leave out wrong
            # info. like saying its 100%. its fucking not". This row is a PROXY,
            # not real Anthropic-side usage. We count spawned-windows.jsonl rows
            # in the last 5h and divide by a tier-aware SOFT cap. The Anthropic
            # /oauth/usage endpoint is what gives the real %; that path is only
            # taken for the default OAuth slot (see is_default branch above).
            _proxy_tag = f"{WARN}[PROXY]{RESET}"
            window_str = (f"{_proxy_tag} {_usage_bar(_spawn_pct)} {DIM}~{_spawn_pct}%  "
                          f"({_spawns_in_5h}/{_cap} spawns 5h, soft cap){RESET}{_over_tag}")

        # RKOJ-ELENO :: 2026-05-25 :: operator hard-canonical "clean up all
        # shit like this. like all this needs to be clean and in theme"
        # (image #8). Canonical themed slot line:
        #   ●  <name>  · <email> · <plan>   <state-callout>
        # Bullet `●` (accent-colored) replaces `*`; slot key is the primary
        # WHITE label; email + plan are secondary DIM; state is ONE warning
        # token ("not logged in" / "ON LINKED") -- no double-callout. The
        # `* ON UNLINKED  ... not logged in` double-callout from prior render
        # is now a single `{WARN}not logged in{RESET}` chip.
        email = (acct.get("email") or acct.get("api_key_hint") or "").strip()
        bullet_col = BRIGHTP if is_default else PURPLE
        # Secondary meta: name (operator/leo/etc), email if present, plan tier.
        meta_bits = [name]
        if email and email.lower() != name.lower():
            meta_bits.append(email)
        meta_bits.append(f"{plan_tier} plan")
        slot_meta = " · ".join(meta_bits)
        if linked:
            state_chip = f"{OK}linked{RESET}"
        else:
            state_chip = f"{WARN}not logged in{RESET}"
            unlinked_labels.append(label)
        # Primary label = the slot's display label (operator-facing). Falls
        # back to name when label is empty.
        primary = label if label else name
        print(f"  {bullet_col}●{RESET} {WHITE}{primary}{RESET} "
              f"{DIM}· {slot_meta}{RESET}  {state_chip}  "
              f"{window_str}  {DIM}today {today}{RESET}{arrow}")

        # When live probe is available + this is the default account, print the
        # 4-bar layout matching the claude.ai/usage dashboard. Per operator
        # 2026-05-25T00:00Z verbatim screenshot.
        if is_default and _live_usage and _live_usage.get("status") == "ok":
            def _bar4(pct, width=14):
                if pct is None:
                    return f"{DIM}[{'-' * width}]{RESET}", "  n/a"
                p = max(0, min(int(pct), 100))
                f_ = int(round(width * p / 100))
                e_ = width - f_
                col = OK if p < 60 else (WARN if p < 90 else FAIL)
                bar = f"{col}[{'#' * f_}{DIM}{'-' * e_}{col}]{RESET}"
                return bar, f"{p:>3}%"

            def _fmt_reset_in(unix_ts):
                if not unix_ts:
                    return "-"
                try:
                    tgt = _dt.fromtimestamp(int(unix_ts), tz=_tz.utc)
                    delta = tgt - _now
                    if delta.total_seconds() < 0:
                        return "0m"
                    h, rem = divmod(int(delta.total_seconds()), 3600)
                    m, _ = divmod(rem, 60)
                    if h > 48:
                        return f"{h // 24}d"
                    if h > 0:
                        return f"{h}h{m:02d}m"
                    return f"{m}m"
                except Exception:
                    return "-"

            def _fmt_reset_day(unix_ts):
                if not unix_ts:
                    return "-"
                try:
                    tgt = _dt.fromtimestamp(int(unix_ts), tz=_tz.utc).astimezone()
                    # e.g. "Wed 11:00 PM"
                    return tgt.strftime("%a %I:%M %p").lstrip("0").replace(" 0", " ")
                except Exception:
                    return "-"

            # RKOJ-ELENO :: 2026-05-25 :: operator hard-canonical *"all things
            # like this need to be simple. i just need to know opus stuff.
            # session and weekly"*. Sonnet + design bars REMOVED from picker
            # panel -- operator only cares about Opus (which is what
            # session + weekly_all measure for max20 OAuth slots). The fields
            # are still fetched + cached for the Token analytics sub-page;
            # only the visual render here is stripped.
            _sess  = _live_usage.get("session") or {}
            _wkAll = _live_usage.get("weekly_all") or {}
            _wkSn  = _live_usage.get("weekly_sonnet") or {}
            _b1, _p1 = _bar4(_sess.get("pct"))
            _b2, _p2 = _bar4(_wkAll.get("pct"))
            _r1 = _fmt_reset_in(_sess.get("reset_unix"))
            _r2 = _fmt_reset_day(_wkAll.get("reset_unix"))
            print(f"      {DIM}session{RESET} {_b1} {WHITE}{_p1}{RESET}  {DIM}resets in {RESET}{_r1}")
            print(f"      {DIM}weekly {RESET} {_b2} {WHITE}{_p2}{RESET}  {DIM}resets {RESET}{_r2}")
            # Clever emphasis line: weekly cap > session full > all clean
            _wkPct = _wkAll.get("pct") or 0
            _sPct  = _sess.get("pct")  or 0
            if _wkPct >= 100:
                _which = "all-models"
                if (_wkSn.get("pct") or 0) >= 100:
                    _which = "sonnet"
                print(f"      {FAIL}[WEEKLY CAP HIT -- {_which} resets {_r2}]{RESET}")
            elif _sPct >= 100:
                print(f"      {WARN}[session full -- resets in {_r1} (rotates fast)]{RESET}")
            elif _wkPct >= 90:
                print(f"      {WARN}[weekly near cap -- {_wkPct}% used, resets {_r2}]{RESET}")

    # Collapse all disabled into one summary footer line. RKOJ-ELENO 2026-05-24T23:55Z:
    # operator "no cap" -- dropped the "N empty" phrasing that implied a 4-slot cap.
    # Only list NAMED disabled slots; "unconfigured" placeholders are just hidden.
    named_disabled = [l for l in disabled_labels if l != "__slot__"]
    if named_disabled:
        print(f"  {DIM}+ {len(named_disabled)} disabled: {', '.join(named_disabled)} "
              f"(press {RESET}{PURPLE}O{RESET}{DIM} to add more){RESET}")
    # RKOJ-ELENO :: 2026-05-25 :: operator hard-canonical "show when its unlinked
    # things like that". Surface the count of enabled-but-unlinked accounts so
    # the operator knows which ones still need a Login/SetKey before they can
    # actually be leased.
    if unlinked_labels:
        print(f"  {WARN}! {len(unlinked_labels)} enabled but UNLINKED: "
              f"{', '.join(unlinked_labels)}{RESET}  "
              f"{DIM}(press {RESET}{PURPLE}O{RESET}{DIM} to log in){RESET}")


# ---------------------------------------------------------------------------
# Account onboarding (RKOJ-ELENO 2026-05-24 — operator 20:00Z)
# "i need this ROUND-ROBIN-ACCOUNT-ONBOARDING.md to be a button in eve exe
#  that i hit to go through the flow of adding accounts"
# Reads the desktop .md for the canonical Path A flow, then walks operator
# through the SetKey -> Test -> Status sequence interactively. Safe: API key
# entry uses getpass (no terminal echo). Calls automations/claude-accounts.ps1.
# ---------------------------------------------------------------------------


# Canonical header/footer per eve-ui-uniformity-doctrine-2026-05-24
# (RKOJ-ELENO :: 2026-05-24T22:40Z — Home key added per operator
#  "back or home button quit all those things with the same look").
_SUB_PAGE_HOME_SENTINEL = "__EVE_HOME__"


def _print_sub_page_header(title: str) -> None:
    """Canonical header line: DARKP --- WHITE BOLD title DARKP ---.

    RKOJ-ELENO :: 2026-05-25T00:15Z :: operator "each menu needs to go to a
    complete clean new menu that is clean and you cannot see the menu you
    just came from". Clear screen + cursor-home FIRST so the new sub-page
    renders on a fresh blank surface (no prior menu visible underneath).
    No-op when ANSI is off (NO_COLOR / TERM=dumb on POSIX).
    """
    if _ANSI_ON:
        try:
            sys.stdout.write("\033[2J\033[H")
            sys.stdout.flush()
        except Exception:
            pass
    # RKOJ-ELENO :: 2026-05-25 :: Item 66. Short page-transition shimmer so
    # EVE feels alive between page changes (operator: "more animations + live").
    # 600ms / 12fps cap; gracefully skipped under NO_COLOR / EVE_QUIET / SKIP_BANNER.
    _shimmer_transition(label=title[:24] if title else "EVE")
    print()
    print(f"  {DARKP}---{RESET} {WHITE}{BOLD}{title}{RESET} {DARKP}---{RESET}")
    print()


# RKOJ-ELENO :: 2026-05-25T01:15Z :: operator hard-canonical (image #61/#62)
# *"centered menu styling like main_menu hero applied to every sub-page"*.
# All sub-page BODY rendering must route through this helper so columns
# align uniformly with the main menu hero.

_DEFAULT_CENTER_WIDTH = 68  # 60-72 clamp; matches eve_ui.DEFAULT_BLOCK_WIDTH


def _strip_ansi_simple(s: str) -> str:
    """Lightweight ANSI-strip for visible-width calc (local copy avoids import)."""
    out: list[str] = []
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


def _term_cols_eve() -> int:
    """Best-effort terminal column width. Falls back to 80."""
    try:
        return max(60, os.get_terminal_size().columns)
    except (OSError, ValueError):
        return 80


def _center_block(lines, width: int | None = None) -> list[str]:
    """Block-center a list of strings. Same algorithm as eve_ui.center_block.

    All lines get the SAME left-pad so internal column alignment is preserved
    while the block as a whole centers on the terminal.
    """
    line_list = list(lines)
    if not line_list:
        return []
    cols = _term_cols_eve()
    if width is None:
        width = _DEFAULT_CENTER_WIDTH
    block_w = min(width, cols)
    max_visible = max((len(_strip_ansi_simple(ln)) for ln in line_list), default=0)
    effective_w = max(max_visible, block_w)
    pad = max(0, (cols - effective_w) // 2)
    pad_str = " " * pad
    return [pad_str + ln for ln in line_list]


def _print_centered(lines, width: int | None = None) -> None:
    """Center + print a body block. Header/footer use full-width prints."""
    for ln in _center_block(lines, width=width):
        print(ln)


# ---------------------------------------------------------------------------
# Idle shimmer + page-transition shimmer (Item 66 — RKOJ-ELENO :: 2026-05-25)
# Operator (image #66 + 22:45Z utterance "more animations"):
#   *"more animations + live ... feel alive between pages."*
#
# Pattern is jcode-inspired (sinister HSV hue drift; see animations.py). NOT a
# jcode parity claim -- the implementation is a stdlib-only port that biases
# hue around Sinister purple 270 deg. No new dependencies; no background
# thread (the picker input is blocking on getwch, and we don't want a race
# between the ticker writing while the user types). Instead:
#
#   - `_shimmer_transition()` runs a SHORT one-shot animation (600ms total,
#     12 fps cap = 8 frames) on a single accent line during page changes.
#   - `_shimmer_accent(text, tick)` returns the input string with each non-
#     space char wrapped in an HSV-rotated ANSI escape; cheap enough to call
#     per banner render so accents subtly drift between page renders.
#
# Pauses on input: nothing runs in the background, so input is never blocked.
# Disabled gracefully when ANSI is off (NO_COLOR / TERM=dumb on POSIX) or
# when the animations module failed to import.
# ---------------------------------------------------------------------------

# Process-wide animation tick. Bumped each time banner() is called so accent
# hue drifts subtly between page renders even without a background ticker.
_EVE_ANIM_TICK = 0
_EVE_ANIM_FPS_CAP = 12  # max frames per second for the transition shimmer
_EVE_SHIMMER_DURATION_S = 0.6  # 600ms total per operator brief


def _shimmer_accent(text: str, tick: int) -> str:
    """Return text with HSV-rotated per-char accent. jcode-inspired (not parity).

    Uses animations._hsv_to_rgb when available; falls back to plain text when
    ANSI is off or the module didn't import. Cheap: O(len(text)) per call.
    """
    if not _ANSI_ON or animations is None or not text:
        return text
    try:
        # Sinister-purple base hue 270deg, drift +/- 30deg over a slow cycle.
        import math as _math
        base_hue = (270.0 + _math.sin(tick / 25.0) * 30.0) % 360.0
        out_parts: list[str] = []
        col = 0
        for ch in text:
            if ch == " " or ch == "\t":
                out_parts.append(ch)
                col += 1
                continue
            hue = (base_hue + col * 4.5) % 360.0
            r, g, b = animations._hsv_to_rgb(hue, 0.55, 0.95)
            out_parts.append(f"\033[38;2;{r};{g};{b}m{ch}")
            col += 1
        out_parts.append(RESET)
        return "".join(out_parts)
    except Exception:
        return text


def _shimmer_transition(label: str = "EVE", duration_s: float = _EVE_SHIMMER_DURATION_S) -> None:
    """One-shot 600ms shimmer animation. Renders on a single line and clears.

    Called between page changes to make EVE feel alive (operator: "feel alive
    between pages"). 12fps cap; bails immediately if ANSI is off or
    SINISTER_SKIP_BANNER=1. Auto-skipped under EVE_QUIET=1.
    """
    global _EVE_ANIM_TICK
    if not _ANSI_ON:
        return
    if os.environ.get("SINISTER_SKIP_BANNER", "").strip() == "1":
        return
    if os.environ.get("EVE_QUIET", "").strip() == "1":
        return
    if animations is None:
        return
    try:
        frame_interval = 1.0 / float(_EVE_ANIM_FPS_CAP)
        end_time = time.monotonic() + duration_s
        # Compose a short shimmer string ~= label expanded with dots.
        core = f"{label}    .  ..  ...  ....  .....  ......"
        while time.monotonic() < end_time:
            _EVE_ANIM_TICK += 1
            painted = _shimmer_accent(core, _EVE_ANIM_TICK)
            try:
                # \r so the animation overwrites itself in place; \033[K clears
                # the remainder of the line to avoid trailing artifacts.
                sys.stdout.write(f"\r  {painted}\033[K")
                sys.stdout.flush()
            except Exception:
                return
            time.sleep(frame_interval)
        # Clear the shimmer line cleanly so the next banner renders fresh.
        try:
            sys.stdout.write("\r\033[K")
            sys.stdout.flush()
        except Exception:
            pass
    except Exception:
        # Animation must never break the launcher; swallow + return.
        try:
            sys.stdout.write("\r\033[K")
            sys.stdout.flush()
        except Exception:
            pass


def _print_sub_page_footer(extra_keys: str = "") -> None:
    """Canonical footer: DIM --- PURPLE B) Back   PURPLE H) Home   PURPLE X) Exit   DIM (extras)."""
    keys = f"{DIM}({extra_keys}){RESET}" if extra_keys else ""
    line = (
        f"  {DIM}---{RESET} {PURPLE}B){RESET} Back   "
        f"{PURPLE}H){RESET} Home   "
        f"{PURPLE}X){RESET} Exit"
    )
    if keys:
        line = f"{line}   {keys}"
    print()
    print(line)


def _sub_page_route_home() -> None:
    """Dispatch back to the main menu (Home action). Best-effort import."""
    try:
        from main_menu import show_main_menu  # type: ignore
        show_main_menu()
    except Exception:
        # main_menu missing or failed -> fall through to parent (Back behavior)
        pass


def _sub_page_handle_nav(resp: str) -> str | None:
    """Common B / H / X dispatch. Returns:
      - "back" : caller should `return` to parent.
      - "home" : caller routed to main menu (then should `return`).
      - None   : caller should continue handling page-specific keys.
    """
    r = resp.strip().lower()
    if r in ("b", "back", ""):
        return "back"
    if r in ("h", "home"):
        _sub_page_route_home()
        return "home"
    if r in ("x", "exit", "q", "quit"):
        import os as _os
        import sys as _sys
        # RKOJ-ELENO :: 2026-05-25 :: P0 fix (Bug #65b) -- operator "now it wont
        # fucking close". sys.exit(0) doesn't kill hung daemon threads or
        # blocked PowerShell subprocesses; os._exit(0) does. Match the main_menu
        # X-key behavior so X always nukes EVE cleanly from ANY sub-page.
        try:
            _sys.stdout.write("\n  [EVE] goodbye.\n"); _sys.stdout.flush()
        except Exception:
            pass
        _os._exit(0)
    return None


# RKOJ-ELENO :: 2026-05-25 :: Item 65b "unlimited flows" helper. Operator
# (verbatim 2026-05-25 image #65): "Allow unlimited flows pages". Prompts that
# previously bailed back on empty input now re-loop until the operator supplies
# a valid value OR explicitly types B/back (cancel) / X/exit (nuke EVE). Used
# by sub-page secondary prompts (URL / lane / slug / tool / slot).
def _prompt_unlimited(prompt: str, label: str = "value") -> str | None:
    """Loop on input() until non-empty value OR B/X. Returns:
      - str  : the entered value (always non-empty / stripped).
      - None : operator cancelled (B / back / empty after warning) — caller
               should NOT proceed (semantic "go back to caller's menu").
    X/exit at ANY iteration calls os._exit(0) via _sub_page_handle_nav.
    """
    import os as _os
    import sys as _sys
    attempts = 0
    while True:
        try:
            val = input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            return None
        if val.lower() in ("x", "exit", "q", "quit"):
            try:
                _sys.stdout.write("\n  [EVE] goodbye.\n"); _sys.stdout.flush()
            except Exception:
                pass
            _os._exit(0)
        if val.lower() in ("b", "back"):
            return None
        if val:
            return val
        attempts += 1
        # First empty Enter on the inner prompt = nudge, not cancel.
        # Second empty Enter = treat as Back (operator clearly wants out).
        if attempts >= 2:
            return None
        print(f"  {WARN}empty {label} -- press Enter again to cancel, or type a value (X=exit, B=back){RESET}")


def _press_enter_or_x(label: str = "Enter to return") -> None:
    """Block on an `input()` prompt, but honor X/exit/quit so the operator can
    nuke EVE from ANY 'press Enter to continue' wait.

    RKOJ-ELENO :: 2026-05-25 :: Bug #65 fix. Operator: "enter here doesnt
    work i need allow flows to ges allow for unlimited use ... and now it
    wont fucking close". Previously every `input("(Enter to return ...)")`
    silently swallowed X. Now X anywhere -> os._exit(0). Empty Enter is the
    documented default; any other input is silently ignored (returns).
    """
    import os as _os
    import sys as _sys
    try:
        resp = input(f"  {DIM}({label} -- X+Enter to exit){RESET} ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        return
    if resp in ("x", "exit", "q", "quit"):
        try:
            _sys.stdout.write("\n  [EVE] goodbye.\n"); _sys.stdout.flush()
        except Exception:
            pass
        _os._exit(0)


# ---------------------------------------------------------------------------
# Arrow-key navigation (RKOJ-ELENO :: 2026-05-25T03:35Z).
# Operator hard-canonical 2026-05-25 ~03:32Z verbatim:
#   "i want the entire menu to be able to be naviagted with teh arrow keys
#    perfectly like perfectly".
# Pattern is verbatim from tools/eve-picker/project_config_grid.py:150 and
# tools/eve-picker/main_menu.py:940+. Stdlib-only (msvcrt on Windows; input()
# fallback elsewhere). Backward-compatible: callers that ignore the sentinels
# will see arrows as "unknown input" and fall through to existing dispatch.
# ---------------------------------------------------------------------------

try:
    import msvcrt as _msvcrt  # type: ignore
    _HAS_MSVCRT = True
except Exception:
    _msvcrt = None  # type: ignore
    _HAS_MSVCRT = False

_ARROW_UP = "\x1b[ARROW_UP"
_ARROW_DOWN = "\x1b[ARROW_DOWN"
_ARROW_LEFT = "\x1b[ARROW_LEFT"
_ARROW_RIGHT = "\x1b[ARROW_RIGHT"
_KEY_ESC = "\x1b"


def _arrow_input(prompt: str = "") -> str:
    """Drop-in replacement for input() that surfaces arrow keys as sentinel strings.

    Returns:
      - On non-Windows or when msvcrt is unavailable: identical to input(prompt).
      - On Windows: blocks on getwch() loop; printable chars accumulate (echoed)
        until ENTER (returns the accumulated string, like input()). Arrow keys
        return their _ARROW_* sentinels IMMEDIATELY (no Enter needed). ESC alone
        returns _KEY_ESC. Ctrl-C raises KeyboardInterrupt (matches input()).
        BACKSPACE deletes from buffer.

    Callers that don't care about arrows can simply ignore the sentinel strings
    -- they won't match any existing dispatch keys, so they'll fall through to
    the page's "unknown input" path harmlessly.
    """
    if not _HAS_MSVCRT or _msvcrt is None:
        return input(prompt)
    try:
        sys.stdout.write(prompt); sys.stdout.flush()
    except Exception:
        return input(prompt)
    buf: list[str] = []
    while True:
        try:
            ch = _msvcrt.getwch()
        except KeyboardInterrupt:
            raise
        if ch == "\x03":  # Ctrl-C
            raise KeyboardInterrupt
        if ch in ("\r", "\n"):
            sys.stdout.write("\n"); sys.stdout.flush()
            return "".join(buf)
        if ch == "\x08":  # Backspace
            if buf:
                buf.pop()
                try:
                    sys.stdout.write("\b \b"); sys.stdout.flush()
                except Exception:
                    pass
            continue
        if ch == "\x1b":  # bare ESC
            sys.stdout.write("\n"); sys.stdout.flush()
            return _KEY_ESC
        if ch in ("\x00", "\xe0"):  # arrow-key / function-key prefix
            try:
                nxt = _msvcrt.getwch()
            except KeyboardInterrupt:
                raise
            arrow_map = {
                "H": _ARROW_UP,
                "P": _ARROW_DOWN,
                "K": _ARROW_LEFT,
                "M": _ARROW_RIGHT,
            }
            tok = arrow_map.get(nxt)
            if tok:
                sys.stdout.write("\n"); sys.stdout.flush()
                return tok
            continue  # unrecognized special key -> ignore
        # printable char
        buf.append(ch)
        try:
            sys.stdout.write(ch); sys.stdout.flush()
        except Exception:
            pass


def _account_onboarding_flow() -> None:
    """Accounts page :: simplified 4-action OAuth manager.

    RKOJ-ELENO :: 2026-05-25 :: operator screenshot #63 verbatim "reduce this
    to jsut have login, logout (s2l ct accountaon it) status refresh needs to
    happen puto.cremove api key". The 4-action canonical menu is:
      1) Login              (Claude OAuth wizard; isolated sandbox per acct)
      2) Logout              (pick a slot + confirm; runs LogoutSlot)
      3) Select active slot (sets which slot the next spawn uses)
      4) Refresh status     (re-render the slot status panel)
      B) Back   H) Home   X) Exit   (T tokens   L limited)

    API-key path was REMOVED (operator: "puto.cremove api key"). Mark-Limited
    moved off the main 4 -- still reachable via the hidden 'L' key per
    operator brief. Token Analytics still reachable via hidden 'T' key.
    Canonical layout per eve-ui-uniformity-doctrine-2026-05-24.
    """
    import subprocess as _subprocess
    import getpass as _getpass
    import os as _os
    while True:
        rc = _accounts_page_render_and_dispatch(_subprocess, _getpass)
        if rc in ("back", "exit"):
            if rc == "exit":
                # RKOJ-ELENO :: 2026-05-25 :: Item 65c. Hard-kill via os._exit
                # to match _sub_page_handle_nav (sys.exit can be swallowed by
                # blocked subprocess / daemon thread).
                _os._exit(0)
            return


def _token_analytics_submenu(_subprocess) -> None:
    """Accounts page :: Token Analytics sub-menu (option 6).

    RKOJ-ELENO :: 2026-05-24T23:30Z. Operator: "add to the account tab a token
    menu so that we can track all token use and see places where we can
    improve our token use and make better systems to become more token
    efficent".

    Shells out to automations/token-analytics.ps1 for the actual scan +
    rendering (single source of truth = the .ps1; eve.py is a UX wrapper).
    Sub-menu layout follows eve-ui-uniformity-doctrine-2026-05-24
    (header + body + footer, 6-color palette, B/H/X canonical).
    """
    if SANCTUM_ROOT_PATH is None:
        print(f"  {FAIL}[token-analytics] SANCTUM_ROOT not resolved.{RESET}")
        time.sleep(1.5)
        return
    ps1 = SANCTUM_ROOT_PATH / "automations" / "token-analytics.ps1"
    if not ps1.exists():
        print(f"  {FAIL}[token-analytics] token-analytics.ps1 missing at {ps1}.{RESET}")
        time.sleep(1.5)
        return

    actions = [
        ("1", "Summary",         "Summary",         "1h / 5h / 24h / 7d windows + cache + cost"),
        ("2", "By project",      "ByProject",       "per-project totals + cache hit + cost"),
        ("3", "Cache report",    "CacheReport",     "per-project cache efficiency"),
        ("4", "Waste report",    "WasteReport",     "abandoned cache / context bloat / tool loops"),
        ("5", "Recommendations", "Recommendations", "5-10 prioritized actions"),
        ("6", "By session",      "BySession",       "top 10 sessions by billable-eq"),
        ("7", "By model",        "ByModel",         "Opus vs Sonnet vs Haiku mix"),
    ]

    while True:
        _print_sub_page_header("Token Analytics")
        # RKOJ-ELENO :: 2026-05-25 :: operator screenshot #61 "i want the
        # cenetered menu on each page". Body block-centered via _center_block.
        tk_body: list[str] = [
            f"{SOFT}Pick a report -- scans ~/.claude/projects/**/*.jsonl on demand (no cache; jcode-inspired).{RESET}",
            "",
        ]
        for key, title, _act, hint in actions:
            tk_body.append(f"  {PURPLE}{key}){RESET} {WHITE}{title:<18}{RESET} {DIM}{hint}{RESET}")
        _print_centered(tk_body, width=72)
        _print_sub_page_footer("R refresh")

        # RKOJ-ELENO :: 2026-05-25 :: Item 65a fix. Empty Enter MUST route to
        # back per eve-ui-uniformity-doctrine ("B/empty-Enter -> main picker").
        # Previous `or "1"` default ate the Enter key and silently re-ran option 1.
        try:
            resp = input(f"  {WHITE}> [B/1-7]:{RESET} ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return

        nav = _sub_page_handle_nav(resp)
        if nav in ("back", "home"):
            return
        if resp == "r":
            continue

        action = None
        for key, _title, ps_act, _hint in actions:
            if resp == key:
                action = ps_act
                break
        if not action:
            print(f"  {WARN}unknown key '{resp}' -- pick 1-7 or B/X.{RESET}")
            time.sleep(0.8)
            continue

        print()
        print(f"  {SOFT}> token-analytics.ps1 -Action {action} (scanning transcripts ...){RESET}")
        try:
            _subprocess.run(
                ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                 "-File", str(ps1), "-Action", action],
                timeout=120,
            )
        except Exception as e:
            print(f"  {FAIL}[!] action '{action}' exception: {e}{RESET}")
        _press_enter_or_x("Enter to return to Token Analytics")


def _accounts_page_render_and_dispatch(_subprocess, _getpass) -> str:
    """Single render + dispatch cycle of the simplified Accounts page.

    RKOJ-ELENO :: 2026-05-25 :: operator screenshot #63: "reduce this to jsut
    have login, logout (s2l ct accountaon it) status refresh needs to happen
    puto.cremove api key" + screenshot #61: "i want the cenetered menu on
    each page".

    Canonical 4-action menu (block-centered body per eve-ui-uniformity):
      1) Login              -- Claude OAuth wizard (isolated sandbox)
      2) Logout             -- pick slot + confirm + LogoutSlot
      3) Select active slot -- writes active-slot pointer (-Action Use)
      4) Refresh status     -- re-runs Status + re-renders panel

    Hidden helper keys (not in main menu, footer-documented):
      T) Token analytics  -- _token_analytics_submenu(...)
      L) Mark limited     -- runs claude-oauth-accounts.ps1 -Action MarkLimited

    Returns 'back' / 'exit' / 'loop'.
    """
    # RKOJ-ELENO :: 2026-05-25 :: operator hard-canonical *"make accounts
    # manager in theme. everything has to follow main page theme and have
    # header and be centered how we do on the main page"*. Title is now
    # "Accounts Manager" + status_body + menu_body merged into a single
    # centered block so internal columns align cleanly with the main hero
    # block (same _DEFAULT_CENTER_WIDTH of 68).
    _print_sub_page_header("Accounts Manager")

    # Live slot status (re-runs every loop iter; "status refresh needs to
    # happen puto" per operator -- so it's ALWAYS at the top, not behind a key)
    status_body: list[str] = []
    if SANCTUM_ROOT_PATH is not None:
        ps1 = SANCTUM_ROOT_PATH / "automations" / "claude-accounts.ps1"
        if ps1.exists():
            try:
                r = _subprocess.run(
                    ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                     "-File", str(ps1), "-Action", "Status"],
                    capture_output=True, text=True, timeout=10, errors="replace"
                )
                status_body.append(f"{SOFT}Current slot status{RESET}")
                # Trim trailing whitespace so block-center math sees the true
                # visible width of each Status line (otherwise the longest
                # whitespace-padded line drives the pad and the block drifts
                # left of the hero).
                for line in (r.stdout or "").splitlines()[:10]:
                    status_body.append(line.rstrip())
            except Exception as e:
                status_body.append(f"{WARN}(status probe failed: {e}){RESET}")

    # 4-action menu body -- block-centered to match main-menu hero width 68
    menu_body: list[str] = [
        f"{WHITE}Actions{RESET}",
        f"  {PURPLE}1){RESET} {OK}{BOLD}Login{RESET}              {DIM}(Claude OAuth -- isolated sandbox){RESET}",
        f"  {PURPLE}2){RESET} {WHITE}Logout{RESET}             {DIM}(pick slot + confirm){RESET}",
        f"  {PURPLE}3){RESET} {WHITE}Select active slot{RESET} {DIM}(next spawn uses this slot){RESET}",
        f"  {PURPLE}4){RESET} {WHITE}Refresh status{RESET}     {DIM}(re-probe Anthropic + re-render){RESET}",
    ]

    # Merge status + menu into a single centered block so the visible
    # left-edge is uniform (matches main-page hero treatment per operator
    # *"how we do on the main page"*).
    full_body: list[str] = []
    if status_body:
        full_body.extend(status_body)
        full_body.append("")
    full_body.extend(menu_body)
    _print_centered(full_body, width=_DEFAULT_CENTER_WIDTH)
    _print_sub_page_footer("T tokens   L limited")

    # RKOJ-ELENO :: 2026-05-25 :: Item 65a fix. Empty Enter routes to back via
    # _sub_page_handle_nav (per eve-ui-uniformity-doctrine). Removed `or "1"`
    # default that silently re-ran option 1 and ate the canonical back signal.
    try:
        mode_pick = input(f"  {WHITE}> [B/1-4]:{RESET} ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return "back"

    # Canonical nav (B/H/X/back/home/exit/empty-Enter)
    nav = _sub_page_handle_nav(mode_pick)
    if nav == "back" or nav == "home":
        return "back"

    # Refresh-status (4) is a no-op-then-loop: status already rendered at top,
    # next iteration re-runs Status fresh
    if mode_pick in ("4", "refresh", "status", "r"):
        return "loop"

    # Hidden T) Token analytics -- still reachable, just off the main 4
    if mode_pick in ("t", "tokens", "token", "analytics"):
        _token_analytics_submenu(_subprocess)
        return "loop"

    # ---- 1) Login -- isolated-HOME OAuth wizard (handles 1 or N accounts) ----
    if mode_pick in ("1", "login", "claude", "oauth", "o"):
        if SANCTUM_ROOT_PATH is None:
            print(f"  {FAIL}[!] SANCTUM_ROOT not resolved.{RESET}")
            time.sleep(1.5)
            return "loop"
        wizard = SANCTUM_ROOT_PATH / "automations" / "eve-bulk-oauth-login.ps1"
        if not wizard.exists():
            print(f"  {WARN}[!] Claude Login wizard not yet built at {wizard}.{RESET}")
            time.sleep(2)
            return "loop"
        print(f"  {SOFT}> Claude Login wizard (interactive -- isolated sandbox per account){RESET}")
        try:
            _subprocess.run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                             "-File", str(wizard)], timeout=3600)
        except Exception as e:
            print(f"  {FAIL}[!] Claude Login wizard exception: {e}{RESET}")
        _press_enter_or_x("Enter to return to Accounts")
        return "loop"

    # ---- 2) Logout -- pick slot + confirm + LogoutSlot ----
    if mode_pick in ("2", "logout"):
        if SANCTUM_ROOT_PATH is None:
            print(f"  {FAIL}[!] SANCTUM_ROOT not resolved.{RESET}")
            time.sleep(1.5)
            return "loop"
        oauth_ps1 = SANCTUM_ROOT_PATH / "automations" / "claude-oauth-accounts.ps1"
        try:
            raw_slot = input(f"  {WHITE}> slot name to logout:{RESET} ").strip()
            confirm = input(f"  {WHITE}> type '{raw_slot}' to confirm:{RESET} ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return "loop"
        if confirm != raw_slot:
            print(f"  {DIM}(confirmation did not match -- aborted){RESET}")
            time.sleep(1.0)
            return "loop"
        import re as _re
        slot = _re.sub(r"[^a-z0-9]+", "-", raw_slot.lower()).strip("-_")
        try:
            r = _subprocess.run(
                ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                 "-File", str(oauth_ps1), "-Action", "LogoutSlot", "-Name", slot],
                capture_output=True, text=True, timeout=15, errors="replace"
            )
            for line in (r.stdout or "").splitlines():
                print(f"    {line}")
        except Exception as e:
            print(f"  {FAIL}[!] LogoutSlot exception: {e}{RESET}")
        _press_enter_or_x("Enter to return to Accounts")
        return "loop"

    # ---- 3) Select active slot -- writes active-slot pointer ----
    # Shells to claude-oauth-accounts.ps1 -Action Use -Name <slot> which sets
    # ~/.claude/.credentials.json to the named slot's OAuth blob. Next spawn
    # consumes that. Also sets SINISTER_FORCE_SLOT in-process so this EVE
    # session uses it immediately for any spawn launched from the picker.
    if mode_pick in ("3", "select", "use", "active"):
        if SANCTUM_ROOT_PATH is None:
            print(f"  {FAIL}[!] SANCTUM_ROOT not resolved.{RESET}")
            time.sleep(1.5)
            return "loop"
        oauth_ps1 = SANCTUM_ROOT_PATH / "automations" / "claude-oauth-accounts.ps1"
        if not oauth_ps1.exists():
            print(f"  {FAIL}[!] claude-oauth-accounts.ps1 missing at {oauth_ps1}.{RESET}")
            time.sleep(1.5)
            return "loop"
        # List available slots first so operator sees the names
        try:
            lst = _subprocess.run(
                ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                 "-File", str(oauth_ps1), "-Action", "List"],
                capture_output=True, text=True, timeout=8, errors="replace"
            )
            print(f"  {SOFT}Available slots:{RESET}")
            for line in (lst.stdout or "").splitlines()[:15]:
                print(f"    {line}")
        except Exception as e:
            print(f"    {WARN}(List failed: {e}){RESET}")
        print()
        try:
            raw_slot = input(f"  {WHITE}> slot to make ACTIVE:{RESET} ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return "loop"
        import re as _re
        slot = _re.sub(r"[^a-z0-9]+", "-", raw_slot.lower()).strip("-_")
        if not slot:
            print(f"  {WARN}[!] empty slot name.{RESET}")
            time.sleep(1.0)
            return "loop"
        try:
            r = _subprocess.run(
                ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                 "-File", str(oauth_ps1), "-Action", "Use", "-Name", slot],
                capture_output=True, text=True, timeout=10, errors="replace"
            )
            for line in (r.stdout or "").splitlines():
                print(f"    {line}")
            if r.returncode == 0:
                # Pin in-process so EVE picker uses this slot for next spawn
                os.environ["SINISTER_FORCE_SLOT"] = slot
                print(f"  {OK}[+] Active slot is now '{slot}'. "
                      f"SINISTER_FORCE_SLOT={slot} pinned for this EVE session.{RESET}")
            else:
                print(f"  {WARN}[!] -Action Use exit {r.returncode}.{RESET}")
        except Exception as e:
            print(f"  {FAIL}[!] -Action Use exception: {e}{RESET}")
        _press_enter_or_x("Enter to return to Accounts")
        return "loop"

    # ---- L) Mark limited -- hidden helper, still reachable ----
    # Moved off the main 4 per operator brief; reachable via 'L' as documented
    # in the page footer. Same MarkLimited flow as before.
    if mode_pick in ("l", "mark", "limited"):
        if SANCTUM_ROOT_PATH is None:
            print(f"  {FAIL}[!] SANCTUM_ROOT not resolved.{RESET}")
            time.sleep(1.5)
            return "loop"
        oauth_ps1 = SANCTUM_ROOT_PATH / "automations" / "claude-oauth-accounts.ps1"
        if not oauth_ps1.exists():
            print(f"  {FAIL}[!] claude-oauth-accounts.ps1 missing.{RESET}")
            time.sleep(1.5)
            return "loop"
        try:
            raw_slot = input(f"  {WHITE}> slot name to mark limited:{RESET} ").strip()
            until = input(f"  {WHITE}> reset date (YYYY-MM-DD; Enter = next Monday):{RESET} ").strip()
            weekly_resp = input(f"  {WHITE}> weekly cap (rolls weekly)? [y/N]:{RESET} ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return "loop"
        import re as _re
        slot = _re.sub(r"[^a-z0-9]+", "-", raw_slot.lower()).strip("-_")
        if not slot:
            print(f"  {WARN}[!] empty slot name.{RESET}")
            time.sleep(1.0)
            return "loop"
        if not until:
            from datetime import datetime as _dt2, timezone as _tz2, timedelta as _td2
            now = _dt2.now(_tz2.utc)
            days_ahead = (7 - now.weekday()) % 7 or 7
            mon = (now + _td2(days=days_ahead)).replace(hour=0, minute=0, second=0, microsecond=0)
            until = mon.strftime("%Y-%m-%dT%H:%M:%SZ")
        elif len(until) == 10 and until[4] == "-":
            until = until + "T00:00:00Z"
        args = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                "-File", str(oauth_ps1), "-Action", "MarkLimited",
                "-Name", slot, "-Until", until]
        if weekly_resp in ("y", "yes"):
            args.append("-Weekly")
        try:
            r = _subprocess.run(args, capture_output=True, text=True, timeout=15, errors="replace")
            for line in (r.stdout or "").splitlines():
                print(f"    {line}")
            if r.returncode == 0:
                print(f"  {OK}[+] Slot '{slot}' marked limited until {until}.{RESET}")
            else:
                print(f"  {WARN}[!] MarkLimited exit {r.returncode}.{RESET}")
        except Exception as e:
            print(f"  {FAIL}[!] MarkLimited exception: {e}{RESET}")
        _press_enter_or_x("Enter to return to Accounts")
        return "loop"

    # Unknown choice -- API key path no longer exists per operator "puto.cremove"
    print(f"  {WARN}unknown choice '{mode_pick}' -- pick 1-4, T/L, or B/H/X.{RESET}")
    time.sleep(1.0)
    return "loop"


# ---------------------------------------------------------------------------
# Mesh dashboard (RKOJ-ELENO 2026-05-24 — v0.4.4)
# Operator: "make sure all ai agents work together in a mesh network in a sense
# in the ba fil and exe"
# Shows: fleet heartbeats (live/idle/stale), per-lane inbox unread, multi-account
# rotation status, last 8 cross-lane commits.
# ---------------------------------------------------------------------------

def _sanctum_automations_menu() -> None:
    """A-key menu :: invoke sanctum automation scripts from EVE picker.

    Operator hard-canonical 2026-05-24T21:25Z: 'make sure all this is in the
    sanctum and startewd with eve'. Exposes the iter-1-6 ships (link-ingest,
    link-route, claude-accounts-status, brain-decay-score, mesh-coordinator,
    bot-lifecycle, fleet-autostart, fleet-update, heartbeat-sweep) as numbered
    picks so operator never types `powershell -File ...`.
    """
    if SANCTUM_ROOT_PATH is None:
        print(f"  {FAIL}[automations] SANCTUM_ROOT not resolved{RESET}")
        return
    auto_dir = SANCTUM_ROOT_PATH / "automations"

    items = [
        ("Account status board",            "claude-accounts-status.ps1", ["-Mode", "Board"]),
        ("Drop a link to ingest",           "link-ingest.ps1",             ["-Action", "Add", "-Url", "__PROMPT_URL__"]),
        ("Process pending links (Run 3)",   "link-download.ps1",           ["-Action", "Run", "-Limit", "3"]),
        ("Route processed links (RouteAll)","link-route.ps1",              ["-Action", "RouteAll", "-Limit", "3"]),
        ("Brain decay score (top 10)",      "brain-decay-score.ps1",       ["-Action", "Score", "-TopDecayed", "10"]),
        ("Mesh-coord list",                 "mesh-coordinator.ps1",        ["-Action", "List"]),
        ("Bot-lifecycle list",              "bot-lifecycle.ps1",           ["-Action", "List"]),
        ("Fleet-update tail (last 5)",      "fleet-update.ps1",            ["-Action", "List", "-Tail", "5", "-Slug", "sanctum"]),
        ("Fleet-autostart Status",          "fleet-autostart.ps1",         ["-Mode", "Status"]),
        ("Heartbeat-sweep DRY-RUN",         "heartbeat-sweep.ps1",         ["-MaxAgeHours", "24"]),
        ("Contradict :: audit (all lanes)", "contradict.ps1",              ["-Action", "Audit", "-WindowDays", "7"]),
        ("Contradict :: tally",             "contradict.ps1",              ["-Action", "Tally"]),
        ("Contradict :: walk lane",         "contradict.ps1",              ["-Action", "Walk", "-Lane", "__PROMPT_LANE__", "-Limit", "10"]),
        ("Cross-agent dispatch (run tool)", "agent-dispatch.ps1",          ["-Action", "Dispatch", "-Target", "__PROMPT_SLUG__", "-Tool", "__PROMPT_TOOL__"]),
        ("Inbox: list tool-dispatch msgs",  "agent-dispatch.ps1",          ["-Action", "Inbox", "-Slug", "__PROMPT_LANE__"]),
    ]

    while True:
        _print_sub_page_header("Sanctum Automations")
        # RKOJ-ELENO :: 2026-05-25T01:15Z :: operator hard-canonical (image #61
        # called the Agents page "left-aligned + ugly"; same fix applies here).
        # Body items now block-center via _center_block helper above.
        body: list[str] = [
            f"{PURPLE}{i:>2}){RESET}  {WHITE}{label}{RESET}"
            for i, (label, _, _) in enumerate(items, start=1)
        ]
        _print_centered(body, width=68)
        _print_sub_page_footer(f"1-{len(items)} to run")
        try:
            choice = input("  > ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return
        nav = _sub_page_handle_nav(choice)
        if nav is not None:
            return
        if not choice.isdigit():
            print(f"  {WARN}not a number{RESET}")
            continue
        idx = int(choice) - 1
        if idx < 0 or idx >= len(items):
            print(f"  {WARN}out of range{RESET}")
            continue
        label, script_name, args = items[idx]
        script_path = auto_dir / script_name
        if not script_path.exists():
            print(f"  {FAIL}[FAIL] script not found: {script_path}{RESET}")
            continue
        # RKOJ-ELENO :: 2026-05-25 :: Item 65b "unlimited flows". Prompts now
        # re-loop via _prompt_unlimited instead of silent-bail on empty input.
        resolved_args = list(args)
        if "__PROMPT_URL__" in resolved_args:
            url = _prompt_unlimited(f"  {DIM}> URL to ingest (B=cancel, X=exit):{RESET} ", "url")
            if url is None:
                continue
            resolved_args = [url if a == "__PROMPT_URL__" else a for a in resolved_args]
        if "__PROMPT_LANE__" in resolved_args:
            lane = _prompt_unlimited(
                f"  {DIM}> lane slug (e.g. sinister-os, sanctum, kernel-apk; B=cancel, X=exit):{RESET} ",
                "lane",
            )
            if lane is None:
                continue
            resolved_args = [lane if a == "__PROMPT_LANE__" else a for a in resolved_args]
        if "__PROMPT_SLUG__" in resolved_args:
            slug = _prompt_unlimited(
                f"  {DIM}> target agent slug (live agents shown via M-key; B=cancel, X=exit):{RESET} ",
                "slug",
            )
            if slug is None:
                continue
            resolved_args = [slug if a == "__PROMPT_SLUG__" else a for a in resolved_args]
        if "__PROMPT_TOOL__" in resolved_args:
            tool = _prompt_unlimited(
                f"  {DIM}> tool name (e.g. brain-decay-score, contradict, heartbeat-sweep; B=cancel, X=exit):{RESET} ",
                "tool",
            )
            if tool is None:
                continue
            resolved_args = [tool if a == "__PROMPT_TOOL__" else a for a in resolved_args]
        cmd = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
               "-File", str(script_path)] + resolved_args
        print(f"  {SOFT}> running {script_name} {' '.join(args)}{RESET}")
        try:
            rc = subprocess.call(cmd, timeout=180)
            tag = f"{OK}exit=0{RESET}" if rc == 0 else f"{WARN}exit={rc}{RESET}"
            print(f"  {tag}")
        except subprocess.TimeoutExpired:
            print(f"  {FAIL}[FAIL] script timed out after 180s{RESET}")
        except Exception as e:
            print(f"  {FAIL}[FAIL] script raised: {e}{RESET}")
        # RKOJ-ELENO :: 2026-05-25 :: Item 65c. Route through _press_enter_or_x
        # so X here also nukes EVE cleanly (was a previously-silent input()).
        _press_enter_or_x("Enter to continue")


def _view_mesh_status() -> None:
    """One-shot mesh-network snapshot.

    Canonical sub-page layout per eve-ui-uniformity-doctrine-2026-05-24
    (header + body + footer with B/H/X/R). RKOJ-ELENO :: 2026-05-24T22:40Z.
    """
    import json as _json
    if SANCTUM_ROOT_PATH is None:
        print(f"  {FAIL}[mesh] SANCTUM_ROOT not resolved{RESET}")
        return
    _print_sub_page_header("Mesh Status")

    body: list[str] = []

    # 1) Fleet heartbeats — live (<=5m) / idle (5m-1h) / stale (>1h)
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
    body.append(f"{SOFT}heartbeats{RESET}  total={WHITE}{total}{RESET}   "
                f"{OK}live={live}{RESET}   {WARN}idle={idle}{RESET}   {DIM}stale={stale}{RESET}")
    hb_rows.sort(key=lambda r: r[1])
    for slug, age, tag in hb_rows[:5]:
        color = OK if tag == "live" else (WARN if tag == "idle" else DIM)
        age_str = f"{age}s" if age < 60 else (f"{age // 60}m" if age < 3600 else f"{age // 3600}h")
        body.append(f"  {color}*{RESET} {WHITE}{slug:<32}{RESET}  {color}{tag:<5}{RESET}  {DIM}{age_str} ago{RESET}")

    # 2) Inbox unread per lane (top 5)
    body.append("")
    body.append(f"{SOFT}inbox{RESET}  per-lane unread (top 5)")
    manifest = SANCTUM_ROOT_PATH / "_shared-memory" / "inbox" / "_manifest.json"
    if manifest.exists():
        try:
            m = _json.loads(manifest.read_text(encoding="utf-8-sig", errors="replace"))
            total_u = m.get("total_unread", 0)
            per_lane = m.get("per_lane", {})
            body.append(f"  {DIM}total unread fleet-wide:{RESET} {WHITE}{total_u}{RESET}")
            top = sorted(per_lane.items(), key=lambda kv: -kv[1])[:5]
            for slug, n in top:
                color = WARN if n > 5 else SOFT
                body.append(f"  {color}*{RESET} {WHITE}{slug:<32}{RESET}  {color}{n} unread{RESET}")
        except Exception as e:
            body.append(f"  {WARN}(manifest unreadable: {e}){RESET}")
    else:
        body.append(f"  {DIM}(no manifest -- run automations/inbox-manifest-build.ps1){RESET}")

    # 3) Account rotation status
    body.append("")
    body.append(f"{SOFT}accounts{RESET}  multi-claude rotation")
    accts_f = SANCTUM_ROOT_PATH / "_shared-memory" / "claude-accounts.json"
    if accts_f.exists():
        try:
            a = _json.loads(accts_f.read_text(encoding="utf-8-sig", errors="replace"))
            body.append(f"  {DIM}strategy={RESET}{a.get('rotation_strategy','?')}  "
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
                body.append(f"  {BRIGHTP}*{RESET} {WHITE}{label:<32}{RESET}  "
                            f"{state_tag}  sessions={cur}/{cap}  today={today}{rate_tag}")
        except Exception as e:
            body.append(f"  {WARN}(accounts file unreadable: {e}){RESET}")
    else:
        body.append(f"  {DIM}(claude-accounts.json not present){RESET}")

    # 4) Recent cross-lane git activity (last 8 commits)
    body.append("")
    body.append(f"{SOFT}recent activity{RESET}  last 8 commits on this branch")
    try:
        log = subprocess.check_output(
            ["git", "log", "--oneline", "-8", "--no-color"],
            cwd=str(SANCTUM_ROOT_PATH), stderr=subprocess.DEVNULL, timeout=3
        ).decode("utf-8", errors="replace").strip().splitlines()
        for ln in log:
            trunc = ln if len(ln) <= 84 else ln[:81] + "..."
            body.append(f"  {DIM}*{RESET} {SOFT}{trunc}{RESET}")
    except Exception as e:
        body.append(f"  {WARN}(git log failed: {e}){RESET}")

    _print_centered(body, width=72)
    _print_sub_page_footer("R)efresh")
    while True:
        try:
            resp = input("  > ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return
        nav = _sub_page_handle_nav(resp)
        if nav is not None:
            return
        if resp == "r":
            _view_mesh_status()
            return


def _view_queue() -> None:
    """Canonical Queue sub-page :: top 3 open OPERATOR-ACTION-QUEUE rows.

    Header + body + footer (B/H/X/R) per eve-ui-uniformity-doctrine-2026-05-24.
    RKOJ-ELENO :: 2026-05-24T22:40Z.
    """
    rows = _queue_top_rows(3)
    _print_sub_page_header("Queue (top 3 open)")
    body: list[str] = []
    if not rows:
        body.append(f"{DIM}(no ## headers found in OPERATOR-ACTION-QUEUE.md){RESET}")
    for r in rows:
        trunc = r if len(r) <= 76 else r[:73] + "..."
        body.append(f"{PURPLE}*{RESET} {SOFT}{trunc}{RESET}")
    _print_centered(body, width=72)
    _print_sub_page_footer("R)efresh")
    while True:
        try:
            resp = input("  > ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return
        nav = _sub_page_handle_nav(resp)
        if nav is not None:
            return
        if resp == "r":
            _view_queue()
            return


def _view_utterances() -> None:
    """Canonical Utterances sub-page :: last 5 unresolved operator utterances.

    Header + body + footer (B/H/X/R) per eve-ui-uniformity-doctrine-2026-05-24.
    RKOJ-ELENO :: 2026-05-24T22:40Z.
    """
    recs = _unresolved_utterances(5)
    _print_sub_page_header("Utterances (last 5 unresolved)")
    body: list[str] = []
    if not recs:
        body.append(f"{DIM}(operator-utterances.jsonl is clean){RESET}")
    for r in recs:
        ts = r.get("ts_utc", "?")
        slug = r.get("session_slug", "?")
        preview = r.get("preview") or r.get("message_full", "")
        preview = preview if len(preview) <= 60 else preview[:57] + "..."
        status = r.get("status", "new")
        body.append(f"{PURPLE}*{RESET} {DIM}{ts}{RESET} "
                    f"{BRIGHTP}{slug}{RESET} {SOFT}({status}){RESET}: {WHITE}{preview}{RESET}")
    _print_centered(body, width=72)
    _print_sub_page_footer("R)efresh")
    while True:
        try:
            resp = input("  > ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return
        nav = _sub_page_handle_nav(resp)
        if nav is not None:
            return
        if resp == "r":
            _view_utterances()
            return


# ---------------------------------------------------------------------------
# Sinister LINK sub-page (L-key) :: cross-machine pairing manager
# Author: RKOJ-ELENO :: 2026-05-25
#
# Operator (verbatim 2026-05-25 ~00:50Z):
#   "Call this Sinister LINK and do waht we need to do so that leo and i can
#    link our machines so our agents and can communicate. place iut in even
#    anmd have it in the main header in ready saying sinister LINK unlinked
#    to eleno. then a way that we can get linked on our exe once he install
#    on his pc and we can have this efficent system we already have working
#    for us."
#
# Backend: automations/sinister-link.ps1 (Status / GenerateInvite /
# AcceptInvite / Sync / Unlink / Health / ListInvites) +
# automations/mesh-coordinator.ps1 -Action ListPeer (peer's active locks).
# Header + body + footer canonical layout per eve-ui-uniformity-doctrine-
# 2026-05-24. Body capped at ~13 lines; sub-actions live behind 1-letter keys.
# ---------------------------------------------------------------------------

def _sinister_link_invoke(args: list[str], timeout: int = 15) -> tuple[int, str]:
    """Run sinister-link.ps1 with args; return (exit_code, combined_output)."""
    if SANCTUM_ROOT_PATH is None:
        return (2, "SANCTUM_ROOT not resolved")
    ps1 = SANCTUM_ROOT_PATH / "automations" / "sinister-link.ps1"
    if not ps1.exists():
        return (2, f"missing: {ps1}")
    cmd = [
        "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", str(ps1),
    ] + args
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        out = (r.stdout or "") + (r.stderr or "")
        return (r.returncode, out)
    except subprocess.TimeoutExpired:
        return (124, f"timeout after {timeout}s")
    except Exception as e:
        return (1, f"exception: {e}")


def _sinister_link_render_status() -> None:
    """Render the LINK status block (4-7 lines). Used by main sub-page body."""
    rc, out = _sinister_link_invoke(["-Action", "Status"], timeout=8)
    if rc != 0:
        print(f"  {WARN}status failed (rc={rc}): {out.strip()[:120]}{RESET}")
        return
    for ln in out.splitlines():
        if not ln.strip():
            continue
        if ln.startswith("Sinister LINK"):
            continue  # header already rendered by sub-page
        # Color-code state field: green for linked, orange for unlinked.
        if "state:" in ln and "unlinked" in ln:
            print(f"  {WARN}{ln.strip()}{RESET}")
        elif "state:" in ln and "linked" in ln:
            print(f"  {OK}{ln.strip()}{RESET}")
        elif "warning:" in ln:
            print(f"  {WARN}{ln.strip()}{RESET}")
        else:
            print(f"  {SOFT}{ln.strip()}{RESET}")


def _sinister_link_show_peer_locks() -> None:
    """Render peer's active mesh-locks (so operator sees what Leo is touching)."""
    if SANCTUM_ROOT_PATH is None:
        print(f"  {WARN}(SANCTUM_ROOT not resolved){RESET}")
        return
    ps1 = SANCTUM_ROOT_PATH / "automations" / "mesh-coordinator.ps1"
    if not ps1.exists():
        print(f"  {WARN}(mesh-coordinator.ps1 missing){RESET}")
        return
    cmd = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
           "-File", str(ps1), "-Action", "ListPeer"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=8)
        out = (r.stdout or "") + (r.stderr or "")
        for ln in out.splitlines():
            if ln.strip():
                print(f"  {SOFT}{ln.rstrip()}{RESET}")
    except Exception as e:
        print(f"  {WARN}(peer-locks lookup failed: {e}){RESET}")


def _sinister_link_page() -> None:
    """Sinister LINK sub-page :: looped, canonical UI.

    Actions:
      P) Pair (generate invite to send to peer)
      C) accept invite Code (peer pastes here)
      S) Sync now
      H) Health snapshot
      V) View peer's mesh locks
      U) Unlink
      R) Refresh status
      B) Back   X) Exit
    """
    while True:
        _print_sub_page_header("Sinister LINK :: cross-machine pairing")
        _sinister_link_render_status()
        # RKOJ-ELENO :: 2026-05-25 :: operator screenshot #61 "i want the
        # cenetered menu on each page". Actions block centered via _center_block.
        link_body: list[str] = [
            f"{SOFT}actions{RESET}",
            f"  {PURPLE}P){RESET} Generate invite (send to peer)   "
            f"{PURPLE}C){RESET} Accept invite Code (paste from peer)",
            f"  {PURPLE}S){RESET} Sync now                          "
            f"{PURPLE}H){RESET} Health snapshot",
            f"  {PURPLE}V){RESET} View peer's mesh locks            "
            f"{PURPLE}U){RESET} Unlink",
        ]
        _print_centered(link_body, width=72)
        _print_sub_page_footer("R)efresh   P/C/S/H/V/U")
        try:
            resp = input("  > ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return
        nav = _sub_page_handle_nav(resp)
        if nav is not None:
            return
        if resp == "r":
            continue
        if resp == "p":
            print()
            try:
                mins_in = input(f"  {SOFT}expires in N minutes [60]:{RESET} ").strip()
                mins = int(mins_in) if mins_in else 60
            except (ValueError, EOFError, KeyboardInterrupt):
                mins = 60
            rc, out = _sinister_link_invoke(
                ["-Action", "GenerateInvite", "-ExpiresMin", str(mins)],
                timeout=10,
            )
            print()
            if rc == 0:
                print(f"  {OK}invite generated{RESET}")
                # Show code + instructions block as-is
                for ln in out.splitlines():
                    print(f"  {ln}")
            else:
                print(f"  {FAIL}generate failed (rc={rc}): {out.strip()[:200]}{RESET}")
            _press_enter_or_x("Enter to return to LINK menu")
            continue
        if resp == "c":
            print()
            try:
                code = input(f"  {SOFT}paste invite code:{RESET} ").strip()
            except (EOFError, KeyboardInterrupt):
                continue
            if not code:
                print(f"  {WARN}(no code entered){RESET}")
                time.sleep(0.6)
                continue
            rc, out = _sinister_link_invoke(
                ["-Action", "AcceptInvite", "-InviteCode", code],
                timeout=10,
            )
            print()
            if rc == 0:
                print(f"  {OK}pairing accepted{RESET}")
                for ln in out.splitlines():
                    print(f"  {ln}")
            else:
                print(f"  {FAIL}accept failed (rc={rc}): {out.strip()[:200]}{RESET}")
            _press_enter_or_x("Enter to return to LINK menu")
            continue
        if resp == "s":
            print()
            print(f"  {SOFT}syncing...{RESET}")
            rc, out = _sinister_link_invoke(["-Action", "Sync"], timeout=20)
            for ln in out.splitlines():
                print(f"  {ln}")
            _press_enter_or_x("Enter to return")
            continue
        if resp == "h":
            print()
            rc, out = _sinister_link_invoke(["-Action", "Health"], timeout=8)
            for ln in out.splitlines():
                print(f"  {ln}")
            _press_enter_or_x("Enter to return")
            continue
        if resp == "v":
            print()
            _sinister_link_show_peer_locks()
            _press_enter_or_x("Enter to return")
            continue
        if resp == "u":
            print()
            try:
                confirm = input(f"  {WARN}unlink this machine from peer? type YES:{RESET} ").strip()
            except (EOFError, KeyboardInterrupt):
                continue
            if confirm != "YES":
                print(f"  {DIM}(cancelled){RESET}")
                time.sleep(0.6)
                continue
            rc, out = _sinister_link_invoke(["-Action", "Unlink"], timeout=10)
            for ln in out.splitlines():
                print(f"  {ln}")
            _press_enter_or_x("Enter to return")
            continue


# ---------------------------------------------------------------------------
# Agents page (K-key) :: project-grouped multi-select fleet manager
# Author: RKOJ-ELENO :: 2026-05-25
#
# Operator (verbatim 2026-05-25 ~00:15Z):
#   "i need you to change the kill fleet selection here to agents. and i need
#    it to be a menu that shows active proejcts that i can see all active
#    running agents and i can scroll through and select the ones i want then
#    i can run actions on them like. kill all, immediate close. save and
#    close button and 2-3 more you think i should have."
#
# Backend: automations/agent-actions.ps1.
# Five per-slug actions:
#   K=KillAll  C=ImmediateClose  S=SaveAndClose  Pa=Pause(toggle)  Msg=Message
# Plus R=Refresh A=SelectAll N=SelectNone n=NextPage p=PrevPage B=Back X=Exit
# ---------------------------------------------------------------------------

_AGENTS_PAGE_SIZE = 10


def _read_heartbeat_rows() -> list[dict]:
    """Scan _shared-memory/heartbeats/*.json (top level only, skip _archive)."""
    import json as _json
    from datetime import datetime as _dt, timezone as _tz
    if SANCTUM_ROOT_PATH is None:
        return []
    hb_dir = SANCTUM_ROOT_PATH / "_shared-memory" / "heartbeats"
    if not hb_dir.exists():
        return []
    rows: list[dict] = []
    now_utc = _dt.now(_tz.utc)
    for p in sorted(hb_dir.glob("*.json")):
        try:
            with p.open("r", encoding="utf-8") as fh:
                obj = _json.load(fh)
        except Exception:
            continue
        slug = obj.get("slug") or p.stem
        ts_raw = obj.get("ts_utc") or obj.get("timestamp") or ""
        age_min: float = 1e9
        if ts_raw:
            try:
                ts_clean = ts_raw.replace("Z", "+00:00")
                ts = _dt.fromisoformat(ts_clean)
                age_min = (now_utc - ts).total_seconds() / 60.0
            except Exception:
                age_min = 1e9
        if age_min < 5:
            state = "live"
        elif age_min < 30:
            state = "idle"
        else:
            state = "stale"
        focus = (
            obj.get("current_focus")
            or obj.get("focus_intent")
            or obj.get("focus")
            or obj.get("phase")
            or ""
        )
        focus = str(focus).strip().replace("\n", " ")
        if len(focus) > 48:
            focus = focus[:45] + "..."
        project = (
            obj.get("project")
            or obj.get("agent_display")
            or obj.get("agent")
            or slug
        )
        rows.append({
            "slug": slug,
            "project": str(project),
            "state": state,
            "age_min": age_min,
            "focus": focus,
            "agent_identity": obj.get("agent_identity", ""),
        })
    state_rank = {"live": 0, "idle": 1, "stale": 2}
    rows.sort(key=lambda r: (state_rank.get(r["state"], 3), r["age_min"]))
    return rows


def _agents_format_age(age_min: float) -> str:
    if age_min > 100000:
        return "  inf"
    # Heartbeats with future timestamps (clock skew) clamp to 0s display.
    if age_min < 0:
        age_min = 0.0
    if age_min < 1:
        return f"{int(age_min * 60):3d}s"
    if age_min < 60:
        return f"{int(age_min):3d}m"
    if age_min < 1440:
        return f"{int(age_min / 60):3d}h"
    return f"{int(age_min / 1440):3d}d"


def _agents_state_color(state: str) -> str:
    return {"live": OK, "idle": WARN, "stale": SOFT}.get(state, DIM)


def _agents_run_action(action: str, slug: str, message: str = "") -> tuple[bool, str]:
    """Invoke agent-actions.ps1; return (ok, one-line summary)."""
    import json as _json
    if SANCTUM_ROOT_PATH is None:
        return False, "SANCTUM_ROOT unset"
    ps1 = SANCTUM_ROOT_PATH / "automations" / "agent-actions.ps1"
    if not ps1.exists():
        return False, f"agent-actions.ps1 missing at {ps1}"
    cmd = [
        "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", str(ps1),
        "-Action", action, "-Slug", slug,
    ]
    if action == "Message" and message:
        cmd += ["-Message", message]
    try:
        cp = subprocess.run(cmd, timeout=20, capture_output=True, text=True)
    except subprocess.TimeoutExpired:
        return False, f"{action}({slug}): timeout after 20s"
    except Exception as e:
        return False, f"{action}({slug}): {e}"
    out = (cp.stdout or "").strip().splitlines()
    last_json = ""
    for line in reversed(out):
        line = line.strip()
        if line.startswith("{") and line.endswith("}"):
            last_json = line
            break
    if last_json:
        try:
            res = _json.loads(last_json)
            return bool(res.get("ok")), str(res.get("detail", "")).strip()
        except Exception:
            pass
    return (cp.returncode == 0), (cp.stdout or cp.stderr or "")[:120].strip()


def _agents_open_multi_launch() -> str:
    """Mu-key: list swarm presets and prompt operator to launch one.

    RKOJ-ELENO :: 2026-05-25 :: Tony Stark command center (operator 06:30Z).
    Delegates to automations/multi_agent_launcher.py.
    """
    if SANCTUM_ROOT_PATH is None:
        return f"{WARN}SANCTUM_ROOT unset{RESET}"
    py = SANCTUM_ROOT_PATH / "automations" / "multi_agent_launcher.py"
    if not py.exists():
        return f"{WARN}multi_agent_launcher.py missing at {py}{RESET}"
    try:
        cp = subprocess.run(
            [sys.executable, str(py), "--list-presets"],
            timeout=15, capture_output=True, text=True,
        )
        print(cp.stdout)
        if cp.returncode != 0:
            return f"{WARN}list-presets failed rc={cp.returncode}{RESET}"
    except Exception as e:
        return f"{WARN}list failed: {e}{RESET}"
    try:
        name = input(f"  {WHITE}preset name (empty = cancel):{RESET} ").strip()
    except (EOFError, KeyboardInterrupt):
        name = ""
    if not name:
        return f"{DIM}multi-launch cancelled{RESET}"
    try:
        cp2 = subprocess.run(
            [sys.executable, str(py), "--swarm", name],
            timeout=60, capture_output=True, text=True,
        )
        print(cp2.stdout)
        if cp2.returncode != 0:
            return f"{WARN}swarm '{name}' rc={cp2.returncode}{RESET}"
        return f"{OK}swarm '{name}' launched{RESET}"
    except Exception as e:
        return f"{WARN}swarm failed: {e}{RESET}"


def _agents_open_dashboard() -> str:
    """Db-key: run multi_agent_status.py --watch in the current terminal.

    RKOJ-ELENO :: 2026-05-25 :: Tony Stark command center.
    Returns when operator hits Ctrl-C inside the dashboard.
    """
    if SANCTUM_ROOT_PATH is None:
        return f"{WARN}SANCTUM_ROOT unset{RESET}"
    py = SANCTUM_ROOT_PATH / "automations" / "multi_agent_status.py"
    if not py.exists():
        return f"{WARN}multi_agent_status.py missing at {py}{RESET}"
    try:
        subprocess.call([sys.executable, str(py), "--watch", "--interval", "5"])
    except KeyboardInterrupt:
        pass
    except Exception as e:
        return f"{WARN}dashboard failed: {e}{RESET}"
    return f"{DIM}dashboard exited{RESET}"


def _agents_open_rate_limit() -> str:
    """Rl-key: print one-table account-balancer recommendation.

    RKOJ-ELENO :: 2026-05-25 :: Tony Stark command center (Image 1 reinforcement
    'over seer track the rate limit rate and slowly adjust things').
    """
    if SANCTUM_ROOT_PATH is None:
        return f"{WARN}SANCTUM_ROOT unset{RESET}"
    py = SANCTUM_ROOT_PATH / "automations" / "account_balancer.py"
    if not py.exists():
        return f"{WARN}account_balancer.py missing at {py}{RESET}"
    try:
        cp = subprocess.run(
            [sys.executable, str(py), "--recommend"],
            timeout=15, capture_output=True, text=True,
        )
        print(cp.stdout)
        if cp.returncode != 0:
            return f"{WARN}recommend rc={cp.returncode}{RESET}"
        try:
            input(f"  {DIM}<enter to return>{RESET} ")
        except (EOFError, KeyboardInterrupt):
            pass
        return f"{OK}rate-limit verdict shown{RESET}"
    except Exception as e:
        return f"{WARN}recommend failed: {e}{RESET}"


def _agents_render(rows: list[dict], selected: set[int], page: int,
                   status_line: str = "") -> None:
    """Render one frame of the Agents page (header + grouped paginated body + footer)."""
    try:
        os.system("cls" if os.name == "nt" else "clear")
    except Exception:
        pass
    _print_sub_page_header("Agents -- active fleet manager")
    n = len(rows)
    total_pages = max(1, (n + _AGENTS_PAGE_SIZE - 1) // _AGENTS_PAGE_SIZE)
    page = max(0, min(page, total_pages - 1))
    lo = page * _AGENTS_PAGE_SIZE
    hi = min(lo + _AGENTS_PAGE_SIZE, n)
    sel_count = sum(1 for i in selected if 0 <= i < n)

    # RKOJ-ELENO :: 2026-05-25T01:15Z :: operator hard-canonical (image #61)
    # *"agents page is left-aligned + ugly -- center the table"*. Body now
    # block-centers via _center_block helper above.
    body: list[str] = []
    body.append(f"{DIM}page {page + 1}/{total_pages} | {n} agent(s) | "
                f"{sel_count} selected{RESET}")
    body.append("")
    if n == 0:
        body.append(f"{DIM}(no heartbeats found in _shared-memory/heartbeats/){RESET}")
    else:
        current_project = None
        for idx in range(lo, hi):
            r = rows[idx]
            proj = r["project"]
            if proj != current_project:
                body.append(f"{BRIGHTP}{BOLD}{proj}{RESET}")
                current_project = proj
            mark = f"{OK}[*]{RESET}" if idx in selected else f"{DIM}[ ]{RESET}"
            num = f"{PURPLE}{idx + 1:3d}{RESET}"
            slug = f"{WHITE}{r['slug']:<28}{RESET}"
            state_col = _agents_state_color(r["state"])
            state = f"{state_col}{r['state']:<5}{RESET}"
            age = f"{SOFT}{_agents_format_age(r['age_min'])}{RESET}"
            focus = f"{DIM}{r['focus']}{RESET}"
            body.append(f"{mark} {num}  {slug} {state} {age}  {focus}")
    body.append("")
    body.append(f"{DIM}--- Actions ---{RESET}")
    body.append(f"{PURPLE}K){RESET} Kill all selected     "
                f"{PURPLE}C){RESET} Immediate close     "
                f"{PURPLE}S){RESET} Save + close")
    body.append(f"{PURPLE}Pa){RESET} Pause/unpause toggle "
                f"{PURPLE}Msg){RESET} Send message       "
                f"{PURPLE}R){RESET} Refresh")
    body.append(f"{PURPLE}A){RESET} Select all            "
                f"{PURPLE}N){RESET} Select none         "
                f"{PURPLE}n/p){RESET} Next/prev page")
    # RKOJ-ELENO :: 2026-05-25 :: Tony Stark command center (operator 06:30Z).
    # M/D/Rl wire the multi-agent toolkit (multi_agent_launcher.py / status / balancer).
    body.append(f"{BRIGHTP}{BOLD}--- Command Center ---{RESET}")
    body.append(f"{PURPLE}Mu){RESET} Multi-Launch preset   "
                f"{PURPLE}Db){RESET} Dashboard (live)     "
                f"{PURPLE}Rl){RESET} Rate-Limit recommend")
    body.append(f"{DIM}Select by typing: 1,3,5  or  2-4  or  all  or  none{RESET}")
    if status_line:
        body.append("")
        body.append(f"{SOFT}{status_line}{RESET}")
    _print_centered(body, width=72)
    _print_sub_page_footer("type number-list to (de)select, or an action key")


def _agents_parse_selection(raw: str, current: set[int], n: int) -> set[int]:
    """Toggle selection. Forms: 'all' / 'none' / '1,3,5' / '2-4' / mix.

    Indexes are 1-based in input; stored as 0-based.
    """
    r = raw.strip().lower()
    if r in ("all", "*"):
        return set(range(n))
    if r in ("none", "clear"):
        return set()
    new_sel = set(current)
    tokens = [t.strip() for t in r.replace(" ", "").split(",") if t.strip()]
    for tok in tokens:
        if "-" in tok and not tok.startswith("-"):
            try:
                a_s, b_s = tok.split("-", 1)
                a = int(a_s) - 1
                b = int(b_s) - 1
                if a > b:
                    a, b = b, a
                for i in range(a, b + 1):
                    if 0 <= i < n:
                        if i in new_sel:
                            new_sel.discard(i)
                        else:
                            new_sel.add(i)
            except ValueError:
                continue
        else:
            try:
                i = int(tok) - 1
                if 0 <= i < n:
                    if i in new_sel:
                        new_sel.discard(i)
                    else:
                        new_sel.add(i)
            except ValueError:
                continue
    return new_sel


def _agents_apply_action(action: str, selected_slugs: list[str],
                         message: str = "") -> str:
    """Run action over every selected slug. Return one-line status."""
    if not selected_slugs:
        return f"{WARN}no selection -- pick at least one row first{RESET}"
    ok_count = 0
    fail_count = 0
    last_detail = ""
    for s in selected_slugs:
        ok, detail = _agents_run_action(action, s, message)
        if ok:
            ok_count += 1
        else:
            fail_count += 1
        last_detail = detail
    if fail_count == 0:
        return f"{OK}{action}: {ok_count}/{len(selected_slugs)} ok{RESET}  {DIM}{last_detail[:60]}{RESET}"
    return (f"{WARN}{action}: {ok_count} ok / {fail_count} fail{RESET}  "
            f"{DIM}{last_detail[:60]}{RESET}")


def _agents_page(smoke: bool = False) -> None:
    """K-key sub-page: project-grouped multi-select agent manager.

    Renders heartbeats (live/idle/stale), paginated scroll, multi-select via
    comma/range list, dispatches 5 per-slug actions through agent-actions.ps1.
    smoke=True renders one frame and returns (no input loop).
    Author: RKOJ-ELENO :: 2026-05-25.
    """
    rows = _read_heartbeat_rows()
    selected: set[int] = set()
    page = 0
    status = ""
    if smoke:
        _agents_render(rows, selected, page, status_line="smoke render OK")
        return
    while True:
        _agents_render(rows, selected, page, status_line=status)
        status = ""
        try:
            resp = input("  > ").strip()
        except (EOFError, KeyboardInterrupt):
            return
        nav = _sub_page_handle_nav(resp)
        if nav is not None:
            return
        r = resp.lower()
        if r == "r":
            rows = _read_heartbeat_rows()
            selected = {i for i in selected if i < len(rows)}
            status = f"refreshed ({len(rows)} agent(s))"
            continue
        if r == "n":
            total_pages = max(1, (len(rows) + _AGENTS_PAGE_SIZE - 1) // _AGENTS_PAGE_SIZE)
            page = min(page + 1, total_pages - 1)
            continue
        if r == "p":
            page = max(0, page - 1)
            continue
        if r == "a":
            selected = set(range(len(rows)))
            status = f"selected all {len(rows)} agent(s)"
            continue
        if r in ("none", "clear"):
            selected = set()
            status = "selection cleared"
            continue
        # Use "pa" / "pause" to disambiguate from page-prev "p"
        action_map = {
            "k": "KillAll",
            "c": "ImmediateClose",
            "s": "SaveAndClose",
            "pa": "Pause",
        }
        if r == "pause":
            r = "pa"
        if r in action_map:
            sel_slugs = [rows[i]["slug"] for i in sorted(selected) if i < len(rows)]
            if r == "k" and sel_slugs:
                try:
                    confirm = input(f"  {WARN}Force-kill {len(sel_slugs)} agent(s)? "
                                    f"type 'yes' to confirm:{RESET} ").strip().lower()
                except (EOFError, KeyboardInterrupt):
                    confirm = ""
                if confirm != "yes":
                    status = f"{DIM}kill cancelled{RESET}"
                    continue
            status = _agents_apply_action(action_map[r], sel_slugs)
            if r in ("k", "c", "s"):
                rows = _read_heartbeat_rows()
                selected = {i for i in selected if i < len(rows)}
            continue
        if r in ("msg", "m", "message"):
            sel_slugs = [rows[i]["slug"] for i in sorted(selected) if i < len(rows)]
            if not sel_slugs:
                status = f"{WARN}select agents first{RESET}"
                continue
            try:
                msg = input(f"  {WHITE}message text:{RESET} ").strip()
            except (EOFError, KeyboardInterrupt):
                msg = ""
            if not msg:
                status = f"{DIM}message cancelled{RESET}"
                continue
            status = _agents_apply_action("Message", sel_slugs, msg)
            continue
        # Number-list selection (digit-led or 'all'/'*')
        if r and (r[0].isdigit() or r in ("all", "*")):
            selected = _agents_parse_selection(r, selected, len(rows))
            status = f"{len(selected)} selected"
            continue
        status = f"{WARN}unknown: {resp}{RESET}"


# Back-compat shim: the old K-key dispatched a fleet-wide kill via main_menu's
# default. K now opens the Agents page (per-slug actions). Callers that still
# import _kill_fleet from eve.py get the new page transparently.
def _kill_fleet() -> None:  # noqa: D401
    """Legacy K-key alias; opens the Agents page (per-slug actions)."""
    _agents_page()


# ---------------------------------------------------------------------------
# Picker UI (jcode-feel polish)
# ---------------------------------------------------------------------------

def _accounts_compact_line() -> str:
    """Render a one-line accounts-per-server view for the banner.

    RKOJ-ELENO :: 2026-05-24 (operator 19:50Z: "see accounts per server in eve
    exe start"). Pulls _shared-memory/claude-accounts.json and renders each
    slot as `state name[/today]` joined by spaces. Truncates to 96 visible
    chars so the banner doesn't wrap.
    """
    try:
        accts_f = SANCTUM_ROOT_PATH / "_shared-memory" / "claude-accounts.json"
        if not accts_f.exists():
            return ""
        import json as _json
        a = _json.loads(accts_f.read_text(encoding="utf-8-sig", errors="replace"))
        rotation = a.get("rotation_strategy", "?")
        parts = []
        for acct in a.get("accounts", []):
            name = acct.get("name", "?")
            enabled = acct.get("enabled", False)
            # RKOJ-ELENO :: 2026-05-25 :: operator hard-canonical "show when its
            # unlinked things like that". Per-slot tag in the compact banner now
            # surfaces UNLINKED so the operator sees missing credentials at a
            # glance (vs. silently rotating to a slot that will fail on spawn).
            linked = acct.get("linked", True)
            rl = acct.get("rate_limited_until_utc")
            today = acct.get("successful_spawns_today", 0)
            if rl:
                tag = f"{WARN}RL{RESET}"
            elif enabled and not linked:
                tag = f"{WARN}UN{RESET}"  # enabled but no real credentials
            elif enabled:
                tag = f"{OK}ON{RESET}"
            else:
                tag = f"{DIM}off{RESET}"
            spawn_seg = f"{DIM}/{today}{RESET}" if enabled and today else ""
            parts.append(f"{tag} {WHITE}{name}{RESET}{spawn_seg}")
        slots = "  ".join(parts) if parts else f"{DIM}(no slots){RESET}"
        return f"{slots}    {DIM}rotation={rotation}{RESET}"
    except Exception:
        return ""


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
    # RKOJ-ELENO :: 2026-05-25T06:35Z :: show 'relentless' when loop_relentless is set.
    loop_relentless_on = loop_on and prefs_def.get("loop_relentless", True)
    swarm_tag = f"{OK}on{RESET}" if swarm_on else f"{DIM}off{RESET}"
    if loop_relentless_on:
        loop_tag = f"{OK}relentless{RESET}"
    elif loop_on:
        loop_tag = f"{OK}on{RESET}"
    else:
        loop_tag = f"{DIM}off{RESET}"

    # RKOJ-ELENO :: 2026-05-25 :: Item 66. Bump the process-wide animation
    # tick so HSV-shimmered accents drift between renders. The accent line
    # below uses _shimmer_accent for jcode-inspired hue rotation.
    global _EVE_ANIM_TICK
    _EVE_ANIM_TICK += 1
    eve_accent = _shimmer_accent("     E V E     ", _EVE_ANIM_TICK)
    print()
    print(f"  {BOLD}{eve_accent}{RESET}{DIM}// jcode-inspired launcher :: Sinister Sanctum{RESET}")
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
    accounts_line = _accounts_compact_line()
    if accounts_line:
        print(f"  {SOFT}accounts{RESET} {accounts_line}")
    recent = _recent_commit_subject()
    if recent:
        if len(recent) > 64:
            recent = recent[:61] + "..."
        print(f"  {DIM}ship  {RESET}{SOFT}{recent}{RESET}")
    print(f"  {DARKP}{'-' * 68}{RESET}")
    print()


def render_picker(state, selected=None, highlight=None) -> None:
    """ANSI-render the picker rows using fields from PickerState.

    v3 spacing (RKOJ-ELENO :: 2026-05-24): widened to 88 cols, display column
    bumped to 28, tag truncated to 46 with ellipsis, blank divider every 5 rows
    for visual grouping. Picker is the operator's most-used surface — readability
    matters more than terminal economy.

    v4 multi-select-first (RKOJ-ELENO :: 2026-05-25T03:10Z) — operator hard-
    canonical: *"i need a multi select approach to select all i want to start"*.
    The picker is now toggle-first: typing a number toggles inclusion in the
    Selected set; ENTER on empty input launches ALL selected. Selected pane
    renders at TOP for high visibility. `selected` is a set of 1-based indices.

    v5 arrow-key nav (RKOJ-ELENO :: 2026-05-25T03:35Z) — operator hard-canonical:
    *"i want the entire menu to be able to be naviagted with teh arrow keys
    perfectly like perfectly"*. `highlight` is a 1-based row index (or None);
    when set, the matching row gets a `>` cursor pointer. UP/DOWN handled by
    the picker input loop.
    """
    if selected is None:
        selected = set()
    # RKOJ-ELENO :: 2026-05-25 :: Item 61. Operator (image #61) "i want the
    # cenetered menu on each page". Picker body block-centered via
    # _center_block so it visually aligns with the main_menu hero + every
    # sub-page. Dividers stay full-width (graceful overflow when terminal <
    # 88 cols -- max_visible drives the pad to 0).
    print()
    print(f"  {WHITE}{BOLD}Pick projects to start{RESET}")
    print(f"  {DARKP}{'-' * 88}{RESET}")
    body: list[str] = []
    # RKOJ-ELENO :: 2026-05-25T03:10Z :: Selected pane at the TOP -- operator's
    # primary affordance. Multi-select is now visible-by-default, not a hidden
    # Space-key easter egg. Operator: *"start" affordance must be obvious*.
    _idx_to_row = {r.index: r for r in state.rows}
    sel_sorted = sorted(int(i) for i in selected if int(i) in _idx_to_row)
    if sel_sorted:
        names_parts = []
        for i in sel_sorted:
            r = _idx_to_row[i]
            disp = r.display if len(r.display) <= 22 else r.display[:19] + "..."
            names_parts.append(f"{PURPLE}{i}){RESET} {WHITE}{disp}{RESET}")
        # Wrap at ~3 per line so the pane stays scannable on 88 cols.
        chunks = []
        for k in range(0, len(names_parts), 3):
            chunks.append("   ".join(names_parts[k:k + 3]))
        body.append(f"{OK}{BOLD}Selected ({len(sel_sorted)}){RESET}  {SOFT}[ENTER to start all]{RESET}")
        for ln in chunks:
            body.append(f"  {ln}")
    else:
        body.append(f"{SOFT}Selected: {DIM}(none -- type numbers to toggle, "
                    f"{RESET}{PURPLE}A{RESET}{DIM} for all, "
                    f"{RESET}{PURPLE}ENTER{RESET}{DIM} on empty starts default){RESET}")
    body.append(f"{DARKP}{'-' * 84}{RESET}")
    # RKOJ-ELENO 2026-05-24: fleet-default hint line. Loop is ON for the whole fleet;
    # per-session override via --no-loop, fleet-wide via agent-prefs.json defaults.loop_mode.
    prefs_def = _read_prefs_defaults()
    loop_word = f"{OK}ON{RESET}" if prefs_def["loop_mode"] else f"{DIM}OFF{RESET}"
    body.append(f"{DIM}fleet-default loop: {loop_word}{DIM}   override per-session: --no-loop  |  "
                f"toggle this session: press {RESET}{PURPLE}L{RESET}{DIM}  |  "
                f"persist: edit agent-prefs.json defaults.loop_mode{RESET}")
    body.append(f"{DIM}tier:{RESET} {BRIGHTP}T1{RESET}{DIM}=critical(reserves operator slot) {RESET}"
                f"{PURPLE}T2{RESET}{DIM}=high {RESET}"
                f"{SOFT}T3{RESET}{DIM}=normal {RESET}"
                f"{DIM}T4=background   edit: projects.json project.tier field{RESET}")
    body.append("")
    # RKOJ-ELENO :: 2026-05-24 :: tier badge color map (operator 19:55Z importance system).
    # T1 = critical (BRIGHTP), T2 = high (PURPLE), T3 = normal (SOFT), T4 = background (DIM).
    _tier_colors = {1: BRIGHTP, 2: PURPLE, 3: SOFT, 4: DIM}
    for i, r in enumerate(state.rows):
        # RKOJ-ELENO :: 2026-05-25T03:10Z :: per-row selection marker.
        # [x] when selected, [ ] when not. Replaces the legacy `*` default marker
        # for selectable rows; default-key still callable via empty ENTER fallback.
        if r.index in selected:
            select_mark = f"{OK}[x]{RESET}"
        else:
            select_mark = f"{DIM}[ ]{RESET}"
        # v5 arrow-key cursor (RKOJ-ELENO :: 2026-05-25T03:35Z).
        if highlight is not None and r.index == highlight:
            cursor = f"{BRIGHTP}>{RESET}"
        else:
            cursor = " "
        tier_color = _tier_colors.get(getattr(r, "tier", 3), SOFT)
        tier_badge = f"{tier_color}T{getattr(r, 'tier', 3)}{RESET}"
        # Truncate tag (tighter to fit T-badge column).
        tag = r.tag if len(r.tag) <= 42 else r.tag[:39] + "..."
        line = (f"{cursor}{select_mark} {PURPLE}{r.index:2}){RESET} {tier_badge}  "
                f"{WHITE}{r.display:<28}{RESET}  "
                f"{SOFT}{tag:<42}{RESET}")
        if r.customized:
            line += f"  {DIM}[{r.agent_name} / {r.accent}]{RESET}"
        body.append(line)
        # Visual grouping: blank line every 5 rows so the eye can scan.
        if (i + 1) % 5 == 0 and (i + 1) < len(state.rows):
            body.append("")
    # Block-center the assembled body so rows align with the main-menu hero.
    # Width 88 matches the legacy hard-coded layout; _center_block clamps to
    # terminal width on graceful overflow (small terms).
    _print_centered(body, width=88)
    print()
    print(f"  {DARKP}{'-' * 88}{RESET}")
    print()
    # RKOJ-ELENO :: 2026-05-24 :: accounts panel between picker rows and bottom menu
    # (operator 20:10Z "i want to see connected claude accounts and there stats in
    # betweenm project picker and the bottom settings"). Render is bounded to <=6 lines.
    _render_accounts_panel()
    print()
    # RKOJ-ELENO :: 2026-05-25 :: operator hard-canonical "clean up all shit
    # like this. like all this needs to be clean and in theme" (image #8).
    # Replaced ad-hoc `--- Menu ---` style flat divider with the canonical
    # sub-section header treatment (DARKP --- WHITE BOLD title DARKP ---)
    # per eve-ui-uniformity-doctrine-2026-05-24. "Actions" reads cleaner
    # than "Menu" for the picker bottom-zone (multi-select + nav keys).
    print(f"  {DARKP}---{RESET} {WHITE}{BOLD}Actions{RESET} {DARKP}---{RESET}")
    print()
    # RKOJ-ELENO :: 2026-05-25T03:10Z :: Footer rewritten — multi-select front-and-
    # center. Operator hard-canonical: *"i need a multi select approach to select
    # all i want to start"*. Numbers TOGGLE inclusion; ENTER on empty STARTS all
    # selected; A selects all; C clears selection. (Note: `A` was previously the
    # automations menu — that's now reached via T) Tools -> 6) Sanctum Automations.)
    print(f"  {DIM}--- {RESET}{PURPLE}ENTER){RESET} Start selected   "
          f"{PURPLE}A){RESET} Select All   "
          f"{PURPLE}C){RESET} Clear   "
          f"{PURPLE}B){RESET} Back   "
          f"{PURPLE}X){RESET} Exit {DIM}---{RESET}")
    print(f"  {DIM}numbers toggle · range {WHITE}1-3{RESET}{DIM} · list {WHITE}1,3,5{RESET}{DIM}"
          f"   |   swarm/loop/cond/priority prompted after ENTER{RESET}")
    print(f"  {DARKP}{'-' * 88}{RESET}")
    print()


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

# Dispatch timeout: PS1 launcher should hand off to mintty+bash within ~90s
# (forge-memory prefetch 3s + window-position monitor spawn + spawned-windows.jsonl write).
# If it stalls past this, the click is hung — surface to the operator instead of
# locking the UI thread (operator 19:17Z: "eve exe just crashed... I cannot x it out").
DISPATCH_TIMEOUT_SEC = 180


def dispatch_project(key: str) -> int:
    if PS1_LAUNCHER is None or not PS1_LAUNCHER.exists():
        print(f"  {FAIL}[FAIL] PS1 launcher not found{RESET}")
        return 2
    cmd = [
        "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", str(PS1_LAUNCHER),
        "-Project", key,
    ]
    try:
        return subprocess.call(cmd, timeout=DISPATCH_TIMEOUT_SEC)
    except subprocess.TimeoutExpired:
        print(f"  {FAIL}[FAIL] PS1 launcher hung past {DISPATCH_TIMEOUT_SEC}s — abandoning click{RESET}")
        print(f"  {SOFT}(check forge-memory daemon / vault lock / spawned-windows.jsonl){RESET}")
        return 124
    except Exception as e:
        print(f"  {FAIL}[FAIL] dispatch_project({key}) raised: {e}{RESET}")
        return 1


def dispatch_interactive() -> int:
    if PS1_LAUNCHER is None or not PS1_LAUNCHER.exists():
        print(f"  {FAIL}[FAIL] PS1 launcher not found{RESET}")
        return 2
    cmd = [
        "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", str(PS1_LAUNCHER),
    ]
    try:
        return subprocess.call(cmd, timeout=DISPATCH_TIMEOUT_SEC)
    except subprocess.TimeoutExpired:
        print(f"  {FAIL}[FAIL] PS1 launcher hung past {DISPATCH_TIMEOUT_SEC}s — abandoning click{RESET}")
        return 124
    except Exception as e:
        print(f"  {FAIL}[FAIL] dispatch_interactive raised: {e}{RESET}")
        return 1


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
    print(f"{H}EVE.exe {EVE_VERSION}{R}  {SOFT}Sinister Sanctum session launcher (jcode-inspired){R}")
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


# RKOJ-ELENO :: 2026-05-24T23:40Z :: Legacy `_main_menu_loop()` DELETED.
# Operator screenshot #50 confirmed the legacy menu (Sinister Sanctum EVE :: MCP
# header + R/G/T/O/N/X numbered list + "pick a letter:" prompt) was still rendering
# despite a prior claim of removal. The function (formerly here, 108 lines) had no
# remaining callers in the live code path but a stale built EVE.exe was still
# shipping the old wiring. Function fully removed so it can never be re-invoked.
# Canonical entry surface is now ONLY main_menu.show_main_menu() in
# tools/eve-picker/main_menu.py (EVE block letters + hero + animation + accounts
# panel + R/A/G/T/N/M/K/X menu). Companion: also deleted play_banner() pumpkin
# call at line ~2248 and removed _LOGO_LINES + play_banner() definition.


def Get_MCPCount() -> int:
    """Lightweight wrapper around the existing helper (case-normalize for menu use)."""
    try:
        return get_mcp_count() if 'get_mcp_count' in globals() else 0
    except Exception:
        return 0


def Get_BotCount() -> int:
    try:
        return get_bot_count() if 'get_bot_count' in globals() else 0
    except Exception:
        return 0


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

    # RKOJ-ELENO :: 2026-05-24 :: first-run gate. Operator 21:24Z "make sure the first
    # time eve runs on a pc it auto sets it self up and has a general agent that it
    # spawns that can aid in setup". Detect + divert to wizard before showing picker.
    # Suppressed by --skip-first-run flag or SINISTER_SKIP_FIRST_RUN=1 env.
    # RKOJ-ELENO :: 2026-05-25 :: --force-setup-wizard flag (operator hard-canonical
    # 2026-05-25 ~00:35Z Leo auto-setup directive). Forces wizard to re-run even if
    # marker present; useful for re-running setup on an already-set-up machine OR for
    # testing the flow.
    skip_first_run = (
        any(a.lower() in ("--skip-first-run", "/skip-first-run") for a in argv)
        or os.environ.get("SINISTER_SKIP_FIRST_RUN", "") == "1"
    )
    force_setup_wizard = any(
        a.lower() in ("--force-setup-wizard", "/force-setup-wizard", "-force-setup-wizard")
        for a in argv
    )
    if force_setup_wizard and SANCTUM_ROOT_PATH is not None:
        _maybe_run_first_run_wizard(force=True)
        return 0
    if not skip_first_run and SANCTUM_ROOT_PATH is not None:
        _maybe_run_first_run_wizard()

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

    # Prereq flow (skip shell warn under --quiet)
    # RKOJ-ELENO :: 2026-05-24T23:40Z :: operator screenshot #50 — pumpkin glyph
    # (play_banner / _LOGO_LINES) was rendering ABOVE main_menu.show_main_menu().
    # Operator wants ONLY the new clean main_menu.py output (EVE block letters,
    # hero, animation, accounts panel). Legacy pumpkin banner DELETED entirely.
    enable_vt_on_windows()
    _quiet = os.environ.get("EVE_QUIET", "").strip() == "1"
    run_autonomy_bootstrap(force=False)
    fire_plugin_check_background()
    spawn_shell_preflight(verbose=False)

    # RKOJ-ELENO :: 2026-05-24T23:35Z :: operator screenshot #47 — two menus
    # stacked: the OLD `_main_menu_loop()` rendered FIRST (header text
    # "[R]esume [G]eneral [T]ools [O]nboard [N]ew [X]it"), then the NEW
    # `main_menu.show_main_menu()` rendered SECOND. Root cause: BOTH menus
    # were being called sequentially. Removed the legacy `_main_menu_loop()`
    # call entirely; `main_menu.show_main_menu()` is now the canonical entry
    # and is wired with full callbacks below so all actions dispatch from
    # the new menu (no fall-through to legacy code).
    #
    # SINISTER_SKIP_MAIN_MENU=1 still bypasses to legacy direct-to-picker.

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

    # RKOJ-ELENO :: 2026-05-24T23:35Z :: operator screenshot #47 fix —
    # The legacy project picker loop is now wrapped in a nested helper so
    # the new main_menu.show_main_menu() can invoke it via the R callback
    # WITHOUT the previous fall-through behavior that rendered both menus.
    # Returns the picker's exit code (0 on normal exit / Ctrl-C / X).

    # Fuzzy filter state (jcode session_picker/filter.rs parity)
    # RKOJ-ELENO :: 2026-05-25T03:10Z :: added "selected" set (1-based row indices)
    # for the multi-select-first picker. Persists across renders within a single
    # picker session; reset whenever build_picker_state rebuilds rows.
    _picker_state = {"filter_query": "", "full_rows": list(state.rows),
                     "state": state, "rc": 0, "selected": set(),
                     # v5 arrow-key nav: 1-based highlight (0 = no cursor yet).
                     # RKOJ-ELENO :: 2026-05-25T03:35Z.
                     "highlight": 0}

    def _run_project_picker() -> int:
        # Bind from outer closure
        nonlocal state
        _filter_query = _picker_state["filter_query"]
        _full_rows = _picker_state["full_rows"]
        _selected: set = _picker_state["selected"]
        _highlight: int = _picker_state["highlight"]
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
            # Drop selections that no longer reference a valid row index (e.g.
            # after a fuzzy filter narrows the list). Keeps the Selected pane
            # consistent with what's actually on screen.
            _valid_idx = {r.index for r in state.rows}
            stale = _selected - _valid_idx
            if stale:
                _selected -= stale
            # Clamp highlight to current visible row range (1-based).
            _max_n = len(state.rows)
            if _max_n == 0:
                _highlight = 0
            elif _highlight < 1 or _highlight > _max_n:
                _highlight = 1
            render_picker(state, selected=_selected,
                          highlight=_highlight if _max_n > 0 else None)
            try:
                raw = _arrow_input(
                    f"  {WHITE}Toggle # or ENTER to start ({len(_selected)} selected) "
                    f"{DIM}[arrows nav · A/C/B/X/T/H/L/Q/U/M/O/G/N/R/K/S/F/ /q]{RESET} "
                    f"{PURPLE}>{RESET} "
                )
                raw = (raw or "").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                _log_session_end("interrupt")
                return 0

            # v5 arrow-key nav (RKOJ-ELENO :: 2026-05-25T03:35Z).
            if raw == _ARROW_UP:
                if _max_n > 0:
                    _highlight = _max_n if _highlight <= 1 else _highlight - 1
                    _picker_state["highlight"] = _highlight
                continue
            if raw == _ARROW_DOWN:
                if _max_n > 0:
                    _highlight = 1 if _highlight >= _max_n else _highlight + 1
                    _picker_state["highlight"] = _highlight
                continue
            if raw in (_ARROW_LEFT, _ARROW_RIGHT):
                # Reserved for future page-tab nav; currently no-op (rerender).
                continue
            if raw == _KEY_ESC:
                # ESC alone -> exit picker cleanly (treat like X).
                print(f"  {SOFT}bye.{RESET}")
                _log_session_end("normal_exit")
                return 0
            # SPACE on highlighted row -> toggle that row's inclusion in selection.
            # (vim-feel for arrow nav users: arrows move, space toggles, enter starts.)
            if raw == "" and _max_n > 0 and _highlight >= 1 and _highlight <= _max_n and _selected:
                # Empty Enter with active selection -> existing "launch selected" flow handles below.
                pass

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

            # Q (queue) :: canonical sub-page (RKOJ-ELENO 2026-05-24T22:40Z)
            # Operator directive 2026-05-24: Q is Queue. X is the new exit key.
            if raw.lower() in ("q", "queue", "qq"):
                _view_queue()
                state = lib.build_picker_state(boot_ms=state.boot_ms)
                continue

            # U (utterances) :: canonical sub-page (RKOJ-ELENO 2026-05-24T22:40Z)
            if raw.lower() in ("u", "utterances"):
                _view_utterances()
                state = lib.build_picker_state(boot_ms=state.boot_ms)
                continue

            # M (mesh) :: fleet network at-a-glance (RKOJ-ELENO 2026-05-24 v0.4.4)
            if raw.lower() in ("m", "mesh", "fleet"):
                _view_mesh_status()
                state = lib.build_picker_state(boot_ms=state.boot_ms)
                continue

            # A (select all) :: multi-select-first picker (RKOJ-ELENO :: 2026-05-25T03:10Z).
            # Operator hard-canonical 2026-05-25 ~03:10Z: *"i need a multi select approach
            # to select all i want to start"*. `A` now selects every row in the visible list.
            # The legacy automations menu is still reachable via the long-form `automations`
            # or `auto` keyword, AND via T) Tools -> 6) Sanctum Automations (canonical path
            # since the 2026-05-25T00:30Z tools-page reorg).
            if raw.lower() == "a":
                _selected.update(r.index for r in state.rows)
                _picker_state["selected"] = _selected
                continue

            # C (clear selection) :: multi-select-first picker (RKOJ-ELENO :: 2026-05-25T03:10Z).
            # Empties the Selected set without touching anything else.
            if raw.lower() == "c":
                _selected.clear()
                _picker_state["selected"] = _selected
                continue

            # Long-form `automations` / `auto` keyword still works for muscle-memory.
            if raw.lower() in ("automations", "auto"):
                _sanctum_automations_menu()
                state = lib.build_picker_state(boot_ms=state.boot_ms)
                continue

            # O (onboarding) :: round-robin account onboarding walkthrough
            # Operator hard-canonical 2026-05-24 20:00Z verbatim:
            #   "i need this ROUND-ROBIN-ACCOUNT-ONBOARDING.md to be a button in eve exe
            #    that i hit to go through the flow of adding accounts ..."
            # RKOJ-ELENO :: 2026-05-24.
            if raw.lower() in ("o", "onboard", "onboarding"):
                _account_onboarding_flow()
                state = lib.build_picker_state(boot_ms=state.boot_ms)
                continue

            # RKOJ-ELENO :: 2026-05-25T03:10Z :: Multi-select-first dispatch.
            # Operator hard-canonical 2026-05-25 ~03:10Z: *"i need a multi select
            # approach to select all i want to start"*. Numbers TOGGLE inclusion;
            # ENTER on empty starts ALL selected (or default if selection empty).
            _max_n = len(state.rows)
            _raw_lower = raw.lower()

            # (1) Empty input -> launch selected, else legacy default.
            if not raw:
                if _selected:
                    # Build keys by walking state.rows directly (1-based index -> key).
                    _by_idx = {r.index: r.key for r in state.rows}
                    _keys = [_by_idx[i] for i in sorted(_selected) if i in _by_idx]
                    if eve_logger is not None:
                        try: eve_logger.info("project_dispatch", verb="multi_selected", keys=",".join(_keys))
                        except Exception: pass
                    try:
                        if len(_keys) == 1:
                            dispatch_project(_keys[0])
                        else:
                            dispatch_multi(_keys)
                    except Exception as e:
                        print(f"  {FAIL}[FAIL] dispatch crashed: {e}{RESET}")
                        time.sleep(2)
                    # Clear selection after a launch so the next pass starts fresh.
                    _selected.clear()
                    _picker_state["selected"] = _selected
                    state = lib.build_picker_state(boot_ms=state.boot_ms)
                    _full_rows = list(state.rows)
                    _filter_query = ""
                    continue
                # Empty + no selection -> legacy default behavior (dispatch default_key)
                if eve_logger is not None:
                    try: eve_logger.info("project_dispatch", verb="default", key=state.default_key)
                    except Exception: pass
                try:
                    dispatch_project(state.default_key)
                except Exception as e:
                    print(f"  {FAIL}[FAIL] dispatch_project crashed: {e}{RESET}")
                    time.sleep(2)
                state = lib.build_picker_state(boot_ms=state.boot_ms)
                _full_rows = list(state.rows)
                _filter_query = ""
                continue

            # (2) Single number -> TOGGLE inclusion in selection.
            if _raw_lower.isdigit():
                _idx = int(_raw_lower)
                if 1 <= _idx <= _max_n:
                    if _idx in _selected:
                        _selected.remove(_idx)
                    else:
                        _selected.add(_idx)
                    _picker_state["selected"] = _selected
                    continue
                # Out of range -> fall through to resolve_pick which prints unknown
                print(f"  {WARN}out of range: {_raw_lower} (1-{_max_n}){RESET}")
                time.sleep(0.8)
                continue

            # (3) Range / comma list -> ADD to selection (do not dispatch immediately).
            _multi_idx = lib.parse_multi(_raw_lower, _max_n)
            if _multi_idx:
                for _i in _multi_idx:
                    _selected.add(_i)
                _picker_state["selected"] = _selected
                continue

            result = lib.resolve_pick(raw, state)

            if result.verb == "quit":
                print(f"  {SOFT}bye.{RESET}")
                _log_session_end("normal_exit")
                return 0
            elif result.verb == "multi":
                # Legacy multi-dispatch path. Unreachable in v4 since (3) above
                # intercepts range/list input — kept for defensive completeness in
                # case parse_multi semantics ever diverge from resolve_pick.
                if eve_logger is not None:
                    try: eve_logger.info("project_dispatch", verb="multi", keys=",".join(result.keys))
                    except Exception: pass
                try:
                    dispatch_multi(result.keys)
                except Exception as e:
                    print(f"  {FAIL}[FAIL] dispatch_multi crashed: {e}{RESET}")
                    time.sleep(2)
            elif result.verb in ("numeric", "default"):
                # Legacy numeric/default — unreachable in v4 (intercepted above).
                if eve_logger is not None:
                    try: eve_logger.info("project_dispatch", verb=result.verb, key=result.keys[0])
                    except Exception: pass
                try:
                    dispatch_project(result.keys[0])
                except Exception as e:
                    print(f"  {FAIL}[FAIL] dispatch_project crashed: {e}{RESET}")
                    time.sleep(2)
            elif result.verb == "general":
                if eve_logger is not None:
                    try: eve_logger.info("project_dispatch", verb="general")
                    except Exception: pass
                try:
                    dispatch_project("general")
                except Exception as e:
                    print(f"  {FAIL}[FAIL] dispatch_project(general) crashed: {e}{RESET}")
                    time.sleep(2)
            elif result.verb in ("auto-resume", "new", "rename", "clear", "autonomy", "full"):
                _log_session_end("interactive_handoff", verb=result.verb)
                try:
                    return dispatch_interactive()
                except Exception as e:
                    print(f"  {FAIL}[FAIL] dispatch_interactive crashed: {e}{RESET}")
                    time.sleep(2)
                    continue
            else:
                print(f"  {WARN}unknown selection: {raw}{RESET}")
                time.sleep(1)
                continue

            # Refresh state so prefs changes via R) show on next iteration
            state = lib.build_picker_state(boot_ms=state.boot_ms)
            _full_rows = list(state.rows)
            _filter_query = ""
            # RKOJ-ELENO :: 2026-05-25T00:00Z :: per spec "each project pick
            # triggers an explicit probe refresh (no stale data on the next-spawn
            # screen)". Force the live usage probe to re-fetch so the bars on
            # the next render reflect post-spawn quota burn.
            if SANCTUM_ROOT_PATH is not None:
                _probe = SANCTUM_ROOT_PATH / "automations" / "anthropic-usage-probe.ps1"
                if _probe.exists():
                    try:
                        import subprocess as _subprocess
                        _subprocess.run(
                            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                             "-File", str(_probe), "-Mode", "Text",
                             "-Slot", "default", "-Force"],
                            capture_output=True, text=True, timeout=15,
                        )
                    except Exception:
                        pass
            try:
                ans = input(f"  {DIM}> press Enter for picker, X to exit:{RESET} ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print()
                _log_session_end("interrupt")
                return 0
            if ans in ("x", "quit", "exit"):
                _log_session_end("normal_exit")
                return 0

    # RKOJ-ELENO :: 2026-05-24T23:35Z :: Canonical entry to main_menu.
    # All actions wired through callbacks. R -> _run_project_picker (the
    # legacy picker, refactored above). X / sys.exit happens inside
    # show_main_menu so we exit cleanly without rendering anything else.
    # SINISTER_SKIP_MAIN_MENU=1 bypasses straight into the picker.
    if os.environ.get("SINISTER_SKIP_MAIN_MENU", "") == "1":
        rc = _run_project_picker()
        return rc

    try:
        from main_menu import show_main_menu  # type: ignore
    except ImportError as _e:
        print(f"  {WARN}[main-menu] import failed ({_e}); falling back to picker{RESET}")
        return _run_project_picker()

    def _cb_resume() -> None:
        _run_project_picker()
        # After picker returns (user backed out), control returns to
        # show_main_menu which re-renders. No fall-through to legacy code.

    def _cb_auto_resume() -> None:
        try:
            dispatch_interactive()
        except Exception as e:
            print(f"  {FAIL}[A] auto-resume failed: {e}{RESET}")
            time.sleep(1.2)

    def _cb_general() -> None:
        try:
            dispatch_project("general")
        except Exception as e:
            print(f"  {FAIL}[G] general dispatch failed: {e}{RESET}")
            time.sleep(1.2)

    def _cb_tools() -> None:
        # RKOJ-ELENO :: 2026-05-25T00:30Z :: operator screenshot #58 -- the
        # picker-bottom letter row is gone; its actions now live under T) Tools
        # on the main menu, which lands on a dedicated themed sub-page that
        # routes to Health / Mesh / Quantum / Queue / Utterances / Sanctum
        # Automations. tools_menu.show_tools_menu() handles render + dispatch;
        # each sub-page clears screen + paints its own canonical header/footer.
        def _cb_health() -> None:
            if health_tools is None:
                print(f"  {WARN}health_tools module not importable.{RESET}")
                time.sleep(1.0)
                return
            try:
                health_tools.menu_loop()
            except Exception as e:
                print(f"  {FAIL}[Health] failed: {e}{RESET}")
                time.sleep(1.2)

        def _cb_quantum() -> None:
            if quantum_tools is None:
                print(f"  {WARN}quantum_tools module not importable.{RESET}")
                time.sleep(1.0)
                return
            try:
                quantum_tools.menu_loop()
            except Exception as e:
                print(f"  {FAIL}[Quantum] failed: {e}{RESET}")
                time.sleep(1.2)

        try:
            from tools_menu import show_tools_menu  # type: ignore
            show_tools_menu(callbacks={
                "health": _cb_health,
                "mesh": _view_mesh_status,
                "quantum": _cb_quantum,
                "queue": _view_queue,
                "utterances": _view_utterances,
                "automations": _sanctum_automations_menu,
            })
        except Exception as e:
            print(f"  {FAIL}[T] tools menu failed: {e}{RESET}")
            time.sleep(1.2)

    def _cb_new() -> None:
        try:
            dispatch_interactive()
        except Exception as e:
            print(f"  {FAIL}[N] new-project flow failed: {e}{RESET}")
            time.sleep(1.2)

    def _cb_accounts() -> None:
        try:
            _account_onboarding_flow()
        except Exception as e:
            print(f"  {FAIL}[M] accounts page failed: {e}{RESET}")
            time.sleep(1.2)

    def _cb_agents() -> None:
        # K-key: Agents page (replaces legacy fleet-kill). Operator 2026-05-25.
        try:
            _agents_page()
        except Exception as e:
            print(f"  {FAIL}[K] agents page failed: {e}{RESET}")
            time.sleep(1.2)

    def _cb_sinister_link() -> None:
        # L-key: Sinister LINK sub-page (cross-machine pairing). Operator
        # hard-canonical 2026-05-25 ~00:50Z.
        try:
            _sinister_link_page()
        except Exception as e:
            print(f"  {FAIL}[L] sinister-link page failed: {e}{RESET}")
            time.sleep(1.2)

    show_main_menu(callbacks={
        "resume": _cb_resume,
        "auto_resume": _cb_auto_resume,
        "general": _cb_general,
        "tools": _cb_tools,
        "new_project": _cb_new,
        "account_mgr": _cb_accounts,
        "agents": _cb_agents,
        "sinister_link": _cb_sinister_link,
        # back-compat key name for older main_menu builds
        "kill_fleet": _cb_agents,
    })
    # show_main_menu only returns on X via sys.exit(0); never reached.
    return 0


if __name__ == "__main__":
    sys.exit(main())
