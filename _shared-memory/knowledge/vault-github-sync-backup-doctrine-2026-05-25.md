# Vault <-> GitHub sync + backup doctrine (2026-05-25)

Author: RKOJ-ELENO :: 2026-05-25
Status: ACTIVE

## Operator verbatim

2026-05-25 ~07:08Z: *"auto update that and github. and backup."*

Binding for every fleet agent that touches the vault.

## 3-tier replication architecture

```
  source(working-tree)  --[vault daemon, Sub-M]-->  vault(mirror)
        |                                              |
        |                                              |--[vault_github_sync.py --auto, 15min]--> github(DR)
        |                                              |
        +-----[vault_backup.py --snapshot, 60min]----> _vault-backups/
```

The four copies (any one survives loss of any other):
1. **Source** — working tree at `D:\Sinister Sanctum\`.
2. **Mirror** — `_vault/sanctum-mirror/<machine-id>/` (Sub-M's daemon writes here).
3. **DR** — GitHub origin via per-spawn `agent/sinister-sanctum/vault-sync-<utc>` branches.
4. **Snapshots** — `_vault-backups/vault-<utc>[.zip]` time-decay retention.

## Conflict resolution rules (deterministic, path-prefix routing)

| Path prefix          | Winner on diff | Rationale                          |
|----------------------|----------------|------------------------------------|
| `_shared-memory/`    | VAULT          | Live runtime state                 |
| `automations/`       | GITHUB         | CI-reviewed scripts                |
| `docs/`              | GITHUB         | Versioned documentation            |
| `deploy/`            | GITHUB         | Release artifacts                  |
| `versions/`          | GITHUB         | Immutable snapshots                |
| `CLAUDE.md`          | GITHUB         | Operator-canonical doctrine        |
| *(everything else)*  | CONFLICT       | Logged + skipped; operator decides |

When `--auto` encounters any CONFLICT row: it skips the entire push/pull, logs every conflicting path, exits 0 (so the schtask stays green). Operator drains via the queue.

## Backup retention math

Default tri-tier:
- **hourly** — keep every snapshot up to 7 days  (~168 snaps)
- **daily**  — keep newest-per-day  up to 30 days (~30 snaps)
- **weekly** — keep newest-per-week up to 52 weeks (~52 snaps)

Per-tier byte budget at 100 MB vault:
- hourly: 168 * 100 MB = 16.8 GB
- daily:   30 * 100 MB =  3.0 GB
- weekly:  52 * 100 MB =  5.2 GB
- **total:** ~25 GB uncompressed, ~6-8 GB with `--compress`.

If vault doubles to 200 MB, the cap doubles to ~50 GB; if it 10x's, snapshot interval should drop to 4h to keep cap < 200 GB. Operator can tune via `--target` to a different disk.

## 5 anti-patterns

1. **Auto-pushing to `main` directly.** Violates single-repo push policy + means a bad sync can corrupt the canonical tree with no review. Always carve `agent/sinister-sanctum/vault-sync-<utc>`.
2. **Silently overwriting conflicts.** "Vault always wins" or "GitHub always wins" loses operator intent. CONFLICT class always halts auto + logs.
3. **No retention rotation.** Snapshots without rotation fill the disk in days. `--rotate` MUST run every cycle.
4. **Backup target on same disk as source.** A drive failure kills both. Default target is on D: today; operator should move `--target` to an external drive once one is provisioned. Doctrine flags this as a known gap.
5. **Unencrypted backups containing auth keys.** `_vault/auth-keys.json` is in the snapshot. Mitigation: snapshots stay on encrypted disks; offsite copies (cloud hook) MUST encrypt at rest.

## Pass criterion

- Vault edit visible on GitHub within 15 min of one schtask tick.
- GitHub edit visible in vault within 15 min of one schtask tick.
- `vault_backup.py --snapshot --dry-run` prints a non-empty plan when vault has files; prints `nothing to snapshot` when empty (NOT a crash).
- `vault_backup.py --rotate --dry-run` shows zero deletions on fresh install; shows expected deletions after 25h of hourly snapshots.
- `vault_github_sync.py --scan` exits 0 even when `_vault/sanctum-mirror/<machine-id>/` does not yet exist (Sub-M race-condition friendly).
- Anti-pattern unit test: `vault_github_sync.py --auto` MUST NOT call `git push` to `main` regardless of conflict state; the branch-guard test in `_ensure_agent_branch()` is the canary.

## Composes with

- `sinister-vault-architecture.md` (vault is the canonical mirror substrate)
- `leo-deploy-folder-bootstrap-doctrine-2026-05-25.md` (deploy/ is github-canonical)
- `version-snapshot-disaster-recovery-doctrine-2026-05-25.md` (snapshot-before-destructive pattern)
- `automate-everything-no-operator-admin-2026-05-25.md` (zero operator clicks)
- `single-repo-push-policy-2026-05-25.md` (never push to main directly)
- `sinister-sync-doctrine-2026-05-25.md` (broader sync philosophy)
