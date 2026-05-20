# Author: Sinister Sanctum master agent (test, Claude) :: 2026-05-20

# Topic: Autonomous-loop launcher mode — full plan-review + scope-synthesize + /loop self-execute

> Status: doctrine + implemented
> Tags: standing-rule, launcher, auto-mode, autonomous-loop, plan-review, scope-plan, /loop, self-paced, taskcreate-driven, 5-check-gate, canonical-16, canonical-19, knowledge-review-and-grow, no-stop, session-start
> First codified: 2026-05-20 (operator directive mid-session)
> Composes with: `expand-mode-contract` + `multi-pass-planning` + `complete-plan-autonomous-mode` + `keep-working-until-done` (canonical-19) + `KNOWLEDGE-REVIEW-AND-GROW contract` + `launcher-trophy-case-integration`

## Operator directive (verbatim 2026-05-20)

> *"the session staret needs to add back the detailed plans when it creates the session for the agent to review everything it needs to do and makes a complete autonous plan to complete the project scope and the /loop to make sure it does not stop. add this as option, use loop. complete this and place new bat on desktop create plan to do all of this ll autonmous"*

Three intertwined requirements:

1. **Detailed plans injected at session-start** so the agent reviews everything before writing its first TODO (vs. the prior 'dev' mode which just said "read CLAUDE.md and ask what we're working on").
2. **Complete autonomous scope-plan** — agent synthesizes ONE plan covering project scope (what's shipped, what's open, what's operator-gated, what's sibling-lane, what's deferred).
3. **`/loop` keeps the agent working** until done — invokes the `loop` skill with no interval (model self-paces) so it cycles through TaskList without stopping.

This is the natural extension of `expand-mode-contract` (audit + forward-plan + hand-off) + `complete-plan-autonomous-mode` (canonical-16: plan paired with prompt + auto-mode for completion) into a single launcher-injected mode.

## The 5-phase autonomous-loop contract

The `'auto'` BuiltinPhrase at `automations/start-sinister-session.ps1::BuiltinPhrases['auto']` instructs the agent through 5 phases:

### PHASE 1 — Plan-review (read EVERY plan-bearing file)

Before writing ANY TaskCreate row:

- `_shared-memory/MASTER-PLAN.md` (full file; every row tagged with project slug or adjacent lane terms)
- `_shared-memory/plans/<PROJECT>-*/` (every subdir; latest forward-plan.md + pass-1-draft.md + plan.json by mtime)
- `<ROOT>/CLAUDE.md` (full lane scope + Existing research + Research gaps)
- `<ROOT>/.claude/memory/` (every file)
- `_shared-memory/PROGRESS/<AGENT>.md` (top 8 entries — what was last in flight + rolling cadence)
- `_shared-memory/knowledge/_INDEX.md` (every row tagged with project slug)
- `_shared-memory/OPERATOR-ACTION-QUEUE.md` (project-relevant rows)
- `_shared-memory/inbox/<your-slug>/` (every JSON; surface cross-agent asks)

### PHASE 2 — Synthesize complete autonomous scope-plan

Write ONE plan to `_shared-memory/plans/<PROJECT>-auto-<UTC>/master-plan.md` with 5 sections:

1. **Shipped** (last 7 days; commit hashes for every claim).
2. **Open master-actionable** — each row carries `EXACT-INSTRUCTIONS` + `EXPECTED-OUTPUT` + `VERIFICATION` + `COMMIT-MESSAGE`.
3. **Operator-gated** — each row carries the exact one-liner unblock the operator needs to run/decide.
4. **Sibling-lane** — cross-agent asks needed; do NOT touch sibling source (canonical-10).
5. **Deferred** — with named blocker (env-var value, hardware arrival, classifier hard-stop, etc.).

### PHASE 3 — TaskCreate every master-actionable row

Mirror section 2 of the scope-plan into the TaskList. Mark `in_progress` when claiming.

### PHASE 4 — Invoke `/loop` (no interval, self-paced)

The `loop` skill cycles continuously per `LOOP DISCIPLINE` (the 6-step ritual):

1. TaskUpdate just-finished → completed
2. TaskList → first pending master-actionable row
3. If found: claim + BEGIN.
4. If TaskList empty: top URGENT row in scope-plan section 2; add to TaskList; claim; BEGIN.
5. Operator-only URGENT row → skip + take next; never wait.
6. Backlog exhausted → brain-capture from session patterns crossed.

### PHASE 5 — 5-check completion gate per iteration

Every visible deliverable gates on:

1. Explicit ask addressed on disk (`Test-Path` the deliverable).
2. TaskList completed-or-deleted-or-deliberately-deferred.
3. PROGRESS appended with the milestone.
4. MASTER-PLAN flags match disk reality.
5. Next-slice surface refreshed.

Operator-only gates surface via the end-of-turn message; the loop **continues** with the next master-actionable item. Silence = bug. "Awaiting input" = bug. "Should I continue?" = bug.

## When to use auto-mode vs other modes

| Mode | When | What the spawned agent does |
|---|---|---|
| `dev` | Single feature/fix you want to scope yourself | Reads CLAUDE.md + asks what to tackle |
| `audit` | Find issues / drift / push-readiness | Surfaces secrets / stale TODOs / broken tests |
| `explore` | Open-ended research | 3 surprising findings → asks direction |
| `debug` | Specific failure mode | Reads BREAKTHROUGH-*.md + asks which mode |
| **`auto`** | **Full project scope, want it to run unattended** | **Reviews every plan + builds scope-plan + /loop** |

Auto-mode is for: "complete everything for this project" sweeps, post-EXPAND-mode RESUME walks, long unattended sessions, fleet-wide drift sweeps. It's NOT for: small targeted fixes (use `dev`), exploratory questions (use `explore`), production deploys with reversibility walls (use `deploy` with operator-paced gates).

## Picker integration

Operator launches `Start-Sinister-Session.bat` (or `Start-Sinister-Auto-Session.bat` on Desktop for one-click) and picks:

- Q2 / objective: **`9) auto    AUTONOMOUS LOOP :: review all plans + scope-plan + /loop`** — alongside the existing 1-8 options.

Custom prompts renumbered to start at `n=10` (was `n=9`) — see PS1 `modeOpts[8]` + `modeMap['9']`.

The Desktop bat `Start-Sinister-Auto-Session.bat` passes `-Mode auto` to the canonical PS1, so the picker still asks for project + agent name + accent + focus but the mode is locked.

## Anti-patterns

- **Auto-mode without scope-plan write.** If the agent skips PHASE 2 (writing `master-plan.md`), there's no append-only artifact the next session can resume from. The `/loop` would just churn TaskList without the durable plan. ALWAYS write the scope-plan file FIRST.
- **`/loop` with a time interval.** Operator's directive was explicit: "to make sure it does not stop" — model-paced is correct. `/loop 5m /foo` would force a heartbeat every 5 min regardless of work state. Use bare `/loop` (no interval) so it self-paces between deliverables.
- **TaskList without project scope.** A 3-row TaskList that ignores 20 open MASTER-PLAN rows is a scoping bug. The PHASE 2 scope-plan MUST cover the full project, not just the obvious-next-thing.
- **Stop on operator-gate.** When an operator-only row is at the top of the TaskList, SKIP it (mark "blocked: <gate>" in the row) and take the next master-actionable. Never block the loop on an operator decision the agent can route around.
- **Skipping PHASE 1 plan-review.** "I'll just check MASTER-PLAN" is not the contract. The 8-file review is what catches sibling-lane asks + cross-agent inbox + stale-plan drift. Skip it and the scope-plan misses 30%+ of the actual work.
- **Adding new bat for every variant.** The Desktop ONE-bat `Start-Sinister-Auto-Session.bat` is the durable entry-point. NEW work goes through the picker, not new bats.

## Where it lives

| File | Role |
|---|---|
| `automations/start-sinister-session.ps1::BuiltinPhrases['auto']` | The 5-phase phrase injected into the agent's cold-start prompt |
| `automations/start-sinister-session.ps1::modeOpts[8]` | The `9) auto` picker row |
| `automations/start-sinister-session.ps1::modeMap['9']` | Numeric picker → mode-key mapping |
| `C:\Users\Zonia\Desktop\Start-Sinister-Auto-Session.bat` | One-click Desktop entry-point |
| `D:\Sinister Sanctum\tools\session-launcher\Start-Sinister-Auto-Session.bat` | Canonical tree mirror |

## Cross-references

- `expand-mode-contract` — EXPAND audit + forward-plan produces the artifacts auto-mode reviews in PHASE 1.
- `complete-plan-autonomous-mode` (canonical-16) — pairing plan with auto-mode for no-time-lost completion; auto-mode is the durable launcher implementation of canonical-16.
- `keep-working-until-done` (canonical-19) — the 5-check gate + LOOP DISCIPLINE auto-mode invokes.
- `KNOWLEDGE-REVIEW-AND-GROW contract` — PHASE 1 reads brain `_INDEX.md` per the contract's session-start requirement.
- `launcher-trophy-case-integration` — the launcher's other cold-start surface; auto-mode composes with the trophy case.
- `audit-shipped-not-flipped` — auto-mode's PHASE 1 catches "shipped but not flipped" drift by reviewing PROGRESS vs MASTER-PLAN.

## Related topics

- [`expand-mode-contract`](./expand-mode-contract.md)
- [`multi-pass-planning`](./multi-pass-planning.md)
- [`complete-plan-autonomous-mode`](./complete-plan-autonomous-mode.md)
- [`launcher-trophy-case-integration`](./launcher-trophy-case-integration.md)
- [`audit-shipped-not-flipped`](./audit-shipped-not-flipped.md)
- [`cross-agent-doctrine-rollout-pattern`](./cross-agent-doctrine-rollout-pattern.md)
