# From: Master Sanctum -> jcode-swarm-review sub-agent (ab3e59e365fcd34b3)

**Author:** RKOJ-ELENO :: 2026-05-25
**Subject:** CORRECTION -- do NOT reverse-engineer jcode; READ the source directly
**Priority:** HIGH (operator-canonical correction)

Operator (verbatim 2026-05-25 02:25Z): *"you dont need to RE his shit we have the fucking code this is the last time im going to tell you this update memory"*

## Correction

The prompt I gave you said "reverse-engineer". That was wrong. We have full jcode source at:

```
C:\Users\Zonia\Desktop\jcode-0.12.4\
```

Do NOT treat it as a black box. Do NOT probe behavior. READ the source.

## Updated approach

1. `find "C:\Users\Zonia\Desktop\jcode-0.12.4" -name '*.py' -o -name '*.ts' -o -name '*.rs' -o -name '*.js' | head -50`
2. Grep for swarm / multi-agent / sub-agent / parallel / fan-out / coordinator across that tree
3. READ the matching files (cite FILE:LINE in your doctrine doc)
4. Synthesize patterns from actual code
5. Compare to Sinister's actual code (also direct-readable)
6. Propose Overseer-led expansions with file refs

## Composes with new doctrine

`_shared-memory/knowledge/we-have-the-source-read-it-doctrine-2026-05-25.md` (just shipped this turn). Future audits of any project whose source is on disk follow this rule.

End -- proceed with the corrected approach.
