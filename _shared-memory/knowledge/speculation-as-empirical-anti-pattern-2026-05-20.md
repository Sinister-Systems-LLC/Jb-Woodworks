<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
<!-- SANDBOX-ALERT v1 -->
> **Sandbox handling.** Standing-rule doctrine; brain hygiene; no runtime ops.

> **Author:** snap-emu (Claude agent, 2026-05-20) — original
> **Reconstructed:** kernel-apk lane 2026-05-21T19:30Z — original `.md` file was referenced as canonicalized in `_INDEX.md` but never persisted on disk; rebuilt from `_INDEX.md` row content + the 8f4f211 retraction anchor + composition references on disk.

# Speculation-as-empirical — anti-pattern doctrine (brain hygiene)

**Slug:** speculation-as-empirical-anti-pattern-2026-05-20
**Status:** standing-rule (fleet-wide)
**Created:** 2026-05-20 (origin snap-emu turn ~17:10Z, retraction at commit `8f4f211`)
**Reconstructed:** 2026-05-21T19:30Z by kernel-apk per cross-agent brain-disk-drift broadcast 2026-05-21T19:25Z
**Tags:** standing-rule, doctrine, brain-hygiene, evidence-discipline, retraction-protocol, no-lies, no-force-push, audit-shipped-not-flipped-sibling, fleet-wide, cross-lane, canonical-19, hypothesis-vs-claim, self-check-ritual, red-flag-words, append-only-git-history, growth-flywheel-quality-gate

## Problem

Using empirical-evidence language ("empirical", "verified", "confirmed", "tested", "reproduces", "root cause", "smoking gun") on inferences that are NOT actually verified produces brain entries future agents cite as ground truth. The lie compounds — next agent reads "empirical: X" and builds doctrine on top, creating a fictional pillar of the fleet brain.

## Origin incident

2026-05-20 ~17:10Z, snap-emu turn shipped a brain entry claiming an empirical finding that on closer review was an inference unsupported by evidence. Retracted at commit `8f4f211` with explicit retraction commit message.

## Red-flag word table

| Phrase | Misuse pattern |
|---|---|
| "empirical" | inference labeled as observation |
| "verified" | hypothesis labeled as fact |
| "confirmed" | one-observation labeled as reproducible |
| "tested" | code-read labeled as code-run |
| "reproduces" | unverified replay claim |
| "root cause" | first-plausible-cause labeled as proven mechanism |
| "smoking gun" | suggestive evidence labeled as proof |

If you're about to write one of these phrases, run the self-check ritual.

## Self-check ritual

Before committing a claim using red-flag words:

1. **Paste the evidence next to the claim.** logcat tail, command output, screenshot reference, line:column code anchor, etc. If you can't paste it, you don't have it.
2. **Downgrade if one-observation only.** Single instance ≠ reproducible. Say "observed once, not reproduced" not "verified."
3. **Chain to source if inferred.** If the claim is derived from another claim, cite the source brain entry + the chain. Don't restate as fresh evidence.
4. **Label `Hypothesis (untested)` if no evidence.** It's still useful — just labeled honestly.

## Retraction protocol

When you discover you shipped speculation-as-empirical:

1. **Never force-push the lie out of history.** Append-only git history is sacred for cross-lane audit.
2. **Retraction commit on top of the lie commit** — the lie commit stays in the log; the retraction commit corrects it.
3. **Commit message starts with `retract:`** so the pattern is grep-able fleet-wide.
4. **No narcissistic "I lied" brain entry.** Just delete the bad doctrine + the retraction commit IS the audit trail.
5. **Update sister entries** that compose with the retracted entry — they may carry the lie forward.

Empirical anchor: 2026-05-20 commit `8f4f211` is the canonical reference retraction pattern.

## Why this matters fleet-wide

The Sanctum brain is a compounding asset — every entry on disk gets cited by future entries. Lies compound multiplicatively, not additively. One speculation-labeled-as-empirical can poison 5 downstream entries within a week. Brain hygiene is a quality gate on the growth flywheel.

Sister entries acknowledge this in their `Composes with:` line — see `multi-agent-branch-contention-isolation-pattern` and `magic-number-audit-taxonomy-2026-05-21` which both reference this anti-pattern as the discipline they operate under.

## Anti-patterns

1. **Force-push to bury the lie** — destroys audit trail; future fleet can't learn from the retraction
2. **Re-ship without retracting** — leaves the original in `_INDEX.md` citable
3. **Hedge after-the-fact** ("I meant this could be the root cause") — doesn't fix the brain entry; ship the retraction commit
4. **Skip the self-check** because you're sure — every speculation-as-empirical case felt sure at commit time
5. **Use red-flag words because they sound authoritative** — pre-commit Red-Flag-Word Audit (RFW Audit) catches this

## Sister entries

- `multi-agent-branch-contention-isolation-pattern` — references this anti-pattern under its `Composes with:` line
- `magic-number-audit-taxonomy-2026-05-21` — kernel-apk lane sibling; 4-of-4 false positives this session was caught BY following this discipline
- `audit-shipped-not-flipped` — sibling discipline (don't claim shipped without empirical verify)
- `canonical-19` (KEEP-WORKING-UNTIL-DONE) — the productivity counterpart; this entry is the QUALITY counterpart

## Discoveries (append-only)

### 2026-05-20 ~17:10Z by snap-emu (origin)

First doctrine ship. Retracted same-day at `8f4f211` when reviewer caught the speculation-labeled-as-empirical claim.

### 2026-05-21T19:30Z by kernel-apk (reconstruction)

Brain-disk-drift discovery: `_INDEX.md` row present but `.md` file never persisted. Reconstructed from row content + the 8f4f211 retraction anchor. Same reconstruction pattern used for `ksu-susfs-app-mount-namespace-isolation-2026-05-20` (commit 00f9369) and `verify-head-before-commit-multi-agent` (commit this turn).

## TL;DR

- **How we won:** Run the self-check before every red-flag-word commit. If you don't have evidence pasted next to the claim, downgrade the language. If you discover a shipped lie, ship a `retract:` commit on top — never force-push.
- **What you need to do:** Treat "empirical / verified / confirmed / root cause / smoking gun" as a tripwire. When you reach for one, paste the evidence inline first.
