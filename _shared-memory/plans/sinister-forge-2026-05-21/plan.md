# Sinister Forge :: Forward Plan

> **Author:** Sinister Sanctum master agent (test, Claude) :: 2026-05-21

## Master-actionable rows

### R1 — Clone `mermaid-rs-renderer` to D:\Research\

- EXACT: `git clone --depth 1 https://github.com/1jehuang/mermaid-rs-renderer.git "D:\Research\mermaid-rs-renderer"`
- EXPECTED: Cargo.toml exists at clone root.
- VERIFICATION: `Test-Path D:\Research\mermaid-rs-renderer\Cargo.toml`
- COMMIT: `chore(research): clone mermaid-rs-renderer for Forge`

### R2 — Clone `agentgrep` to D:\Research\

- EXACT: `git clone --depth 1 https://github.com/1jehuang/agentgrep.git "D:\Research\agentgrep"`
- EXPECTED: Cargo.toml exists.
- VERIFICATION: `Test-Path D:\Research\agentgrep\Cargo.toml`
- COMMIT: `chore(research): clone agentgrep for outline/trace eval`

### R3 — Wire github-research-watcher into bootstrap-portability.ps1

- EXACT: edit `automations/bootstrap-portability.ps1` STEP 3 to dispatch `automations/github-research-watcher.ps1` hidden background alongside auto-backup + auto-cleanup. So every session start picks up any new Desktop\Github Research\ drops + writes audit + drops [ASK] in inbox.
- EXPECTED: bootstrap fires 3 background scripts now (backup + cleanup + watcher) instead of 2.
- VERIFICATION: grep bootstrap-portability for "github-research-watcher" returns 1+.
- COMMIT: `feat(bootstrap): wire github-research-watcher into session-start`

### R4 — Add `forge` mode to launcher BuiltinPhrases + picker

- EXACT: edit `automations/start-sinister-session.ps1`. Add `'forge'` to BuiltinPhrases with phrase loading Forge contract. Add picker row (after `securityaudit`). Extend modeMap.
- EXPECTED: PSParser 0 errors; `-Mode forge -NoLaunch -Fast` exits 0.
- COMMIT: `feat(launcher): add 'forge' mode for Sinister Forge sessions`

### R5 — `Sinister Forge.bat` (DONE in this commit; tools/session-launcher mirror)

- ✅ DONE.

### R6 — Update bumble-emu key in projects.json to bumble-emulator-api (lane key rename)

- EXACT: ensure projects.json reflects operator's 9-project canonical order with the new keys (`bumble-emulator-api` not `sinister-bumble-emu` etc).
- EXPECTED: 9 projects total with new keys.
- COMMIT: rolls in with R4.

### R7 — RKOJ Workstation Forge dashboard tab (cross-agent ASK to rkoj)

- EXACT: drop `_shared-memory/inbox/rkoj/<UTC>-forge-dashboard-spec.json` with spec for new Launcher-tab section: live Forge sessions + cross-agent inbox + mermaid-rs-rendered diagrams. Paired markdown spec in cross-agent/.
- COMMIT: `docs(forge): cross-agent ASK to RKOJ for Forge dashboard tab`

### R8 — mermaid-rs-renderer subprocess wrapper

- EXACT: write `projects/sinister-forge/source/mermaid_render.py` wrapping the binary. In → .mmd path or stdin; out → PNG/SVG at `_shared-memory/forge-diagrams/<sha>.png`.
- COMMIT: `feat(forge): mermaid-rs-renderer subprocess wrapper`

### R9 — agentgrep 30-minute eval against Sinister Panel

- EXACT: cargo build agentgrep, run outline/trace queries against `projects/sinister-panel/source/`. Compare vs built-in Grep. Write verdict to `_shared-memory/plans/sinister-forge-2026-05-21/agentgrep-eval.md`.
- COMMIT: `docs(forge): agentgrep eval verdict`

### R10 — Multi-provider routing contract (extends AUP-RESPECT)

- EXACT: write `automations/agent-host-routing.md` mapping providers (Claude/Codex/Gemini/Ollama/LM Studio/Together/Fireworks) to task types + Sinister projects. Add as CONTRACT 7 in session-contracts.md.
- COMMIT: `feat(forge): multi-provider routing contract`

### R11 — Brain entry: sinister-forge-harness-pattern

- EXACT: write `_shared-memory/knowledge/sinister-forge-harness-pattern.md`. Index it.
- COMMIT: `docs(brain): sinister-forge-harness-pattern doctrine`

### R12 — Sinister-Forge GitHub repo

- O-row (operator one-liner): `gh repo create Sinister-Systems-LLC/Sinister-Forge --private`. Then master pushes `projects/sinister-forge/source/` as initial.

## Operator-only rows

- O1: Authorize GitHub repo creation (R12).
- O2: Authorize multi-provider key store touch (R10).
- O3: RKOJ Forge tab thumb-up (R7).

## Composes with

- `automations/session-contracts.md` — 6 contracts
- `_shared-memory/knowledge/auto-mode-launcher-pattern.md` — sibling pattern
- `_shared-memory/knowledge/multi-agent-branch-contention-isolation-pattern.md` — Forge work happens on isolated branches
