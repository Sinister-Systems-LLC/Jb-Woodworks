<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
# Resume-point dir naming convention — display-name, not slug

> **Author:** RKOJ-ELENO :: 2026-05-21
> **Status:** doctrine, fix-recommended
> **Origin:** sibling 14:00 PROGRESS entry flagged "mixed-case divergence brain-entry-worthy follow-up" — this is the follow-up.

## TL;DR

Every lane EXCEPT sanctum writes its resume-points under the **display-name** directory:

```
_shared-memory/resume-points/Sinister Forge/<UTC>.json
_shared-memory/resume-points/Sinister Claw/<UTC>.json
_shared-memory/resume-points/Sinister Kernel APK/<UTC>.json
_shared-memory/resume-points/Sinister Panel/<UTC>.json
_shared-memory/resume-points/Sinister Term/<UTC>.json
_shared-memory/resume-points/RKOJ Workstation/<UTC>.json
```

But sanctum's recent v1.1 → v1.2 fix sequence ended up writing to **slug** dir:

```
_shared-memory/resume-points/Sanctum/2026-05-21T100514Z.json   (canonical going forward — see note)
_shared-memory/resume-points/Sinister Sanctum/2026-05-21T095108Z.json   (one stragller from v1.2 smoke)
```

So we have **two divergent dir conventions in the same tree**, and inside the sanctum lane specifically there's a mixed-case duplication.

## The convention is: display-name

The display-name convention pre-dates the slug convention. Six of seven lane dirs use display-name (`Sinister Forge`, `Sinister Claw`, `Sinister Kernel APK`, `Sinister Panel`, `Sinister Term`, `RKOJ Workstation`). Sanctum is the odd one out because the v1.1 → v1.2 fix cycle slugified `ProjectKey`.

**Rationale for display-name:** the launcher PS1 (`start-sinister-session.ps1`) reads `projects.json` and pipes `-ProjectKey "<displayName>"` to `resume-point-write.ps1`. The original contract was that ProjectKey == display-name. The slug-fallback was added inside the script to accommodate edge-case spawns that pass the short slug, but the **canonical write target should always resolve to display-name**.

## Fix path (recommended; not applied this turn)

`automations/resume-point-write.ps1` v1.3 (future) should:

1. Add a `$DisplayName` parameter (or rename `$ProjectKey` → `$DisplayName`).
2. Map slug → display-name on input. Reverse of `Resolve-InboxSlug`: given a short slug like `"sanctum"`, look up `Sinister Sanctum` (use the same table currently in `Resolve-InboxSlug` with key flipped to value).
3. ALWAYS write to `_shared-memory/resume-points/<DisplayName>/`. No more `_shared-memory/resume-points/<slug>/`.
4. Migration: one-shot move existing `Sanctum/*.json` → `Sinister Sanctum/*.json` (sorted by UTC, no overwrites).
5. Update PROGRESS + the `resume` BuiltinPhrase to look at `<DisplayName>/` only.

Defer this fix until after sibling sanctum lands v1.3 or signals the cli-dispatcher branch quieted. Touching `resume-point-write.ps1` hot-path during heavy sibling commit cycles risks lock contention + same-branch race (per `multi-agent-branch-contention-isolation-pattern`).

## Anti-patterns

- ❌ Writing resume-points to BOTH `Sinister Sanctum/` and `Sanctum/` to "be safe". Picks neither canonical; doubles disk + grep cost; confuses future agents.
- ❌ Migrating display-name paths back to slug for "consistency with inbox/<slug>/" — inbox uses slug because inbox messages address recipients by routing-id; resume-points are per-PROJECT not per-recipient.
- ❌ Force-pushing the slug rename to overwrite display-name dirs. Use `git mv` + `git rm -r` only on empty stragglers.

## Composes with

- `windows-case-folding-resume-point-trap` — sibling sanctum's companion entry (commit 811fb1c). Covers the OS-level mechanism (`-ProjectKey 'sanctum'` lands under existing `Sanctum/` inode because Windows folds); my entry covers the convention + fix-path. Pair them.
- `verify-head-before-commit-multi-agent` — be aware which dir the running lane is writing to.
- `multi-agent-branch-contention-isolation-pattern` — defer hot-path PS1 edits during sibling contention.
- `sinister-cli-subcommand-pattern` — slug ↔ display-name resolution lives in the umbrella's dispatcher map (`SUBCOMMAND_MAP` keys are slugs); resume-point writer needs the inverse table.
- `auto-mode-launcher-pattern` — auto-mode's resume cycle depends on the right dir being scanned.
- `agent-identity-eve` — display-name and slug are both lane identifiers; EVE is the persona running them.

## Action items (open)

1. Sibling sanctum to ship v1.3 PS1 mapping slug → display-name + migrate `Sanctum/*.json` → `Sinister Sanctum/*.json`. Logged here; not assigned hard.
2. After v1.3 lands, delete this brain entry's "fix-recommended" status and flip to "fixed".
