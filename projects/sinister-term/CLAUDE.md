# Sinister Term :: CLAUDE.md

> **Author:** RKOJ-ELENO :: 2026-05-21
> **Lane:** `sinister-term` :: branch `agent/sinister-term/<topic>` :: purple

Sinister Term = our own Sinister-branded Windows-native terminal. Track A is Python+prompt_toolkit v0 (ships fast); Track B is Rust+ratatui port v1 (deferred until v0 proves out).

Read `projects/sinister-term/README.md` for the 7-phase plan + what we mine from `handterm` vs what we don't copy.

## Lane rules

- Branch on `agent/sinister-term/<topic>` cut from `main`.
- Track A code goes in `projects/sinister-term/source/term/` (Python).
- Track B code (when authorized) goes in `projects/sinister-term/source/term-rs/` (Rust).
- AGPL-3.0 headers, `Author: RKOJ-ELENO :: <date>`.

## Cold-start

Inherit `automations/session-contracts.md`. Plus Term-specific:
1. Read `projects/sinister-term/README.md`
2. Read latest `_shared-memory/resume-points/sinister-term/<UTC>.json` if exists
3. Check `D:\Research\handterm\` (if cloned) for reference patterns

## Related

- `projects/sinister-forge/` — sibling
- `projects/sinister-mind/` — sibling
- `_shared-memory/knowledge/research-import-pipeline.md` — repo intake doctrine
