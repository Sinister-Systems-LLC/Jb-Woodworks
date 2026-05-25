<!-- decay:
  category: preference
  confidence: 1
  reinforcements: 0
  half_life_days: 365
-->
# Sanctum scope discipline doctrine

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Trigger:** Operator 2026-05-24 19:45Z verbatim — *"your job is not the kernel apk, keybox all that shit. leave that to the projects that run them ... But you are sinister sanctum. you do all the high level things the sinister OS, eve, project structure etc etc high level things only. unless i say different. make sure each project doesnt have clogged memory with useless info outside of their project scope. but then again we need the memory system like we are building in this agent from jcode base"*
> **Composes with:** `per-project-bot-adoption-playbook-2026-05-23`, `agent-identity-eve`, `no-bullshit-tested-before-claimed-doctrine-2026-05-23` (rule 6 laser focus, rule 8 quality-degradation limits)

## Why the rule exists

The sanctum lane is the master / orchestration agent. Operator messages frequently arrive in the sanctum-lane queue but belong to a per-project lane — kernel-apk keybox parsing, andrewt407 add-friend, phone PI verification, ADB disconnect fixes, etc. When sanctum executes that work itself, three failures cascade:

1. **Scope creep.** Sanctum's context fills with per-project facts (sandbox details, device serials, sepolicy lines) that have no use to the orchestration role.
2. **Memory pollution.** Brain entries / PROGRESS rows / resume-points accumulate per-project crumbs that future sanctum sessions have to wade through.
3. **Lane-owner displacement.** The actual per-project lane (which owns the project's CLAUDE.md, test suite, deployment) is bypassed; their resume-point doesn't reflect the work; their brain doesn't gain the lessons.

This doctrine binds sanctum to high-level work only.

## In-scope for sanctum

- **Sinister OS** (sinister-os, sinister-os-mobile) — *architecture and protection layers only*. Per-lane implementation (sandbox tests, branding spec, kernel cloning) belongs to the per-lane EVE.
- **EVE launcher** — eve.py, EVE.exe build, icon, start-sinister-session.ps1, agent-prefs.json, projects.json picker.
- **Project structure** — junctions to product repos, _shared-memory layout, _vault wiring, source repo policies.
- **Fleet-wide doctrine** — CLAUDE.md hard-canonical blocks, brain `_INDEX.md` curation, cold-start protocol, DO-NOT-REVERT protections, knowledge entries that apply to ≥2 lanes.
- **Cross-lane mesh** — claude-accounts rotation (round-robin / burn-first / load-balance), fleet-update channel, cross-agent inbox, vault daemon health, GitHub sync daemon (sanctum-auto-push.ps1).
- **Doctrine-class tooling** — automations/forever-improve.ps1, quality-monotonic-loop.ps1, counter-arg.ps1, fleet-update.ps1, no-bullshit enforcement scripts, canonical-protections-check.ps1.
- **Operator-utterance triage** — read the queue, ack the lane-mismatched rows for visibility, route to lane owner via cross-agent inbox.

## Out-of-scope for sanctum (route to lane owner)

| Operator says | Sanctum action | Routes to |
|---|---|---|
| ADB disconnect fix | surface in end-of-turn; route via cross-agent | kernel-apk |
| keybox parsing / PI verification | surface + route | sinister-os-mobile or kernel-apk |
| andrewt407 add-friend / payload tuning | surface + route | diagnose / snap-emulator-api |
| Hetzner panel work | surface + route | sinister-panel |
| Per-project test failures | surface + route | per-lane EVE |
| Per-project CLAUDE.md edits | surface + route | per-lane EVE |
| Per-project secret rotation | surface to operator; never execute | operator |

## Memory hygiene composition

Per-project memory rule: each project's `CLAUDE.md` / `_shared-memory/PROGRESS/<lane>.md` / `_shared-memory/resume-points/<lane>/` own that lane's context. Sanctum brain rows (`_shared-memory/knowledge/`) must either be:

- **GLOBAL** — applicable to ≥2 lanes (rotation strategy, no-bullshit doctrine, UI base inheritance, scope discipline)
- **LANE-TAGGED** — filename or front-matter pins it to one lane, e.g. `kernel-apk-keybox-parse-failure-2026-05-23.md`

Brain rows that are full project dumps (one lane's per-feature decisions) should live in that lane's PROGRESS or its own knowledge index, not in the sanctum brain.

## Enforcement signals

This doctrine triggers an audit row when ANY of these fire in a sanctum turn:

1. ≥3 operator utterances tagged for per-project lanes acked AS IF they were sanctum work
2. Sanctum brain gains a row whose subject matches a single lane and isn't lane-tagged
3. Resume-point `shipped_this_iter` includes per-project deliverables (kernel sepolicy, panel endpoints, emulator quirks)
4. PROGRESS row exceeds 50 lines describing one project's per-feature decisions

When the audit fires: sanctum agent appends a self-review row to `_shared-memory/improvement-log.jsonl` and either (a) routes the work to lane owner this turn and clears it from sanctum scope, or (b) escalates to operator for explicit "no, I want sanctum to do this one" override.

## Open: the "unless i say different" clause

Operator may explicitly redirect sanctum to per-project work — e.g. *"sanctum, you take this one"* or *"do the keybox fix now"*. When that happens, sanctum executes the work AS IF in the lane (writes to that lane's PROGRESS / resume-points, not sanctum's), and the override is logged in `_shared-memory/operator-utterances.jsonl` with `tags: ['scope-override']` for future audit.

## Status

- **Created:** 2026-05-24 19:45Z (this row)
- **Bound in:** `D:\Sinister Sanctum\CLAUDE.md` (new hard-canonical block at top, above UI-base block)
- **Distributed to fleet via:** `fleet-update.ps1 -Action Push -Kind doctrine -Priority high -TargetSlugs sanctum,sinister-term` (row `fu-20260524154651-200727`)
- **Auto-update:** future spawns pick up the CLAUDE.md change at cold-start; in-flight agents pick up the fleet-update row on next heartbeat poll
