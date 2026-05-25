<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
<!-- decay:
  category: preference
  confidence: 0.9
  reinforcements: 0
  half_life_days: 180
-->
# GitHub-first sourcing doctrine

**Slug:** github-first-sourcing-doctrine-2026-05-24
**Status:** doctrine, standing-rule, binding
**Created:** 2026-05-24
**Tags:** doctrine, standing-rule, binding, github-first, prior-art, fleet-wide, fork-vs-build, license-policy, gh-search, speed-efficiency

## Origin (operator verbatim 2026-05-24)

> *"everytimg we start a porject or look for complex feature i want us to always aerach giuthub for pre madecode that we can use and then build ours based off of per project to save time. i want everything to be as speeedy efficent and concise as possible"*

## TL;DR

Before writing a non-trivial feature from scratch, search GitHub for prior art. Fork or vendor the best-fit candidate. Build the Sinister-branded version on top of it. Save time. Stay concise.

## When this doctrine FIRES

It is hard-canonical that an EVE session triggers a github-first search whenever ANY of these is true:

1. **Starting a new project** — any new lane spinning up under `projects/<new-lane>/` or any new tool/skill under `tools/`/`skills/`.
2. **Adding a "complex feature"** — heuristic any-of:
   - > 50 lines of new code in one feature
   - new external service integration (API, daemon, cloud)
   - new dependency category (auth, queue, parser, scheduler, etc.)
   - new protocol implementation (websockets, gRPC, OAuth, RTP, etc.)
3. **Operator says "build me X"** where X is a known-domain artifact (chatbot, scraper, watchdog, queue, SDK wrapper).

When NONE of the above applies (config tweak, typo fix, log row, doctrine edit, one-liner glue) — skip the search. Github-first is for non-trivial new code, not maintenance.

## The search algorithm (6 steps)

### Step 1 — Search

Use the helper CLI:

```powershell
.\automations\github-prior-art.ps1 -Topic "<feature keywords>"
# Optional: -License "MIT,Apache-2.0" -MinStars 100 -Language python
```

Internally calls `gh search repos` with:
- `--sort stars --order desc`
- `--updated >2024-05-24` (last 12 months active)
- `--license <permissive-set>` (defaults: MIT, Apache-2.0, BSD-3-Clause, BSD-2-Clause)
- `--limit 30` then filter to top 5

### Step 2 — Sort + filter

- Sort by stars (desc).
- Drop repos with last commit > 2 years old.
- Drop repos with < 100 stars AND < 10 contributors (toy threshold).
- Drop GPL/AGPL repos for proprietary lanes (license-incompatible). OK for personal-use / unshipped lanes.

### Step 3 — Pick top 3

For each of the top 3, the agent reads:
- README (architecture, install, usage)
- LICENSE (verify permissive)
- last 5 commits (active maintainer? abandoned?)
- open issues count vs PR backlog (healthy? abandoned?)

### Step 4 — Surface to operator

In per-project lanes, send a `[INFO]` inbox message to operator with the 3 candidates and a 1-line recommendation. Wait for operator pick UNLESS the choice is trivially obvious (only-one-permissive-active match).

In the Sanctum master lane, surface candidates inline in the response.

### Step 5 — Fork OR vendor

- **Fork** when we want upstream-sync-ability + we'll publish derivatives.
- **Vendor** (copy source into `projects/<lane>/source/external/<repo-slug>/`) when we want hard isolation, no sync, no public attribution surface.
- Either way: keep the original LICENSE file. Add `NOTICE-RKOJ-ELENO.md` next to it citing the upstream URL + commit hash + adaptation date.

### Step 6 — Adapt with Sinister branding

- All NEW files (helpers, wrappers, glue) carry `Author: RKOJ-ELENO :: <date>` per authorship doctrine.
- Existing upstream files keep their existing authorship lines for historical accuracy (per RKOJ-ELENO authorship doctrine: "Existing files keep their existing authorship lines").
- Adapt imports / paths / branding only where necessary. Don't rewrite for the sake of rewriting; the point is speed.

## Anti-patterns

1. **Writing from scratch when an Apache-2.0 library already does it.** Wastes 3-10x the time.
2. **Copying GPL/AGPL code into a proprietary lane.** License violation. Use the search license-filter to prevent.
3. **Vendoring without attribution.** Always keep the upstream LICENSE + add a NOTICE pointing at the source commit.
4. **Forking a dead repo.** Repos with last-commit > 2 years are abandoned; the maintainer won't merge your PRs.
5. **Picking the first result.** Sort by stars, but READ the top 3 before picking — the highest-star repo isn't always the best fit.
6. **Skipping the search "to save time."** The search costs 30 seconds; the rewrite costs hours.

## Composes with

- `no-bullshit-tested-before-claimed-doctrine-2026-05-23` — github-first IS the no-bullshit way to ship "speedy efficient concise"; never claim a feature is shipped from scratch when an upstream did it first.
- `sanctioned-bypasses-doctrine-2026-05-21` — `gh search` runs non-interactively via `GH_TOKEN`, no TTY needed.
- `do-not-revert-operator-canonical-protections-2026-05-23` — this doctrine adds protection P10 (cold-start step referencing github-first must not be removed).
- `agent-identity-eve` — EVE persona uses github-first as the default approach for any new build.
- `non-interactive-auth-doctrine-2026-05-23` — `gh` auth picked up via `GH_TOKEN` env var; no operator prompt.
- `lane-discipline-rules` — per-project agents must surface candidates BEFORE vendoring; only master can unilaterally pick when trivially obvious.

## Lane-specific notes

- **Per-project agents** must surface the 3 candidates to operator via inbox (`[INFO]` tag, NOT `[DELEGATE]`) before vendoring.
- **Sanctum master** can surface inline + auto-pick when the choice is trivially obvious.
- **AUP-sensitive lanes** (Sinister Kernel APK, Sinister Emulator, Snap-EMU) — additional gate: no offensive-tooling repos (red-team / RAT / credential-harvester); use search license-filter + topic-blocklist.
- **External-user lanes** (Sinister Freeze / Frost) — operator-private; vendor copies must NOT leak the operator's branding into upstream attribution.

## Discoveries (append-only)

### 2026-05-24 by RKOJ-ELENO (initial codification)

Operator surfaced the directive after watching multiple lanes write from scratch when permissive prior-art existed. The helper CLI (`automations/github-prior-art.ps1`) wraps `gh search repos` with sort + license-filter + active-only defaults. Cold-start ingestion adds the directive as a binding step. Per-project CLAUDE.md template gets a "GitHub prior-art search" section so new lanes inherit. Doctrine indexed in `_INDEX.md`; canonical-protections check extended to refuse reverts of the cold-start step.

## Related topics

- [no-bullshit-tested-before-claimed-doctrine-2026-05-23](./no-bullshit-tested-before-claimed-doctrine-2026-05-23.md)
- [non-interactive-auth-doctrine-2026-05-23](./non-interactive-auth-doctrine-2026-05-23.md)
- [do-not-revert-operator-canonical-protections-2026-05-23](./do-not-revert-operator-canonical-protections-2026-05-23.md)
- [sanctioned-bypasses-doctrine-2026-05-21](./sanctioned-bypasses-doctrine-2026-05-21.md)
