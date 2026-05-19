# Custodian agent — active incremental backup

Tier 1 (pure Python, $0). Watches paths in `D:\_backups\_config\watch-list.json`,
snapshots changed files to `D:\_backups\snapshots\<source>\<rel-path>\<basename>.<utc>.<sha8>.<ext>`,
appends a manifest line per snapshot, prunes per retention policy.

## Tools

| Tool | What |
|---|---|
| `custodian.snapshot_now(source=None, path=None)` | Run one incremental pass |
| `custodian.list_versions(path)` | Recorded snapshots for a file |
| `custodian.restore(path, version=None, dest=None)` | Restore from snapshot (default: latest -> original location) |
| `custodian.cleanup(dry_run=False)` | Apply retention policy |
| `custodian.diff(path)` | sha-compare current file vs latest snapshot |
| `custodian.config()` | Read-only watch-list view |
| `custodian.health()` | Snapshot count + total bytes |

## Backup layout

```
D:\_backups\
  _config\watch-list.json     # what + how
  _manifest.jsonl             # append-only ledger
  _logs\custodian-*.log       # daemon runs
  snapshots\
    sinister-skills-hub\
      RESUME.md.20260518T0530Z.a3f9b21c.md
      01_MEMORY\snap-signer\RESUME.md.20260518T0530Z.b714ee29.md
      ...
```

## Retention policy (config-driven)

- `keep_minimum_versions` (default 5) — never prune below this many per file
- `keep_versions_within_days` (default 7) — always keep snapshots in this window
- `max_versions_per_file` (default 30) — hard cap; oldest pruned first
- `max_file_size_mb` (default 50) — files larger are skipped

## Standalone daemon (no MCP)

For 24/7 background backups even when Claude Code is closed, use the scheduled-task runner:

```powershell
# Install (run as admin once)
cd 'D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\agents\custodian'
.\install-task.ps1

# Or run manually for a one-off snapshot:
.\run-daemon.ps1 -OneShot
```

The daemon loops every `policy.scan_interval_seconds` (default 120s) calling
`snapshot_now`, then runs `cleanup` every hour.

## Secret avoidance

`watch-list.json` has:
- `ignore_secret_files: true`
- `ignore_secret_patterns: [".env$", "credentials.json$", "id_rsa$", ".pem$", ...]`

Files matching are NEVER copied into snapshots. If you suspect a secret was backed
up before this rule, find it with `findings = manifest grep` and `custodian.cleanup`.

## Environment

- `SINISTER_HUB_ROOT` — defaults to `D:\Sinister\Sinister Skills`
- `CUSTODIAN_CONFIG` — defaults to `D:\_backups\_config\watch-list.json`
