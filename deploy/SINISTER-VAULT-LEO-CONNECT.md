# Leo - Sinister Vault Connect (Live)

> **Author:** RKOJ-ELENO :: 2026-05-25

Operator (verbatim 2026-05-25 ~07:08Z): *"i need the sinister link system to work so leo and i can connect our eve's like we talked about. place the sinister vault live and place the entire sinster sanctum there and link to leo over sinister link and auto update that and github. and backup."*

This is **Leo's side** of the vault-backed Sinister LINK connect flow. Operator has the vault daemon LIVE on `:5078`, Sanctum mirrored at `D:\sinister-vault\sanctum-mirror\<operator-host>\`, and the LINK transport wired. Follow this doc to mirror that state on your machine, then pair.

Cross-links: `docs/LEO-VAULT-SETUP.md` (one-page intro), `tools/sinister-vault/AUTOSTART.md` (daemon details), `_shared-memory/knowledge/sinister-vault-live-doctrine-2026-05-25.md` (full doctrine).

---

## 1. Pick your mode

| Mode | When to use | Trade-off |
|---|---|---|
| **A. Own daemon** | You want offline-first; vault works without operator's PC | Heavier (Python venv + Syncthing local) |
| **B. Tailscale to operator's daemon** | You want lightest footprint | Depends on operator's PC being online |

Mode A is recommended -- Syncthing handles divergence on reconnect and you get a full local 1 TB store.

---

## 2. Mode A - Own daemon (recommended)

### 2.1 Clone Sanctum to canonical path

```powershell
git clone https://github.com/<operator>/Sinister-Sanctum.git "D:\Sinister Sanctum"
cd "D:\Sinister Sanctum"
git checkout leo-ready-2026-05-23   # last end-to-end tested snapshot
```

### 2.2 Bootstrap the vault daemon

```powershell
cd "D:\Sinister Sanctum\tools\sinister-vault"
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\python.exe daemon.py --port 5078
# Should print: "starting vault daemon v1.0.0 on 127.0.0.1:5078 ..."
# Ctrl+C to stop after verifying.
```

### 2.3 Make it auto-start at logon

Drop a 5-line `.cmd` shim into your Startup folder (no admin required; the
schtask path needs Administrator, so the operator's machine + yours both use
this fallback per `automate-everything-no-operator-admin` doctrine):

```powershell
$startup = [Environment]::GetFolderPath('Startup')
@"
@echo off
tasklist /FI "IMAGENAME eq python.exe" /V 2>nul | findstr /I "daemon.py" >nul && exit /b 0
start "" /B "D:\Sinister Sanctum\tools\sinister-vault\.venv\Scripts\pythonw.exe" "D:\Sinister Sanctum\tools\sinister-vault\daemon.py" --port 5078
"@ | Set-Content -LiteralPath (Join-Path $startup 'SinisterVaultDaemon.cmd') -Encoding ASCII
```

Verify:

```powershell
Invoke-RestMethod http://127.0.0.1:5078/api/vault/health
# {ok:true, version:'1.0.0', uptime_s:N, ...}
```

### 2.4 Pull operator's Sanctum mirror

The vault's `sanctum-mirror/<operator-host>/` subtree will replicate to you
via Syncthing once paired (next step). Until then it's empty.

After Syncthing is up, your side runs the read-side helper to drop the
operator's mirror over your own checkout (read-only fast-forward):

```powershell
python "D:\Sinister Sanctum\automations\sanctum_to_vault_mirror.py" --dry-run
# Prints what your machine would push to vault under sanctum-mirror/<your-host>/
```

You ALSO mirror your own machine into vault (15-min cadence) so operator
gets your view:

```powershell
python "D:\Sinister Sanctum\automations\sanctum_to_vault_mirror.py" --install-schtask
```

### 2.5 Pair Syncthing with operator

1. Install Syncthing: https://syncthing.net/downloads/
2. Launch -> opens `http://127.0.0.1:8384`.
3. Copy your Device ID (Actions -> Show ID).
4. Send to operator via Signal / SMS (NEVER over GitHub or email).
5. Operator adds your device + shares the `sinister-vault-sync` folder.
   Accept the share on your side; folder path = `D:\sinister-vault\sync\`.
6. Operator pastes your device ID into `_vault/accounts/leo.json`
   (`syncthing_device_id` field) and restarts `SinisterVaultDaemon`.

LAN sync <2s; WAN ~5s. Test by touching a file under `sync/`:

```powershell
"hello from leo" | Set-Content "D:\sinister-vault\sync\leo-ping.txt"
# Operator: Get-Content "D:\sinister-vault\sync\leo-ping.txt" within seconds
```

---

## 3. Mode B - Tailscale to operator's daemon

Use when you want lightest footprint and operator's PC is reliably online.

```powershell
# 3.1 Install Tailscale, sign in, join operator's tailnet (operator approves)
# 3.2 Point Sanctum at operator's daemon
setx SINISTER_VAULT_HOST "http://<operator-tailscale-name>:5078"
# Open a new PowerShell so the env-var loads.
Invoke-RestMethod $env:SINISTER_VAULT_HOST/api/vault/health
```

No local daemon needed. Syncthing still recommended for blob replication;
the daemon API only carries the control plane.

---

## 4. Accept a Sinister LINK invite (vault transport)

Operator generates an invite tagged `-Transport vault`:

```powershell
# Operator side:
& "D:\Sinister Sanctum\automations\sinister-link.ps1" `
    -Action GenerateInvite -Transport vault -ExpiresMin 120
# Returns: invite-id + base64 invite blob; operator sends blob to you OOB.
```

You accept:

```powershell
# Leo side:
& "D:\Sinister Sanctum\automations\sinister-link.ps1" `
    -Action AcceptInvite -InviteCode <base64-from-operator>
# Wires _shared-memory/sinister-link-state.json to vault transport.
```

Verify transport health:

```powershell
python "D:\Sinister Sanctum\automations\sinister_link_vault_transport.py" --health
# {ok:true, daemon_url:'http://127.0.0.1:5078', bucket_count:N, actor:'leo'}
```

Push a test payload from one side, pull from the other:

```powershell
# Operator:
"hello leo" | Set-Content C:\tmp\ping.json
python "D:\Sinister Sanctum\automations\sinister_link_vault_transport.py" `
    --push <invite-id> --payload C:\tmp\ping.json

# Leo (within ~5s):
python "D:\Sinister Sanctum\automations\sinister_link_vault_transport.py" `
    --pull <invite-id> --out C:\tmp\got.json
Get-Content C:\tmp\got.json   # -> "hello leo"
```

---

## 5. Daily flow

1. Boot your PC -> Startup shim launches the vault daemon.
2. Double-click `Sinister Start.bat` -> EVE picker -> pick a project lane.
3. EVE spawns with `--dangerously-skip-permissions`.
4. Your agents auto-mirror Sanctum -> vault -> Syncthing -> operator (15-min).
5. LINK state syncs sub-minute via vault transport (`sync/sinister-link/`).
6. Audit stream visible on both sides at `D:\sinister-vault\audit\<date>.jsonl`.
7. Per-agent branches: `agent/<slug>/<topic>`; auto-push every 30 min.

---

## 6. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `Connection refused` on :5078 | Daemon not up | Re-run Startup shim or `python daemon.py --port 5078` |
| LINK push not landing on peer | Syncthing not paired | Check `http://127.0.0.1:8384`; same folder ID both sides |
| `404 no such bucket` on pull | Invite-id typo or Syncthing lag | `--list` to see your buckets |
| Vault `over_warn` | >950 GB used | `Invoke-RestMethod /api/vault/quota` -> trim snapshots |
| `daemon at .. not reachable` from transport | Mode B and operator offline | Run own daemon (Mode A) OR wait |
| Mirror skipping all files | Wrong working dir | All paths are absolute; check `SANCTUM_ROOT` const |

Full troubleshooting matrix: `tools/sinister-vault/AUTOSTART.md`.

---

## 7. Pass criterion

From your clean machine:

1. Clone Sanctum at `D:\Sinister Sanctum`.
2. Run vault bootstrap (2.2 + 2.3 above) -> daemon answers `/api/vault/health`.
3. Pair Syncthing with operator (2.5) -> `sync/sinister-link/` exchange works.
4. Operator generates vault-transport invite; you accept -> LINK state has `transport: vault`.
5. Push/pull round-trip <30s.
6. Run `python sanctum_to_vault_mirror.py` -> non-zero `copied` count, exit 0.
7. After 15 min, operator's machine sees your `sanctum-mirror/<your-host>/` populated.

If any of those fails: see Troubleshooting matrix above, then post to the
shared audit stream (`POST /api/vault/audit`) so the operator sees the
failure live.

---

## 8. What NOT to touch

- `~/.claude/.mcp.json` (operator-gated; agents never edit)
- `_vault/auth-keys-DELIVER-TO-LEO.txt` (operator-private)
- Per-project source under `projects/*/source/` (lane owners only)
- `main` branch (only `sanctum-auto-push` daemon writes there)
