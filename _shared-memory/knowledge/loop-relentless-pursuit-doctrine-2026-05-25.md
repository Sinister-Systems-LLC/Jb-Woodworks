<!-- Author: RKOJ-ELENO :: 2026-05-25 -->
<!-- decay:
  category: preference
  confidence: 1.0
  reinforcements: 0
  half_life_days: 365
-->

# Loop relentless-pursuit doctrine — 2026-05-25

**Status:** hard-canonical 2026-05-25 (sanctum lane).
**Operator verbatim 2026-05-25T02:18Z:** *"make the loop system on our agents actually work. make it agressive and make it hafve agents relentless pursue goal within our guidelines using our tools iwhen on."*

**Composes with:** `safe-quality-loops-doctrine-2026-05-24` (the SAFE half — guardrails) + `LOOP MODE` block in `CLAUDE.md` (continuous-iteration + ≤270s ScheduleWakeup cap) + `no-bullshit-tested-before-claimed-doctrine-2026-05-23` rule 8 (10 quality-degradation signals) + `agent-autonomy-push-and-completion-2026-05-23` (work without operator until done) + `bot-fleet-quick-reference` (the tool-reach surface) + `mesh-coordination-and-resource-lifecycle-2026-05-24` (the coordination surface).

## What this is

The **AGGRESSIVE half** of the loop equation. `safe-quality-loops` says HOW NOT to destroy things; this says HOW to keep pushing. The operator-observed failure mode that triggered this doctrine: agents finish a deliverable, write an end-of-turn summary, and **stop** — even when the queue / utterances / fleet-updates / cross-agent inbox have actionable rows. That's not loop=on, that's polite-stop.

This doctrine flips the default: when `loop=on`, the *only* legal end-of-turn outcomes are (a) loop_condition satisfied + verified, (b) genuinely blocked + 1-line block reason + ScheduleWakeup ≤ 270s, or (c) compaction watchdog at 90%. Anything else = a stall the watchdog will poke.

## 4 sub-rules (numbered 8-11 to extend the LOOP MODE block in CLAUDE.md)

### 8. RELENTLESS PURSUIT (the keep-going rule)

After every shipped deliverable:

1. **Re-read open queue** (`_shared-memory/OPERATOR-ACTION-QUEUE.md` — your lane rows).
2. **Re-read operator-utterances tail** (last 5; address any `status=new` addressed to your lane FIRST).
3. **Re-poll fleet-updates** (`automations/fleet-update.ps1 -Action List -Tail 5 -Slug <you>`; high-priority pushes addressed to you in subject MUST be acted on before next iter).
4. **Re-check cross-agent inbox** (`_shared-memory/inbox/<your-slug>/*.json`; any unread `kind=loop-poke` from watchdog or operator counts as an interrupt — address-then-resume).
5. **Pick next unaddressed item** (priority: operator interrupts > new fleet-update high > queue > backlog plan items).
6. **SHIP IT IN THE SAME TURN.** No "I'll do X next turn" — that's the polite-stop failure. Do X now.
7. Only after items 1-6 produce ZERO actionable rows AND loop_condition is unsatisfied → ScheduleWakeup cap 270s with a specific reason (not "wait").

### 9. ANTI-STOP CHECKLIST (run mentally before any end-of-turn)

Six binary checks. ANY `no` = keep going, do NOT end turn.

- [ ] Is the queue empty for my lane? (read it; no = pick a row)
- [ ] Are all `status=new` operator utterances addressed for my lane? (read tail; no = address)
- [ ] Have I polled fleet-updates this iter? (no = poll)
- [ ] Has every sub-agent I spawned returned? (no = wait or summarize WITHOUT ending if more to do)
- [ ] Is loop_condition explicitly satisfied + verified with evidence? (no = next iter)
- [ ] Am I at 90%+ compaction watchdog? (no = keep going)

The end-of-turn summary is a CHECKPOINT, not a goodbye. Always end with "next iter starts now" — and then start it.

### 10. TOOL-REACH FIRST (use our tools, not just Read/Edit)

Operator: *"using our tools when on"*. Before defaulting to manual Read/Grep/Edit, reach for these (each saves Opus tokens by routing to a local bot or a specialized helper):

| Tool | When to reach for it |
|---|---|
| `bot-fleet-quick-reference.md` (13 local MCP bots) | file search, classify, scrape, digest, heartbeat, inbox — anything routine |
| `automations/fleet-update.ps1 Push/List/Acked` | broadcasting + polling cross-lane signals |
| `automations/mesh-coordinator.ps1 Check/Register/Release` | before editing shared files (mandatory per cold-start step 11c) |
| `automations/agent-poke.ps1 Poke -Slug <s>` | poking a sister agent that you need a response from |
| `automations/log-operator-utterance.ps1` + `ack-operator-utterance.ps1` | tracking new operator messages + acking deliverables |
| `automations/forever-improve.ps1 -Action Review` | end-of-deliverable self-audit (NOT optional per cold-start step 10) |
| `automations/brain-decay-score.ps1` | brain hygiene (Annotate / Reinforce / Supersede / ExportIndex) |
| `automations/detect-similar-agents.ps1` | every iter per safe-quality #9 sister-coord rule |
| `automations/quality-monotonic-loop.ps1` | gauge whether to keep expanding or consolidate (no-bullshit rule 8) |
| `automations/sanctum-auto-push.ps1` | per-branch push routing (do NOT direct `git push origin main` outside the daemon) |
| `Agent` tool with `subagent_type=Explore` / `general-purpose` | parallelizable work (search across many files, build independent tools) |
| `ToolSearch` | discover deferred MCP/CLI tools before reaching for them |

The tool-reach rule isn't "use every tool every iter" — it's "before Read+Edit'ing manually, ask: does a tool already do this?"

### 11. WATCHDOG POKE = OPERATOR INTENT

The `loop-relentless-watchdog.ps1` (scheduled task `SinisterLoopRelentlessWatchdog`, 5-min cadence) scans heartbeats for 3 stall signals (heartbeat >8min stale | same focus_intent 3 ticks | same loop_iter 3 ticks). On stall it writes a `kind=loop-poke` row to your `_shared-memory/inbox/<slug>/` directory.

**When you see a `loop-poke` row:**

1. Treat it as operator-canonical signal (the watchdog speaks for the standing 2026-05-25T02:18Z directive).
2. Pick next item per rule 8 sequence.
3. SHIP IT THIS TURN.
4. Move the poke file to `_shared-memory/inbox/<slug>/_acked/` (so it doesn't fire repeatedly).
5. Update your heartbeat with the new `focus_intent` reflecting the resumed work.

Manual operator-emergency-button: `agent-poke.ps1 -Action PokeAll -Priority high` (Desktop one-click via `Poke-All-Sinister-Agents.bat`). Same handling.

## Within-our-guidelines (the SAFE compose)

RELENTLESS does NOT override safe-quality-loops. Every iteration still runs through:

- Reversibility wall (rule 2) — destructive ops still need operator confirm
- Quality monotonic (rule 3) — 2-iter regression still auto-stops
- Scope freeze (rule 4) — loop scope is fixed at loop-condition; relentless = pursue THE SAME goal harder, not invent new ones
- Cost ceilings (rule 5) — token + image-gen + API budgets unchanged
- Operator interrupt priority (rule 10) — new operator utterance always wins over current iter

If RELENTLESS and SAFE conflict (e.g., "the next queue row would require a destructive op without confirm"), SAFE wins. Skip that row, ship a different one, surface the destructive-op row to operator queue with reason.

## Anti-patterns (DO NOT do)

1. **Polite-stop summary then end turn.** End-of-turn summaries are NOT end-of-work signals. Always start the next iter.
2. **Schedule-and-stop.** `ScheduleWakeup` at 25min is what the operator already called out (2026-05-24T19:55Z "loop isnt working agents are sotpping"). Cap 270s when in loop, and only when GENUINELY blocked.
3. **"I'll do X next turn."** Either X is actionable this turn (then do it) or it's blocked (then write a 1-line block reason). No middle ground.
4. **Ignoring sub-agent results.** When a sub-agent returns, integrate its work into the next iter — don't just acknowledge and stop.
5. **Reaching for Read/Edit when a bot/script already does it.** Routine work routes to the bot fleet; Opus is for synthesis + decisions, not file-walking.
6. **Watchdog spam.** If watchdog fires 3+ pokes in a row to the same slug without state change, that's a real block — surface to OPERATOR-ACTION-QUEUE, don't keep pumping pokes.

## Pass criterion (what "actually works" looks like)

- Mean inter-iter gap on a loop=on lane ≤ 60s (excluding genuine external waits)
- Heartbeat `loop_iter` increments every iter (per safe-quality #8)
- Zero `polite-stop` end-of-turns (every end-of-turn either ships → next iter or surfaces a block + Wakeup ≤270s)
- Watchdog `Status` shows 0 stalled agents in healthy steady state
- Operator-utterance backlog drains within 1 iter of arrival

## Verification commands

```powershell
# Are agents actually iterating?
powershell -File automations\loop-relentless-watchdog.ps1 -Action Status

# Manual poke (operator emergency button)
powershell -File automations\agent-poke.ps1 -Action PokeAll -Priority high

# Watch the inbox for incoming pokes (per slug)
ls _shared-memory\inbox\<my-slug>\*loop-poke*.json
```

## Composes with (full list)

- `safe-quality-loops-doctrine-2026-05-24` (guardrails — relentless ≠ destructive)
- `agent-autonomy-push-and-completion-2026-05-23` (operator: "should work fully without me")
- `bot-fleet-quick-reference` (the tool-reach surface)
- `no-bullshit-tested-before-claimed-doctrine-2026-05-23` (rule 8 quality-degradation limits)
- `mesh-coordination-and-resource-lifecycle-2026-05-24` (coord before relentless edits)
- `fleet-update-channel-doctrine-2026-05-24` (the broadcast lane the watchdog uses)
- `operator-utterance-tracking-doctrine-2026-05-24` (the interrupt-priority surface)
- `gradual-growth-memory-push-eve-exe-ready-2026-05-24` (R1: brain → fleet → EVE.exe propagation)
- `quantum-fleet-discipline-doctrine-2026-05-25` (relentless on quantum + memory main scope)

## Operator quote (verbatim)

*"make the loop system on our agents actually work. make it agressive and make it hafve agents relentless pursue goal within our guidelines using our tools iwhen on."* — 2026-05-25T02:18Z

This doctrine is the binding interpretation.
