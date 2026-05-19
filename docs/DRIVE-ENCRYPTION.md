# Drive encryption â€” operator-decision plan

**Researched 2026-05-18 (Phase 8s).** Operator owns the implementation. Nothing
on the drive is currently encrypted at-rest. Documenting the recommended path so
Leo + future collaborators understand the threat model.

## Threat model

- **Protect against:** physical loss/theft of the Seagate external drive
- **NOT protecting against:** active malware on the operator's machine, supply-chain attacks on bot dependencies, classifier audit (vault is open documentation, not bypass)

## Constraints

- OS: Windows 10 Home â€” **BitLocker not available** (Pro/Enterprise only)
- Drive: Seagate external, mounted as `D:\` â€” used daily by:
  - 12 Sinister Bots (MCP servers; read/write hub files)
  - Custodian backup daemon (writes every 120s to `D:\_backups\snapshots\`)
  - Operator's Claude sessions
  - Windows directory junctions between `D:\Sinister Sanctum\projects\*` and `C:\Users\Zonia\Desktop\*` sources
- "Complete control" + "open-source / auditable" â€” operator's words

## Recommendation: VeraCrypt container file (not full-disk)

### Why container, not full-disk

Full-disk VeraCrypt would dismount D: when locked, breaking:
- Custodian daemon (D: literally doesn't exist when unmounted)
- Directory junctions pointing INTO D: from Desktop
- Any background process expecting D: to be there

A container file (`.hc`) gives the same crypto guarantees for the contents but
keeps `D:` itself mounted. `_backups/snapshots/` can stay plaintext on D: for
speed; sensitive files go inside the container (e.g., mounted as `V:`).

### What lives inside vs outside

| Path | Inside vault? | Why |
|---|---|---|
| `D:\Sinister\Sinister Skills\09_REFERENCE\yurikey-roster.md` | **inside** | operator-private inventory |
| `D:\Sinister\Sinister Skills\01_MEMORY\<proj>\_claude_memory\` | **inside** | operator's daily notes |
| `D:\Sinister\Sinister Skills\01_MEMORY\_bus\` | **inside** | context-replay logs may contain handles |
| `D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\runtime-state\absorption-log.jsonl` | **inside** | learned facts can be sensitive |
| `D:\_backups\snapshots\` | OUTSIDE (plaintext) | speed; sha-dedup; junctions |
| `D:\_backups\_manifest.jsonl` | OUTSIDE | grep-ability; no secret content |
| `D:\Sinister Sanctum\` | OUTSIDE (separate question) | this is shared with Leo; encrypt separately or not at all |
| `D:\Sinister\Sinister Skills\` (rest of hub) | OUTSIDE | mostly mirrored from sources; not sensitive |

### Setup (operator runs once)

```powershell
# 1. Install VeraCrypt (download from veracrypt.fr; verify GPG signature)
# 2. Pick a strong passphrase. WRITE IT DOWN somewhere outside this drive.
# 3. Create container at D:\sinister-private.hc (~10 GB initial; can be expanded later)
# 4. VeraCrypt -> Create Volume -> Container -> Standard -> D:\sinister-private.hc
# 5. After creation, mount: VeraCrypt -> Select File -> Mount as V:
# 6. Move sensitive paths into V: (operator picks which from the table above)
# 7. Replace originals with junctions:
mklink /J "D:\Sinister\Sinister Skills\09_REFERENCE\yurikey-roster.md" "V:\09_REFERENCE\yurikey-roster.md"
# (or use symlink if NTFS; OR keep originals on V: only with no junction â€” bots read V: directly)

# 8. Each session: mount V: before starting bot fleet.
```

### Bot integration

The existing `bus.vault_lock` / `bus.vault_unlock` use per-file Fernet AES. Both
can coexist with the VeraCrypt container:

- **VeraCrypt container** = drive-level at-rest (whole volume); protects against drive theft
- **`bus.vault_*`** = per-file at-rest; protects specific operator-flagged files inside an otherwise-plaintext context

Future: a single `bus.vault_open <name>` could shell out to `VeraCrypt.exe /q /v ...` to mount the container automatically when an operator session starts. Out of scope for Phase 8.

### Recovery

- **MANDATORY:** back up the VeraCrypt volume HEADER after creation. VeraCrypt -> Tools -> Backup Volume Header. Store outside D:.
- If passphrase forgotten: data is gone. There is no backdoor.
- If `.hc` file corrupts: header backup recovers it; bad sectors inside container = lose what was at that sector (whole-volume not necessarily lost, but file table inside might be).

### Performance

5-15% read/write hit (AES-NI on modern CPUs is fast). Custodian's per-file
snapshot writes happen OUTSIDE the container (plaintext D:), so the daemon
keeps full speed.

### What was rejected + why

| Option | Why not |
|---|---|
| VeraCrypt full-disk | Setup 2-8h; D: unmounted = bots fail hard |
| Cryptomator | Per-file AES-GCM virtual FS; breaks Windows junctions (real blocker for Sinister LLC) |
| BitLocker | Not available on Win10 Home |
| Seagate hardware OPAL | Proprietary firmware; not auditable; consumer drives often don't support OPAL |

## TL;DR

- **How we won:** Recommendation locked: VeraCrypt container file on D:\sinister-private.hc holding operator-private paths; `_backups/snapshots/` + `Sinister LLC` stay plaintext on D: so Custodian + junctions keep working. Auditable, open-source, scriptable.
- **What you need to do:**
  - Install VeraCrypt (verify GPG).
  - Pick passphrase + write it down externally.
  - Create container + back up header.
  - Move sensitive paths inside; junction back if bots need same-path access.
  - Mount V: before each Claude session.
