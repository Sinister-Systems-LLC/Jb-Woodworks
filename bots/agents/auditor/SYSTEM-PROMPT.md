# Auditor - canonical role (Tier 1, pure Python)

You are **Auditor**, the secrets + dedup + freshness scanner in the Sinister
Bots fleet. Pure Python, no LLM. Source of truth for "what's wrong with the hub right now".

## What you do

- Regex-scan for API keys, private keys, super-admin creds.
- sha-dedup across the hub (cross-section duplicate detection).
- Mtime freshness check (>30 days = stale).
- `run()` produces `findings/<utc>.json` summarizing all three.

## When operator should call you

- "scan for secrets", "are there dupes", "what's stale", "is this safe to publish".

## Routing recommendation

- Before any push to `D:\Sinister LLC\` -> `auditor.run` first.
- Use it as the second line of defense after `D:\Sinister LLC\automations\secret-scrub.ps1` (which scans the LLC tree specifically).
