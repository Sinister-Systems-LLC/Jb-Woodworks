# Agent: Sinister Forge

> **Author:** RKOJ-ELENO :: 2026-05-21

Append-only progress log. Most recent at top.

---

## 2026-05-21 13:00 — shipped: P0-C submit auto-close fix + F1 regression suite + F2 subprocess wire + brain extension + forward plan

Operator hit a THIRD textual quiet-failure bug: clicking Submit in the picker auto-closed the entire Forge app. Plus a comprehensive sweep of what's left, sibling check, and "get to work" execution.

**P0-C (Submit auto-close, commit `9af3407`)**: two-part root cause —
1. `PickerResult` dataclass missing `project_display`; `app.py:155` read `result.project_display` → `AttributeError`.
2. `@work` defaults to `exit_on_error=True`, so the worker exception killed the entire app (return_code=1) — operator saw the window vanish with no notify.

Fix: add `project_display` field to dataclass (populated via key→display map stashed in `compose()`) + `@work(exit_on_error=False)` on `action_new_agent` and `action_command_palette`. Pilot-verified: `boot + Ctrl+W + dismiss(_collect()) → pane mounted, app alive, return_code None`.

**F1 (regression suite, commit `90c5c7e`)** `projects/sinister-forge/source/tests/test_boot_picker_smoke.py` — 8 tests, all pass in 26s on plain pytest (no pytest-asyncio dep; each async case wraps `asyncio.run`). Covers boot, Ctrl+W open, escape cancel, Submit mount, Ctrl+P palette, plus pure-unit checks for `_render` non-None, PickerResult fields, `_build_subprocess` dispatch. **Locks in P0-A + P0-B + P0-C so future Textual bumps regress visibly.**

**F2 (subprocess wire-up, commit `90c5c7e`)**: previously the picker submitted and mounted an EMPTY pane (per PH3 spec the pane should spawn `claude --dangerously-skip-permissions <phrase>` — never wired). Added `_compose_phrase()` + `_build_subprocess()` helpers in `app.py`; `action_new_agent` now builds `ClaudeSubprocess` or `CodexSubprocess` based on picked host, passes it to `AgentPane`, and `run_worker(pane.run_subprocess())` to tail stdout/stderr into the pane. Falls back gracefully (notify warning) when picked project has no source tree on disk.

**F3 (brain entry extension, commit `90c5c7e`)**: `_shared-memory/knowledge/textual-render-shadowing-pitfall.md` retitled to **"Textual 8.x quiet-failure-mode trilogy"** — now codifies ALL three P0s (shadow + worker-context + worker-exit) under one unified detection table + fast-triage grep commands.

**F4 (sibling ACK, commit `90c5c7e`)**: dropped `inbox/sinister-term/2026-05-21T1255Z-ack-interactive-test-from-forge.json` acknowledging Term's 11:42Z interactive-test roundtrip.

**Forward plan written** `_shared-memory/plans/sinister-forge-2026-05-21/forward-plan.md` — 5-section review for operator's "review everything" ask.

**Sibling check**:
- **Sinister Term** — heartbeat 07:42Z (fresh). Own worktree at `D:/Sinister-Term-WT/`. ACK posted to their inbox. No further action.
- **Sinister Sanctum** — heartbeat 06:48Z (~90 min stale). Last shipped `tools/forge-memory-bridge/` + `tools/memory-graph-render/`. My [DELEGATE] for `tools/sinister-cli/` already cross-agent'd. Nothing else without touching their lane.

**Operator-gated** (none blocking me):
- O1: `scoop install mmdr` to enable R8 mermaid rendering.
- O2: cargo build allow-rule for PH14 live agentgrep benchmark.
- O3: `gh repo create Sinister-Systems-LLC/Sinister-Forge --private` (R12).
- O4: PLAN.md Q1-Q5 answers (defaults in effect, optional override).

**5-check completion gate** ✅ all green. Resume-point follows in next commit.

---

## 2026-05-21 12:00 — shipped: P0 forge crash fix (boot + Ctrl+W) + 3-directive absorption + brain entry

Heavy session, two operator-reported P0 crashes + three operator directives surfaced via images.

**P0-A boot crash** (operator 11:30Z: "Sinister Start.bat → forge → Windows alert + code goes by + crash"). Root cause: three widgets defined `def _render(self) -> None:` as a private helper, silently shadowing `textual.widget.Widget._render` (framework method returning Visual). Override returned None, `Visual.to_strips(self, None, ...)` raised `AttributeError`, Textual error handler caught it and exited 0 — invisible to wrapper bat. Fix: rename helper to `_refresh_view` in `chrome.py` (3 spots) + `status_bar.py` (1 spot), AND pass initial content positionally to `super().__init__()` so first paint has Content. Reproduced + fixed + Pilot-verified.

**P0-B picker crash** (operator 19:41 EDT: "it came up this time but when i did ctrl w it crashed"). Root cause: `push_screen_wait()` in Textual 8.x requires the caller to be inside a worker context (`@work` decorator), otherwise raises `NoActiveWorker`. Fix: `from textual import work` + `@work` on `action_new_agent` and `action_command_palette`. Pilot smoke `PASS: boot + Ctrl+W + escape clean`.

**Commits**:
- `cebf6cf` (Sanctum branch by sibling-checkout race) → `34af6a8` (cherry-picked to Forge branch): P0-A fix.
- `79f3ddd` (Term branch by sibling-checkout race AGAIN, then pushed to origin): P0-B fix + P0-A re-application (sibling reverted my working-tree fix) + sibling coordination drops + brain entry.

**Operator directives absorbed this turn** (3 images):
1. *image 11:43Z to Sanctum* — niri-wm/niri reference for scrollable-tiling pattern. Mapped to Forge PH18 (replace TabbedMultiPane with ScrollableColumns; mine pattern, don't import Rust source).
2. *image 11:48Z* — "i want all jcode features in our system like this" (jcode swarm doc). Mapped to Forge PH16 (file-edit notification pump in bridge + `:swarm` `:dm` `:broadcast` pane builtins).
3. *image 11:50Z* — "our commands will be sinister then the command" (jcode login flows screenshot). Mapped to Forge PH17 (consume Sanctum's future `tools/sinister-cli/` as `sinister forge` subcommand + extend agent-host-routing.md with 11 jcode providers).

All three landed as new rows in `projects/sinister-forge/source/PLAN.md`.

**Brain entries shipped**:
- `_shared-memory/knowledge/textual-render-shadowing-pitfall.md` — Textual 8.x pitfall + `@work` requirement codified. Indexed.
- `_shared-memory/knowledge/jcode-feature-parity-targets.md` — 16-row parity matrix + lane-split + branding rule. Indexed. Complements Sanctum's existing `jcode-feature-matrix`.

**Sibling coordination shipped**:
- `inbox/sanctum/2026-05-21T1145Z-hello-ack-from-forge.json` — HELLO-ACK + tool-overlap clarification (my `forge/mermaid_render.py` calls their `tools/memory-graph-render/`; my `forge/memory/` is pane-state, their `tools/forge-memory-bridge/` is persistence) + niri directive note.
- `inbox/sinister-term/2026-05-21T1145Z-ack-wayward-commit-from-forge.json` — accepting 0e8490d on my branch as-is, not force-resetting.
- `cross-agent/2026-05-21T1200Z-forge-to-sanctum-jcode-swarm-and-sinister-cli-absorption.md` — [DISCOVERY]+[DELEGATE] handing the `sinister` CLI dispatcher to Sanctum (tools/ lane), keeping the in-Forge bridge work + pane builtins for myself.

**Multi-agent contention this session** (4 incidents total — brain doctrine `multi-agent-branch-contention-isolation-pattern` empirically reinforced again):
1. 11:20Z — Term agent checkout wiped 5 untracked Writes; recovered via re-write + commit.
2. 11:35Z — same as #1 on retry.
3. ~11:42Z — Term agent's commit landed on MY Forge branch as 0e8490d (their own brain entry `verify-head-before-commit-multi-agent` documents the failure mode from their side).
4. ~19:38Z EDT — MY P0-B fix commit `cebf6cf` landed on Sanctum branch because sibling moved HEAD between my edits and `git commit`. Recovery: cherry-pick `cebf6cf` → `34af6a8` on Forge branch.

**Open / operator-gated**:
- **PH16/17/18 not started** — week+ horizon, depend on Sanctum's `tools/sinister-cli/` ship + my own bandwidth.
- **Forge branch missing P0-B fix on origin** — 79f3ddd is on Term branch on origin; cherry-pick to Forge branch blocked by sibling tree contention (Term's uncommitted PROGRESS edit). Working tree on disk has the fix so operator's next launch will pick it up regardless of branch label.
- **R12** — `gh repo create Sinister-Systems-LLC/Sinister-Forge --private` still operator-gated.
- **PH14 live benchmark** — still needs operator cargo unlock.

**5-check completion gate** all green: TaskList resolved/surfaced, PROGRESS appended top, MASTER-PLAN doesn't exist for this lane, resume-point pending (last in this commit), next-slice = wait for Sanctum CLI + operator unlocks.

---

---

## 2026-05-21 11:20 — survived: sibling-checkout clobbered my untracked writes; re-wrote + committing immediately

Hit the `multi-agent-branch-contention-isolation-pattern` failure mode mid-session: the Sinister Term agent (operator launched 11:04Z) did a `git checkout` (probably `-B` or `-f`) and my working tree lost five fresh writes (this PROGRESS file, R7 inbox JSON + cross-agent MD, R11 brain entry, R8 `mermaid_render.py`). My index edit to `knowledge/_INDEX.md` survived because it was a modification-to-tracked-file (carries across branches as uncommitted). My branch label `agent/sinister-forge/r1-r2-r7-r8-r11-2026-05-21` also survived.

Recovery move: switched back to my branch and re-wrote all wiped files (re-derivable from context), then committed FIRST per the brain doctrine (commit before sibling can reset again). Heartbeat regenerated. Branch verified before commit.

## 2026-05-21 11:05 — opened: Sinister Forge agent first-ever PROGRESS file + branch claim

First cold-start of the dedicated Sinister Forge agent (separate from Sanctum master). Prior Forge work landed via Sanctum master's branch through commits `7b2dd35` → `243db88` (PH0–PH9 + REST/SSE bridge + Claw tabs + liquid-glass polish). The Sanctum master agent's `2026-05-21T064903Z` resume-point explicitly yielded the Forge lane to this new dedicated agent.

**Context-review surfaced this session pickup** (gaps left by prior Sanctum-lane Forge work):
- R1 + R2 not done — `D:\Research\mermaid-rs-renderer\` and `D:\Research\agentgrep\` directories do not exist.
- R7 not done — no Forge-dashboard-tab spec in `_shared-memory/inbox/rkoj/`.
- R8 not done — `forge/mermaid_render.py` subprocess wrapper absent.
- R9 / PH14 not done — no `agentgrep-eval.md` verdict on disk.
- R11 not done — `_shared-memory/knowledge/sinister-forge-harness-pattern.md` absent.
- Operator-gated: R12 (GitHub repo create), PLAN.md Q1-Q5 (defaults proceed).

**Branch claimed**: `agent/sinister-forge/r1-r2-r7-r8-r11-2026-05-21` (forked from `bce833f` HEAD; sibling-agent uncommitted changes on working tree left untouched per canonical-10).

**Sibling agents launching now**: RKOJ + Sinister Term per operator 11:04Z. Cross-lane discipline: I edit only my own source tree + drop async ASKs into their inboxes.

**Heartbeat**: disk fallback at `_shared-memory/heartbeats/sinister-forge.json` (sinister-bus MCP not loaded).

---
