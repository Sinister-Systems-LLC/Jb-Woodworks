<!-- Author: RKOJ-ELENO :: 2026-05-23 -->
# EVE.exe :: completion plan (finish-the-build)

> **Status:** plan, ready-to-execute. Scaffold exists; this plan finishes it.
> **Origin (operator verbatim 2026-05-23):** *"make a complete detailed plan to finish the eve.exe you were suppose to build. get to work and use all parralll agents you need"*
> **Anchor doctrine:** `_shared-memory/knowledge/eve-exe-launcher-jcode-speed-parity-2026-05-23.md`
> **Composes with:** `launcher-v6-concise-rewrite-2026-05-23.md`, `launcher-v6.1-jcode-style-directives-2026-05-23.md`, `handterm-vs-sinister-term-clarification-2026-05-23.md`, `agent-identity-eve.md`, `do-not-revert-operator-canonical-protections-2026-05-23.md`, `jcode-feature-matrix.md`
> **TL;DR:** EVE.exe is a stdlib-only Python picker compiled by PyInstaller `--onefile --noupx` to a ~15-20 MB single-file binary that boots in <300 ms. It hosts the common-case picker UI (numeric pick / G / multi-select), dispatches to `start-sinister-session.ps1 -Project <key>` for the spawn, and falls through to the interactive PS1 picker for A/N/R/K/S/F. `Sinister Start.bat` v5 already probes three EVE.exe paths and falls back to PS1 if none found. This plan finishes the binary, validates parity, and ships it.

---

## 0. Snapshot of current state (as of 2026-05-23T12:30Z)

Existing artifacts:
- `automations/eve-launcher/eve.py` (306 lines, stdlib-only, working scaffold)
- `automations/eve-launcher/build-eve-exe.bat` (PyInstaller wrapper with `--noupx --onefile --clean`)
- `automations/eve-launcher/README.md` (tool card)
- `automations/eve-launcher/.gitignore`
- Sinister Start.bat v5 (probes 3 EVE.exe paths; falls back to PS1)
- `automations/session-templates/projects.json` v7 (14 picker entries)
- `automations/session-templates/agent-prefs.json` v2 (per-project agent_name + accent)
- `automations/start-sinister-session.ps1` (1396 lines — truth source for spawn behavior)
- `automations/session-art/01-skull.txt … 08-wolf.txt` (8-piece ASCII pool)

Not yet present:
- `dist/EVE.exe` (not built)
- No copies at any of the 3 install paths
- No measured cold-start time on operator's machine
- ASCII-art pool not yet rendered in `eve.py` (banner uses inline one-liner)
- No `--profile` switch (R5 of jcode-parity audit)

---

## 1. What EVE.exe must do (verb-by-verb capability list)

1:1 cross-reference against `start-sinister-session.ps1` v6.1 (truth source) so nothing regresses.

| # | Verb | PS1 ref | EVE.exe behavior | Handoff |
|---|---|---|---|---|
| 1 | Numeric pick (1-14) | Resolve-Pick L384 | render_picker + int(raw) | `-Project <key>` headless |
| 2 | G) General | Resolve-Pick L390 | resolve to 'general' | `-Project general` headless |
| 3 | A) Auto-Resume | Pick-ResumeRow L479-549 | fall through to PS1 | PS1 no `-Project` |
| 4 | N) New Project | Create-NewProject L1342-1363 | fall through to PS1 | PS1 |
| 5 | R) Rename + Color | Customize-Project | fall through to PS1 | PS1 |
| 6 | K) Clear ctx | Clear-Context | fall through to PS1 | PS1 |
| 7 | S) Autonomy Setup | L1276-1297 | fall through to PS1 | PS1 |
| 8 | F) Full picker | (EVE-exclusive) | bypass EVE → PS1 | PS1 |
| 9 | Q) Quit | L1270-1275 | sys.exit(0) | none |
| 10 | Multi-select (`1,3,5` or `1-3`) | (PS1 v6 removed it) | EVE-exclusive: dispatch each key with 400ms gap | sequential PS1 calls |
| 11 | Default (Enter) | L383 | dispatch_project(default_key) | `-Project sanctum` |
| 12 | Looping picker | L1262-1394 do-while | `while True:` loop | re-render banner + picker |
| 13 | Banner (jcode info block) | Draw-Banner L268-317 | banner() + 4-line info + pills | inline |
| 14 | MCP count | Get-MCPCount L98-115 | count_mcp() reads `~/.claude/.mcp.json` | inline |
| 15 | Bot count | Get-BotCount L117-121 | count_bots() | inline |
| 16 | Boot-time self-report | (PS1 doesn't) | banner shows `boot N ms` | inline |
| 17 | Status pills | Launch-Session shell | picker-level subset (3 pills) | inline |
| 18 | Per-project agent + accent display | Render-Picker L323-350 | render_picker matches | inline |
| 19 | utf-8-sig JSON read | L129 | encoding='utf-8-sig' | inline |
| 20 | VT enablement on Windows | (conhost default) | enable_vt_on_windows() | inline |
| 21 | Refresh prefs between iterations | L1264 | read_prefs() in loop | inline |
| 22 | Unknown selection → warn + retry | (PS1 fallback) | warn + sleep 1s + continue | inline |

**Parity audit:** scaffold covers verbs 1-2, 9-22 directly. Verbs 3-8 dispatch to PS1 (correct per architecture). Verb 10 is EVE-exclusive (see Q1).

---

## 2. Architecture spec

### File layout under `automations/eve-launcher/`

```
automations/eve-launcher/
├── eve.py                 # ~270-350 LOC stdlib-only after polish
├── build-eve-exe.bat      # PyInstaller wrapper (--noupx --onefile --clean)
├── README.md
├── .gitignore             # build/, dist/, __pycache__/, *.pyc, *.spec
├── build/                 # PyInstaller scratch (gitignored)
├── dist/                  # PyInstaller output EVE.exe (gitignored)
└── __pycache__/           # Python bytecode (gitignored)
```

NO new directories. NO third-party requirements. NO Rust crate. NO daemon mode. NO PowerShell helper inside the dir.

### Dispatch model

```
EVE.exe (eve.py main loop)
    |
    +-- [1-14, G, Enter, multi] -> dispatch_project(key)/dispatch_multi(keys)
    |       subprocess.call(['powershell.exe', '-NoProfile', '-ExecutionPolicy',
    |                        'Bypass', '-File', PS1, '-Project', key])
    |
    +-- [A, N, R, K, S, F] -> dispatch_interactive()
    |       subprocess.call(['powershell.exe', '-NoProfile', '-ExecutionPolicy',
    |                        'Bypass', '-File', PS1])  (no -Project; PS1 picker drops in)
    |
    +-- [Q] -> sys.exit(0)
```

### Strict stdlib-only constraint

eve.py imports ONLY from stdlib: `json`, `os`, `subprocess`, `sys`, `time`, `pathlib`, `ctypes` (Windows VT enablement only).

**NEVER add:** `rich`, `textual`, `prompt_toolkit`, `click`, `typer`, `pyfiglet`, `colorama`, `blessed`, `urwid`, `windows-curses`. Each balloons PyInstaller output by 5-15 MB and adds 100-300 ms cold-start.

### PyInstaller target <15-20 MB

`build-eve-exe.bat` already uses:

```
pyinstaller --onefile --name EVE --noconsole-warning \
    --distpath dist --workpath build --specpath build \
    --clean --noupx eve.py
```

`--noupx` saves ~50 ms cold-start (Windows Defender skips UPX scan).

### Why this layering

Single source of truth = start-sinister-session.ps1. EVE.exe ONLY handles picker UI then hands off. PS1 owns:
- mintty spawn + Transparency settings
- Trust-pre-acceptance (Confirm-AgentPrefs)
- 6 jcode-style status pills (in spawned bash shell)
- sterm post-claude handoff
- Resume-point auto-write
- Build-Phrase + AUP-RESPECT sandbox doctrine + Plan-then-execute preamble

EVE.exe never reimplements any of these.

---

## 3. Picker UI

### ANSI 256-color status pills

| Pill | Escape | Use |
|---|---|---|
| PILL_A | `\033[48;5;91;38;5;15;1m` | purple — agent name |
| PILL_M | `\033[48;5;30;38;5;15;1m` | teal — resume marker |
| PILL_D | `\033[48;5;94;38;5;15;1m` | amber — model |
| PILL_G | `\033[48;5;22;38;5;15;1m` | green — mcp:N |
| PILL_B | `\033[48;5;19;38;5;15;1m` | blue — bots:M |
| PILL_R | `\033[48;5;52;38;5;15;1m` | red — --skip-perms |
| PILL_Z | `\033[0m` | reset |

### jcode-style info block (matches PS1 Draw-Banner full mode)

```
     E V E     // jcode-speed launcher
------------------------------------------------------------
server Sanctum    client EVE    2026-05-23 12:30
model  claude-opus-4-7[1m]   speed turbo   token compact
boot   142 ms   [ mcp:5 ]  [ bots:11 ]  [ --skip-perms ]
------------------------------------------------------------
```

After P3 (banner upgrade), centered ASCII-art piece from `session-art/` renders above the info block.

### 8-piece random ASCII art pool

Source: `automations/session-art/*.txt`. Constraints (per launcher-v6.1 pattern #4): ≤50 chars wide, ≤18 lines tall, ASCII/low-Unicode only, speckle/silhouette style.

P3 implementation (new function):

```python
def pick_random_art() -> list[str] | None:
    art_dir = SANCTUM_ROOT / 'automations' / 'session-art'
    if not art_dir.is_dir():
        return None
    txts = list(art_dir.glob('*.txt'))
    if not txts:
        return None
    chosen = random.choice(txts)
    try:
        lines = chosen.read_text(encoding='utf-8').splitlines()
        while lines and not lines[-1].strip():
            lines.pop()
        return lines
    except OSError:
        return None
```

Center each line in `shutil.get_terminal_size().columns` (fallback 100).

### Picker layout (compact)

```
  Pick a project
  ------------------------------------------------------------
  *  1) Sanctum               orchestration hub
     2) Sinister Panel        Control Center @ snap.sinijkr.com
     ... [14 total]

  ------------------------------------------------------------
  G) General      A) Auto-Resume  N) New Project  R) Rename + Color
  K) Clear ctx    S) Autonomy     F) Full picker  Q) Quit
      multi-select: 1,3,5 or 1-3
  ------------------------------------------------------------
  Selection [1-14 / G / A / N / R / K / S / F / Q, default=sanctum] >
```

### Hot-path constraints

- No file reads beyond projects.json, agent-prefs.json, optional `~/.claude/.mcp.json` (4-12 KB total)
- No subprocess calls until operator hits a key
- No network calls ever
- Banner ASCII read only if P3 enabled (opt-out via `EVE_NO_ART=1`)

---

## 4. Speed budget

Target: **<300 ms** cold boot. Stretch: **<150 ms**. jcode baseline: 48 ms (Rust; future P9).

| Phase | Budget | What |
|---|---|---|
| Python interpreter cold-start | <150 ms | PyInstaller bootloader + zipimport unpack |
| Import stdlib | <30 ms | json/os/subprocess/sys/time/pathlib/ctypes |
| VT enablement | <5 ms | ctypes SetConsoleMode |
| Read projects.json | <15 ms | ~7 KB |
| Read agent-prefs.json | <10 ms | ~1 KB |
| Read .mcp.json (count_mcp) | <5 ms | optional |
| count_bots dir listing | <5 ms | <100 entries |
| Pick + read 1 ASCII art | <20 ms | 1 of 8 .txt, <2 KB |
| Render picker stdout | <50 ms | ~22 lines + ANSI |
| **Total to first frame** | **<285 ms** | sum above |

Escape hatches if profiling reveals >150 ms Python boot:
1. `--strip-debug` (saves ~10-30 ms)
2. `--exclude-module tkinter,unittest,xml,email,pydoc,lib2to3` (saves ~20-50 ms)

### `--profile` switch (P6)

```python
if '--profile' in sys.argv:
    print(f'[profile] vt={t_vt} proj={t_proj} prefs={t_prefs} mcp={t_mcp} bots={t_bots} art={t_art} render={t_render}')
    sys.exit(0)
```

Baseline stored at `_shared-memory/script-runs/eve-boot-baseline.json` (via `--profile-save`).

---

## 5. Build pipeline

`build-eve-exe.bat` already has the right flags. No edits required for P1.

Output: `dist/EVE.exe` (~15-20 MB). Bat prints size via `for %%I in (dist\EVE.exe) do echo size = %%~zI bytes`.

Manual run from `automations/eve-launcher/`:

```cmd
cd /D "D:\Sinister Sanctum\automations\eve-launcher"
build-eve-exe.bat
```

P7 may add `install-eve-exe.bat` that auto-copies to all 3 install paths.

---

## 6. Three placement paths

Sinister Start.bat v5 L70-73 probes in order:

| # | Path | Use case |
|---|---|---|
| 1 | `%~dp0EVE.exe` (Desktop) | Operator's most common location |
| 2 | `%SANCTUM_ROOT%\automations\eve-launcher\dist\EVE.exe` | Build output (auto-pickup after rebuild) |
| 3 | `%LOCALAPPDATA%\Sinister\EVE.exe` | Per-user install for multi-machine portability |

**Fallback if none:** PS1 launcher (Sinister Start.bat L85-97). Zero regression.

---

## 7. Fallback behavior

```
Sinister Start.bat
    EVE.exe found? YES -> run EVE.exe -> respect exit code
                   NO  -> fall through to PS1 launcher
```

**Decision:** if EVE.exe crashes (non-zero exit), bat does NOT auto-fall-back to PS1. Crash should be visible; operator can rename EVE.exe to force PS1 path.

**Inside EVE.exe:** PS1 invocations (`dispatch_project` + `dispatch_interactive`) don't fall back if PS1 fails — print `[FAIL] PS1 not found at <path>` and return 2.

---

## 8. Smoke + acceptance criteria

### Phase-by-phase smoke

| Phase | Test | Pass |
|---|---|---|
| P1 | `python eve.py` | Picker renders, 14 projects shown, Q quits clean |
| P2 | `python eve.py` → 1 | PS1 launches `-Project sanctum`; mintty within ~3 sec |
| P3 | `python eve.py` → banner | Random art centered; pills show mcp/bots/skip-perms; boot ms <300 |
| P4 | `python eve.py` → A | PS1 Auto-Resume flow drops in; operator can pick or cancel |
| P5 | (handoff) | Operator types free-text query in spawned PS1 picker; works |
| P6 | `python eve.py --profile` | All phases <50 ms; total <200 ms (raw Python) |
| P7 | `build-eve-exe.bat` | Builds clean; dist\EVE.exe size 15-20 MB; --profile <300 ms |
| P8 | Click Sinister Start.bat → 1 | Cold boot → mintty → agent ready ≤ 5 seconds total |

### Acceptance criteria

- EVE.exe boot <300 ms (cold; first-run after reboot)
- bat → EVE.exe → mintty → protections → agent ready ≤ 5 seconds
- All 14 picker projects launch via numeric pick
- EVE.exe size ≤ 20 MB
- No single `--profile` phase >150 ms
- Multi-select `1,3,5` spawns 3 windows in ~3 sec (if kept — see Q1)
- A) Auto-Resume fall-through preserves stdin
- Q returns within 50 ms
- Malformed projects.json → exit 2 with reason
- Build artifacts gitignored

### 14-project test matrix

(See plan Section 8.3 — sequence covers sanctum, sinister-panel, kernel-apk, sinister-emulator-bundle, rkoj, snap-emu, tiktok-emu, bumble-emu, sinister-freeze, jb-woodworks, showmasters, letstext, sinister-generator, jkor + G for general.)

---

## 9. Phasing

| Phase | What | Effort | R-class |
|---|---|---|---|
| **P1** | smoke-test scaffold; fix edge cases; remove unused `shutil` import | 30 min | R1 |
| **P2** | numeric pick headless dispatch; smoke 3 of 14 | 1 hr | R2 |
| **P3** | TUI banner + status pills + ASCII art pool; EVE_NO_ART opt-out | 2 hr | R2 |
| **P4** | A/N/R/K/S handlers fall-through; smoke each | 2 hr | R2 |
| **P5** | free-text resume search verify (PS1-owned; just confirm stdin handoff) | 30 min | R1 |
| **P6** | `--profile` + `--profile-save`; tune to <150 ms | 2 hr | R3 |
| **P7** | build-eve-exe.bat run + install to 3 paths via install-eve-exe.bat | 1 hr | R2 |
| **P8** | acceptance smoke 14 projects + 5-sec target + fallback verify | 2 hr | R2 |

**Total:** ~11 hr single-agent sequential. **~8 hr with 3 parallel agents** (Agent 1 owns eve.py edits sequential; Agent 2 smoke-tests as Agent 1 lands; Agent 3 P6+P7 once stable).

---

## 10. Anti-patterns

1. Don't reimplement spawn in Python (mintty/trust/sterm/pills/resume-write stays in PS1)
2. No third-party deps on boot path (stdlib only)
3. No daemon mode (one-shot picker)
4. Don't replace Sinister Start.bat (operator muscle memory + first-run autonomy gate)
5. Don't put EVE.exe in `~/.claude/`
6. Don't commit dist/EVE.exe
7. Don't lazy-import to fake profile numbers
8. Always `python -m py_compile eve.py` after meaningful edit
9. Use `'\033[...m'` strings, not literal ESC characters
10. No argparse (~30 ms overhead); inline `if '--profile' in sys.argv:`
11. No debug prints in hot path (gate behind `EVE_DEBUG`)

---

## 11. Open questions for operator

**Q1.** Multi-select retention? Recommend **keep**.
**Q2.** Install primary path? Recommend **Desktop** as primary, install all 3 for redundancy.
**Q3.** `--noupx` accepted? Recommend **keep** (speed > size).
**Q4.** Lock-file for double-click? Recommend **no lock** (parallel windows are meaningful).
**Q5.** Auto-fallback on EVE crash? Recommend **no** (crash should be visible).
**Q6.** Banner ASCII art on by default? Recommend **yes** (<20 ms cost; `EVE_NO_ART=1` opt-out).
**Q7.** EVE-side free-text resume search? Recommend **defer** (keep in PS1).
**Q8.** Start Rust port in parallel? Recommend **no** (finish Python first, profile, decide).

---

## 12. Critical-file index

- `automations/eve-launcher/eve.py` (lines noted in plan: 1-306)
- `automations/eve-launcher/build-eve-exe.bat` (L23-29 PyInstaller invocation)
- `automations/eve-launcher/.gitignore`
- `automations/start-sinister-session.ps1` (L20-30 params; L81-96 art pool; L98-121 counts; L153-167 visible; L176-228 confirm; L268-317 banner; L323-396 picker+dispatch; L402-549 resume; L1242-1258 headless arm; L1262-1394 picker loop)
- `Sinister Start.bat` L70-83 EVE.exe probe + L85-97 fallback
- `automations/session-templates/projects.json` (picker.visible_keys 14 entries)
- `automations/session-templates/agent-prefs.json`

---

## 13. Implementation order

```
P1 smoke -> P2 numeric -> P3 banner+art -> P4 interactive -> P5 resume verify
  -> P6 --profile -> P7 build+install -> P8 acceptance
```

Critical-path agent: single agent on eve.py edits (P1-P4). Parallel-ok: smoke-testing, P6 profiler, P7 build.

---

## 14. Composability

Composes with: `launcher-v6-concise-rewrite-2026-05-23`, `launcher-v6.1-jcode-style-directives-2026-05-23`, `handterm-vs-sinister-term-clarification-2026-05-23`, `agent-identity-eve`, `do-not-revert-operator-canonical-protections-2026-05-23`, `jcode-feature-matrix`.

---

## 15. Done definition

EVE.exe is **done** when:

1. `dist/EVE.exe` exists, 15-20 MB
2. Copied to `%~dp0EVE.exe` (Desktop)
3. `EVE.exe --profile` reports <300 ms cold-start
4. All 14 picker projects launch via numeric pick
5. G/A/N/R/K/S/F/Q all dispatch correctly
6. bat → EVE.exe → mintty → claude → ≤ 5 seconds
7. Fallback to PS1 works when EVE.exe is missing
8. `jcode-feature-matrix.md` updated with EVE.exe row
9. Brain `_INDEX.md` updated with this plan
10. Plan moved to `_shared-memory/plans/_archive/` after P8 sign-off

---

*End of plan.*
