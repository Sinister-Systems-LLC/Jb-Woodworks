<!-- Author: RKOJ-ELENO :: 2026-05-25 -->
<!-- decay:
  category: preference
  confidence: 1.0
  reinforcements: 1
  half_life_days: 365
-->
# Brain auto-annotate + push-all-agent-branches doctrine

**Status:** HARD-CANONICAL 2026-05-25T03:00Z (operator hard-canonical 2026-05-25T~02:50Z + 2026-05-25T02:02Z).

## What this is

Two paired automations shipped 2026-05-25 that close the long-standing operator pains:

1. **Brain at 100% stays at 100%** without operator intervention even when 6-8 sibling lanes are adding entries faster than the master can hand-annotate.
2. **Every-agent branch reaches GitHub** every 10 min — not just the branch that the auto-push daemon's shell happens to be on at any moment.

## 1. `automations/brain-auto-annotate.ps1`

Defensive sweep that injects decay frontmatter into any brain entry that lacks it.

**Heuristic (filename-substring → category/confidence/half-life-days):**

| Match | Category | Conf | Half-life |
|---|---|---:|---:|
| doctrine \| canonical \| directive \| policy \| playbook \| charter | preference | 1.0 | 365 |
| bug \| fix \| regression \| fail \| crash \| broken | correction | 1.0 | 365 |
| issue \| lesson \| gotcha \| trap \| antipattern | correction | 0.95 | 365 |
| audit \| findings \| investigation \| smoke \| verified \| probe | fact | 0.9 | 180 |
| pattern \| architecture \| design \| spec \| schema | fact | 0.85 | 180 |
| (anything else) | fact | 0.85 | 180 |

Invokes `brain-decay-score.ps1 -Action Annotate -Slug ... -Category ... -Confidence ... -HalfLifeDays ...` per entry. Skips: `_INDEX.md`, `_INDEX-DECAY-SCORES.md`, `README.md`, `_TEMPLATE.md`.

**Scheduled task:** `SinisterBrainAutoAnnotate` — every 30 min, hidden (`-WindowStyle Hidden` per `no-visible-powershell-windows-doctrine-2026-05-25`).

**Pass criterion:** `head -10 *.md | grep -q "decay:"` returns 0 for every real brain entry within 30 min of any new addition.

**Composes with:**
- `brain-decay-implementation-schema-2026-05-25` (the decay contract this enforces)
- `memory-backbone-3-tier-hybrid-better-than-jcode-2026-05-24` (Tier 2 stays 100%)
- `gradual-growth-memory-push-eve-exe-ready-2026-05-24` (R3 prune-as-add — auto-annotate is the dual-pair of prune)
- `no-bullshit-tested-before-claimed-doctrine-2026-05-23` (rule 5 forever-upgrade)

## 2. `automations/sanctum-push-all-agent-branches.ps1`

Iterates over every local `agent/*` branch and pushes those that are ahead of upstream. Creates upstream-less branches with `-u`. Skips diverged branches (operator-decision territory).

**Logic per branch:**
1. `git rev-parse --verify --quiet $branch` → local SHA
2. `git rev-parse --verify --quiet origin/$branch` → remote SHA
3. If no remote: `git push -u origin $branch` (create + push)
4. If equal: skip
5. `git rev-list --count` ahead / behind:
   - behind=0, ahead>0 → push
   - behind>0 → DIVERGED, skip (surfaced for operator)

**Fetch tolerance:** does NOT exit-fatal on `git fetch --all` rc=1 because a single down remote (e.g. local Gitea `localhost:3000`) leaves origin (GitHub) reachable. Pushes proceed independently.

**Scheduled task:** `SinisterPushAllAgents` — every 10 min, hidden.

**JSONL log:** `_shared-memory/sinister-term-history/push-all-agent-branches.jsonl` — one summary row per run + per-branch details (action, elapsed, rc, ahead, behind, err).

**Smoke evidence 2026-05-25T02:55Z:** 40 branches seen, 6 created, 1 pushed, 4 diverged-skip, 0 failed. Branches that landed on GitHub this run: `agent/jb-woodworks/scaffold-and-launch`, `agent/rkoj/complete-without-operator-2026-05-23`, `agent/showmasters/scaffold-and-launch`, `agent/sinister-freeze/ph1-mvp-day3-brief`, `agent/sinister-os/p1-iter10-15-2026-05-25-2026-05-25`, `agent/sinister-sanctum/eve-exe-headless-jcode-audit-2026-05-25`, `agent/sinister-sanctum/window-persist-fix-temp-2026-05-24`.

**Composes with:**
- `sanctum-auto-push` (existing 30-min current-branch daemon; this adds the every-agent fan-out)
- `sanctum-push-policy-2026-05-25` (refuses out-of-policy pushes; same gate)
- `branch-convention-2026-05-25` (only branches matching `agent/<project-key>/...` are touched)
- `sinister-link-doctrine-2026-05-25` (Leo's machine also runs this; both peers fan)
- `frequent-detailed-commits-per-agent-2026-05-25` (this is the SHIPPING mechanism for that doctrine)
- `agent-autonomy-push-and-completion-2026-05-23` (per-agent push freedom)

## 3. PowerShell gotchas shipped same turn (sub-doctrine)

While building #2 hit two PS 5.1 traps worth memorialising:

1. **`$Args` is auto-shadowed in functions** — `function foo { param([string[]]$Args) ... & cmd @Args }` silently doesn't pass through. PS's automatic `$Args` collection wins. **FIX: rename to `$GitArgs` / `$CmdArgs` / anything not `$Args`.**

2. **`git fetch --quiet` suppresses success indicator lines** — when you need to detect "fetch partial-OK vs all-down" you can't rely on rc alone (rc=1 fires on any single remote failure); the `From <url>` lines are the success signal but `--quiet` eats them. **FIX: drop `--quiet` when post-processing fetch output for diagnostics.**

## Anti-patterns (NEVER)

- Hand-annotating brain entries one-by-one when 6+ sibling lanes are active — the auto-annotator handles new entries; reserve hand-annotation for re-classification only
- Pushing only the master branch and assuming siblings' work reaches GitHub — they have their OWN branches; push-all-agent-branches handles them
- Auto-pushing DIVERGED branches — that's a force-push waiting to happen. Always surface diverged for operator decision.
- Forgetting `-WindowStyle Hidden` on the scheduled task (regression test: `Get-ScheduledTask | %{$_.Actions[0].Arguments}` should never show a Sinister* task without Hidden)
- Treating `git fetch --all` rc=1 as fatal when only one of multiple remotes is down

## Measurable pass criteria

- `head -10 _shared-memory/knowledge/*.md | grep -c "decay:"` ≥ count of `.md` files in that dir (minus 4 metadata files), checked every 30 min by cron
- `_shared-memory/sinister-term-history/push-all-agent-branches.jsonl` has a summary row in the last 10 min during normal operation
- No Sinister* scheduled task lacks `-WindowStyle Hidden` (zero rows from the audit grep)
- After Leo pulls origin, his local clone shows the same `agent/*` branch list as operator's (minus operator-machine-private branches)

Updated: 2026-05-25
