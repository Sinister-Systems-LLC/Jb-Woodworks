# Cross-project: SESSION-START aggregator

## Problem

All 11 projects use the SESSION-START.md handoff convention but no project sees the others. Operator opens 11 files manually for cross-project context.

## Proposed solution

Already implemented:
- `01_MEMORY/_consolidated/ALL-SESSION-STARTS.md` — concatenated view (TOC at top)
- `01_MEMORY/_consolidated/ALL-WHERE-I-STOPPED.md` — latest anchor per project
- `01_MEMORY/_consolidated/ALL-FOLLOWUPS.md` — TODO surface

These auto-regen via `refresh.ps1 -Section 01`.

## Schedule

Wire to `/loop 30m refresh.ps1 -Section 01` for continuous freshness, OR to operator's `Stop` hook (regenerate on every session exit).

## Status

✅ Implemented in Step 1 of hub build. Refresh scaffold pending Step 11.

## Cross-references

- `01_MEMORY/_consolidated/*.md`
- `05_SKILLS/proposed/06-anchor-multi.md` — companion skill
