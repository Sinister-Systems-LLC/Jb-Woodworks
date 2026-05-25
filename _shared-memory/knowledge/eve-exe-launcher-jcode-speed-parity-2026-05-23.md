<!-- Author: RKOJ-ELENO :: 2026-05-23 -->
<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
# EVE.exe launcher :: jcode-speed parity for Sinister Sanctum

> **Status:** doctrine, in-flight implementation, binding for the launcher lane.
> **Origin:** operator 2026-05-23, verbatim:
> 1. *"make sure everything is concise and as effiecnt as possible all jcode memory features all of that. i want our terminals to function just how the jcode exe does."*
> 2. *"do what you need to do to achieve that and link into the bat file start."*
> 3. *"can we make bat file start a exe file start like jcode does that has our starting features to spawn agents and such."*
> 4. *"make sure we have all speed settings and performacnce increase from jcode and term"*
> 5. *"i want this as eve.exe not the rkoj exe"* (clarification — binary is EVE.exe, not Sinister.exe, not modifying RKOJ.exe)

## The benchmark gap (from operator screenshots 2026-05-23)

| Tool                 | Time to first input | Time to first frame | Single-session RAM |
|----------------------|---------------------|---------------------|--------------------|
| jcode (baseline)     | 48.7 ms             | 14.0 ms             | 167 MB (27 MB w/o embeddings) |
| Antigravity CLI      | 383.7 ms            | 383.5 ms            | 243 MB             |
| pi                   | 596.4 ms            | 590.7 ms            | 144 MB             |
| Codex CLI            | 905.8 ms            | 882.8 ms            | 140 MB             |
| OpenCode             | 1047.9 ms           | 1035.9 ms           | 371 MB             |
| GitHub Copilot CLI   | 1583.4 ms           | 1518.6 ms           | 333 MB             |
| Cursor Agent         | 1978.7 ms           | 1949.7 ms           | 214 MB             |
| **Claude Code**      | **3512.8 ms**       | **3436.9 ms**       | **386 MB**         |
| **EVE.exe** (target) | **< 300 ms**        | **< 50 ms**         | **~30 MB**         |
| PS1 launcher (today) | ~800-1200 ms        | n/a                 | n/a (no resident host) |

handterm reference (the Rust terminal jcode-aligned with):

| Terminal   | Binary | Install | RAM (1 win) | RAM (each addl) |
|------------|--------|---------|-------------|-----------------|
| foot       | 477 KB | ~1 MB   | 24 MB       | +24 MB          |
| **handterm** | **3.4 MB** | **3.4 MB** | **61.3 MB** | **+1-2 MB**     |
| alacritty  | 8.9 MB | ~9 MB   | (varies)    | (varies)        |
| kitty      | 88 KB* | ~18 MB  | (varies)    | (varies)        |
| ghostty    | 26 MB  | ~29 MB  | (varies)    | (varies)        |

handterm shared-GPU host = the low-RAM-per-additional-window winner. Our `sinister-term` should mine this pattern.

## Architecture decision: thin EVE.exe wrapper, NOT a rewrite

The temptation is to port the entire PS1 launcher to Python/Rust to get the speed win everywhere. We rejected that for three reasons:

1. **Surface duplication.** The PS1 launcher has ~1100 lines of subtle behavior (trust-pre-acceptance, mintty spawn, sterm handoff, status pills, resume-point write, custom-color terminal). Two implementations = guaranteed drift.
2. **Operator-known good.** The PS1 launcher works today. Rewriting risks regressing operator-visible behavior.
3. **Hot-path speed is the picker, not the spawn.** Operator spends 80% of launcher time looking at the picker UI. The actual claude-spawn is async (forks mintty + bash). Making the picker fast = making the launcher *feel* fast.

So EVE.exe is a **thin picker wrapper**:

```
Sinister Start.bat
       |
       +-- if EVE.exe exists ----> EVE.exe (Python stdlib, ~150-300 ms cold-start)
       |                              |
       |                              +-- numeric pick / G / multi ---> spawn PS1 -Project <key> (headless)
       |                              +-- A / N / R / K / S / F -------> spawn PS1 (interactive picker)
       |                              +-- Q -----------------------------> exit
       |
       +-- else -------------------> start-sinister-session.ps1 (no regression)
```

EVE.exe is **just the picker UI**. All heavy lifting (mintty / sterm / trust / status pills / resume-points) stays in PS1, which keeps lane-of-truth boundaries clean.

## Shipped artifacts (2026-05-23 06:35Z)

- `automations/eve-launcher/eve.py` — stdlib Python launcher (~270 LOC, no third-party imports)
- `automations/eve-launcher/build-eve-exe.bat` — PyInstaller --onefile --name=EVE build script
- `automations/eve-launcher/README.md` — tool card
- `automations/eve-launcher/.gitignore` — build/dist/pycache
- `C:\Users\Zonia\Desktop\Sinister Start.bat` v4 — probes 3 EVE.exe paths, falls back to PS1
- `_shared-memory/knowledge/eve-exe-launcher-jcode-speed-parity-2026-05-23.md` — this entry

Operator one-click to build:

```
"D:\Sinister Sanctum\automations\eve-launcher\build-eve-exe.bat"
```

Requires Python 3.10+ on PATH. Installs PyInstaller automatically if missing. Output: `dist\EVE.exe` (~15-20 MB).

## EVE.exe responsibilities (single source of truth)

| Responsibility | Owner | Why |
|---|---|---|
| Fast picker UI | EVE.exe | The hot path operator sees first |
| Read projects.json + agent-prefs.json | EVE.exe | Needed for picker rendering |
| Display per-project agent_name + accent | EVE.exe | Makes Rename + Color visible (mirrors PS1 fix) |
| Numeric / G project dispatch | EVE.exe -> PS1 headless | Common case; fast path |
| Multi-select (1,3,5 / 1-3) | EVE.exe -> PS1 headless (loop) | Common case |
| A / N / R / K / S / F | EVE.exe -> PS1 interactive | Sub-flows have multi-prompt UX |
| mintty spawn | PS1 | Owns terminal-color env setup |
| trust-pre-acceptance | PS1 | Owns ~/.claude.json edits |
| 6 jcode status pills | PS1 | Runs in spawned shell, not picker |
| sterm post-claude handoff | PS1 | Runs in spawned shell |
| Resume-point auto-write | PS1 | Runs in spawned shell |
| Token-saving compact phrase | PS1 (Build-Phrase) | Already shipped |

## Speed wins enumerated

1. **No PowerShell host bootstrap.** PowerShell.exe takes ~600 ms even with `-NoProfile`. EVE.exe has zero PowerShell on the hot path.
2. **No script-parse overhead.** PS1 is ~53 KB; parsing it every spawn is non-trivial.
3. **Stdlib-only.** No `import` cascade. `json`, `os`, `subprocess`, `sys`, `time`, `pathlib`, `shutil` only.
4. **utf-8-sig decode.** Handles both BOM and non-BOM JSON files transparently (PS1 also does, but Python's default `utf-8` does not — fixed in v0.1.1).
5. **Inline ANSI banner.** No file read for the banner ASCII art on the hot path (PS1 does Pick-RandomArt -> reads 8 .txt files looking).
6. **One-shot stdin.** No multi-prompt wizard on the common path.

## Token-saving (operator ask "without losing efficiency")

The PS1 launcher already uses the **compact phrase** mode (`automations/session-contracts.md` reference instead of inlining 6 contracts × ~600 chars). Per `_shared-memory/knowledge/launcher-v6-concise-rewrite-2026-05-23.md`, this saves ~3000 tokens per spawn.

EVE.exe **does NOT alter the cold-start phrase**. It dispatches into PS1 which builds the phrase exactly as before. No token-saving regression risk.

## Anti-patterns to never repeat

1. **Don't reimplement the spawn logic in Python.** EVE.exe is JUST the picker. The moment EVE.exe tries to spawn mintty itself, we have two sources of truth for terminal-spawn behavior. Operator-visible drift inevitable.
2. **Don't add third-party deps to eve.py.** No `rich`, no `textual`, no `prompt_toolkit`. PyInstaller bundles them all and the binary balloons from ~15 MB to ~50+ MB. Stdlib is enough for a picker.
3. **Don't make EVE.exe a daemon.** handterm's daemon mode is for terminal hosting (multi-window GPU sharing). The launcher is a one-shot picker; daemon mode is overhead with no benefit.
4. **Don't replace `Sinister Start.bat` with `Sinister Start.exe`.** The bat is the operator's muscle memory + it gates first-run autonomy bootstrap + plugin check. EVE.exe is one of the bat's two execution paths, not its replacement.
5. **Don't put EVE.exe in `~/.claude/`.** That's Claude Code's territory. Operator-owned per CLAUDE.md.
6. **Don't ship EVE.exe to the repo.** PyInstaller output is platform-specific binary; `dist/` is `.gitignore`'d. Operator builds locally.

## Roadmap (post-MVP)

- **Phase 2**: measure actual EVE.exe boot time on operator's machine, compare to jcode 48 ms target. If we're > 300 ms after build, investigate `--noupx`, cold-start profiling, lazy imports.
- **Phase 3**: optional Rust port if Python boot consistently > 300 ms. Targets jcode-class 50 ms boot. Requires Rust toolchain (currently operator-gated per OPERATOR-ACTION-QUEUE.md).
- **Phase 4**: integrate handterm's shared-GPU host pattern for `sinister-term` (separate brain entry; cross-lane to forge + term).
- **Phase 5**: add jcode-memory parity audit to `sinister-term` post-claude shell (currently sterm fallback). Coordinate via inbox.

## Composability

This doctrine composes with:

- `jcode-feature-matrix.md` (add row 31 for EVE.exe)
- `agent-identity-eve.md` (binary name = persona name)
- `launcher-v6-concise-rewrite-2026-05-23.md` (token-saving compact phrase mode; EVE preserves it)
- `do-not-revert-operator-canonical-protections-2026-05-23.md` (EVE dispatches to PS1 which honors all 6 protections)
- `handterm-vs-sinister-term-clarification-2026-05-23.md` (sterm = our shell; EVE is upstream of it)
- `forever-expanding-modular-architecture-doctrine.md` (append-only; EVE adds a new launcher path without removing the PS1 path)
- `sinister-launcher-fast-boot-doctrine` (new, future) — boot-time measurement + regression protection

## Tags (for INDEX.md)

doctrine, in-flight, launcher, eve-exe, jcode-speed-parity, pyinstaller, thin-wrapper, picker-ui, stdlib-only, boot-time, 48ms-baseline, handterm-shared-gpu, sinister-term, fallback-to-ps1, single-responsibility, 2026-05-23
