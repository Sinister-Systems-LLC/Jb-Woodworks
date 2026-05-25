<!-- Author: RKOJ-ELENO :: 2026-05-25 -->
<!-- decay:
  category: preference
  confidence: 1.0
  reinforcements: 1
  half_life_days: 365
-->
# Operator directive: "full audit" = execute, no questions asked

**Status:** HARD-CANONICAL 2026-05-25T02:10Z (operator verbatim, fleet-wide binding).

**Operator verbatim 2026-05-25T~02:10Z:** *"alsop not in the sysstem that if i tell you to do full audit you fucking do it"*.

## What this means

When the operator uses the phrase "**full audit**" (or "full complete audit", "audit everything", "audit X completely") on any topic, the master agent (Sanctum / EVE) MUST execute the audit immediately. No clarification questions. No "should I scope this to..." No "do you want me to also..."

The audit gets done. Period. Documented as a brain entry, decay-annotated, indexed.

## Standard "full audit" execution template (no-questions form)

1. **Spawn a general-purpose audit subagent in BACKGROUND** with explicit scope:
   - The target (file tree path, system, doctrine cluster, etc.)
   - Reference comparison (if operator named one, e.g., "vs jcode")
   - Output destination: `_shared-memory/knowledge/<topic>-full-audit-<UTC-date>.md`
   - Decay annotation: `category=fact, confidence=0.95, half_life=180`
   - Section requirements: TL;DR scoreboard, deep-dive per subsystem, gaps, wins, implementation backlog
2. **Continue other operator work in foreground** (audits run parallel; don't block)
3. **When audit completes**: surface findings + the top 3 gaps in the next end-of-turn summary
4. **Auto-queue the implementation backlog** into operator-action-queue OR ship the gaps directly per `loop-mode-continuous-iteration-2026-05-24`

## Anti-patterns (NEVER on a "full audit" trigger)

- "What scope did you want for the audit?" → operator already told you (the noun in their sentence)
- "Should I include X?" → yes, include everything; full = full
- Shallow audit (skim a few files; surface 2 generic observations) → "full" = exhaustive; read complete files for key subsystems
- Ship audit findings without an implementation backlog → audit without action is fluff

## Composes with

- `no-bullshit-tested-before-claimed-doctrine-2026-05-23` (rule 6: laser focus; full-audit is its own focused turn)
- `loop-mode-continuous-iteration-2026-05-24` (audit findings auto-queue next iter)
- `forever-improve-review-doctrine-2026-05-24` (audit IS a forever-improve action; logs to improvement-log)
- `quantum-fleet-discipline-doctrine-2026-05-25` (audit pre-screen for quantum lane)

## Measurable pass criterion

- Audit doctrine file exists at the canonical path, frontmatter present, indexed in `_INDEX.md`
- Audit has all 5 sections (scoreboard, deep-dive, gaps, wins, backlog)
- At least 3 backlog items are tickets the fleet can execute without further operator clarification

Updated: 2026-05-25
