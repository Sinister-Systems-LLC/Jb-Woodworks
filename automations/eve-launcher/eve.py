"""EVE :: Sinister Sanctum session launcher (thin fast picker)

Author: RKOJ-ELENO :: 2026-05-23

Goal: jcode-speed boot (target <300 ms cold-start) for the common case
(operator wants to spawn a project agent). Stdlib only. PyInstaller --onefile
yields a ~15-20 MB EVE.exe.

Architecture (P2 of eve-into-rkoj-integration-2026-05-23T1330Z):

    eve_picker_lib (D:\\Sinister Sanctum\\tools\\eve-picker\\)
        - render-agnostic picker logic
        - read_projects / read_prefs / visible_projects
        - build_picker_state / resolve_pick / parse_multi
        - banner_text / picker_text_rows  (plain text rows)

This file (eve.py) is the EVE.exe surface:
    - ANSI 256-color wrappers around the lib's text rows
    - subprocess.call(PS1) dispatch for spawn (numeric / G / multi)
    - subprocess.call(PS1 interactive) for A / N / R / K / S sub-flows

Profile mode: `EVE.exe --profile` prints `boot=<N>ms` and exits 0.
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path


def _setup_lib_path() -> None:
    """Add tools/eve-picker to sys.path before importing eve_picker_lib.

    When running from source: D:\\Sinister Sanctum\\tools\\eve-picker is added.
    When running from a PyInstaller --onefile bundle: the lib is already bundled
    via `--paths` so this is a no-op (but cheap).
    """
    here = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
    candidates = [
        Path(os.environ.get("SINISTER_SANCTUM_ROOT", r"D:\Sinister Sanctum")) / "tools" / "eve-picker",
        here.parent.parent / "tools" / "eve-picker",
    ]
    for cand in candidates:
        if cand.exists() and str(cand) not in sys.path:
            sys.path.insert(0, str(cand))


_setup_lib_path()
import eve_picker_lib as lib  # noqa: E402


SANCTUM_ROOT = lib.SANCTUM_ROOT
PS1_LAUNCHER = SANCTUM_ROOT / "automations" / "start-sinister-session.ps1"

# ANSI 256-color escapes (purple-everything)
PURPLE = "\033[38;5;141m"
DARKP = "\033[38;5;91m"
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


def banner(state: lib.PickerState) -> None:
    """ANSI-render the picker banner using fields from PickerState."""
    now = time.strftime("%Y-%m-%d %H:%M")
    print()
    print(f'  {PURPLE}{BOLD}     E V E     {RESET}{DIM}// jcode-speed launcher{RESET}')
    print(f'  {DARKP}{"-" * 60}{RESET}')
    print(f'  {SOFT}server{RESET} Sanctum    {SOFT}client{RESET} EVE    {DIM}{now}{RESET}')
    print(f'  {SOFT}model{RESET}  claude-opus-4-7[1m]   {SOFT}speed{RESET} turbo   {SOFT}token{RESET} compact')
    print(f'  {SOFT}boot{RESET}   {OK}{state.boot_ms} ms{RESET}   '
          f'{PILL_G} mcp:{state.mcp} {PILL_Z}  {PILL_B} bots:{state.bots} {PILL_Z}  '
          f'{PILL_R} --skip-perms {PILL_Z}')
    print(f'  {DARKP}{"-" * 60}{RESET}')
    print()


def render_picker(state: lib.PickerState) -> None:
    """ANSI-render the picker rows using fields from PickerState."""
    print(f'  {WHITE}Pick a project{RESET}')
    print(f'  {DARKP}{"-" * 60}{RESET}')
    for r in state.rows:
        marker = "*" if r.is_default else " "
        line = (f'  {PURPLE}{marker} {r.index:2}){RESET} '
                f'{WHITE}{r.display:<20}{RESET} '
                f'{SOFT}{r.tag:<36}{RESET}')
        if r.customized:
            line += f' {DIM}[{r.agent_name} / {r.accent}]{RESET}'
        print(line)
    print()
    print(f'  {DARKP}{"-" * 60}{RESET}')
    print(f'  {PURPLE}G){RESET} General      '
          f'{PURPLE}A){RESET} Auto-Resume  '
          f'{PURPLE}N){RESET} New Project  '
          f'{PURPLE}R){RESET} Rename + Color')
    print(f'  {PURPLE}K){RESET} Clear ctx    '
          f'{PURPLE}S){RESET} Autonomy     '
          f'{PURPLE}F){RESET} Full picker  '
          f'{PURPLE}Q){RESET} Quit')
    print(f'  {DIM}    multi-select: 1,3,5 or 1-3{RESET}')
    print(f'  {DARKP}{"-" * 60}{RESET}')


def dispatch_project(key: str) -> int:
    """Spawn the PS1 in headless project-mode (skips the PS1 picker)."""
    if not PS1_LAUNCHER.exists():
        print(f'{FAIL}  [FAIL] PS1 launcher not found at {PS1_LAUNCHER}{RESET}')
        return 2
    cmd = [
        "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", str(PS1_LAUNCHER),
        "-Project", key,
    ]
    return subprocess.call(cmd)


def dispatch_interactive() -> int:
    """Hand off to the full PS1 picker for A/N/R/K/S sub-flows."""
    if not PS1_LAUNCHER.exists():
        print(f'{FAIL}  [FAIL] PS1 launcher not found at {PS1_LAUNCHER}{RESET}')
        return 2
    cmd = [
        "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", str(PS1_LAUNCHER),
    ]
    return subprocess.call(cmd)


def dispatch_multi(keys: list[str]) -> int:
    """Spawn multiple projects sequentially (400ms stagger)."""
    rc = 0
    for k in keys:
        print(f'  {SOFT}[multi] spawning {WHITE}{k}{RESET}')
        rc = dispatch_project(k) or rc
        time.sleep(0.4)
    return rc


def _profile_and_exit() -> int:
    """`EVE.exe --profile`: measure boot, print one machine-parsable line, exit 0.

    Captures lib import + projects.json read + prefs read + state assembly +
    count_mcp/bots. This is the L7 acceptance gate (target <300 ms cold-start).

    The lib's import time is captured by the harness (process start -> now);
    file I/O happens inside build_picker_state.
    """
    t0 = time.monotonic()
    state = lib.build_picker_state(boot_ms=0)
    boot_ms = int((time.monotonic() - t0) * 1000)
    print(f"boot={boot_ms}ms rows={len(state.rows)} mcp={state.mcp} bots={state.bots}")
    return 0


EVE_VERSION = "0.3.0"  # /loop iter 25 :: ported --version + --help on top of P2 lift-shift refactor


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    # Probe-style flags: handle BEFORE any heavy work so Sinister Start.bat
    # can sanity-check EVE.exe without spawning the picker UI (which blocks
    # on input()). /loop iter 25 merge: kept --version + --help from main
    # branch's v0.2.0, kept --profile from P2 refactor.
    if argv:
        arg0 = argv[0].lower()
        if arg0 in ("--version", "-v", "/version"):
            print(f"EVE.exe {EVE_VERSION} :: Sinister Sanctum session launcher")
            return 0
        if arg0 in ("--help", "-h", "/help", "/?"):
            print(f"EVE.exe {EVE_VERSION} - Sinister Sanctum session launcher (jcode-speed picker)")
            print("Usage: EVE.exe [--version | --help | --profile]")
            print("  --version  Print version + exit 0 (probe-friendly; no picker).")
            print("  --help     Print this help + exit 0.")
            print("  --profile  Print 'boot=<N>ms rows=N mcp=N bots=N' + exit 0 (L7 gate).")
            print("  (no args)  Open interactive picker (1-N / G / A / N / R / K / S / F / Q + multi).")
            print("  Sub-flows (A/N/R/K/S) hand off to start-sinister-session.ps1.")
            return 0
    if "--profile" in argv:
        return _profile_and_exit()

    t0 = time.monotonic()
    enable_vt_on_windows()
    state = lib.build_picker_state(boot_ms=0)
    state.boot_ms = int((time.monotonic() - t0) * 1000)

    while True:
        banner(state)
        render_picker(state)
        try:
            raw = input(
                f'  {WHITE}Selection [1-{len(state.rows)} / G / A / N / R / K / S / F / Q, '
                f'default={state.default_key}] {PURPLE}>{RESET} '
            ).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0

        result = lib.resolve_pick(raw, state)

        if result.verb == "quit":
            print(f'  {SOFT}bye.{RESET}')
            return 0
        elif result.verb == "multi":
            dispatch_multi(result.keys)
        elif result.verb in ("numeric", "default"):
            dispatch_project(result.keys[0])
        elif result.verb == "general":
            dispatch_project("general")
        elif result.verb in ("auto-resume", "new", "rename", "clear", "autonomy", "full"):
            # All these sub-flows live in the full PS1 picker
            return dispatch_interactive()
        else:
            print(f'  {WARN}  unknown selection: {raw}{RESET}')
            time.sleep(1)
            continue

        # Refresh state so prefs changes via R) show on next iteration
        state = lib.build_picker_state(boot_ms=state.boot_ms)
        try:
            ans = input(f'  {DIM}> press Enter for picker, Q to quit:{RESET} ').strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if ans in ("q", "quit", "exit"):
            return 0


if __name__ == "__main__":
    sys.exit(main())
