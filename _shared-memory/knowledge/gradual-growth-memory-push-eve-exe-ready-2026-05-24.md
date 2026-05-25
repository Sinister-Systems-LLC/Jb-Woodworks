<!-- Author: RKOJ-ELENO :: 2026-05-24 -->

<!-- decay:
  category: preference
  confidence: 0.9
  reinforcements: 0
  half_life_days: 180
-->
# Gradual-growth + memory-push + EVE.exe-ready doctrine

**Created:** 2026-05-24 20:04Z
**Authority:** Operator hard-canonical 2026-05-24T20:02Z (verbatim):
> *"ship fleet-autostart.ps1 next and complete everything else in parralel. make sure as you update memory you push to agents and its ready to go in the eve exe so we can grow gradually and never stop thats the goal. update memory"*

---

## The goal (operator's words)

**Grow gradually. Never stop.** Every memory update lands in the agents in-flight. Every new tool is reachable from EVE.exe on the next spawn. No big-bang cutovers, no shipped-but-undiscoverable additions, no operator-must-restart-everything moments.

---

## Three binding rules for every Sanctum lane

### Rule 1 — Memory updates push to live agents

When a doctrine / fix / tool / command lands:

1. **Brain entry** (or doctrine update) → `_shared-memory/knowledge/<slug>-<date>.md` + index in `_INDEX.md`.
2. **Push to fleet** via `automations/fleet-update.ps1 -Action Push -Kind doctrine|fix|tool|feature -Priority high|normal|low -Message "..."`. Live agents poll the channel per CLAUDE.md cold-start step 11.
3. **Inbox affected lanes directly** for lane-specific deliverables: `_shared-memory/inbox/<their-slug>/<UTC>-from-<your-slug>-<subject>.json`.

Don't leave updates in a private branch / local TODO file / "I'll push it later" buffer. The fleet doesn't know until the channel knows.

### Rule 2 — Ready in EVE.exe on next spawn

Every new tool / script / capability must be:

1. **Reachable from a path EVE.exe already inspects** (`automations/` for ps1+py, `projects.json` for project entries, `bots/` for MCP servers).
2. **Discoverable without re-running build steps the operator doesn't know about** — if the tool needs a one-time `Register-ScheduledTask` or `pip install`, document it in the script's header AND in the next-iter PROGRESS row AND queue it for the operator if elevation is required.
3. **Composable with `start-sinister-session.ps1`** if it changes per-spawn behavior — wire via flag (`-SINISTER_SKIP_*` env-var gates), not by silent fork.

### Rule 3 — Gradual, never stop

1. **Ship verified small wins per iter** — no "rewrite the world" PRs. Per-iter shipped = 3–8 small items (vs 1 monolithic).
2. **Never end a loop turn with queueable work remaining** (composes with `loop-mode-continuous-iteration-2026-05-24`). End-of-turn lists `Shipped (verified)` + `Open queued (next iter)`.
3. **Honor the prune-as-add doctrine** — every add prunes a stale or duplicate counterpart (composes with `no-bullshit` rule 8 quality-degradation limits).
4. **Forever-improve checkpoint** every meaningful unit — `automations/forever-improve.ps1 -Action Review` against the work, log finding, act/dismiss.

---

## Implementation shipped same turn

| Component | Purpose | Verified |
|---|---|---|
| `automations/fleet-autostart.ps1` | Wait for Docker Ready → warm bot-lifecycle → run mesh + heartbeat sweeps → push announce row | shipped + smoke-tested |
| `automations/fleet-update.ps1` | Push channel (already shipped; bugfix this turn) | smoke OK |
| `automations/mesh-coordinator.ps1` | File-lock + TTL for "don't toe-step on shared edits" | smoke 6/6 |
| `automations/bot-lifecycle.ps1` | Refcount Acquire/Release/Sweep — bots SLEEP at refcount=0, wake on next Acquire | smoke 7/7 |
| `automations/heartbeat-sweep.ps1` | 24h+ stale heartbeats → `_archive/<yyyymmdd>/` | first run pruned 25 |
| Docker Desktop `AutoStart=true` | Boot precondition for fleet-autostart | flipped + verified |
| Brain `_INDEX.md` row for this doctrine + mesh-coord doctrine | Discoverability | both indexed |
| `OPERATOR-ACTION-QUEUE.md` row 19:48Z | Memory-backbone canonicalization decision (gated) | open |

---

## Anti-patterns

1. **Shipping a tool without a fleet-update push.** Live agents won't see it until cold-start; in a 5-agent loop session that's 30+ minutes of blind work.
2. **Ad-hoc bot spawn outside bot-lifecycle.** Bypasses refcount; can leave orphan processes after agent close.
3. **Editing `start-sinister-session.ps1` without checking for sibling lanes' in-flight edits** (use mesh-coordinator `Check` first).
4. **Skipping the index row in `_INDEX.md`.** Brain entries that aren't indexed get lost; doctrine-rot.
5. **Adding a step to CLAUDE.md cold-start without pruning another.** Rule 8: >10 steps = consolidation signal. Fold into existing steps.

---

## Composes with

- `no-bullshit-tested-before-claimed-doctrine-2026-05-23` (rules 4, 5, 8 — prune-as-add quality)
- `mesh-coordination-and-resource-lifecycle-2026-05-24` (the lock + refcount primitives)
- `resource-refcount-cleanup-sleep-wake-doctrine-2026-05-24` (process-level lifecycle; complementary)
- `fleet-update-channel-doctrine-2026-05-24` (the push surface)
- `loop-mode-continuous-iteration-2026-05-24` (continuous in-turn loop, no ScheduleWakeup-and-stop)
- `sanctum-scope-discipline-2026-05-24` (this doctrine is high-level — fleet-shape, not per-project work)
- `agent-identity-eve` (EVE is the persona on every spawn surface this doctrine references)

---

## Verification

```powershell
# 1. Fleet-autostart status
powershell -File automations/fleet-autostart.ps1 -Mode Status

# 2. Boot-time dry-run (no side effects on Status mode)
powershell -File automations/fleet-autostart.ps1 -Mode WarmOnly

# 3. Fleet-update visibility
powershell -File automations/fleet-update.ps1 -Action List -Tail 5 -Slug <your-slug>

# 4. EVE.exe-ready check
ls "D:\Sinister Sanctum\automations\eve-launcher\dist\EVE\EVE.exe"   # binary present
Get-Content "$env:APPDATA\Docker\settings-store.json" | Select-String 'AutoStart'   # true
```
