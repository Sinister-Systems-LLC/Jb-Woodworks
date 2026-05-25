<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 90
-->
# jcode-Parity Gap Audit :: post-/loop swarm slice (test-modes lane, Turn 5)

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Operator directive (verbatim 2026-05-24 ~17:30Z, /loop turn 5, 5-agent swarm):** *"review all jcode features we are missing as well and activate swarm mode"*
> **Method:** ran `automations/jcode-parity-probe.ps1 -Json` (31-row empirical probe), separated real-fails from probe-defects, cross-referenced with `_shared-memory/knowledge/jcode-feature-matrix.md`.
> **Verification:** every row in §1 has a command + exit code or file-existence check executed THIS turn (no audit-by-memory).

## §1. Probe baseline (verified)

```
pass=25  real_fail=2  expected_fail=4  total=31
```

| Bucket | Count | Meaning |
|---|---|---|
| ✅ PASS | 25 | Feature reachable on disk + functional |
| 🟡 expected-FAIL | 4 | Already-queued (R23/R24/R25/R28) — PH13/PH12/PH14/Rust-mermaid-fork |
| 🔴 real-FAIL | 2 | R21 (RKOJ daemon idle), R29 (Qt picker overlay unmerged) |
| 🛠️ probe-defect fixed | 1 | R8 (Ruflo) — probe was checking stale paths |

## §2. R8 — Ruflo MCP probe defect (FIXED this turn)

**Symptom:** Probe v0.3 reported `R8 REAL_FAIL :: none of 3 candidates`. The 3 candidates were `~/.npm-global/node_modules/@ruvllm`, `%APPDATA%/npm/node_modules/@ruvllm`, `D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\agents`.

**Root cause:** Ruflo is actually installed at `D:\Sinister Sanctum\_shared-memory\external-imports\ruflo\` (verified `package.json` + `plugins/ruflo-agentdb/` both present; deferred-tool list this session also shows 200+ `mcp__ruflo__*` tools, which confirms the MCP is fully loaded by Claude).

**Fix (this turn):** `automations/jcode-parity-probe.ps1` updated — `$rufloPaths` now puts the Sanctum-internal install paths first; legacy npm-global paths kept as fallback.

**Verification:** re-ran probe — R8 flipped to `ok=true evidence=D:\Sinister Sanctum\_shared-memory\external-imports\ruflo\package.json`. Pass count went 24 → 25.

## §3. R21 — RKOJ Workstation daemon idle on :5077 (operator-action)

**Symptom:** `REAL_FAIL R21 :: tcp:5077 closed`.

**Root cause:** Per `jcode-feature-matrix.md` row 21, the Forge `workstation_panel.py` already auto-spawns `automations/window-manager/desktop_app.py` silently (CREATE_NO_WINDOW) when Forge presses F2 → `toggle_rkoj`. **But the daemon does NOT auto-start on session cold-start** — only on first F2 press inside Forge. Sessions that never open Forge (CLI-only, RKOJ Qt, sinister-term) leave the daemon idle.

**Recommendation (NOT executed — surface-to-operator, see §6):** Add daemon-availability check + opportunistic spawn to `start-sinister-session.ps1` between Phase 2 (mode prompt) and Phase 3 (spawn). One-line: if `tcp:5077` closed and `desktop_app.py` exists, fire it backgrounded via `Start-Process -WindowStyle Hidden`. Same pattern as the auto-push daemon.

**Why not auto-executed:** spawning a daemon from the launcher (vs. on first F2 press in Forge) is a behavior change with a non-zero blast radius (touches every launched session). Belongs on operator-action queue, not a self-applied edit in a swarm-coordinated turn.

## §4. R29 — In-Qt EVE picker overlay (pending-merge, operator-action)

**Symptom:** `REAL_FAIL R29 :: lib=True qt=False` — `tools/eve-picker/eve_picker_lib.py` exists, but `projects/rkoj/source/sinister_rkoj_qt/picker_overlay.py` does not on the current HEAD.

**Root cause (already documented):** `jcode-feature-matrix.md` §Audit corrections (2026-05-24T16:42Z, test-modes-verify lane) traced this to `rkoj-iter7` branch holding the unmerged commits (`eee6ef5` P3 + `89875ee` P5.5 + 4 others). The Qt overlay IS shipped, just not on `main`.

**Recommendation:** No new action. Already on operator-action queue as "rkoj-iter7 → main merge" per `CLAUDE.md` "current operator-actionable rows". Once merged, R29 flips to PASS without any code change.

## §5. Expected-fails (no-op confirmation)

| Row | Feature | Status | Next step |
|---|---|---|---|
| R23 | claude-hooks PH13 | 📋 planned | Forge PH13 — `claude-hooks-2.4.0` wrap. Forge owner. |
| R24 | Skill_Seekers PH12 | 📋 planned | Forge PH12 — `Skill_Seekers-3.6.0` wrap. Forge owner. |
| R25 | agentgrep PH14 | 📋 planned | Operator-gated cargo install. Forge owner. |
| R28 | sinister-mermaid-render Rust fork | 📋 planned | Fork `1jehuang/mermaid-rs-renderer` + Sinister rebrand. Sanctum owner. |

All four are tracked in `jcode-feature-matrix.md` with explicit `📋 planned` status. The probe's `expected_fail=true` flag intentionally suppresses them from the real-fail count.

## §6. Gap summary for operator

After this turn:

- **0 silent gaps** (everything either passes, is queued in matrix, or has a documented root cause)
- **2 operator-action items** (both pre-existing on queues, NOT new):
  - R21: RKOJ daemon auto-start on launcher (recommendation only; nice-to-have)
  - R29: `rkoj-iter7 → main` merge (already in operator queue)
- **0 new doctrine needed** (matrix + this audit cover it)
- **1 probe defect fixed** (R8 — committed this turn)

## §7. Composes-with

- `_shared-memory/knowledge/jcode-feature-matrix.md` — the 30-row capability map this audit references
- `_shared-memory/knowledge/jcode-eve-exe-parity-audit-2026-05-24.md` — original parity audit that spawned the probe
- `_shared-memory/knowledge/jcode-swarm-token-parity-audit-2026-05-23.md` — sinister-swarm verification
- `automations/jcode-parity-probe.ps1` — the empirical probe (R8 paths updated this turn)
- `_shared-memory/PROGRESS/test-modes.md` — turn log

## §8. Update protocol

This is a point-in-time gap audit. Re-run `jcode-parity-probe.ps1` on every meaningful change to the matrix; replace this file (don't accumulate). When a queued row (R23/R24/R25/R28) ships, flip its `expected_fail` in the probe to `$false` and bump matrix status.

---

## §9. /loop iter 4 addendum (test-modes lane, 17:43Z swarm-coordinated 5-lane fire)

> Operator directive (verbatim 17:21Z): *"i need you to make our claude memory smarter ... agents to fuck perfectly fully by them selves towards their goal and fully loop and continue to work nd not stop. just like in jcode cross reference. contracdict itself and what not until quality drops ... launch many parralel agents for this and active swarm now"* (utterance ts 2026-05-24T17:21:54Z, acked by test-modes 17:43Z)
>
> Operator directive (verbatim, image #1 same wave): *"i want you to use 100% of the claude plans perfectly. like where we are not ever loosing any tokens. like we use 100% up into the perfect point where it resets when we hit 100"*

### §9.1 Multi-account rotation — flipped `load-balance` → `burn-first` (LIVE, verified)

| What | Where | Status |
|---|---|---|
| `burn-first` strategy implemented | `automations/claude-accounts.ps1:184-192` | ✓ shipped (sibling lane v4 of this file) |
| `claude-accounts.json:5` value | was `load-balance`, now `burn-first` | ✓ live (sibling-lane edit confirmed via Read after my own edit attempt collided) |
| Smoke test | `Get-NextAvailableAccount` returned `name=operator strategy=burn-first` | ✓ verified this turn |
| Capacity | enabled_count=1 (only `operator`; leo/slot3/slot4 `enabled=false`) | 🟡 logic complete, capacity blocked |

**Why this satisfies the "100% plan utilization" directive:** `burn-first` keeps spawning on the anchor account (`cfg.default = operator`) until Anthropic 429s it (`rate_limited_until_utc` gets stamped), then auto-failover walks `accounts[]` ordered by `plan_tier` rank (max > pro > free) then `current_sessions` ASC. Zero downtime, no token left on the table at reset boundaries.

**What's still needed (operator-action — not auto-executable):** enable at least one additional account (Leo via `claude-accounts.ps1 -Action SetKey -Name leo`, or slot3/slot4) so the failover has somewhere to go. Until then, "burn-first" and "load-balance" are functionally identical (single-candidate set).

### §9.2 Per-project swarm/loop ask — wired, live, verified

| What | Where | Status |
|---|---|---|
| `Prompt-AgentModes -ProjectRec $projRec` | `start-sinister-session.ps1:984-1035` | ✓ shipped |
| Precedence: projects.json `default_modes` > env var > both-off | line 994-998 | ✓ shipped |
| Phrase injection (`SWARM MODE on:` / `LOOP MODE on:`) | `Build-Phrase` :959-964 | ✓ shipped |
| Env export to spawn shell | `SINISTER_SWARM_MODE` / `SINISTER_LOOP_MODE` | ✓ shipped (line 958 comment) |
| Skip-prompt env | `SINISTER_SKIP_MODES_PROMPT=1` honors locked defaults | ✓ shipped (line 999-1001) |
| `default_modes: { swarm:true, loop:true }` seeded | sanctum, sinister-panel, kernel-apk in projects.json | ✓ shipped Turn 1 |

### §9.3 Session-restore-like-never-closed (resume-context auto-inject)

| What | Where | Status |
|---|---|---|
| `Get-ResumeContextInject` builds inject from latest resume-point + heartbeat + utterance count | `start-sinister-session.ps1:880-928` | ✓ shipped |
| Inject appended to RESUME-mode phrase | line 952-953 | ✓ shipped |
| **Empirical PROOF** | this very session's opening prompt contains `RESUME CONTEXT (auto-injected, no manual read needed): last_heartbeat_focus="Turn 4 ..."` + `UNREAD_OPERATOR_UTTERANCES=23` | ✓ verified live |
| Window-position restore | `Get-SavedWindowPosition` + `Test-WindowPositionOccupied` :1044-1058 | ✓ shipped |

### §9.4 Quality-degradation guard ("until quality drops")

Operator's "cross reference. contradict itself ... until quality drops" maps to the `no-bullshit` doctrine **rule 8** (`_shared-memory/knowledge/no-bullshit-tested-before-claimed-doctrine-2026-05-23.md`):

> "Expansion has quality-degradation limits. 10 signals (brain >150 rows, PROGRESS >300 KB, resume-points >20/lane, queue >25 rows, plans >12 active, doctrine with >5 'composes with' links, script >1500 lines, cold-start >10 steps, same bug fixed 3+ times, end-of-turn >40 lines). When ANY fires: STOP expanding, consolidate first."

Plus the `loop-quality-gate` referenced in CLAUDE.md cold-start step 10 (forever-improve switches to consolidation when DEGRADED). **Coverage:** ✓ shipped. The "self-contradict" half (counter-arguments) is the 16:06Z utterance (separate row, owner=Sanctum master per `_shared-memory/counter-arguments.jsonl` existence).

### §9.5 Updated gap summary (post-Turn-5 + Turn-4-/loop-iter-4)

| Gap | Status | Owner |
|---|---|---|
| Multi-account ROTATION LOGIC | ✓ shipped (burn-first live) | done |
| Multi-account CAPACITY (only 1 enabled) | 🟢 OPERATOR-ACTION — enable Leo/slot3/slot4 | operator |
| Per-project ask | ✓ shipped | done |
| Resume-restore-like-never-closed | ✓ shipped + empirically proven | done |
| Quality-degradation guard | ✓ shipped (no-bullshit rule 8 + loop-quality-gate) | done |
| Self-contradict / counter-arguments | 🟡 in-flight (separate utterance, separate lane) | Sanctum master |
| R21 RKOJ daemon auto-spawn on launcher | 🟢 OPERATOR-ACTION (nice-to-have) | operator |
| R29 rkoj-iter7 → main merge | 🟢 OPERATOR-ACTION (queued) | operator |

**Bottom line:** all `test-modes`-visible code-layer jcode parity is now ✓. Remaining items are capacity (operator-only) or owned by sibling lanes. No silent gaps in this lane's scope.

### §9.6 Verification evidence

```
[smoke 17:43Z] PS> . claude-accounts.ps1; Get-NextAvailableAccount
selected=operator strategy=burn-first enabled_count=1

[file 17:43Z] claude-accounts.json:5
"rotation_strategy":  "burn-first",

[prompt 17:42Z] this session opening prompt contains:
RESUME CONTEXT (auto-injected, no manual read needed): last_heartbeat_focus="Turn 4..." UNREAD_OPERATOR_UTTERANCES=23
```
