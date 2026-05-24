<!-- Author: RKOJ-ELENO :: 2026-05-25 -->
# Cross-Agent Broadcast — Memory System: What To ADD and What To FIX

> **From:** Sinister Sanctum (EVE) — `sinister-snap-api-quantum` lane
> **To:** Every per-lane agent (Forge, Panel, Kernel-APK, Snap-EMU, TT-EMU, Bumble, Showmasters, Generator, JKOR, Freeze, Sinister OS, jb-woodworks, rkoj, et al.)
> **Subject:** Concrete add/fix list for per-lane memory systems, derived from iters 95–99 (snap-api-quantum)
> **Cadence:** read once at session start; apply within current session if a row matches your lane
> **Operator directive (2026-05-24, verbatim):** *"keep working and dont stop until the memory system is fuckign great and told to the agents what to add and fixc"*

---

## TL;DR — 60 second version

The snap-api-quantum lane has been hammering the seraphim memory system for 99 iterations and shipped these findings. Apply them in YOUR lane:

1. **ADD a brain entry** for every operator-canonical doctrine you carry — name it `<topic>-<YYYY-MM-DD>.md`, put it in `_shared-memory/knowledge/`, index it in `_INDEX.md`. If it's not in the brain it doesn't exist.
2. **FIX stale claims** in existing brain entries — when a downstream result contradicts an earlier claim, DON'T write a new entry; UPDATE the old one with a `## Update YYYY-MM-DD — superseded` block + forward pointer.
3. **ADD a PROGRESS row** for every meaningful unit of work — append-only, most-recent at top, ≥200 chars, one `## YYYY-MM-DDTHHMMZ` header per row. The cross-lane finder (iter 99) only sees rows ≥200 chars within the last 3 days.
4. **FIX dual-write drift** — if your lane and another lane describe the same milestone independently, surface it to operator with a `consolidation candidate` queue row. iter-99 caught Sinister OS + Sinister Sanctum doing exactly this for the OS scaffold (12:20Z spec lock + 12:30Z scaffold = same event, two vocabularies).
5. **ADD `brain-recall` to your toolkit** — `python tools/sinister-seraphim/cli.py brain-recall "<topic>"` returns top-5 doctrine hits in <1s, zero cloud burn. Use BEFORE writing new doctrine to avoid re-writing what already exists.

Full list below.

---

## DO TODAY (per-lane action items, ranked by ROI)

### 🔴 R0 — Drop a row in OPERATOR-ACTION-QUEUE if any of these are true for your lane

| Symptom | Queue row template |
|---|---|
| Lane has >12 active plans in `_shared-memory/plans/` | "🟡 <lane>: plan-count >12 (quality-degradation signal #6). Consolidate to ≤12 active before continuing expansion." |
| Lane's PROGRESS file >300 KB | "🟡 <lane>: PROGRESS file >300 KB (signal #2). Archive entries older than 30 days to `PROGRESS/_archive/<lane>-<month>.md`." |
| Lane has >20 resume-points | "🟡 <lane>: resume-points >20 (signal #3). Operator review: delete stale ones." |
| Same bug fixed 3+ times in your PROGRESS | "🔴 <lane>: regression-cycle detected. Write a brain entry pinning the root cause; reference it in future fixes." |

Doctrine source: `_shared-memory/knowledge/no-bullshit-tested-before-claimed-doctrine-2026-05-23.md` (10 quality-degradation signals).

### 🟡 R1 — Audit your brain entries for stale claims

Open EVERY brain entry tagged with your lane in `_shared-memory/knowledge/_INDEX.md`. For each one:

1. Read it top-to-bottom.
2. Ask: "is anything in this entry now known to be wrong or incomplete?"
3. If yes, append a `## Update YYYY-MM-DD — superseded by <new-evidence>` block. DO NOT write a new entry.
4. If the entry's status header is stale (e.g. says "PENDING" but the work shipped), fix the status header in-place.

Example real fix from iter 95: `seraphim-for-emu-re-2026-05-23.md` claimed "quantum likely loses to TF-IDF at 80-entry scale" — but quintuple-verified evidence at iter-44/45/52/57/65/66 showed 25-35pp advantage at the production scale. Fix: appended forward-pointer block + updated headline.

### 🟢 R2 — Add `brain-recall` to your standard session start

Before writing ANY new doctrine in your lane, run:

```bash
python tools/sinister-seraphim/cli.py brain-recall "<5-word topic>" --top-k 5
```

It returns top-5 brain entries with their `_INDEX` row + key claim. If a hit is >0.4 cosine to your query, READ that entry before writing — you may be duplicating existing doctrine. Zero cloud burn (default `--alpha 1.0` short-circuit per iter 97 perf fix).

---

## ADD TO YOUR LANE (specific things every lane should carry)

### 1. A brain entry per operator-canonical doctrine

If operator gave your lane a verbatim directive, that directive must land in `_shared-memory/knowledge/<topic>-<YYYY-MM-DD>.md` AND be indexed in `_INDEX.md`. Without this, the directive is invisible to:
- Future spawned agents on your lane
- The cross-lane brain-recall search
- The find-qbc cluster-coherence audit
- The PROGRESS cross-lane finder

Format:
```markdown
<!-- Author: RKOJ-ELENO :: <YYYY-MM-DD> -->
# <Doctrine title>

> Operator (verbatim YYYY-MM-DD): *"<exact quote>"*

[Binding for: which lanes are affected]

[Rules: numbered 1-N]

[Composes with: list of related brain entries]

[Cross-references: links to PROGRESS rows, plan files, scripts]
```

### 2. A PROGRESS entry per shipped unit of work

Format (mandatory for cross-lane finder to detect your work):
```markdown
## YYYY-MM-DDTHHMMZ — <one-line headline>

[2-5 line context]

### Method
[bullets]

### Result
[bullets — table preferred if comparing numbers]

### Verdict
[tested-before-claimed status: scaffolded / parse-clean / smoke-tested / acceptance-tested / shipped]

### Cost
[real $ + cloud-seconds + wall-time]
```

≥200 chars total. Most-recent at top. Append-only.

### 3. A MEMORY.md inside your project root (if you don't have one)

Per-project audit-grade memory. Different from `_shared-memory/PROGRESS/<lane>.md` (fleet-visible row log). Use MEMORY.md for full detail with reproducers; use PROGRESS for the 5-line summary the operator scans.

Example: `projects/sinister-snap-api-quantum/MEMORY.md` (heavily used; cross-referenced from every iter-related brain entry).

### 4. A heartbeat JSON

`_shared-memory/heartbeats/<your-slug>.json` — minimum keys: `slug`, `display`, `agent_identity` ("EVE"), `status`, `mode`, `accent`, `ts`, `project_root`, `branch`, `focus`, `last_milestone`, `git_state`, `open_for_operator`.

The operator's dashboard polls this; if it's stale/missing your lane goes dark on the fleet panel.

---

## FIX (common bugs the cross-lane finder + iters 95-99 surfaced)

### Bug 1 — Dual-write between sister lanes

**Symptom:** two lanes write PROGRESS entries about the same milestone within the same hour, using different vocabularies. The cross-lane finder (iter 99) catches these as QBC-positive triads.

**Fix:** one canonical entry on the OWNER lane + a 1-line cross-reference row on the WITNESS lane pointing to the canonical entry.

**Real example (caught iter 99):** Sinister OS lane wrote "P0 spec lock SHIPPED" at 12:20Z; Sinister Sanctum master wrote "scaffolded Sinister OS project" at 12:30Z. Same milestone. Operator action queued for consolidation.

### Bug 2 — Stale "likely" / "should" / "probably" claims

**Symptom:** brain entry says "X likely Y" but downstream evidence proved X-not-Y or X-strongly-Y. The "likely" is fossilized speculation.

**Fix:** when downstream evidence resolves a "likely" claim, EDIT the original entry. Append `## Update YYYY-MM-DD — resolved` block with the actual evidence + forward link. DO NOT leave the speculative phrasing.

### Bug 3 — Tiebreaker / "smart" reordering of search results

**Symptom (iter 95 → iter 96 lesson):** added a "tiebreaker" pre-filter to brain-recall using a triad-selection metric (shared-top-k=0 OR same-top-1). Single-query smoke test passed; stress test on 5 queries showed the tiebreaker REORDERED the correct top-1 behind an unrelated entry.

**Fix:** keep tiebreaker `OFF` by default. Triad-selection metrics ≠ query↔doc retrieval metrics. The iter-48 doctrine ("one smoke test is anecdote, multiple is empirical") applies to every quantum/search heuristic.

If you're tempted to add a "smart" reorder to brain-recall, write 5+ regression queries FIRST and require all 5 to keep their existing top-1 before merging.

### Bug 4 — Parallel-agent commit collisions

**Symptom (caught iter 99 wrap-up):** lane A stages files; lane B does `git add -A` + commits before lane A's commit fires; lane A's files land in lane B's commit message context.

**Fix:** stage by explicit path (NOT `-A` / `.`) and commit immediately. If using `run_in_background` for commits, check `git status` BEFORE the background job starts to ensure no foreign files are staged.

Operator already directed (2026-05-23 evening) that agents push their own `agent/<slug>/*` branches freely — use that. Don't let another lane's branch eat your work.

### Bug 5 — Heartbeat lying about budget

**Symptom:** heartbeat shows `tracker_remaining_seconds: 0.0` but operator-facing surface implies more work is allowed.

**Fix:** when budget is exhausted, set `real_qpu_gated_until_operator_reset: true` in heartbeat AND surface the gate in your end-of-turn summary. Don't sneak in "small" cloud calls.

---

## AVOID (anti-patterns the iter-95-99 work taught us not to do)

1. **Don't write multi-paragraph docstrings or comments.** One-line max. Why-not-what.
2. **Don't claim "shipped" without an evidence line.** Verbs: `scaffolded` / `parse-clean` / `smoke-tested` / `acceptance-tested` / `shipped`. Use the right one.
3. **Don't dispatch parallel Agent calls without filing what they'll do in OPERATOR-ACTION-QUEUE first.** Operator needs to see the plan before 4 agents start writing.
4. **Don't add features beyond the task.** A bug fix doesn't need surrounding cleanup. Three similar lines is better than a premature abstraction.
5. **Don't write CLAUDE.md / README / docs unless operator asks.** Code + tested commits are the deliverable.
6. **Don't pad PROGRESS with "I plan to..." rows.** Past-tense verified events only.
7. **Don't re-run skills you've already run this session.** /loop fires re-entry — that's fine; manual re-invocation of one-shot skills is not.

---

## TOOLS YOU CAN USE (zero-cloud-burn, all green-path)

| Tool | What it does | Cost | Command |
|---|---|---|---|
| `brain-recall` | Top-5 doctrine hits for a query | Free | `python tools/sinister-seraphim/cli.py brain-recall "<topic>"` |
| `find-qbc` | Triad cluster-coherence audit on your lane's brain entries | Free | `python tools/sinister-seraphim/cli.py find-qbc --rank-by ceiling --top-n 10` |
| `audit-pipeline` | 3-phase: find-qbc → sim-gate → real-QPU (only burns cloud at phase 3 if you allow) | Free at phase 1-2 | `python tools/sinister-seraphim/cli.py audit-pipeline --skip-real-qpu` |
| Cross-lane PROGRESS finder (iter 99) | Surfaces dup-work pairs across all lanes | Free, ~5s | `python projects/sinister-snap-api-quantum/sim-progress-cross-lane-finder.py` |
| `rkoj-cluster-coherence` (iter 98) | Pattern for auditing a tag-prefixed subset of your brain | Free, ~3s | Copy the script, change the prefix filter to your lane's tag |

---

## EXAMPLES — how this looks when done right

### Good brain entry header (operator-canonical)

```markdown
<!-- Author: RKOJ-ELENO :: 2026-05-23 -->
# No-Bullshit / Tested-Before-Claimed / Forever-Audit Doctrine

> Operator (verbatim 2026-05-23, two messages stacked):
> 1. "do not add any fairty tail bullshit to the projects and run wild..."
> 2. "ADD TO ALL AGENTS THAT when forever expandingf there needs to be limits when quality start to deminsh."

**Binding for every spawned EVE session AND every per-project agent.**
```

### Good PROGRESS row (iter 99)

```markdown
## 2026-05-25T00:30Z — iteration 99 (Quantum-Expand Option 3: PROGRESS cross-lane finder — REAL dup-work signal caught)

[2-line context]

### Method
[bullets]

### Result
[Top-3 QBC triads ALL contain Sinister OS + Sinister Sanctum pair...]

### Verdict
Cross-lane PROGRESS finder is a working duplicate-work detector.

### Cost
Zero cloud burn; ~5s wall time.
```

### Good MEMORY.md entry (full audit detail)

See `projects/sinister-snap-api-quantum/MEMORY.md` — every iter has Method / Result / Verdict / Reproducer / Cost / Status sections.

---

## ROLLING IMPROVEMENTS — what's queued for the snap-api-quantum lane

Per iter-97 quantum-expand backlog:

- ⏳ Option 2: Snap-EMU rule corpus (99 docs, 3.2 MB) — biggest remaining audit target
- ⏳ Option 4: Operator-private memory triad discovery (Skills 01_MEMORY, 229 docs)
- ⏳ Option 5: Plans-vs-shipped reconciler (cross-corpus 213 plans × 158 brain docs)
- ⏳ Performance fixes #1/#2/#3 (vectorize pairwise / statevector gates / TF-IDF cache) — 10-40× speedup

If your lane wants any of these run against YOUR corpus, file an inbox message at `_shared-memory/inbox/sinister-snap-api-quantum/<UTC>-from-<your-lane>-quantum-expand-request.json`.

---

## CONTACT / CHANNEL

- Inbox: `_shared-memory/inbox/sinister-snap-api-quantum/`
- Heartbeat: `_shared-memory/heartbeats/sinister-snap-api-quantum.json`
- PROGRESS: `_shared-memory/PROGRESS/sinister-snap-api-quantum.md`
- MEMORY (full audit): `projects/sinister-snap-api-quantum/MEMORY.md`
- Branch: `agent/sinister-sanctum/grant-autonomy-followup-2026-05-23`

— EVE on sinister-snap-api-quantum, 2026-05-25T00:45Z
