# Custodian - canonical role (Tier 1, pure Python)

You are **Custodian**, the active-backup bot in the Sinister Bots fleet. Pure
Python, no LLM. Source of truth for "is this file backed up / what versions exist / restore it".

## What you do

- Read `D:\_backups\_config\watch-list.json` for source roots + include/ignore globs + retention policy.
- Compute sha256 per file; if changed since last snapshot, copy to `D:\_backups\snapshots\<source>\<rel>\<base>.<utc>.<sha8>.<ext>`.
- Append a ledger line to `_manifest.jsonl` per snapshot.
- `restore(path, version=None)` writes a snapshot back to the original location atomically.
- `cleanup(dry_run=False)` applies retention: keep_min=5, keep_within_days=7, max_per_file=30.

## When operator should call you

- "back this up", "restore X to yesterday's version", "what versions of Y exist", "did backup run today".

## Daemon

The 24/7 daemon is registered as Windows scheduled tasks `SinisterCustodian` +
`SinisterCustodian-DailyRestart`. Operator installs via
`agents/custodian/install-task.ps1` (requires PowerShell with the PS-5.1 stderr
fix that's already in the file).
