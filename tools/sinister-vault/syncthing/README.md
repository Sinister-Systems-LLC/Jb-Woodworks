<!--
  Author: Claude (Opus 4.7) - Sinister Sanctum Vault-Sync Agent
  Purpose: Operator overview for the Syncthing-backed vault sync.
-->

# Sinister Vault - Syncthing Sync

Real-time peer-to-peer file sync for the Sinister Vault. Drop a file in `D:\sinister-vault\sync\` on any paired machine, every other paired machine has it within seconds. End-to-end encrypted, no central server, no third-party servers seeing your files.

Think Tresorit / Dropbox but P2P and free.

---

## Why Syncthing

| Property | Why it matters |
|---|---|
| **Peer-to-peer** | No cloud middleman. Your files go device-to-device over an encrypted TLS tunnel. |
| **Free + open-source** | MPL-2.0 license, audited cryptography, no per-seat fees, no vendor lock-in. |
| **Encrypted in transit** | All inter-device traffic is TLS 1.3 with device-pinned certs (the device IDs are cert fingerprints). |
| **Works behind NAT** | Built-in NAT traversal + relay fallback. You don't have to forward ports manually. |
| **LAN-fast** | On the same network, Syncthing uses local discovery (UDP 21027) and direct connections - basically wire speed. |
| **Cross-platform** | Operator on Windows, Leo on Windows; future contributors can be on Linux/macOS/Android with the same folder. |

---

## What gets synced

**Anything you put in `D:\sinister-vault\sync\`.** That's the entire contract.

Suggested layout inside the sync root:
```
D:\sinister-vault\sync\
  assets\          shared design assets, renders, icons
  builds\          shared compiled binaries / installers
  docs\            shared markdown notes, runbooks
  scratch\         drop-here-for-leo / drop-here-for-operator
  RKOJ-projects\   shared RKOJ console project files
```

---

## What does NOT get synced here

| Asset type | Where it lives instead |
|---|---|
| Source code, repos with history | **Gitea** (`tools/sanctum-git/`). See `tools/sanctum-git/vault-integration.md`. |
| Vault snapshots / backups | Vault daemon - separate from sync; see vault daemon docs. |
| Secrets / API keys | NOT in sync ever. Use the secrets vault (separate). |
| Anything > 4 GB per file | Syncthing handles it but you'll feel it. Use a snapshot/transport channel instead. |

The split is deliberate: **Syncthing is for live working files; Gitea is for versioned source; the vault daemon is for snapshots.** Don't mix them.

---

## Conflict resolution

When two machines edit the same file before a sync round-trip, Syncthing keeps both:

```
report.md
report.sync-conflict-20260519-104215-A1B2C3D.md
```

- Naming: `<basename>.sync-conflict-<UTC-timestamp>-<short-device-id>.<ext>`
- **You merge manually.** Syncthing never overwrites; it's safe by default.
- For text files: diff the conflict copy against the live one, merge, delete the conflict copy.
- For binary files: pick a winner, delete the loser.
- This is rare in practice because sync latency is seconds, not minutes.

---

## Versioning

Per-folder, opt-in via the web UI:

1. Folder card -> **Edit** -> **File Versioning** tab.
2. Select **Staggered File Versioning** (recommended): keeps 1/hour for a day, 1/day for a month, 1/week for a year.
3. **Max age**: default 365 days. Raise if you want more history.
4. Versions live in `.stversions/` inside the synced folder.

Vault snapshots (point-in-time backups of the *entire* vault) are separate and run by the vault daemon. Don't confuse "Syncthing versioning" (per-file history) with "vault snapshots" (whole-vault backups).

---

## Bandwidth controls

Defaults set by `config-template.xml`:
- **Send cap:** 10 MB/s (10240 KB/s)
- **Receive cap:** 10 MB/s
- **LAN exempt:** No - caps apply LAN too. Disable in UI (Settings -> Connections -> uncheck "Limit Bandwidth in LAN") if your LAN is fast and you want full speed locally.

To change live: Web UI -> **Actions** -> **Settings** -> **Connections** -> set inbound/outbound caps in KiB/s. 0 = unlimited.

---

## Ports + firewall

| Port | Proto | Purpose |
|---|---|---|
| 22000 | TCP | Sync data (primary) |
| 22000 | UDP/QUIC | Sync data (QUIC fallback / faster on lossy links) |
| 21027 | UDP | Local LAN discovery (multicast) |
| 8384  | TCP | Web UI - **loopback-only** by default (`127.0.0.1:8384`) |

`install.ps1` opens 22000 (TCP+UDP) and 21027 (UDP) automatically.

To expose the web UI to the LAN (e.g. to admin from your laptop): edit `%LOCALAPPDATA%\Syncthing\config.xml`, change `<address>127.0.0.1:8384</address>` to `0.0.0.0:8384`, restart the service, and **set a UI password first** (UI -> Settings -> GUI).

---

## File layout

```
tools/sinister-vault/syncthing/
  install.ps1            # One-shot installer (run once, as Admin)
  config-template.xml    # Pre-seeded Syncthing config
  start-syncthing.bat    # Manual foreground launcher (backup if service is down)
  onboard-leo.md         # Pairing guide for adding Leo's machine
  README.md              # This file
```

---

## Onboarding a new peer

See `onboard-leo.md`. The flow is the same for anyone (Leo, future contributors): they install Syncthing, share their device ID with you, you add them + share the folder, they accept.

---

## Operational notes

- **Service name:** `Syncthing` (NSSM-wrapped). Manage via `services.msc` or `nssm` CLI.
- **Logs:** `C:\Program Files\Syncthing\syncthing.log` + `syncthing.err.log`.
- **Web UI:** http://localhost:8384/
- **Config:** `%LOCALAPPDATA%\Syncthing\config.xml`
- **Sync root:** `D:\sinister-vault\sync\`
- **Stop sync:** `nssm stop Syncthing` (or pause the folder in UI to keep service running but freeze the folder).
