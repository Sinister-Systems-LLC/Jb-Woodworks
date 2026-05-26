# Brain Entry :: New-Project Intake Flow — Canonical 6-Stage Pipeline 2026-05-26

> **Author:** RKOJ-ELENO :: 2026-05-26
> **Status:** active (P0 — every new project MUST flow through this)
> **Decay:** preference / 1.0 / 365 (operator-canonical "this needs to be flow")
> **Composes with:**
> - `we-have-the-source-read-it-doctrine-2026-05-25.md`
> - `github-first-sourcing-doctrine-2026-05-24.md`
> - `full-relentless-swarm-fanout-mindset-doctrine-2026-05-25.md`
> - `no-bullshit-tested-before-claimed-doctrine-2026-05-23.md`
> - `sanctum-scope-discipline-2026-05-24.md`
> - `automate-everything-no-operator-admin-2026-05-25.md`
> - `no-bat-no-ps1-do-it-for-me-doctrine-2026-05-25.md`
> - `jcode-parity-loop-swarm-upgrades-2026-05-26.md`
> - `single-repo-push-policy-2026-05-25.md`
> - `branch-convention-2026-05-25.md`

## Operator directive (verbatim 2026-05-26)

*"make sure each new project takes my idea. deeply reviews it with all knowledge we have prior and then does alot of github research to look for repos that have code we can use to get it working. then complie all that and see where we can make things better and do things better based on all that knowledge. then we create plan and get to work. this needs to be flow when i create project in eve or if i tell any agent in the network to do this."*

## Canonical 6-stage pipeline

**Implementation:** `automations/new_project_intake.py` (RKOJ-ELENO :: 2026-05-26).

**One-line invocation:**
```bash
python automations/new_project_intake.py --project-key <key> --idea-file <path-or-text>
```

### Stage 1 — INTAKE
Capture operator's raw idea verbatim to `projects/<key>/vault/intake/intake.md`. Includes UTC timestamp + branch prefix declaration. Idempotent.

### Stage 2 — PRIOR-KNOWLEDGE REVIEW
Compose three signals into `projects/<key>/vault/intake/prior-knowledge-review.md`:
1. `forge-memory recall <kw>` for top 4 extracted keywords (10 results each, best-effort).
2. Grep `_shared-memory/knowledge/` for adjacent doctrine entries.
3. Cross-reference `projects/` for adjacent lanes + `tools/_INDEX.md` + `inventions/` for reusable assets.

### Stage 3 — GITHUB RESEARCH (parallel via `sinister_swarm.py`)
Fan out 5 sub-agent slices (matches `MAX_SLICES=5` cap from `jcode-parity-loop-swarm-upgrades-2026-05-26`):
- `topic-search` — `gh search repos --topic`
- `lang-stars-search` — `gh search repos --stars '>500'`
- `awesome-list-crawl` — fetch awesome-* READMEs and extract project links
- `issue-pattern-search` — closed issues solving the same problem
- `keyword-deep-search` — `gh search code` for specific terms

Each slice writes findings to `projects/<key>/vault/intake/github-research/<utc>/<slice>.md`.

**Mesh-coord pre-flight:** each slice declares `owned_paths` so two slices can't write the same file.

### Stage 4 — COMPILE + IMPROVE
Synthesize all per-slice findings into `projects/<key>/vault/intake/compile-improvements.md`. Three implicit sub-sections (master fills in):
- **improvements.md** — where each found repo helps vs an adjacent Sanctum asset
- **gaps.md** — where no existing repo covers it (we innovate)
- **anti-patterns.md** — what NOT to copy (failures, dead projects, license issues)

### Stage 5 — PLAN
Emit `_shared-memory/plans/<key>-master-<utc>/plan.md` with explicit P0/P1/P2 milestone bands. Each item must include: file_path, acceptance_criteria, smoke_command, composes_with.

### Stage 6 — SHIP
Auto-create `projects/<key>/CLAUDE.md` from template + emit `projects.json.patch-hint.json` (master appends to `projects.json` after operator-aware review). Optionally `--spawn` to launch the lane immediately via `start-sinister-session.ps1`.

## Operator entrypoints (3)

1. **EVE.exe "new project" picker** — calls `python automations/new_project_intake.py --project-key <slug> --idea-text "<verbatim>"` (project picker hand-off lives in `eve.py`; rebuild via `verify-eve-features.ps1 -AutoRebuild -SyncMirror`).
2. **Operator utterance tagged `new-project`** — any agent receiving such utterance MUST invoke the CLI before any other action.
3. **Cold-start gate** — if a spawn has env `NEW_PROJECT_KEY` set, the cold-start phrase requires running `new_project_intake.py --stage prior-knowledge` then `--stage github-research --dry-run` to surface findings to operator BEFORE any code-write.

## Pass criterion

A project is "intake-complete" only when ALL 6 stage outputs exist:
- `projects/<key>/vault/intake/intake.md`
- `projects/<key>/vault/intake/prior-knowledge-review.md`
- `projects/<key>/vault/intake/github-research/<utc>/*.md` (≥3 slice outputs)
- `projects/<key>/vault/intake/compile-improvements.md`
- `_shared-memory/plans/<key>-master-<utc>/plan.md`
- `projects/<key>/CLAUDE.md` (scaffolded)

Until all 6 exist, the lane is NOT shippable. P0 plan items can only ship AFTER all 6 land.

## Anti-patterns (operator hard-canonical)

- **Skipping prior-knowledge review** — every new project must re-use what's already shipped; rolling-our-own when something exists violates `expansion-has-quality-degradation-limits`.
- **Single-slice GitHub research** — fan-out is mandatory; single-slice gives biased coverage.
- **Plan without smoke command** — every P0/P1 item must include a verification one-liner per `no-bullshit-tested-before-claimed`.
- **Inventing new tools when an adjacent lane has them** — Stage 2 surfaces these; reuse via `bot-fleet-quick-reference.md`.
- **`adopt-everything-found` bias** — Stage 4's anti-patterns section is mandatory; verdict per repo must include REJECT/WATCH options, not only ADOPT.

## Smoke (iter-23 verification command)

```bash
python automations/new_project_intake.py --project-key smoke-test --idea-text "test project that does nothing" --stage intake
ls projects/smoke-test/vault/intake/intake.md
python automations/new_project_intake.py --project-key smoke-test --stage prior-knowledge
ls projects/smoke-test/vault/intake/prior-knowledge-review.md
```

Expected: both files exist, prior-knowledge-review.md has ≥3 sections.

## Composes-with reasoning

- `we-have-the-source-read-it-doctrine-2026-05-25` — Stage 2 (prior-knowledge) AND Stage 3 sub-agents READ source directly per the doctrine; no reverse-engineering.
- `github-first-sourcing-doctrine-2026-05-24` — this doctrine IS the canonical implementation; supersedes the lighter `github-prior-art.ps1` invocation for new projects (which remains the lighter feature-research path).
- `full-relentless-swarm-fanout-mindset-doctrine-2026-05-25` — Stage 3 IS the canonical fan-out pattern (5 parallel slices, `MAX_SLICES=5` cap honored).
- `no-bat-no-ps1-do-it-for-me-doctrine-2026-05-25` — implementation is Python (`new_project_intake.py`), not `.bat` or `.ps1`.

## Future hardening (next iter)

- F2 from iter-23 freeze brain entry: `mcp_health_probe.py` could be invoked from Stage 3 before fanout to pre-skip broken MCP servers.
- Add per-stage Test-Protection in `canonical-protections-check.ps1` so we never accidentally ship a project missing one of the 6 outputs.
- Consider absorbing routa's `wait_mode = immediate` into Stage 3 (per `routa-deep-audit-2026-05-26.md` finding) so master keeps shipping while research slices run.
- Consider rmux's `revision counter` on heartbeats so Stage 6's optional `--spawn` knows the new agent is genuinely alive (not just `mtime`-fresh).
