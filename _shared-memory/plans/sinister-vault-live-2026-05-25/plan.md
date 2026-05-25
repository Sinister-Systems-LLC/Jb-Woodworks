# Sinister Vault LIVE — Sanctum-in-vault + LINK + GitHub auto + Backup

> Author: RKOJ-ELENO :: 2026-05-25
> Sub-D of sanctum iter-24. Plan ONLY — no services started/stopped.

Operator urgent 2026-05-25T07:08:40Z: "place the sinister vault live and place the entire sinster sanctum there and link to leo over sinister link and auto update that and github. and backup."

## Section 1 — Live now?

| Item | Status | Evidence |
|---|---|---|
| Vault daemon HTTP `:5078` | LIVE | `curl -v http://127.0.0.1:5078/api/vault/health` -> `200 OK`, `{"ok":true,"version":"1.0.0","uptime_s":38.1,"used_gb":0.0,"vault_root":"D:\\sinister-vault"}`. Server: uvicorn. |
| Vault tree | EXISTS | `D:\sinister-vault\` contains `repos/ sync/ gitea/ snapshots/ audit/ accounts/ _quota.json` per `tools/sinister-vault/README.md` schema. |
| Heartbeat | FRESH | `_shared-memory/heartbeats/sinister-vault.beat` mtime delta = 8 s (rule of thumb: stale > 120 s). |
| Auth model | localhost-only | Daemon binds 127.0.0.1 only; no remote socket. Multi-account profiles in `D:\sinister-vault\accounts\` (currently empty — operator + leo not provisioned). |
| Quota | 0 % of 1024 GB | `used_human: "356 B"`, `over_warn:false`, `over_max:false`. |
| `SinisterVault` schtask | REGISTERED | `schtasks /Query /TN SinisterVault` -> `Status: Ready`, `Logon Mode: Interactive only`. (Daemon already running so trigger has fired this session.) |
| `SinisterVaultGitHubSync` schtask | **MISSING** | `schtasks /Query` -> "system cannot find the file specified". `vault_github_sync.py --install-schtask` never ran. |
| Sanctum mirror in vault | **MISSING** | `_vault/sanctum-mirror/` does not exist; `vault_github_sync.py` scan-skips with `vault_missing=True`. No content has flowed through yet. |
| Gitea inside vault | UNCONFIGURED | `D:\sinister-vault\gitea\data/` is empty; `config/` present but no Sinister-Sanctum mirror repo created. |
| Syncthing | NOT VERIFIED HERE | `D:\sinister-vault\sync/` is empty. Per `docs/LEO-VAULT-SETUP.md` operator + Leo must pair Device IDs OOB. |
| Backup (3rd copy) | PARTIAL | `automations/auto-backup.ps1` exists (24 h sentinel; target `D:\Sinister Sanctum\backups\<UTC>\`) but `backups/` directory absent on disk -> never ran successfully on this machine, or every run was within 24 h. |
| GitHub origin | LIVE | `agent/sinister-sanctum/*` branches pushed via `sanctum-auto-push.ps1` daily. |
| Sinister LINK | UNLINKED | `_shared-memory/sinister-link-invites/inv-20260525020204-b1ae72.json` present (invite issued); no `sinister-link-state.json` -> Leo has not accepted. |

**Summary:** Vault daemon IS live. The three integration arms (Sanctum-in-vault mirror / vault->github auto-push schtask / 24 h backup) are partially wired but not running end-to-end. LINK has an issued invite waiting for Leo.

## Section 2 — Sanctum in vault

### Target layout (per `vault_github_sync.py` design)

```
D:\Sinister Sanctum\_vault\sanctum-mirror\<machine-id>\
   <full Sanctum tree, minus EXCLUDE_DIRS>
        .git/  node_modules/  __pycache__/  .venv/  dist/
        _vault/  _vault-backups/  _tmp/
```

`<machine-id>` = `socket.gethostname().lower().replace(" ","-")` (currently `desktop-lto4lus`) OR override via `$env:SINISTER_MACHINE_ID`. This per-machine subdir is what lets operator + Leo share the SAME mirror root without merge fights.

### Sync scheme (already coded; needs first-run + schtask install)

`automations/vault_github_sync.py` (331 lines) is the canonical idempotent sync engine. Three modes:

- `--scan` — sha256-walk vault mirror + repo, classify deltas via `PREFER_VAULT={_shared-memory/}` and `PREFER_GITHUB={automations/,docs/,deploy/,versions/,CLAUDE.md}` -> three buckets `vault_newer / github_newer / conflicts`.
- `--auto` — scan; if zero conflicts, push vault_newer to `agent/sinister-sanctum/vault-sync-<UTC>` branch + pull github_newer into mirror.
- `--install-schtask` — registers `SinisterVaultGitHubSync` schtask at 15-min cadence, `RunLevel LIMITED` (no UAC; aligns with `automate-everything-no-operator-admin` doctrine).

### Idempotent one-shot to make Sanctum live in vault

```powershell
# from D:\Sinister Sanctum\
python automations\vault_github_sync.py --pull-from-github       # seeds _vault\sanctum-mirror\<host>\ from current repo tree
python automations\vault_github_sync.py --scan                   # sanity: vault_newer=0 github_newer=0 conflicts=0
python automations\vault_github_sync.py --install-schtask        # registers 15-min auto loop
schtasks /Run /TN SinisterVaultGitHubSync                        # smoke once now
schtasks /Query /TN SinisterVaultGitHubSync /V /FO LIST          # confirm Status=Ready, LastResult=0
```

Verification: `Get-ChildItem D:\Sinister Sanctum\_vault\sanctum-mirror\desktop-lto4lus\ | Measure-Object` should return a count roughly matching `git ls-files | Measure-Object` minus excluded dirs.

## Section 3 — LINK transport=vault

Default LINK transport per `sinister-link-doctrine-2026-05-25.md` is `git` (free, 30-s-to-30-min latency). The `transport=vault` field is RESERVED but the wiring requires:

1. Both peers have the vault daemon running on `:5078`.
2. Both peers have Syncthing pairing the `D:\sinister-vault\sync\` folder via Device ID exchange (`docs/LEO-VAULT-SETUP.md` Mode A) OR Tailscale path to operator's daemon (Mode B).
3. LINK state machine writes `_shared-memory/sinister-link-state.json` with `transport: "vault"` so the 60-s poller knows to expect sub-minute deltas from Syncthing rather than git fetches.

### Concrete steps to bring LINK up for Leo

```powershell
# Operator side (already done — invite issued 2026-05-25T02:02Z)
powershell -File automations\sinister-link.ps1 -Action GenerateInvite -ExpiresMin 60

# Operator hands the printed base64 code to Leo OOB (Signal/SMS), then registers the 60-s poller:
powershell -File automations\install-sinister-link-poller.ps1

# Leo side, after running deploy/setup.py + EVE.exe on his box:
# EVE.exe -> L (Sinister LINK) -> C (Accept invite Code) -> paste code
# Leo's machine writes sinister-link-state.json pointing at operator and runs first Sync.
```

For `transport=vault` upgrade (sub-minute, large blobs), additionally:

```powershell
# Operator side:
# 1. Add Leo's Syncthing Device ID to D:\sinister-vault\accounts\leo.json (syncthing_device_id field)
# 2. Share the sinister-vault-sync folder via the Syncthing UI at http://127.0.0.1:8384
# 3. Edit sinister-link-state.json transport: "vault"  (re-pair required per doctrine)
```

NOTE: this plan does NOT alter LINK state — Leo accepting the existing invite is an operator-OOB action.

## Section 4 — Auto-update GitHub

Two independent push paths cover this:

### Path A — Branch auto-push (already shipped)

`automations/sanctum-auto-push.ps1` (per `agent-autonomy-push-and-completion-2026-05-23` doctrine):
- 30-min schtask + session-end trigger pushes the CURRENT `agent/<slug>/*` branch.
- On `main` it stages + commits + pushes; on `agent/*` it pushes existing commits only.
- Always does `git fetch --all --prune` for Leo-sync.
- Verify schtask exists:
  ```powershell
  schtasks /Query /TN SinisterSanctumAutoPush /V /FO LIST
  ```

### Path B — Vault-to-GitHub bidir (15-min, NEW — needs install)

`vault_github_sync.py --auto` (Section 2 install commands above) — every 15 min:
1. scan vault mirror vs repo tree
2. if vault has fresher files (typically `_shared-memory/` runtime state from Leo's box), checkout an `agent/sinister-sanctum/vault-sync-<UTC>` branch, copy them in, `git add` + `git commit -m "vault-sync: N files updated from vault (<machine>)"`, `git push -u origin <branch>`.
3. if GitHub has fresher files, copy them into the vault mirror (Leo's box will pick them up via Syncthing within ~5 s).

Conflict policy is deterministic + path-prefix-based (`PREFER_VAULT={_shared-memory/}`, `PREFER_GITHUB={automations/,docs/,deploy/,versions/,CLAUDE.md}`); everything else logged + skipped pending operator decision.

### Optional Path C — Gitea inside vault (NOT YET WIRED)

`D:\sinister-vault\gitea\` is the data dir for a Gitea instance that would expose `http://localhost:3000` as a private remote. Per `docs/LEO-VAULT-SETUP.md` operator runs `bootstrap-users.py --leo-key-file <leo.pub>` to provision Leo's account. Right now `gitea/data/` is empty -> Gitea binary not started. This path is OPTIONAL for the current operator ask; Paths A+B together already satisfy "auto update github". Defer until operator explicitly wants offline-private remotes.

## Section 5 — Backup (3rd copy)

### What exists

`automations/auto-backup.ps1` (v1 :: 2026-05-21):
- 24-h sentinel-gated; fires from `bootstrap-portability.ps1` on every session start.
- Target: `D:\Sinister Sanctum\backups\<YYYY-MM-DD-HHMM>\` (gitignored).
- Snapshots `_shared-memory/`, `automations/`, `docs/`, `SESSION-START/`, `SANCTUM.md`, `CLAUDE.md`, `DIRECTIVES`, `.gitignore`, `.github/workflows/`.
- Skips `_vault/`, `backups/`, `projects/*/source/`, build artifacts.

### What is broken / missing

1. `D:\Sinister Sanctum\backups\` does not exist on this machine -> auto-backup has never produced a directory, OR last run was wiped. **Fix:** run once manually + confirm sentinel
   ```powershell
   powershell -File automations\auto-backup.ps1
   Get-Item D:\Sinister Sanctum\backups\.last-backup-utc
   Get-ChildItem D:\Sinister Sanctum\backups\
   ```
2. Backup is **on the SAME drive** as Sanctum (`D:`). Drive D failure = single point of loss. **Gap:** no off-drive / off-machine 3rd copy.
3. Off-drive option 1 — vault snapshot endpoint already exists:
   ```powershell
   $body = @{ subtree="repos"; label="sanctum-daily"; actor="auto-backup" } | ConvertTo-Json
   Invoke-RestMethod -Uri http://127.0.0.1:5078/api/vault/snapshot -Method POST -Body $body -ContentType "application/json"
   ```
   Lands at `D:\sinister-vault\snapshots\<UTC-iso>-sanctum-daily\` — STILL on D:.
4. Off-machine option (recommended, NOT YET WIRED) — wrap `auto-backup.ps1` to also rclone/robocopy the snapshot to an external drive OR to GitHub via the bidir sync (already covered) OR to OneDrive / S3. Operator has not chosen the off-site target; this is the open question. Suggested default: piggy-back on Path B above so EVERY backup that lands in `backups/` also lands in GitHub via the vault mirror — that gets a third physical copy on GitHub's infra for free.

### Smoke evidence command (after install)

```powershell
powershell -File automations\auto-backup.ps1
Test-Path D:\Sinister Sanctum\backups\.last-backup-utc       # expect True
Get-ChildItem D:\Sinister Sanctum\backups\ -Directory | Select-Object -Last 1 | ForEach-Object {
    Get-ChildItem $_.FullName -Recurse -File | Measure-Object | Select-Object Count
}                                                            # expect Count > 100
```

## TL;DR — 5 fix items operator can authorize this turn

1. **Seed vault mirror:** `python automations\vault_github_sync.py --pull-from-github`
2. **Install vault<->GitHub schtask:** `python automations\vault_github_sync.py --install-schtask`
3. **Run auto-backup once:** `powershell -File automations\auto-backup.ps1`
4. **Install LINK 60-s poller (operator side):** `powershell -File automations\install-sinister-link-poller.ps1`
5. **Leo accepts existing invite OOB** (invite id `inv-20260525020204-b1ae72`) — operator hands code via Signal/SMS, Leo runs `EVE.exe -> L -> C`.

Optional follow-ups (deferred, operator decides):
- Wire Gitea + Syncthing pairing for `transport=vault` LINK upgrade (`docs/LEO-VAULT-SETUP.md` Mode A).
- Add off-machine backup target (external drive / S3 / OneDrive) — current backup is single-drive only.

## Composes with

- `sinister-vault-architecture.md` (vault primitives)
- `sinister-link-doctrine-2026-05-25.md` (LINK transport choices)
- `single-repo-push-policy-2026-05-25.md` (always agent/<slug>/* branch)
- `automate-everything-no-operator-admin-2026-05-25.md` (zero-click install, LIMITED schtask)
- `no-bullshit-tested-before-claimed-doctrine-2026-05-23.md` (claim only after smoke evidence above passes)
- `version-snapshot-disaster-recovery-doctrine-2026-05-25.md` (vault snapshot endpoint as recovery substrate)
