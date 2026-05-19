# 04-RECOVERY — when things look wrong

## If the drive letter changed (D: → E: / F: etc.)

The Sinister external drive normally mounts as `D:\`. If other USB drives are
plugged in first, it may take a different letter.

```powershell
# Find it
Get-Volume | Where-Object { $_.FileSystemLabel -eq 'Sinister' }

# Re-write absolute paths inside the hub (operator-only):
cd '<new-letter>:\Sinister\Sinister Skills'
.\refresh.ps1 -RewritePaths -NewRoot '<new-letter>:\Sinister\Sinister Skills'
```

After that, also update `~/.claude/.mcp.json` since each bot has a hard-coded
`cwd` and env `SINISTER_HUB_ROOT`. Run:

```powershell
cd '<new-letter>:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION'
.\install-fleet.ps1 -SkipInstall   # re-registers with new paths
```

## If a bot won't start

```
sinister-bus.health
   -> shows total_endpoints + which bots are reachable
sinister-bus.list_network
   -> per-bot kind + tool_count
```

If the bus itself won't start, check:
1. `~/.claude/.mcp.json` exists + has bot entries
2. `python --version` resolves
3. Hub root exists at `D:\Sinister\Sinister Skills\`

## If Custodian backup is failing

```
custodian.health
   -> snapshot_count, snapshot_total_bytes, config_path
```

If `snapshot_count` hasn't grown in > 4 hours, the daemon likely stopped. Check
the scheduled task:

```powershell
schtasks /Query /TN SinisterCustodian /V /FO LIST
schtasks /Run /TN SinisterCustodian   # manual trigger
```

Daemon log: `D:\_backups\_logs\custodian-<today>.log`.

## If MCP servers can't talk to Anthropic / Ollama

- Anthropic: `scribe.health` → `api_key_present: false` means env var not set
- Ollama: `librarian.health` → `ollama_healthy: false` means Docker stack not running. Start: `cd 12_LLM_ORCHESTRATION/docker; .\setup.bat`

Both bots degrade gracefully; this is not catastrophic.

## If everything looks broken, rollback to last restore point

```
ls D:\Sinister\Sinister Skills\_logs\restore-points\
   -> pick the most-recent phase8*.md
```

Each restore point doc has a "Rollback" section with the exact commands to
revert that phase. Restore points are append-only; the hub itself is the source-of-truth.

## Disaster recovery: lost the drive

The backup root `D:\_backups\snapshots\` lives on the SAME drive as the source.
If the drive is lost, snapshots are lost too. For cross-drive backup:

1. Robocopy `D:\Sinister\Sinister Skills\` to another physical drive periodically.
2. Or set up VeraCrypt container + cloud-sync the encrypted `.hc` file (slow but safe).
3. Drive encryption itself is operator-owned (see `04-RECOVERY-DRIVE-ENCRYPTION.md` for the plan).

## Drive encryption plan (researched 2026-05-18; operator decides)

**Recommendation:** VeraCrypt **container file** on D:\ (not full-disk).

- Setup: 30 min, no whole-drive wipe required
- Hold sensitive paths (`09_REFERENCE/yurikey-roster.md`, `01_MEMORY/*/_claude_memory/`, operator notes) inside the container
- Leave `_backups/snapshots/` PLAINTEXT on D: so Custodian keeps full speed + junctions don't dangle
- Auditable (open-source, 2014-2016 audited)
- Recovery option: VeraCrypt header backup is mandatory; passphrase loss = data loss
- Bot integration: `bus.vault_lock` / `bus.vault_unlock` use the same Fernet-AES scheme (per-file) — VeraCrypt covers the at-rest case, our Fernet covers the per-file case. Both can coexist.

**Alternatives + why rejected:**
- VeraCrypt full-disk: 2-8h setup, breaks Custodian (D: gone when unmounted)
- Cryptomator: breaks Windows junctions (which Sinister LLC uses extensively)
- BitLocker: not available on Windows 10 Home edition
- Seagate hardware OPAL: proprietary firmware, not "complete control"
