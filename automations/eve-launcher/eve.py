"""EVE :: Sinister Sanctum session launcher (thin fast picker)

Author: RKOJ-ELENO :: 2026-05-23

Goal: jcode-speed boot (target <300 ms cold-start) for the common case
(operator wants to spawn a project agent). Stdlib only. PyInstaller --onefile
yields a ~15-20 MB EVE.exe; cold-start ~150-300 ms vs PowerShell launcher's
~800-1200 ms (PS1 has to initialize the host + parse 50+ KB of script every
spawn).

How it composes with the existing launcher:

  - For NUMERIC project picks (1-11) and G (General): EVE.exe shows the
    picker in Python (fast), then dispatches to
    `start-sinister-session.ps1 -Project <key>` in headless mode. The PS1
    still owns: trust-pre-acceptance, mintty spawn, status pills, sterm
    handoff, resume-point auto-write. EVE.exe is JUST the picker UI.
  - For A / N / R / K / S (the interactive sub-flows): EVE.exe falls
    through to invoking the full PS1 picker. Those sub-flows have their
    own multi-prompt UX which is faster to maintain in PS1.
  - Q: clean exit, no PS1 invocation.

Speed wins:
  - No PowerShell host bootstrap (~600 ms).
  - No 50 KB script parse per spawn.
  - Stdlib-only -> no module import cascade.
  - Banner art is small inline ASCII -> no file read for the common path.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

SANCTUM_ROOT = Path(os.environ.get('SINISTER_SANCTUM_ROOT', r'D:\Sinister Sanctum'))
PROJECTS_JSON = SANCTUM_ROOT / 'automations' / 'session-templates' / 'projects.json'
PREFS_JSON = SANCTUM_ROOT / 'automations' / 'session-templates' / 'agent-prefs.json'
PS1_LAUNCHER = SANCTUM_ROOT / 'automations' / 'start-sinister-session.ps1'

# ANSI 256-color escapes (purple-everything)
PURPLE = '\033[38;5;141m'   # light purple
DARKP = '\033[38;5;91m'     # darker purple
WHITE = '\033[97m'
SOFT = '\033[38;5;245m'     # gray
DIM = '\033[38;5;240m'      # dim gray
OK = '\033[38;5;46m'        # green
WARN = '\033[38;5;220m'     # yellow
FAIL = '\033[38;5;196m'     # red
RESET = '\033[0m'
BOLD = '\033[1m'

# 256-color pill backgrounds
PILL_A = '\033[48;5;91;38;5;15;1m'   # purple
PILL_M = '\033[48;5;30;38;5;15;1m'   # teal
PILL_D = '\033[48;5;94;38;5;15;1m'   # orange
PILL_G = '\033[48;5;22;38;5;15;1m'   # green
PILL_B = '\033[48;5;19;38;5;15;1m'   # blue
PILL_R = '\033[48;5;52;38;5;15;1m'   # red
PILL_Z = '\033[0m'


def enable_vt_on_windows() -> None:
    """Enable ANSI escape interpretation in the Windows console."""
    if os.name != 'nt':
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


def read_projects() -> dict:
    try:
        # utf-8-sig handles both BOM and non-BOM transparently
        return json.loads(PROJECTS_JSON.read_text(encoding='utf-8-sig'))
    except Exception as exc:
        print(f'{FAIL}  [FAIL] could not read projects.json: {exc}{RESET}')
        sys.exit(2)


def read_prefs() -> dict | None:
    if not PREFS_JSON.exists():
        return None
    try:
        return json.loads(PREFS_JSON.read_text(encoding='utf-8-sig'))
    except Exception:
        return None


def visible_projects(projects_json: dict) -> list[dict]:
    by_key = {p['key']: p for p in projects_json.get('projects', [])}
    visible_keys = (projects_json.get('picker') or {}).get('visible_keys') or list(by_key)
    return [by_key[k] for k in visible_keys if k in by_key]


def get_agent_name(key: str, prefs: dict | None) -> str:
    if prefs and (entry := (prefs.get('per_project') or {}).get(key)):
        return entry.get('agent_name') or key
    return key


def get_accent(key: str, prefs: dict | None) -> str:
    if prefs and (entry := (prefs.get('per_project') or {}).get(key)):
        return entry.get('accent_color') or 'purple'
    return 'purple'


def count_mcp() -> int:
    for cand in (Path.home() / '.claude' / '.mcp.json', Path.home() / '.claude.json'):
        if not cand.exists():
            continue
        try:
            data = json.loads(cand.read_text(encoding='utf-8'))
            n = len(data.get('mcpServers') or {})
            if n:
                return n
        except Exception:
            continue
    return 0


def count_bots() -> int:
    bot_dir = Path(r'D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\agents')
    if not bot_dir.exists():
        return 0
    return sum(1 for _ in bot_dir.iterdir() if _.is_dir())


def banner(boot_ms: int, mcp: int, bots: int) -> None:
    print()
    print(f'  {PURPLE}{BOLD}     E V E     {RESET}{DIM}// jcode-speed launcher{RESET}')
    print(f'  {DARKP}{"-" * 60}{RESET}')
    now = time.strftime('%Y-%m-%d %H:%M')
    print(f'  {SOFT}server{RESET} Sanctum    {SOFT}client{RESET} EVE    {DIM}{now}{RESET}')
    print(f'  {SOFT}model{RESET}  claude-opus-4-7[1m]   {SOFT}speed{RESET} turbo   {SOFT}token{RESET} compact')
    print(f'  {SOFT}boot{RESET}   {OK}{boot_ms} ms{RESET}   '
          f'{PILL_G} mcp:{mcp} {PILL_Z}  {PILL_B} bots:{bots} {PILL_Z}  '
          f'{PILL_R} --skip-perms {PILL_Z}')
    print(f'  {DARKP}{"-" * 60}{RESET}')
    print()


def render_picker(rows: list[dict], default_key: str, prefs: dict | None) -> None:
    print(f'  {WHITE}Pick a project{RESET}')
    print(f'  {DARKP}{"-" * 60}{RESET}')
    for i, p in enumerate(rows, 1):
        marker = '*' if p['key'] == default_key else ' '
        agent = get_agent_name(p['key'], prefs)
        accent = get_accent(p['key'], prefs)
        customized = (agent != p['key']) or (accent != 'purple')
        tag = (p.get('tag') or '')[:34]
        line = f'  {PURPLE}{marker} {i:2}){RESET} {WHITE}{p["display"]:<20}{RESET} {SOFT}{tag:<36}{RESET}'
        if customized:
            line += f' {DIM}[{agent} / {accent}]{RESET}'
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
        'powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass',
        '-File', str(PS1_LAUNCHER),
        '-Project', key,
    ]
    return subprocess.call(cmd)


def dispatch_interactive() -> int:
    """Hand off to the full PS1 picker for A/N/R/K/S sub-flows."""
    if not PS1_LAUNCHER.exists():
        print(f'{FAIL}  [FAIL] PS1 launcher not found at {PS1_LAUNCHER}{RESET}')
        return 2
    cmd = [
        'powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass',
        '-File', str(PS1_LAUNCHER),
    ]
    return subprocess.call(cmd)


def dispatch_multi(keys: list[str]) -> int:
    """Spawn multiple projects sequentially (mirrors PS1 multi-project arm)."""
    rc = 0
    for k in keys:
        print(f'  {SOFT}[multi] spawning {WHITE}{k}{RESET}')
        rc = dispatch_project(k) or rc
        time.sleep(0.4)
    return rc


def parse_multi(pick: str, max_n: int) -> list[int]:
    """Parse '1,3,5' or '1-3' or '1,3-5,7' -> sorted unique 1-based indices."""
    pick = pick.strip()
    if ',' not in pick and '-' not in pick:
        return []
    out: set[int] = set()
    for part in pick.split(','):
        part = part.strip()
        if not part:
            continue
        if '-' in part:
            try:
                a, b = (int(x.strip()) for x in part.split('-', 1))
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


def main() -> int:
    t0 = time.monotonic()
    enable_vt_on_windows()
    projects_json = read_projects()
    prefs = read_prefs()
    rows = visible_projects(projects_json)
    default_key = projects_json.get('default') or 'sanctum'
    mcp = count_mcp()
    bots = count_bots()
    boot_ms = int((time.monotonic() - t0) * 1000)

    while True:
        banner(boot_ms, mcp, bots)
        render_picker(rows, default_key, prefs)
        try:
            raw = input(
                f'  {WHITE}Selection [1-{len(rows)} / G / A / N / R / K / S / F / Q, '
                f'default={default_key}] {PURPLE}>{RESET} '
            ).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        t = raw.lower()
        # Multi-select
        if (multi := parse_multi(t, len(rows))) and len(multi) >= 2:
            keys = [rows[i - 1]['key'] for i in multi]
            dispatch_multi(keys)
        elif t in ('q', 'quit', 'exit'):
            print(f'  {SOFT}bye.{RESET}')
            return 0
        elif t == 'g':
            dispatch_project('general')
        elif t == 'f':
            # Operator wants the full PS1 picker (A/N/R/K/S also dispatch here)
            return dispatch_interactive()
        elif t in ('a', 'n', 'r', 'k', 's', 'rename', 'clear', 'setup', 'autonomy'):
            return dispatch_interactive()
        elif t.isdigit():
            idx = int(t) - 1
            key = rows[idx]['key'] if 0 <= idx < len(rows) else default_key
            dispatch_project(key)
        elif not t:
            dispatch_project(default_key)
        else:
            print(f'  {WARN}  unknown selection: {raw}{RESET}')
            time.sleep(1)
            continue
        # Refresh prefs for next iteration so R) changes show next time
        prefs = read_prefs()
        try:
            ans = input(f'  {DIM}> press Enter for picker, Q to quit:{RESET} ').strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if ans in ('q', 'quit', 'exit'):
            return 0


if __name__ == '__main__':
    sys.exit(main())
