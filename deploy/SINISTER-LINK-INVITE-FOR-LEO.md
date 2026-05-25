# Sinister LINK — Pair with Operator (Leo: do this AFTER first install)

**Author:** RKOJ-ELENO :: 2026-05-25
**Issued:** 2026-05-25T06:24Z · **Expires:** 2026-06-01T06:24Z (7 days) · **Invite id:** `inv-20260525022410-0c051d`

---

## What this does

Sinister LINK pairs **two machines** (operator's + Leo's) into one synchronized Sinister Sanctum workspace. Once paired, both machines can:

- See each other's running agents (fleet-updates, heartbeats, PROGRESS rows)
- Hand off in-progress work via cross-agent inbox messages
- Push to the same agent branches without stomping (mesh-coordinator handles file locks)
- Watch the same project state in real-time

It's the difference between "Leo cloned the repo" and "Leo and operator are working on the same project at the same time."

---

## Quickstart (Leo, run on YOUR machine — operator already has the daemon)

### Step 1: First-time install

If you haven't yet:

```cmd
git clone https://github.com/Sinister-Systems-LLC/Sinister-Sanctum.git "D:\Sinister Sanctum"
cd "D:\Sinister Sanctum"
python deploy\setup.py
```

This auto-elevates UAC and runs the 9-step installer (Python deps + winget Git/PowerShell + 3 scheduled tasks + Claude config seed + EVE.exe mirror + Desktop shortcut + first launch).

### Step 2: Accept the LINK invite

The invite code below is **single-use** and expires 2026-06-01. Treat it like a one-time password — don't paste it in public channels.

**Accept it:**

```powershell
powershell -File "D:\Sinister Sanctum\automations\sinister-link.ps1" -Action AcceptInvite -InviteCode "eyJleHBpcmVzX3V0YyI6IjIwMjYtMDYtMDFUMDY6MjQ6MDlaIiwiaXNzdWVyX25vdGUiOiJTaW5pc3RlciBMSU5LIGludml0ZSBmcm9tIG9wZXJhdG9yIiwiaXNzdWVkX3V0YyI6IjIwMjYtMDUtMjVUMDY6MjQ6MTBaIiwicGVlcl9kaXNwbGF5Ijoib3BlcmF0b3IiLCJwZWVyX25hbWUiOiJkZXNrdG9wLWx0bzRsdXMiLCJwc2siOiJtLWRiUnVxdDA3UkR3T1J0WURydlh2Q3giLCJ2IjoxLCJ0cmFuc3BvcnQiOiJnaXQiLCJwZWVyX3RhaWxzY2FsZV9pcCI6IiJ9"
```

Expected output:

```
Sinister LINK invite accepted
  paired-with: operator (desktop-lto4lus)
  transport:   git
  status:      LINKED — first sync starting...
```

### Step 3: Verify the link is live

```powershell
powershell -File "D:\Sinister Sanctum\automations\sinister-link.ps1" -Action Status
```

You should see two rows: your machine + operator's, both `state=LINKED`. The poller (`SinisterLinkPoller` scheduled task, 5-min cadence) keeps both sides in sync automatically — `first_time_setup.py` registered it for you.

If the row shows `state=PENDING` for >2 minutes, run:

```powershell
powershell -File "D:\Sinister Sanctum\automations\sinister-link.ps1" -Action Sync
```

…to force-poll once.

---

## Day-to-day use

Once linked, the operator's fleet-updates, PROGRESS rows, and cross-agent inbox messages flow to your `_shared-memory/` automatically (and vice versa). The flow is **git-transport**: each side commits + pushes to its own `agent/<slug>/*` branch on the same GitHub repo, and the poller `git fetch --all --prune`s the others. Single-repo policy keeps everything in `Sinister-Sanctum` (see `docs/BRANCH-CONVENTION.md`).

To **send a message** to one of operator's agents:

```powershell
powershell -File "D:\Sinister Sanctum\automations\agent-poke.ps1" -Action Poke -ToSlug sanctum -Message "Leo here — picking up the chatbot lane"
```

To **claim a project lane** that operator's fleet is also touching:

```powershell
powershell -File "D:\Sinister Sanctum\automations\mesh-coordinator.ps1" -Action Register -Focus "projects/<project-key>/<file>" -OwnerSlug leo
```

Lock + release cycles prevent edit collisions.

---

## If the invite expired before you got here

Ask operator to regenerate:

```powershell
powershell -File "D:\Sinister Sanctum\automations\sinister-link.ps1" -Action GenerateInvite -ExpiresMin 10080 -PeerName "Leo"
```

…and replace the code in this file (or use the new one out-of-band).

---

## Safety + troubleshooting

- **Single-use:** accepting consumes the invite — don't try to accept twice. Operator generates a new one if you need to re-pair.
- **PSK exposure:** the code embeds a pre-shared key. Don't paste in Discord/GitHub/Slack. Use Signal / iMessage / direct text.
- **Git transport:** both sides must have GitHub auth working (operator's installer seeds gh CLI; if Leo's first push fails with auth error, run `gh auth login` once).
- **Tailscale optional:** if both sides have Tailscale installed, the link auto-upgrades from git-transport to direct LAN sync (lower latency). Without Tailscale, git-transport works fine — just polls every 5 minutes instead of pushing realtime.
- **Pair audit log:** every pair/unpair event lands in `_shared-memory/sinister-link/audit.jsonl`. Inspect with `automations/sinister-link.ps1 -Action AuditTail -N 10`.

---

## Composes with

- `_shared-memory/knowledge/sinister-link-doctrine-2026-05-25.md` (the canonical doctrine)
- `_shared-memory/knowledge/cross-machine-mesh-coord-doctrine-2026-05-25.md` (file-lock coordination across machines)
- `_shared-memory/knowledge/single-repo-push-policy-2026-05-25.md` (both sides push to Sinister-Sanctum, never to private repos)
- `docs/SINISTER-LINK.md` (full operator + dev reference)
