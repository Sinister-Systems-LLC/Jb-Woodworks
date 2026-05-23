# Sinister Freeze :: partition layout

> **Author:** RKOJ-ELENO :: 2026-05-21
> **Pattern:** mirrors `projects/sinister-term/` (me/ + eleno/ + source/)

```
projects/sinister-freeze/
├── README.md                      # public-facing description
├── CLAUDE.md                      # cold-start protocol + lane rules
├── PLAN.md                        # phase plan (drafted once research lands)
├── _PARTITION-README.md           # this file
├── me/                            # Zonia (operator) partition — operator-internal notes, ops scratch
├── eleno/                         # ELENO partition — operator's other identity / collab space
├── joe/                           # Joe's partition — his data, his drafts, his lead notes (gitignored if needed)
└── source/                        # the code itself (AGPL-3.0-or-later)
    ├── pyproject.toml             # Python package (FastAPI backend likely)
    ├── freeze/                    # backend
    ├── web/                       # frontend (Electron+React likely per research)
    ├── joe-mode/                  # Joe-friendly Claude-session wrapper
    └── tests/
```

## Why partitions

- **`me/`** + **`eleno/`** = operator's identities, both can land notes here without cross-pollinating
- **`joe/`** = Joe's data partition; keep it cleanly separable for portability + privacy
- **`source/`** = the actual codebase

Joe's customer data NEVER lands in `source/` (which is git-tracked + may be open-sourced). Joe's data lives in `joe/` (gitignored) and in `_shared-memory/forge-memory/freeze/` (also gitignored — that whole subdir is ephemeral working memory).
