> **Author:** RKOJ-ELENO :: 2026-05-21
> **Tracked copy of `D:\Backups\README.md`** — version-history mirror of the README that lives outside the Sanctum git tree. Update both when you edit one.

---

# D:\Backups\ — Sinister Sanctum workstation backup root

Single consolidated backup root for the Sinister Sanctum workstation. Replaces the prior dual-folder layout (`D:\Backups\` + `D:\_backups\`).

Operator directive 2026-05-21: *"we should have one backups folder in the d drive not two"*. This dir collects every Sanctum-related backup stream — daily snapshots, custodian live-mirror, manifest event log, daemon logs — under a single root.

See `D:\Backups\README.md` for the authoritative copy. This in-tree mirror tracks layout + retention + restore steps via git history.

## Layout

```
D:\Backups\
├── README.md                   <- authoritative
├── MANIFEST.md                 <- Phase-1/2 migration history
├── _config\
├── _logs\
├── _manifest.jsonl
├── sanctum-daily\<YYYY-MM-DD>\
└── custodian\
```

## Retention

| Stream | Retention | Owner |
|---|---|---|
| `sanctum-daily/` | 7 days rolling | `SinisterSanctumDailyBackup` schtask |
| `custodian/` | 30 days rolling | custodian daemon |
| `_logs/` | 90 days | passive |
| `_manifest.jsonl` | unbounded | append-only |

## Operator-facing entry points

- `D:\Sinister Sanctum\Backup-Sanctum.bat` — manual one-shot
- `automations\install-sanctum-daily-task.ps1` — registers the 24h schtask
- `D:\Backups\README.md` — full README on disk
