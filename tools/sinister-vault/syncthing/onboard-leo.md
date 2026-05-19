<!--
  Author: Claude (Opus 4.7) - Sinister Sanctum Vault-Sync Agent
  Purpose: Step-by-step guide for pairing Leo's machine with the operator's
           via Syncthing for shared real-time file sync.
-->

# Onboarding Leo to the Sinister Vault Sync

Welcome. This walks you (Leo) and the operator through pairing two machines so anything dropped in `D:\sinister-vault\sync\` on either side shows up on the other within seconds. Peer-to-peer, encrypted, no cloud.

Estimated time: 10 minutes.

---

## Part A - Leo's machine (you)

### 1. Install Syncthing
- Go to https://syncthing.net/downloads/
- Download the Windows installer (or the bare `.zip` and run `syncthing.exe` from inside).
- Run the installer / launch `syncthing.exe`.
- If Windows Defender / SmartScreen complains, click "More info" -> "Run anyway" (Syncthing is open-source and signed but not whitelisted).

### 2. Open the web UI
- Your browser should auto-launch at `http://localhost:8384/`.
- If not, open it manually.
- First-launch wizard: set a UI username/password (recommended). Pick anything; it's local-only.

### 3. Grab YOUR device ID
- Top-right menu -> **Actions** -> **Show ID**.
- A QR code + a long base32 string (looks like `XXXXXXX-XXXXXXX-XXXXXXX-XXXXXXX-XXXXXXX-XXXXXXX-XXXXXXX-XXXXXXX`) appears.
- **Copy the full string.**

### 4. Send the device ID to operator
- Send via Signal, encrypted email, or another secure channel. **Do NOT paste it in Discord / Slack / public chat.**
- The device ID itself is not a secret per se (it's a public key fingerprint), but limiting its spread keeps strangers from probing your node.

### 5. Wait for operator to add you
- Operator does Part B (below).
- A notification will pop up in your Syncthing UI: **"New Device" - operator wants to connect**.
- Click **Add Device** -> accept defaults -> **Save**.

### 6. Accept the shared folder
- Within a few seconds: another notification: **"New Folder" - operator wants to share `Sinister Vault Sync`**.
- Click **Add**.
- Pick the local path where you want the synced files - the default `~/Sync/sinister-vault` works, or use `D:\sinister-vault\sync\` to mirror operator's layout.
- Click **Save**.

### 7. Watch it sync
- Within ~10 seconds the folder will say **Up to Date**.
- Drop a test file in your folder; operator will see it on their side in a few seconds.

### 8. Optional - install RKOJ.exe
- If you want the same project console as operator, install **RKOJ** too - both consoles read the same shared project files via this folder.
- Operator will point you at the RKOJ installer location.

---

## Part B - Operator (you, the host)

Assuming `install.ps1` was run and Syncthing is up at `http://localhost:8384/`.

### 1. Add Leo's device
- Web UI -> **Add Remote Device**.
- Paste Leo's device ID into the **Device ID** field.
- **Device Name**: `Leo's Machine`
- Tab: **Sharing** -> tick `sinister-vault` (the Sinister Vault Sync folder).
- **Save**.

### 2. Share folder with Leo (if not already in step 1)
- Folder card `sinister-vault` -> **Edit** -> **Sharing** tab -> tick Leo's device -> **Save**.

### 3. Confirm pairing
- Within seconds Leo will see two notifications: device + folder. He accepts both.
- Status in operator UI: `Connected` (green) under Leo's device card.

### 4. Smoke test
- Drop `hello-leo.txt` in `D:\sinister-vault\sync\`.
- Within ~10 seconds the file appears in Leo's chosen sync path.
- Have Leo drop `hello-operator.txt`; it should land in your sync root within seconds.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| Devices never connect | Both sides must have UDP 22000 + UDP 21027 open. Re-run `install.ps1` on operator side; Leo opens those ports in Windows Defender Firewall. |
| "Out of Sync" stuck on one file | Check disk space; check file isn't held open by another process. |
| `.sync-conflict-*` file appears | Both sides edited the same file before sync caught up. Open both, merge manually, delete the conflict copy. |
| Web UI not reachable | Service stopped. Run `services.msc`, find `Syncthing`, click Start. Or use `start-syncthing.bat` for foreground mode. |
| Leo's machine on different LAN | Syncthing uses global discovery + relays by default, so different networks still work - just slower (relay-bandwidth-limited). |

---

## Daily use after onboarding

- Drop anything in `D:\sinister-vault\sync\` -> Leo gets it.
- Leo drops anything in his synced folder -> operator gets it.
- **Code repos do NOT go here.** Use Gitea (see `tools/sanctum-git/vault-integration.md`). This folder is for assets, docs, raw notes, builds, anything not version-controlled.
