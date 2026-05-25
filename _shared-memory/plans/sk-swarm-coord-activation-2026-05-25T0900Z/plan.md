# Plan: sk-swarm-coord Activation

**Author:** RKOJ-ELENO :: 2026-05-25  
**Priority:** HIGH  
**Requested:** Operator 2026-05-25 ("review this and create a high priority plan to complete it")  
**Source skill:** `D:\Sinister Sanctum\skills\sk-swarm-coord\`  
**Status:** OPEN

---

## Goal

Activate `sk-swarm-coord` as a live, operator-thumb'd fleet capability so that Sinister Sanctum can launch multi-agent swarms via a single command instead of 3+ separate launcher invocations. Resolves the "swarm=on but no actual topology management" gap.

---

## Acceptance Criterion

`swarm_init topology=hierarchical maxAgents=6` succeeds via Ruflo MCP. At least one sub-agent spawns and registers in the swarm tree. `swarm_status` returns live topology. EVE.exe Accounts/Tools panel shows swarm status row.

---

## Steps

### P0 — Operator Thumb (unblocked immediately)
- [ ] **P0.1** Write operator-thumb verdict to `_shared-memory/case-studies/2026-05-19-sk-swarm-coord.md` — change status from `candidate` to `approved`. This unblocks all downstream steps.

### P1 — Verify Ruflo MCP has swarm plugin loaded
- [ ] **P1.1** Call `mcp__ruflo__swarm_health` (ToolSearch → invoke). If it responds, plugin is active. If not, run `claude mcp add ruflo -s user -- npx ruflo@latest mcp start` to refresh.
- [ ] **P1.2** Verify `swarm_init`, `swarm_status`, `swarm_shutdown`, `swarm_health` all resolve via ToolSearch. Log results to PROGRESS.

### P2 — Wire Sanctum defaults
- [ ] **P2.1** Add `swarm_defaults` block to `automations/session-templates/agent-prefs.json`:
  ```json
  "swarm_defaults": {
    "topology": "hierarchical",
    "maxAgents": 6,
    "consensus": "raft",
    "strategy": "specialized",
    "worktree_isolation": true
  }
  ```
- [ ] **P2.2** Update `_shared-memory/knowledge/cross-agent-coordination.md` — add "After ruflo-swarm" section describing the new patterns (swarm_init flow, topology picker, how inbox + swarm compose).

### P3 — Integrate with session launcher
- [ ] **P3.1** In `start-sinister-session.ps1` `Build-Phrase`, when `$swarmMode` is `on` or `relentless`, append swarm init instruction to `$base`: "If swarm tools available: call swarm_init topology=hierarchical maxAgents=6 consensus=raft at session start and register this agent in the swarm."
- [ ] **P3.2** Confirm `$defSwarm = $true` default (already set per iter-22) injects the instruction on every spawn.

### P4 — EVE.exe status surface
- [ ] **P4.1** In `tools/eve-picker/main_menu.py` `_hero_lines()`, add swarm status probe: call `swarm_status` if available; surface as `{SOFT}swarm:{RESET} {OK}hierarchical 3/6{RESET}` gem-line entry.
- [ ] **P4.2** If swarm not initialized, show `{DIM}swarm: off{RESET}` (graceful no-op).

### P5 — Brain + index update
- [ ] **P5.1** Add brain entry `sk-swarm-coord-activation-2026-05-25.md` summarizing the activation, topology defaults, and compose links.
- [ ] **P5.2** Update `_shared-memory/knowledge/_INDEX.md` with the new entry row.

### P6 — Smoke test
- [ ] **P6.1** Via ToolSearch, invoke `swarm_init` with hierarchical topology. Verify response contains swarm ID.
- [ ] **P6.2** Invoke `swarm_status` — verify topology shows master + at least 1 worker slot.
- [ ] **P6.3** Log smoke test results to PROGRESS.

### P7 — Commit + push
- [ ] **P7.1** Stage all modified files (agent-prefs, start-sinister-session, main_menu, cross-agent-coordination, brain, plan itself).
- [ ] **P7.2** Commit: `sanctum: activate sk-swarm-coord — ruflo swarm topology integration`
- [ ] **P7.3** Push current agent branch.

---

## Blockers

- **P0.1 must happen first** — the case-study verdict file needs to move from `candidate` to `approved` before this plan is officially sanctioned. Sanctum master agent can write this verdict directly (operator verbal thumb 2026-05-25 counts as approval).

---

## Dependencies

- Ruflo MCP: already registered (`claude mcp add ruflo -s user -- npx ruflo@latest mcp start`, done 2026-05-19)
- Claude Code 2.1+ (Task/SendMessage/Monitor): satisfied
- `agent-prefs.json` `swarm=true` default: already set (iter-22)

---

## Estimates

| Step | Effort |
|---|---|
| P0 | 5 min (write verdict) |
| P1 | 10 min (MCP probe) |
| P2 | 15 min (config + brain) |
| P3 | 20 min (launcher edit) |
| P4 | 20 min (EVE.exe UI) |
| P5 | 10 min (brain index) |
| P6 | 10 min (smoke test) |
| P7 | 5 min (commit) |
| **Total** | **~95 min** |
