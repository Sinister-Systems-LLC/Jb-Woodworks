> **Author:** RKOJ-ELENO :: 2026-05-23

# Topic: Sanctum mirror dirs orphan/corrupt; canonical product repos are truth

**Slug:** sanctum-mirror-orphan-corruption-pattern-2026-05-23
**First discovered:** 2026-05-23 by Sinister Sanctum master agent (EVE)
**Last updated:** 2026-05-23 by Sinister Sanctum master agent (EVE)
**Status:** workaround
**Tags:** git, repo-hygiene, sanctum-mirror, multi-lane, fleet-wide, fsck, corruption

## Problem

The Sanctum repo has per-project wrapper directories at
`D:/Sinister Sanctum/projects/<project>/source/` that mirror the canonical product repos at
`D:/Sinister/01_Projects/Sinister/<project>/source/`. TWO of these mirrors have corrupted
git trees as of 2026-05-23:

- `D:/Sinister Sanctum/projects/sinister-kernel-apk/source/source/` — `git fsck` reports
  4 missing tree objects (`3b3617a8`, `1ec11513`, `25a5e503`, `03e62221`) + 4 broken links.
  HEAD ref `agent/sinister-kernel-apk/crispy-cosmos-resume` intact; commit log readable;
  working-tree files exist on disk. Note the doubled `source/source/` path — this mirror
  is nested one extra level vs. the convention.
- `D:/Sinister Sanctum/projects/sinister-panel/source/` — `.git/refs/heads/main` points
  at missing object `0a832c28c21c82d4d3baa637c25ad41da5d5dc41`. Operator-side one-line
  fix is `echo 25a58cfaecf75d31abf12d1b5e3f3a3b51e30a2a > .git/refs/heads/main`
  (rewinds main to the last reachable commit).

Critical observation: **the canonical product repos at
`D:/Sinister/01_Projects/Sinister/<project>/source/` are HEALTHY in both cases.**
kernel-apk verified by committing 47 files (commit `f11f9d3`) to the canonical repo
cleanly while the Sanctum mirror remained broken. So the pattern is: mirror copies
drift / corrupt; canonical product repos remain the source of truth.

## Why it happens

Likely root cause (hypothesis, refinement welcome):

1. Sanctum mirrors were originally created by clone / rsync / junction at project
   onboarding and have since diverged.
2. Concurrent writers: Sanctum auto-push daemon (`SinisterSanctumAutoPush` scheduled
   task) plus per-project agent sessions plus operator-side git ops can all touch
   the mirror's `.git` directory at the same time.
3. Interrupted writes (laptop sleep, daemon kill, RKOJ window close mid-commit) leave
   loose objects unwritten while refs already point at them.
4. NTFS junction interactions: some mirrors may be junctions, some real clones — a
   junction edit reflected into the source can race the daemon's pack/gc.

The kernel-apk mirror's extra `source/source/` nesting hints at a structural mistake
during onboarding (cloned into `source/` while the wrapper already had a `source/`
directory). The panel mirror sits at the canonical `source/` depth — same corruption
class, different nesting.

## Fix or workaround

**Standing rule: do all real work in the canonical product repo, not the Sanctum mirror.**

- Canonical product repos: `D:/Sinister/01_Projects/Sinister/<project>/source/`
- Sanctum mirrors are advisory only — never assume they are committable.

Per-lane recovery:

```bash
# kernel-apk side: mirror is orphan — DO NOT EDIT. Just work in canonical repo.
# No fix needed; treat D:/Sinister Sanctum/projects/sinister-kernel-apk/source/source/
# as read-only-bystander state. Future cleanup: delete the nested source/source/ dir
# and re-create as a junction to the canonical repo (operator-gated).

# panel side: one-line ref rewind (operator runs; reversible)
cd "D:/Sinister Sanctum/projects/sinister-panel/source"
echo 25a58cfaecf75d31abf12d1b5e3f3a3b51e30a2a > .git/refs/heads/main
git fsck            # verify clean
git status          # confirm working tree intact
```

Verification (tested for kernel-apk canonical):

```bash
cd "D:/Sinister/01_Projects/Sinister/sinister-kernel-apk/source"
git add <files>
git commit -m "..."     # produced commit f11f9d3 cleanly
git fsck                # clean
```

Status: workaround. Operator runs the panel one-line ref fix when convenient.
kernel-apk mirror is left orphan — no fix needed as long as agents respect the
canonical-repo rule.

## Discoveries (append-only log, most-recent at top)

### 2026-05-23 by Sinister Sanctum master agent (EVE)
Pattern recognized fleet-wide after the kernel-apk lane (`agent/rkoj/complete-without-operator-2026-05-23`)
ran a resume audit and surfaced the corruption in their `source/source/` mirror.
Cross-checked with the panel side via Sanctum OPERATOR-ACTION-QUEUE.md — same class
of failure, different ref. Codified the canonical-truth rule (always write to
`D:/Sinister/01_Projects/Sinister/<project>/source/`, never the Sanctum mirror).

## Related topics

- [multi-agent-branch-contention-isolation-pattern](./multi-agent-branch-contention-isolation-pattern.md)
- [verify-head-before-commit-multi-agent](./verify-head-before-commit-multi-agent.md)
- [mcp-junction-fix-pattern-2026-05-23](./mcp-junction-fix-pattern-2026-05-23.md)
- [resume-point-dir-name-convention](./resume-point-dir-name-convention.md)
