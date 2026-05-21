# Author: RKOJ-ELENO :: 2026-05-21

# Topic: Launcher mode evolution — full mode roster + when to pick which mode

> Status: doctrine + reference
> Tags: launcher, builtinphrases, mode-picker, decision-tree, session-contracts, evolution, sanctum-launcher, start-sinister-session
> First codified: 2026-05-21 (master-plan M4 close)
> Composes with: `auto-mode-launcher-pattern` (deep-dive on `'auto'`) + `expand-mode-contract` (deep-dive on `'expand'`) + `coaudit-mode-pattern` (deep-dive on `'coaudit'`) + `forge-mode-pattern` (deep-dive on `'forge'`)

## TL;DR

`automations/start-sinister-session.ps1` exposes 15 cold-start modes via the `$BuiltinPhrases` hashtable. Each mode bakes a specific CONTRACT cocktail into the agent's opening phrase (context-review + no-stop + AUP-respect + parallel + AUP-suffix). New modes are added when (a) an existing mode no longer fits a recurring operator workflow, or (b) a new doctrine emerges that needs its own cold-start phrasing.

## Current mode roster (15 modes, 2026-05-21)

| Mode | Purpose | When to pick | Suffix-stack |
|---|---|---|---|
| `rkoj` | RKOJ workbench-only launch (no Claude spawn) | Operator opens just the workbench EXE | none — no Claude |
| `overview` | Project state + 3-5 master-actionable next moves | Cold visit to a project after >1 day away | C+N+A+P |
| `dev` | Top 3-5 feature/fix candidates; pick highest-priority; BEGIN | Standard daily ship session | C+N+A+P |
| `audit` | Secrets, stale TODOs, broken tests, push-readiness | Pre-push hygiene or weekly drift sweep | C+N+A+P |
| `resume` | RESUME-POINT-DISCIPLINE surgical context-load | Cold-start after a prior session that wrote a resume-point | C+N+A+P |
| `expand` | 7-step deep audit + clean-up + forward-plan + handoff (NO source edits) | "Plan-only" session before a big push | C+N+A+P |
| `coaudit` | Second-pair-of-eyes on a primary already running (lane-disciplined) | Parallel quality-pass on a sibling's in-flight work | C+N+A+P |
| `auto` | Full autonomous-loop scope plan + `/loop` self-paced cycling | Long unattended push; full lane scope | C+N+A+P |
| `smoketest` | Discover endpoints + loop test cases + auto-fix server-side findings | Post-deploy or new-endpoint shakedown | C+N+A+P |
| `securityaudit` | Surface discovery + probe + auto-fix; escalate P0 auth/keys/signing | Pre-release security pass | C+N+A+P |
| `deploy` | Staged deploy walk with canonical-11 reversibility gate | Production cut | C+N+A+P |
| `push` | Secret-scrub + commit + push to GitHub | End-of-session ship | C+N+A+P |
| `debug` | Last-unresolved-failure pickup; cheapest-first | Mid-session unblock | C+N+A+P |
| `explore` | Open exploration; 3 surprising findings + follow-ups | Curiosity-driven discovery pass | C+N+A+P |
| `forge` | jcode-pattern-mining onto Sanctum stack (Ruflo + Vault + mermaid + agent-host-routing) | Forge lane work; prefer Opus 4.7 1M | C+N+A+P |

Suffix-stack key: **C** = ContextReviewSuffix (CONTRACT 1) · **N** = NoStopSuffix (CONTRACT 2) · **A** = AUPRespectSuffix (CONTRACT 3) · **P** = ParallelSuffix (CONTRACT 4). All 14 non-rkoj modes carry the full C+N+A+P stack.

## Version history (rough timeline, mode-add commits)

| Version | Modes shipped | Notes |
|---|---|---|
| v1 (pre-2026-05) | `dev`, `audit` | Initial pair — work + check |
| v2 | + `overview` | Cold-visit need |
| v3 | + `deploy`, `push` | Production lifecycle |
| v4 | + `debug` | Mid-session unblock |
| v5 | + `explore` | Curiosity pass |
| v6 | + `rkoj` | Workbench-only (no Claude spawn) |
| v7-v8 (2026-05-19) | + `expand` (formal contract via brain entry `expand-mode-contract`) | 7-step deep-audit pattern |
| v9-v10 (2026-05-20) | NoStopSuffix + AUPRespectSuffix added to all modes | Refinement, not new mode |
| v11 (2026-05-20) | + `coaudit` | Sibling QA-pass without lane violation |
| v12 (2026-05-20) | Consolidate to one bat + promote auto + RKOJ spec | Single Start-Sinister-Session.bat for all modes |
| v13-v14 (2026-05-20) | + `auto` (commit `c145aff`); + operator pruning + Personal launcher rename + multi-operator partition | Autonomous-loop arrives via `auto-mode-launcher-pattern.md` |
| v15-v16 (2026-05-21) | + `smoketest`, `securityaudit`, `resume` | Recurring workflows that prior modes didn't capture cleanly |
| v17 (2026-05-21) | Compact mode (READ-CONTRACTS pointer instead of inlined contracts) | -3000 tokens per cold-start |
| v18 (2026-05-21) | + `forge` (jcode-pattern-mining lane); agent-host-routing prefers Opus 4.7 1M | Forge becomes its own mode |

Commit-anchor for the autonomous-loop arrival: `c145aff` on `agent/sinister-sanctum/launcher-auto-mode-2026-05-20` — 10 commits ahead of main (clean fast-forward; see master-plan M6 verification 2026-05-21).

## Mode-picking decision tree

```
Is the operator just opening the workbench?  →  rkoj

Cold-start after a prior session that wrote a resume-point?  →  resume

Long unattended push, full lane scope, /loop OK?  →  auto

A specific job to do?
  ├─ Single feature/fix today                           →  dev
  ├─ Cold visit, see-what's-there first                 →  overview
  ├─ Drift/secret sweep before push                     →  audit
  ├─ Pre-release security pass                          →  securityaudit
  ├─ Post-deploy endpoint shakedown                     →  smoketest
  ├─ Production cut walk                                →  deploy
  ├─ End-of-session ship to GitHub                      →  push
  ├─ Pick up the last unresolved failure                →  debug
  ├─ Curiosity / surprise-finding pass                  →  explore
  ├─ Deep audit + forward-plan + handoff (NO edits)     →  expand
  ├─ Parallel QA-pass on a sibling's primary            →  coaudit
  └─ Forge lane (jcode-pattern-mining on Sanctum stack) →  forge
```

## When to add a NEW mode vs. reuse an existing one

**Add a new mode IF all three apply:**

1. The workflow recurs (≥3 operator-issued sessions hitting the same pattern in ≤30 days).
2. An existing mode's opening phrase materially mis-steers (agent ends up reading the wrong files first or invoking the wrong contract subset).
3. The new mode warrants its own brain entry deep-dive (the "doctrine first" rule from `auto-mode-launcher-pattern.md`).

**Reuse an existing mode IF:**

- The workflow is one-off (write a `[ASK]` or hand-poke the agent instead of forging a launcher mode).
- A natural-language refinement of `dev` / `audit` / `explore` would steer the agent correctly.
- The desired behavior is already covered by a CONTRACT suffix (e.g. don't add a "noisy-context-load" mode — `dev` + the context-review contract already covers it).

## Suffix-stack composition rule

All non-rkoj modes get the full CONTRACT-1/2/3/4 suffix stack. Adding a CONTRACT-5 suffix would be wrong because cross-agent communication is opt-in per-task (the agent should always check on-disk first per the cross-agent-coordination-pattern), and CONTRACT-6 (end-of-turn style) is implicit — agents don't get prompted to follow it; they're trained to.

The compact-mode pointer at session-contracts.md handles all CONTRACT 1-7 in one ~200-char reference, replacing the ~3500-char inlined-contracts era.

## Anti-patterns

- **Forging a one-off mode for a single session.** Add a `dev` + custom-prompts override instead. Mode-bloat dilutes the picker UX.
- **Duplicating CONTRACT-suffix logic in the mode phrase.** The CONTRACT-suffixes are append-only at the bottom of every non-rkoj mode — never inline them into the mode body.
- **Adding a mode without a brain-entry deep-dive.** The roster above is the registry; the deep-dives are the doctrine. Both must land in the same commit.
- **Letting modes drift between branches.** `BuiltinPhrases` lives only in `automations/start-sinister-session.ps1` — single source of truth on `main` (or the launcher branch when one is in flight).

## Related topics

- `auto-mode-launcher-pattern.md` — `'auto'` deep-dive (5-phase contract)
- `expand-mode-contract.md` — `'expand'` deep-dive (7-step audit + handoff)
- `coaudit-mode-pattern.md` — `'coaudit'` deep-dive
- `forge-mode-pattern.md` (if/when written) — `'forge'` lane deep-dive
- `complete-plan-autonomous-mode.md` (canonical-16) — plan-paired-with-prompt doctrine
- `keep-working-until-done.md` (canonical-19) — no-stop contract origin
- `multi-agent-branch-contention-isolation-pattern.md` — why each new mode that auto-creates a new branch needs an isolation step

## Verification (this entry)

- 15 modes documented above match the 15 modes listed in `automations/session-contracts.md` CONTRACT 6 "Modes (BuiltinPhrases keys)" section.
- Suffix-stack inventory matches `start-sinister-session.ps1::BuiltinPhrases` grep (lines 1391-1421+; every non-rkoj mode carries `$ContextReviewSuffix$NoStopSuffix$AUPRespectSuffix$ParallelSuffix`).
- M6 merge-probe (master-plan auto-2340Z) verified clean fast-forward of `agent/sinister-sanctum/launcher-auto-mode-2026-05-20` → `main` (10 ahead, 0 behind, `git merge-tree --write-tree` returns tree-SHA with no conflict markers).
