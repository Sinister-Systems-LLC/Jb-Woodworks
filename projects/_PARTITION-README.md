# Per-project me/ + eleno/ partition — canonical template

> **Author:** Sinister Sanctum master agent (test, Claude) :: 2026-05-21
> **Applies to:** every canonical project in `projects/<proj>/`

## What this is

Every project folder carries three subfolders for multi-operator collaboration:

```
projects/<proj>/
├── source/         ← shared canonical codebase (tracked in full)
├── me/             ← Zonia's local-only working state (folder tracked, contents partially gitignored)
└── eleno/          ← ELENO's local-only working state (same shape as me/)
```

## What goes in me/ and eleno/

| File / subdir | Tracked? | Purpose |
|---|---|---|
| `me/README.md` | YES | Operator's project notes / what they're focused on |
| `me/configs/` | YES | Operator-specific configs that ARE shareable (e.g. preferred port numbers if both operators want them documented) |
| `me/scratch/` | NO (gitignored) | Ephemeral experiments, throwaway scripts, dump output |
| `me/NOTES.md` | YES | Append-only working notes (alternative to brain entries for un-promoted thoughts) |
| `me/.env.local` | NO (gitignored) | Operator-local secrets / API keys |

The same shape applies to `eleno/`. Both operators see both folders on their clone; each writes ONLY to their own.

## Why two folders both visible

- **Visibility** — Zonia can see what ELENO is working on (his `eleno/NOTES.md`) without context-switching to a branch.
- **Zero merge conflict on source/** — operator-specific state is partitioned by FOLDER, so concurrent commits never collide.
- **Mirror symmetry** — ELENO clones the repo and gets the same two folders; the agent identity (`$env:SINISTER_OPERATOR_SLUG`) flips based on which machine is running.

## Full spec

See `docs/MULTI-OPERATOR-COLLABORATION.md` for: branch model, auto-push contract, conflict resolution, ELENO onboarding, coordination cadence.

## Related

- `docs/MULTI-OPERATOR-COLLABORATION.md` — full doctrine
- `_shared-memory/inbox/me/` — Zonia's cross-agent inbox
- `_shared-memory/inbox/eleno/` — ELENO's cross-agent inbox
