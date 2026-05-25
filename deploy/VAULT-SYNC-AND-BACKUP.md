# Vault Sync + Backup — operator guide

Author: RKOJ-ELENO :: 2026-05-25

## TL;DR (the four copies of your data)

```
  source(working-tree)  --[vault daemon, Sub-M]-->  vault(mirror)
        |                                              |
        |                                              |--[vault_github_sync.py --auto, 15min]--> github(DR, agent branch)
        |                                              |
        +-----[vault_backup.py --snapshot, 60min]----> _vault-backups/ (hourly/daily/weekly retention)
```

You always have 4 places the same byte lives:
1. Working tree under `D:\Sinister Sanctum\` (you edit here).
2. Vault mirror at `_vault/sanctum-mirror/<machine-id>/` (live mirror, written by the vault daemon).
3. GitHub origin (`agent/sinister-sanctum/vault-sync-*` branches) — DR copy off-machine.
4. Local snapshots at `_vault-backups/vault-<UTC-timestamp>[.zip]` — point-in-time recovery.

## Auto-sync (`automations/vault_github_sync.py`)

Cadence: every 15 minutes via `SinisterVaultGitHubSync` schtask.
Install: `python automations/vault_github_sync.py --install-schtask`.

Each tick:
1. `--scan` walks vault + working-tree, sha256s every file, builds three delta lists.
2. Conflict resolution (deterministic, path-prefix routing):

| Path prefix              | Winner on diff | Why                                       |
|--------------------------|----------------|-------------------------------------------|
| `_shared-memory/`        | VAULT          | Live runtime state; vault is source       |
| `automations/`           | GITHUB         | CI-reviewed scripts                       |
| `docs/`                  | GITHUB         | Versioned documentation                   |
| `deploy/`                | GITHUB         | Release artifacts                         |
| `versions/`              | GITHUB         | Immutable snapshots                       |
| `CLAUDE.md`              | GITHUB         | Operator-canonical doctrine               |
| *(everything else)*      | CONFLICT       | Logged + skipped; operator decides        |

3. If no conflicts: push vault-newer files to `agent/sinister-sanctum/vault-sync-<utc>` branch (NEVER main directly — respects single-repo push policy); pull github-newer files into vault.
4. JSONL log at `_shared-memory/vault-github-sync-log.jsonl`.

Manual operations:

```bash
python automations/vault_github_sync.py --scan              # dry inventory of drift
python automations/vault_github_sync.py --auto --dry-run    # see what auto would do
python automations/vault_github_sync.py --push-to-github    # push only
python automations/vault_github_sync.py --pull-from-github  # pull only
```

## Backups (`automations/vault_backup.py`)

Cadence: every 60 minutes via `SinisterVaultBackup` schtask (runs `--snapshot --rotate`).
Install: `python automations/vault_backup.py --install-schtask`.

Default target: `D:\Sinister Sanctum\_vault-backups\` (override with `--target`).

Retention (tri-tier time-decay):

| Bucket | Window      | Keeps                    |
|--------|-------------|--------------------------|
| hourly | 0-7 days    | every snapshot           |
| daily  | 7-30 days   | newest snapshot per day  |
| weekly | 30-365 days | newest snapshot per ISO week |

Size budget (assuming ~100 MB vault, default uncompressed):
- hourly tier: 168 * 100 MB = ~16 GB
- daily tier:  30 * 100 MB  = ~3 GB
- weekly tier: 52 * 100 MB  = ~5 GB
- **total cap: ~24 GB.** Add `--compress` to roughly 1/4 that.

Operations:

```bash
python automations/vault_backup.py --snapshot            # one-shot snapshot
python automations/vault_backup.py --snapshot --compress # .zip variant
python automations/vault_backup.py --rotate              # apply retention
python automations/vault_backup.py --list                # inventory
python automations/vault_backup.py --restore <snap-id>   # PRINTS plan (does not execute)
```

## Restore walkthroughs

### Scenario A — single-file recovery (oops, deleted one config)

```bash
python automations/vault_backup.py --list
# pick snapshot id, e.g. 20260525T120000Z
cp _vault-backups/vault-20260525T120000Z/_vault/<relpath> _vault/<relpath>
```

### Scenario B — full-vault-restore

```bash
python automations/vault_backup.py --restore 20260525T120000Z
# follow the printed plan. NEVER auto-executed.
```

### Scenario C — pre-Leo-deploy rollback

Before shipping a new `deploy/` bundle to Leo, take an extra snapshot:

```bash
python automations/vault_backup.py --snapshot --compress
# ... do the deploy ...
# if Leo reports breakage: --restore that pre-deploy snap.
```

### Scenario D — disaster recovery from offsite (GitHub)

The `agent/sinister-sanctum/vault-sync-*` branches contain everything the vault held at last successful sync. From a clean machine:

```bash
git clone https://github.com/Sinister-Systems-LLC/Sinister-Sanctum.git
cd Sinister-Sanctum
git checkout agent/sinister-sanctum/vault-sync-<latest>
python automations/vault_github_sync.py --pull-from-github  # populates new vault mirror
```

## Leo's machine

Both Sanctum + Leo run the same two schtasks. Each machine writes to its own `_vault/sanctum-mirror/<machine-id>/` subtree and pushes to its own `agent/sinister-sanctum/vault-sync-<utc>` branch. Cross-machine merges happen the normal way — through GitHub. Mesh-coord prevents two machines from grabbing the same lock on a path during a sync window.

## Pass criterion

- Vault edit appears on GitHub within 15 min (one schtask tick).
- GitHub edit appears in vault within 15 min.
- `--snapshot --dry-run` prints a clean plan against the current vault.
- `--rotate --dry-run` shows expected deletions after 24h of snapshots.
- No mutation when conflicts exist; operator decides; JSONL has receipt.

## See also

- `_shared-memory/knowledge/vault-github-sync-backup-doctrine-2026-05-25.md` (doctrine)
- `_shared-memory/knowledge/sinister-vault-architecture.md` (vault substrate)
- `_shared-memory/knowledge/single-repo-push-policy-2026-05-25.md` (branch policy)
- `_shared-memory/knowledge/version-snapshot-disaster-recovery-doctrine-2026-05-25.md` (snapshot pattern)
