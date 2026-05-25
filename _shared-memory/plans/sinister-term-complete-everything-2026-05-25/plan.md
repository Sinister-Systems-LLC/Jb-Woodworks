# Sinister Term :: Complete Everything Master Plan

> **Author:** RKOJ-ELENO :: 2026-05-25
> **Lane:** `sinister-term` :: branch `agent/sinister-term/complete-everything-plan-2026-05-25`
> **Mode:** RESUME → RELENTLESS LOOP
> **Operator trigger:** 2026-05-25T11:32:18Z — *"create a plan to complete everything i have said to do"*

---

## What this is

One consolidated plan that names every operator-given Sinister Term ask + every queued
inbox item + every regression detected this turn, organized by priority, with binary
pass criteria so each item is either SHIPPED-VERIFIED or visibly still in-flight.

This composes with the fleet doctrines (CLAUDE.md hard-canonicals) — NO GATE QUESTIONS,
RELENTLESS PURSUIT, FULL-RELENTLESS SWARM FAN-OUT, NO-BULLSHIT TESTED-BEFORE-CLAIMED.

---

## State snapshot (entering this plan)

- **Branch:** session opened on `agent/sinister-os/eve-llm-bridge-spec-2026-05-25` (sister lane);
  switching to `agent/sinister-term/complete-everything-plan-2026-05-25` for all sinister-term commits.
- **Source layout:** `projects/sinister-term/source/term/{app,commands,completer,keybindings,theme,status,aliases,ipc,ipc_client,login_stub,cli,swarm}.py`
- **Phases shipped (per README + PROGRESS):** PH0-PH14 all complete as of 2026-05-21.
- **Detected regression:** PH14 pytest suite dropped from 21 → 3 collected (test_dispatch.py + test_keybindings.py + test_status.py + conftest.py missing from `tests/`). Sister-agent inbox-reorg or branch-merge dropped them. **P0 fix this turn.**
- **Inbox unread:** 18 items queued from 2026-05-21 through 2026-05-25T01:15Z (3 actionable [DELEGATE]/[ASK] tags; rest [INFO]/[ACK]).

---

## P0 — THIS TURN (relentless, ship before end-of-turn)

| # | Item | Why | Pass criterion | Owner |
|---|---|---|---|---|
| P0-1 | Restore PH14 pytest suite (test_dispatch.py + test_keybindings.py + test_status.py + conftest.py) | Resume-point 2026-05-21T07:38Z claims 21 passing; current state is 3. Real regression. | `pytest -q` collects ≥18 tests with all passing | this agent, inline |
| P0-2 | Smoke-test `pip install -e .` + `python -m term --version` | Confirm import path still works after 4 days of sister-lane churn touching shared files | both commands exit 0 | this agent, inline |
| P0-3 | Switch to `agent/sinister-term/complete-everything-plan-2026-05-25` branch + commit + push | Single-repo push policy: own lane only | branch exists on origin/sanctum remote | this agent, inline |
| P0-4 | Write resume-point + PROGRESS entry + heartbeat | Loop-mode rule 1 (next iter fires this turn) | files updated; heartbeat <60s old | this agent, inline |

---

## P1 — NEXT 1-3 ITERS (queued inbox items, swarm-parallelizable)

All P1 items have inbox [DELEGATE]/[feature-request] tags — they are operator-directed work
sitting in `_shared-memory/inbox/sinister-term/` since 2026-05-24/25.

### P1-A — jcode context+usage+concise-log triad (inbox 2026-05-25T01:15Z)

Operator verbatim 2026-05-25T01:15Z: *"i want this to be permanent header i can see on the top of the sinister terms and i want the jcode popups to track context and to track usage and to have the concise logging system that he has add this and pickup wheere we left off work on our terms"*

**Three deliverables** (sanctum handles the scroll-region in `start-sinister-session.ps1`; we own the in-TUI surfaces):

1. **`term/context_popup.py`** — read `~/.claude/projects/<proj>/*.jsonl`, parse last assistant message for token-count + cache breakdown, render `context: 65k/200k (32%)` in toolbar AND in OSC-2 window-title append.
   - Source pattern reference: `C:\Users\Zonia\Desktop\jcode-0.12.4\src\compaction.rs:1-100` (reactive+proactive semantic compaction triggers @ 80% token-limit).
   - Pass criterion: spawn a fresh `sterm`, run any command, bottom toolbar shows `ctx:NN%/100%` segment that updates within 5s of new assistant turn.

2. **`term/usage_popup.py`** — wrap `automations/claude-usage-meter.ps1` (already exists, OAuth-compatible) for 5h-window remaining + today's spawn count + plan tier.
   - Pass criterion: bottom toolbar shows `usage:5h-left=NN%/spawns=N/plan=opus`; refreshes on 60s TTL via `status._cached`.

3. **`term/log_concise.py`** — port jcode `src/logging.rs:145-426` structured `[srv:SHORT|ses:SHORT|prv:SHORT|mod:SHORT] EVENT key=value` format with `min_interval` rate-limit dedup HashMap.
   - Pass criterion: importable + 5 unit tests covering format + rate-limit + dedup; SINISTER_TERM_VERBOSE=1 env disables (legacy fallback).

### P1-B — Swarm HUD widget in status bar (inbox 2026-05-24T22:30Z)

Operator verbatim 2026-05-24T22:25Z: *"make sure swarm is working like jcode when you turn it on because i turned it on for kernel apk and it doesnt look like its on or working"*.

- **`term/swarm_hud.py`** — when `SINISTER_SWARM_MODE=1` in child env, status-bar shows:
  ```
  swarm: 3/5 active · roles=lead,worker,worker · last-report 14s ago
  ```
- Source pattern: jcode `crates/jcode-swarm-core/src/lib.rs` (`SwarmMemberRecord`/`SwarmLifecycleStatus`/`SwarmRole`).
- Read swarm state from: `_shared-memory/swarm-state/<session-id>.json` (poll 2s TTL via `status._cached`).
- Pass criterion: with `SINISTER_SWARM_MODE=1` set and a mock swarm-state json, `_bottom_toolbar()` includes the swarm segment; hidden when env var unset.

### P1-C — jcode-style banner animations (inbox 2026-05-24T19:45Z)

Operator verbatim 2026-05-24T18:55Z: *"i need a way in the exe to see my logged in accounts. usage on them. agents on each. and make this how jcode is [screenshot] that has all the random antimations. just use his exact code and use his colors everything same on those aniimations"*.

- **`term/animations.py`** — port `C:\Users\Zonia\Desktop\jcode-0.12.4\src\tui\ui_animations.rs:1-50` donut + orbit_rings 3D ASCII with HSV→RGB hue rotation `hue=(time_hue + t * 160.0) % 360.0` ease-out-cubic 150ms.
- Render mode: `sterm --animate` flag boots into animation demo; `theme.BANNER` becomes a static frame of the donut.
- Pass criterion: `python -m term --animate` runs for 5s without crash + uses jcode's exact HSV rotation formula.

### P1-D — Persistent header coupling (sanctum-shipped scroll-region scope)

Sanctum is shipping the DECSTBM scroll-region pill banner in `start-sinister-session.ps1` (top 3 rows fixed). We must:
- Verify `sterm`'s prompt + bottom_toolbar don't violate the top-3-rows budget (Rich `Console` should respect cursor position; bottom_toolbar already lives at row N-1).
- Pass criterion: launch sanctum-spawned bash → `sterm` → pill banner still visible at top after multiple commands scroll.

---

## P2 — STRUCTURAL / CROSS-LANE (iter 4+)

| # | Item | Trigger | Pass criterion |
|---|---|---|---|
| P2-1 | Wire `forge-memory recall` builtin (`/recall <topic>`) | Cold-start blurb mentions forge-memory CLI for disk-stored memory recall | `/recall jcode-parity-probe` returns prior rows; jsonl logged |
| P2-2 | Wire `sinister-bus` MCP heartbeat call into `app.py` startup | Canonical Rule 9: every agent calls `sinister-bus.heartbeat` every turn | MCP heartbeat row appears in bus log per session |
| P2-3 | `/swarm <task>` builtin to spawn parallel sub-agents from inside sterm | FULL-RELENTLESS SWARM FAN-OUT default-on doctrine | command spawns 3 mintty children via sinister-swarm CLI |
| P2-4 | Bot-fleet quick reference: `/bot <local-name>` routes to MCP-served local bots before reaching for Opus | Cold-start guidance + `_shared-memory/knowledge/bot-fleet-quick-reference.md` | `/bot librarian "search X"` invokes local MCP bot, not subagent |

---

## P3 — DESKTOP / OPERATOR UX (iter 7+)

| # | Item | Pass criterion |
|---|---|---|
| P3-1 | `sterm.exe` PyInstaller one-file build → desktop shortcut | clicking shortcut launches sterm with sinister palette + sanctum cwd |
| P3-2 | EVE.exe picker entry "S) Sinister Term standalone" | picker row appears + selecting it spawns sterm in a fresh mintty |
| P3-3 | Crash recovery: dump traceback to `_shared-memory/eve-crash-log.jsonl` (composes with eve.py 808-845 hardening) | forced crash leaves a jsonl row + sterm restarts via watchdog |

---

## P4 — TRACK B (RUST PORT, deferred per README)

Per README: defer until v0 has 30 days operator-use. We are at 4 days (2026-05-21 → 2026-05-25). Re-evaluate 2026-06-20. Nothing to do this iter.

---

## Order of operations this iter (RELENTLESS)

1. **NOW (this turn):** P0-1 → P0-2 → P0-3 → P0-4. End-of-turn deliverable = working tests + pushed branch.
2. **Next iter:** spawn 3 parallel sub-agents for P1-A.1 (context_popup), P1-A.3 (log_concise), P1-B (swarm_hud) — non-overlapping files, safe to swarm.
3. **Iter after:** verify all P1 land + ship P1-C (animations) + P1-D (persistent header coupling).
4. **Iter after that:** start P2 (recall + bus + swarm builtin + bot router) in another parallel fan-out.
5. **Iter after that:** P3 desktop ship.
6. **Loop condition** (re-checked each iter): sinister-term P0+P1+P2 SHIPPED + pytest green + sterm boots clean + heartbeat fresh. ANY no → keep going.

---

## Pass criteria summary (binary)

- [ ] P0-1: `pytest -q` ≥18 collected, 0 failed
- [ ] P0-2: `pip install -e .` exit 0, `python -m term --version` (or `sterm --version`) exit 0
- [ ] P0-3: `git push origin agent/sinister-term/complete-everything-plan-2026-05-25` exit 0
- [ ] P0-4: resume-point json written + PROGRESS entry + heartbeat <60s old
- [ ] P1-A.1: `ctx:NN%` segment in toolbar
- [ ] P1-A.2: `usage:5h-left=NN%` segment in toolbar
- [ ] P1-A.3: 5 unit tests pass for log_concise
- [ ] P1-B: `swarm:N/M` segment shows when env=1, hidden when env=0
- [ ] P1-C: `python -m term --animate` runs 5s clean
- [ ] P1-D: pill banner stays visible across multi-command session
- [ ] P2-1: `/recall <topic>` returns rows
- [ ] P2-2: sinister-bus heartbeat row per session
- [ ] P2-3: `/swarm <task>` spawns 3 mintty
- [ ] P2-4: `/bot librarian` invokes local MCP
- [ ] P3-1: desktop shortcut works
- [ ] P3-2: EVE.exe picker row works
- [ ] P3-3: crash recovery jsonl row

---

## Composes with

- `_shared-memory/knowledge/no-gate-questions-execute-directly-doctrine-2026-05-25.md`
- `_shared-memory/knowledge/loop-relentless-pursuit-doctrine-2026-05-25.md`
- `_shared-memory/knowledge/full-relentless-swarm-fanout-mindset-doctrine-2026-05-25.md`
- `_shared-memory/knowledge/no-bullshit-tested-before-claimed-doctrine-2026-05-23.md`
- `_shared-memory/knowledge/sanctum-scope-discipline-2026-05-24.md`
- `_shared-memory/knowledge/single-repo-push-policy-2026-05-25.md`
- `_shared-memory/knowledge/frequent-detailed-commits-per-agent-2026-05-25.md`
- `_shared-memory/knowledge/sinister-ui-canonical-dashboard-skeleton-inheritance-2026-05-24.md` (term is TUI not web, but accent-purple + 6-color palette discipline applies)
