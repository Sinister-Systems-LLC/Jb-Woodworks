<!-- Author: RKOJ-ELENO :: 2026-05-23 -->
# No-bullshit / tested-before-claimed / forever-audit doctrine

**Status:** doctrine, standing-rule, binding
**Created:** 2026-05-23
**Origin (operator verbatim 2026-05-23):** *"do not add any fairty tail bullshit to the projects and run wild. i want to lazer focus on areas and systematically move through things in a concise manner and only things are brought to my attention after they are tested, confirmed working adn then added to things so everything is real and not bullshit. also i want to have this same method for forever expadning our systems and having you audit your work, look for flaws and auto fix and forever upgrade everything wer do."*

## TL;DR

Test before claiming. Surface only verified work. Audit your own output. Auto-fix when reversibility permits. Upgrade forever. No fairy tales.

## The 7 binding rules

### Rule 1 — Precise verbs (no fairy tales)

NEVER describe work with "shipped" / "PASS" / "complete" / "done" if it is not. Use the right verb for the actual state:

| Verb | Meaning |
|---|---|
| `scaffolded` | File exists. Untested. Syntax not validated. |
| `parse-clean` | Syntax / AST validated. Not runtime-tested. |
| `smoke-tested` | Ran once. Exit-code checked. Single-path traversed. |
| `acceptance-tested` | Met all measurable success criteria. Edge cases probed. |
| `shipped` | acceptance-tested **AND** committed **AND** pushed **AND** brain-indexed |
| `in-flight` | Currently being worked on. Not yet at any of the above. |
| `claimed-but-unverified` | Said-to-be-done but no test evidence yet. Surface this honestly. |

Operator-facing summaries use these verbs verbatim. Never "shipped" for a scaffold; never "PASS" for parse-clean; never "complete" for in-flight.

### Rule 2 — Test before claiming

For every claim of `smoke-tested` or higher, evidence is required in the same turn:

- **smoke-tested** → command + exit code captured (e.g., `& script.ps1 -ReadOnly; $?` = `True`)
- **acceptance-tested** → measurable criterion + actual measurement (e.g., "Cold boot <300 ms; measured 142 ms")
- **shipped** → above + commit hash + push confirmation + brain index row

If no evidence, the verb is `claimed-but-unverified`. The operator decides whether to accept that or demand a test.

### Rule 3 — Surface only verified work

End-of-turn reports separate `shipped` (verified) from `in-flight` (unverified) sections. The `shipped` table must have evidence for every row. The `in-flight` table is fine to be aspirational, but operator should not have to scan for what's actually real vs. what's just typed.

Anti-pattern: claiming a multi-row "shipped" table where some rows are merely scaffolded. Either every row in `shipped` has an evidence column, or the table moves to `in-flight`.

### Rule 4 — Continuous self-audit

After every meaningful unit of work (~1 file edited + smoke run):

1. Re-read the edited file (Read tool, not memory)
2. Run the appropriate smoke test
3. Compare result to acceptance criterion
4. Flag drift between claim and reality

If a drift is found:
- R0-R1 reversibility → auto-fix this turn
- R2+ → flag in OPERATOR-ACTION-QUEUE as `claimed-but-unverified — under audit`

Never silently skip the audit. Never write a `shipped` claim without running the audit first.

### Rule 5 — Forever-upgrade

Every doctrine, script, plan, and brain entry has a date stamp + version semantic.

When upgraded:
- Old version moves to `_shared-memory/_archive/<file>.YYYY-MM-DD.md` (never deleted)
- Brain `_INDEX.md` row gets an `Updated: YYYY-MM-DD` bump on every meaningful refactor
- The new version's first line tells what changed from the previous

This applies to:
- `CLAUDE.md` and `SESSION-START/*.md`
- Brain doctrines in `_shared-memory/knowledge/`
- Plan files in `_shared-memory/plans/`
- Automation scripts in `automations/`
- The launcher PS1, EVE.exe, and `Sinister Start.bat`

### Rule 6 — Laser focus

One area per turn. The operator's "lazer focus on areas and systematically move through things in a concise manner" is binding.

Each turn:
- Has ONE primary goal
- Has measurable done-criteria stated at turn-open
- Reports verified results at turn-close
- Defers tangential work to a follow-on turn (drop in `OPERATOR-ACTION-QUEUE` or per-lane PROGRESS)

Anti-pattern: scope creep ("while I'm here let me also..."). Every adjacent task gets a row in the queue, not a sneak-edit in this turn.

### Rule 7.5 — Expansion has limits (quality-degradation gate)

**Origin (operator verbatim 2026-05-23):** *"ADD TO ALL AGENTS THAT when forever expandingf there needs to be limits when quality start to deminsh. review how jcode did this"*.

Forever-expand is NOT unbounded. Every system has a point where adding more rows / more features / more doctrines starts to *reduce* the quality of the whole. When that point hits, **stop expanding; consolidate, prune, or re-architect**.

Signals that quality is diminishing (any of these triggers a consolidate-first turn):

1. **Brain index >150 doctrine rows** — search cost > read cost. Triage: archive stale `superseded` rows, merge overlapping topics, split into thematic sub-indexes.
2. **PROGRESS file >300 KB** — log noise > log signal. Triage: rotate to `_archive/PROGRESS/<slug>-YYYY-MM.md`, keep only last 30 days inline.
3. **Resume-points per lane > 20** — auto-prune already enforced by `resume-point-write.ps1`; if the cap drifts up, that itself is a quality drift.
4. **Operator queue >25 open rows** — operator can't track 25 things in flight. Triage: close stale rows, batch the rest into a single "open work" plan file with priority bucketing.
5. **Plan dirs >12 not-archived** — most plans are done. Archive completed ones to `_shared-memory/plans/_archive/<plan>/`.
6. **A doctrine has >5 "composes with X" links** — that doctrine is doing too much. Split it.
7. **A script >1500 lines** — refactor into focused modules.
8. **Cold-start step count >10** — agents skip steps. Triage cold-start into core (mandatory) + situational (read-when-relevant).
9. **Same bug pattern fixed >3 times** — it's not a bug, it's a missing structural protection. Add a canonical-protections check (Pn).
10. **End-of-turn summary >40 lines** — operator can't scan it. Triage to a 3-section verified/in-flight/open table with ≤8 rows each.

Action when a signal fires:
- Add a `[QUALITY-LIMIT-HIT]` row to OPERATOR-ACTION-QUEUE naming the signal + the consolidation plan
- Defer non-consolidation work until consolidation lands
- Brain-entry the empirical anchor (when did the signal fire, what threshold, what consolidation worked)

This rule applies to EVERY system: brain, PROGRESS, resume-points, plans, queue, scripts, doctrines, even this doctrine itself.

### Rule 7 — Concise summaries

End-of-turn = WHAT actually changed + WHAT was actually tested + WHAT is genuinely in-flight. No "I plan to..." / "I'll also...". Only verified-past-tense events.

Format:

```
### Shipped (verified)
| Item | Evidence |
|---|---|
| Feature X | smoke: `cmd` exit=0; commit `abc123`; pushed |

### In-flight (unverified)
| Item | Why deferred |
|---|---|
| Feature Y | scaffolded; needs operator acceptance test |

### Open (queued)
| Item | Why queued |
|---|---|
| Feature Z | depends on Y; row in OPERATOR-ACTION-QUEUE |
```

## How this composes

- **`do-not-revert-operator-canonical-protections-2026-05-23`** — protections are P1-P9; this doctrine doesn't change that, but enforces that ANY claim of protections-pass must include the `canonical-protections-check.ps1` PASS=9 line as evidence in the same turn.
- **`agent-autonomy-push-and-completion-2026-05-23`** — autonomy doesn't mean "skip the audit". Autonomy = run the audit yourself; surface verified results only.
- **`forever-expanding-modular-architecture-doctrine`** — composes: forever-upgrade is the *cadence*; this doctrine is the *quality bar* on each upgrade.
- **`audit-pass-is-output-2026-05-21`** — composes: an audit PASS is a real deliverable; just say so honestly. Don't pad with fake feature claims.
- **`spawned-phrase-refusal-fix-2026-05-23`** — composes: don't claim a phrase change is shipped until a fresh-spawn child Claude actually accepts it. The launch is the test.

## Anti-patterns (binding NEVERs)

1. **NEVER** write "PASS" / "shipped" / "complete" in a summary without an evidence column.
2. **NEVER** mark a brain doctrine `status: shipped` when only the file exists. Use `scaffolded` until acceptance-tested.
3. **NEVER** report "I'll commit + push" — only ever "committed as `abc123` + push completed (`Everything up-to-date` or push log)".
4. **NEVER** describe a future state in past tense. "EVE.exe boots in <300 ms" is FALSE until `EVE.exe --profile` has actually been run. Until then: "EVE.exe target boot <300 ms (not yet measured)".
5. **NEVER** claim a fix without naming the test that proves it. "Hook now hidden" → bad. "Hook now uses `-WindowStyle Hidden`; smoke: spawn next session and observe no window flash (operator-verified pending restart)" → good.
6. **NEVER** include adjacent / opportunistic work in the same commit as the named work. Each commit has one focused subject.
7. **NEVER** carry uncommitted other-agent work into your own commit. Stage only your own files.

## Forever-audit checklist (run before any end-of-turn summary)

For every row I'm about to surface to the operator:

- [ ] Did I run a smoke test? What command? What exit code?
- [ ] Did I verify the file contents post-edit (Read tool, not memory)?
- [ ] Did I commit? What hash?
- [ ] Did I push? What was the remote response?
- [ ] If I'm claiming a doctrine is indexed, did I grep `_INDEX.md` for the slug?
- [ ] If I'm claiming a protections-check PASS, did I run `canonical-protections-check.ps1` THIS TURN?
- [ ] If I'm claiming a metric (boot time, RAM, latency), did I measure it THIS TURN?
- [ ] If I can't check any of the above, did I downgrade the verb to `claimed-but-unverified`?

If any answer is "no" → fix it before the summary is sent, or downgrade the verb.

## Self-application

This doctrine applies to EVE on Sanctum (this lane) FIRST. The same operator stack from 2026-05-23 included end-of-turn reports with `✅ shipped` rows for items that were only parse-validated, not acceptance-tested. That's a fairy-tale row. Going forward: those rows say `parse-clean` until smoke-tested.

## Status

scaffolded → parse-clean (markdown opens) → smoke-tested (this very turn — operator will tell me if a future report drifts from this verb table) → acceptance-tested (after 3 turns of compliant reports with no operator pushback) → shipped (operator confirms doctrine is now operator-canonical).

Current: **scaffolded** at file-write time. Will be **smoke-tested** at end-of-turn when operator sees the summary against the verb table.
