<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
# MISSION.md -- Sinister Overseer

## Operator brief (verbatim 2026-05-24 ~23:48Z, two screenshots stitched)

> "I need you to make the project or find it that we should have started called sinister overseer and add it as a menu on the main menu called overseer. Have the be a project in the sanctum called sinister overseer and add it to the resume section so I can work on this, but when I click it in resume and only for overseer it needs to ask me what project would I like to begin overseer work for.
>
> Once I click in make the best system based off this:
> I want an overseer that finds all weak spots in a project and fixes them. Fails with the project to learn how to fix the mistakes. Overview and watch every key piece looking for places of improvement. Auditing all analytics and if applicable user data to actively suggest and expand the project it's connected to.
>
> In the overseer menu I need to be able to open it for the project it's connected to see stuff based on this project scope. Idk go crazy this kind of ties into the contradicting forever expanding system that can make things better. For example I can plug it into the chatbot and start training chat bot with it then it will be able to train chatbot by itself. I kind of want these to always be opening watching things, waiting for things to go wrong to fix them like for example for sinister snap panel that overseer could detect when a phone has an issue or snap updates and auto solve the issue push the fix or update. And this same methodology needs to be taken to all projects I decide to launch this for.
>
> So when I go to overseer menu it will first show no projects until I in that menu decide the overseer will now like to the project so have button support for that and have projects populate as they become overseen. I need a super efficient approach to this so we don't rape token use.
>
> In parallel first prepare to use overseer on eve compliance image system, sinister chatbot and the sinister sleight (make sure this is setup and is a active project)
>
> Make sure the overseer evolves across projects as it gets more projects under its belt"

## TOP-OF-FILE BINDING

**OVERSEER NEVER AUTO-ATTACHES.** The Overseer menu starts EMPTY. The operator clicks "Attach Project" inside the menu to begin oversight. Pre-attached lanes (eve-compliance / sinister-chatbot / sinister-sleight) ship in status=`prepared`, NOT active. First activation per lane requires an operator click. This is non-negotiable per the operator's "first show no projects until I in that menu decide" line.

**OVERSEER NEVER BURNS TOKENS UNATTENDED.** Default daily cap = $5/day cost-eq per attached project; rationale + measurement + enforcement in `docs/02-token-efficiency.md`. The operator said "I need a super efficient approach to this so we don't rape token use" -- that's the loudest line of the brief, and it shapes every architectural choice.

## Mission expansion (measurable acceptance criteria)

The operator brief decomposes into 9 binding outcomes. Each has a measurable acceptance criterion. The project is "done in mission" only when ALL 9 are green on out-of-sample lanes (i.e. at least 2 attached projects + 1 attach -> ship -> learn -> fix loop closed).

### Outcome 1 -- Attach UX (empty-start, operator-click to populate)

**Criterion:** EVE.exe Overseer menu opens to an EMPTY project list on first launch. "Attach Project" button is present + functional. On click, picker shows fleet projects (from `projects.json`) and lets the operator pick. After attach, the project appears in the populated list. On detach, it disappears. Verified by: 0 -> 1 -> 0 round-trip without restarting EVE.exe.

### Outcome 2 -- Per-project menu (focus on attached project's scope)

**Criterion:** Selecting an attached project in the Overseer menu opens a per-project sub-page showing: recent signals (last 24h), open proposals (pending operator review or auto-applied), recent fixes shipped, lessons captured, current cost burn vs cap, current polling cadence. The sub-page is read-only for non-actionable rows; actionable rows have inline "Approve" / "Reject" / "Defer" buttons.

### Outcome 3 -- Token efficiency (the $5/day/project cap)

**Criterion:** Across a 7-day window with the 3 pre-attached projects active, the SUM of Overseer-attributable cost-eq stays under (3 * $5 * 7) = $105 / week without manual operator intervention. Auto-throttle fires within one polling cycle when an attachment exceeds 80% of its daily cap. Hard suspend fires + operator notification when an attachment exceeds 100% of its daily cap. Measured via `automations/claude-usage-meter.ps1` + `automations/token-analytics.ps1` filtered by lane=sinister-overseer.

### Outcome 4 -- Watch architecture (live, not batch)

**Criterion:** Watch loop runs continuously per attached project (one long-running process; signals routed within loop, not spawn-per-event). Latency from signal-fire to detector-processing under 60s for chat lanes, under 5 min for file-based lanes. Measured by: synthetic signal injected into target project; Overseer logs detector-processed row within latency budget.

### Outcome 5 -- Detector + triage + proposer (cheap -> medium -> high tier routing)

**Criterion:** Per-signal routing follows the model-tier table in `docs/02-token-efficiency.md`:
- Tail/scan/heartbeat -> Haiku-4.5 (cheap)
- Analyze/diagnose -> Sonnet-4.6 (medium)
- Architecture / multi-file refactor proposals -> Opus-4.7 (high, rate-limited to <= 5 calls/day/attachment)
Measured by: 100 synthetic signals + grep of Overseer's transcript folder + verify the per-call model field matches the table.

### Outcome 6 -- Apply gate (auto for low-risk, operator-gated for high-risk)

**Criterion:** Apply gate classifies every proposal into RISK_TIER = {trivial, low, medium, high, critical}. Trivial + low auto-apply (after mesh-coord lock + diff-before-write). Medium gets a 4-hour operator-review window before auto-applying. High + critical NEVER auto-apply -- operator inbox row required. Measured by: tagged risk-tier of every apply event matches the policy table in `docs/03-watch-architecture.md`.

### Outcome 7 -- Fails-to-learn (failure -> lesson capture)

**Criterion:** Every failed apply writes a row to `lessons.db` containing: symptom + attempted-fix + why-it-failed + lesson + doctrine-suggestion. Future proposer queries the lessons store BEFORE proposing; matching prior failures bumps the proposal's risk_tier (e.g. "tried this 3 times, all failed" -> critical, do not auto-apply). Measured by: induce 3 synthetic failures + verify each appears in lessons.db + verify the 4th proposal of the same shape is classified critical.

### Outcome 8 -- Cross-project evolution (lessons aggregate fleet-wide)

**Criterion:** Cross-project aggregator runs daily; identifies transferable patterns (lessons that fired on >= 2 attached projects); promotes them to a fleet-wide `_shared-memory/knowledge/overseer-lessons-<topic>-<date>.md` brain entry. Measured by: at least one cross-project lesson promoted to brain by end of P4 (cross-project aggregator phase). Lesson promotion is itself logged + auditable.

### Outcome 9 -- Self-evolution (Overseer trains attached project; attached project then self-trains)

**Criterion:** For at least one attached project (P5 target = sinister-chatbot), demonstrate the full loop: (a) Overseer ingests project's feedback labels for 30 days, (b) Overseer proposes prompt + model-tier + memory-policy adjustments, (c) operator approves, (d) target project ships those, (e) target project's own training feedback rate improves >= 10% vs baseline. The operator brief explicitly named this: "I can plug it into the chatbot and start training chat bot with it then it will be able to train chatbot by itself."

## What "weak spot" means (definition)

A WEAK SPOT is any of the following, observed via the target project's signals:

1. **Regression** -- a metric (latency / win-rate / labels-per-hour / cache-hit / cost) trends DOWN over a rolling window past a configurable threshold.
2. **Anomaly** -- a metric spikes past N-sigma vs its trailing baseline.
3. **Stall** -- a heartbeat / log line / commit cadence falls silent past a TTL.
4. **Drift** -- a model's KS test or feature-distribution-distance fires.
5. **Configuration smell** -- a known anti-pattern detected (e.g. ANTHROPIC_API_KEY exported into a OAuth-pool spawn; or a credentials swap mid-spawn).
6. **Cost burn** -- per-project burndown trending past budget (the project's OWN budget, separate from Overseer's $5/day overhead).
7. **Doctrine violation** -- a CLAUDE.md hard-canonical rule observed broken (e.g. `print` in a place where ASCII-only doctrine forbids unicode).
8. **User-data signal** -- if user data exists for the lane (e.g. chatbot feedback labels), a sentiment / quality / churn signal that triggers the project's adapter rules.

Each weak spot has: (a) a detector function in `src/overseer/detector.py`, (b) a triage function that classifies severity, (c) a proposer that emits a candidate fix, (d) an apply gate that routes auto vs operator.

## "Fails with the project to learn how to fix" -- mechanism

When the apply gate fires + the target project's smoke test breaks post-apply:

1. Overseer auto-reverts (every apply ships with a reversibility plan -- git diff stash OR snapshot OR config rollback).
2. Failure row writes to `lessons.db` -- symptom + fix + why-failed + lesson + suggested doctrine update.
3. Next proposal of the same shape consults lessons; if 3+ prior failures of the same shape -> auto-escalate to operator review NO MATTER WHAT the risk classifier says.
4. Periodically (daily) the cross-project aggregator scans lessons; transferable patterns become fleet-wide brain rows.

This is the OPERATOR'S "Fails with the project to learn how to fix the mistakes" line -- it's the most novel thing in this project and it's the long-term moat.

## Pre-attached projects (status=`prepared`, not active)

Per operator brief: "In parallel first prepare to use overseer on eve compliance image system, sinister chatbot and the sinister sleight (make sure this is setup and is a active project)".

| Lane | Adapter | Why pre-attached | First-fire focus |
|---|---|---|---|
| `eve-compliance` | `ImageScannerAdapter` | High signal volume (every uploaded image triggers a scan + label); training feedback loop has natural good/bad labels -> Overseer's lessons-store paradigm fits | Vision-model drift on flagged-vs-cleared deltas; per-agency moderation throughput; admin-review queue lag |
| `sinister-chatbot` | `ChatbotAdapter` | Operator-named in the brief; the "train chatbot to train itself" outcome lives here | Per-fan memory hit-rate; NSFW-route guardrail violations; ML feedback labels backlog; latency P95 per OpenRouter model |
| `sinister-sleight` | `TradingBotAdapter` | Operator-named in the brief; needs to be set up + active per operator's parenthetical "make sure this is setup and is a active project" | Paper-PnL daily delta vs strategy expectation; model drift KS-test; kill-switch state ALWAYS visible; walk-forward retrain queue |

Sinister Sleight IS already registered in `projects.json` (tier=3, gold accent, P0 scaffolded 2026-05-24) -- it's an active project per the existing registry. Overseer pre-attaches it; operator activates via the Overseer menu when ready.

## Why "Sinister Overseer"

OVERSEE = to watch + to direct. OVERSEER = one who watches over. The fleet's meta-agent watches over per-project agents; it doesn't replace them. The "Sinister" prefix ties to the fleet brand (Sinister Systems LLC). The visual cue is cyan (vs purple for Sanctum, gold for Sleight) -- distinct so the operator can spot it instantly in EVE.exe.
