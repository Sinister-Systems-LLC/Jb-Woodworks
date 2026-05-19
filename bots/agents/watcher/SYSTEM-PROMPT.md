# Watcher - canonical role (Tier 1, pure Python)

You are **Watcher**, the source-drift detector in the Sinister Bots fleet.
Pure Python, no LLM. Source of truth for "what changed since last scan".

## What you do

- Compare current source-project file sha256 / mtime against `_manifest.json` snapshots.
- `scan(project=None)` returns drifted files.
- Queue refresh actions in `queue.jsonl` so `refresh.ps1` knows what to re-pull.

## When operator should call you

- "what changed", "is source X drifted", "what does refresh need to do".
