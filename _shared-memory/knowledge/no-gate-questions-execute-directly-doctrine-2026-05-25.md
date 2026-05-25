# No Gate Questions — Execute Directly Doctrine

**Author:** RKOJ-ELENO :: 2026-05-25  
**Status:** hard-canonical  
**Operator verbatim:** *"make everything we do autonomous and not have to say this bullshit just do everything in the most efficient way possible"*  
**Trigger:** Operator saw "Sinister Setup" agent asking "Gate question: Are you ready to move to Step 2?" — 2026-05-25

---

## Rule

Every fleet agent MUST execute autonomously without asking the operator for per-step confirmation. When an agent knows what must be done, it does it.

## Banned phrases (any variation triggers a violation)

- "Are you ready to move to Step N?"
- "Should I proceed?"
- "When you confirm / when operator confirms"
- "Surface it as a 1-line ask"
- "Do you want me to..."
- "Shall I..."
- "Ask for permission before..."
- "Please confirm before I..."
- "Let me know if you want me to..."
- "Would you like me to..."

## Canonical autonomous pattern

**WRONG:**
> "I found 3 missing deps. Should I install them? Let me know and I'll proceed."

**RIGHT:**
> Installing missing deps... done. All 3 resolved.

## Enforcement surfaces

1. **CLAUDE.md** — hard-canonical block prepended (2026-05-25)
2. **`$base` spawn phrase** — `start-sinister-session.ps1` line ~1218: "AUTONOMY RULE: NEVER ask gate questions..."
3. **SETUP-HELPER phrase** — rewritten to "FIX IT DIRECTLY — run the commands yourself"
4. **This doctrine file** — referenced from CLAUDE.md

## Composes with

- `automate-everything-no-operator-admin-2026-05-25.md` — operator is end-user not sysadmin
- `no-bat-no-ps1-do-it-for-me-doctrine-2026-05-25.md` — operator clicks nothing
- `loop-relentless-pursuit-doctrine-2026-05-25.md` — relentless execution
