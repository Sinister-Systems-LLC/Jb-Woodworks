# Sinister LINK :: cross-machine pairing

> Author: RKOJ-ELENO :: 2026-05-25

Pair operator (eleno) + Leo's workstations so their EVE agents can
coordinate without stepping on each other. Built on top of GitHub +
sanctum-auto-push + mesh-coordinator + Tailscale + (optionally)
Sinister Vault — NOT a new transport.

## Quick pair (operator perspective)

1. Launch EVE.exe.
2. Header reads `Sinister LINK :: unlinked  (press L to pair with peer)`.
3. Press `L`, then `P`, accept the default 60-min expiry.
4. Copy the printed base64 invite code.
5. Send to Leo out-of-band (text / email / Signal).
6. Once Leo accepts, header flips to
   `Sinister LINK :: linked to leo  (last sync 45s ago)` (green).

## Quick pair (Leo perspective)

1. Launch EVE.exe.
2. Press `L`, then `C`.
3. Paste the invite code operator sent.
4. Header flips to `Sinister LINK :: linked to eleno  (no sync yet)`,
   then green `(last sync 45s ago)` after first sync.

## What gets synced

Everything in `_shared-memory/` that the auto-push daemon pushes:

- `heartbeats/<slug>.json` — peer's live agent slugs
- `mesh-locks/<focus>.json` — peer's active resource locks
  (now carry `owner_machine` so conflicts show `[PEER]` flag)
- `inbox/<slug>/*.json` — per-lane cross-agent messages
- `fleet-updates.jsonl` — fleet-wide broadcasts
- `PROGRESS/<slug>.md` — milestone log
- `sinister-link-state.json` — the pairing itself
- Any `agent/<peer>/*` branch the peer has pushed (visible via
  `git log` and `git diff`)

Polled every 60s by `SinisterLinkPoll` scheduled task (separate
installer; operator runs once after pairing).

## EVE.exe `L) Sinister LINK` sub-page

```
--- Sinister LINK :: cross-machine pairing ---

  state:          linked
  tag:            linked to leo (last sync 45s ago)
  local machine:  desktop-lto4lus
  local display:  operator
  peer name:      leo-machine
  peer display:   leo
  peer tailscale: 100.99.88.77
  paired at:      2026-05-25T01:12:00Z
  transport:      git
  last sync:      2026-05-25T01:15:32Z

  actions
    P) Generate invite (send to peer)   C) Accept invite Code (paste from peer)
    S) Sync now                          H) Health snapshot
    V) View peer's mesh locks            U) Unlink

--- B) Back   H) Home   X) Exit   (R)efresh   P/C/S/H/V/U)
```

## Install the 60s poller

```
powershell -File automations\install-sinister-link-poller.ps1
```

Creates `SinisterLinkPoll` scheduled task running every 1 min (Windows
schtasks floor; the .ps1 itself exits early when unlinked so steady-state
cost is one process spawn / min returning in <50ms).

Uninstall:
```
powershell -File automations\install-sinister-link-poller.ps1 -Uninstall
```

## Headless CLI

```
# Status
powershell -File automations\sinister-link.ps1 -Action Status [-Json]

# Generate invite (operator)
powershell -File automations\sinister-link.ps1 -Action GenerateInvite -ExpiresMin 60

# Accept invite (Leo)
powershell -File automations\sinister-link.ps1 -Action AcceptInvite -InviteCode <code>

# Manual sync now
powershell -File automations\sinister-link.ps1 -Action Sync

# Unlink
powershell -File automations\sinister-link.ps1 -Action Unlink

# Health
powershell -File automations\sinister-link.ps1 -Action Health

# List issued invites (own machine)
powershell -File automations\sinister-link.ps1 -Action ListInvites
```

Direct pair (no invite, when both operators are co-present):
```
powershell -File automations\sinister-link.ps1 -Action Pair `
  -PeerName leo-machine -PeerTailscaleIP 100.99.88.77 `
  -PreSharedKey <psk> -Transport git
```

## Double-work prevention

Mesh-coordinator extension means peer-owned locks show `[PEER]` flag:

```
$ powershell -File automations\mesh-coordinator.ps1 -Action Check -Focus automations\eve-launcher\eve.py
LOCKED [PEER]: 'automations\eve-launcher\eve.py' by leo-eve-lane@leo-machine until 2026-05-25T02:00:00Z (hint: Leo refactoring picker)
```

List everything peer is touching:
```
powershell -File automations\mesh-coordinator.ps1 -Action ListPeer
```

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Header stuck on STALE | Peer machine offline / Tailscale down | Verify with `tailscale ping <peer-ip>`; restart Tailscale; run `-Action Sync` manually |
| `peer git head: (none on origin yet)` | Peer has not pushed any `agent/<slug>/*` branch yet | Wait for first auto-push cycle (30 min) or have peer manually `git push -u origin agent/<slug>/...` |
| `git fetch failed` warning | No network / no GitHub auth | Run `git fetch origin` manually to surface the real error; fix auth |
| Invite expired | Default TTL is 60 min | Operator generates a new one with longer `-ExpiresMin` (e.g. 480 for 8h) |
| Want to switch transport | Currently a re-pair | `Unlink`, then re-`GenerateInvite -Transport vault` |
| Both peers paired but not seeing each other | sanctum-auto-push not running | Verify with `schtasks /Query /TN SinisterSanctumAutoPush`; reinstall if missing |

## Security notes

- PSK is in the invite code (base64 JSON). Send OOB — anyone with the
  code in the expiry window can claim to be the peer.
- PSK is hashed (SHA-256) into the state file; never logged cleartext.
- Trust boundary is Tailscale ACL + GitHub repo access. PSK is currently
  advisory (no signed sync yet).
- `Unlink` broadcasts `[LINK-UNLINK]` via fleet-update channel so peer's
  lane agents see the unlink on their next cold-start poll.

## Full doctrine

`_shared-memory/knowledge/sinister-link-doctrine-2026-05-25.md` —
design, transports, smoke evidence, composes-with chain.

`_shared-memory/knowledge/cross-machine-mesh-coord-2026-05-25.md` —
mesh-coordinator extension details.
