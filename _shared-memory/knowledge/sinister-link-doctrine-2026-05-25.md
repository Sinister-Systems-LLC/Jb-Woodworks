# Sinister LINK doctrine

> Author: RKOJ-ELENO :: 2026-05-25

## Operator hard-canonical 2026-05-25 ~00:50Z (verbatim)

> "Call this Sinister LINK and do waht we need to do so that leo and i can
> link our machines so our agents and can communicate. place iut in even
> anmd have it in the main header in ready saying sinister LINK unlinked
> to eleno. then a way that we can get linked on our exe once he install
> on his pc and we can have this efficent system we already have working
> for us. find the best way to do it and do it."

## What Sinister LINK is

A thin cross-machine coordination layer that lets operator (eleno) and Leo
pair their workstations so their per-lane EVE agents can:

- See each other's heartbeats, mesh-locks, inbox, fleet-updates without
  re-architecting any of those primitives.
- Detect when both are about to edit the same file / topic and pick a
  non-overlapping slice (NO double-work, NO double-delete).
- Surface the pairing state in EVE.exe header so it's never ambiguous.

It is NOT a new transport — it composes the fleet's existing primitives.

## Composed primitives (no new infra)

| Primitive | What LINK uses it for |
|---|---|
| GitHub Sinister-Sanctum repo | Source of truth for all shared state files |
| `sanctum-auto-push.ps1` | Pushes both peers' `agent/<slug>/*` branches every 30 min + on session-end; LINK piggy-backs |
| `_shared-memory/heartbeats/` | Per-slug liveness; cross-machine after the next git pull |
| `_shared-memory/mesh-locks/` | Per-focus locks; extended w/ `owner_machine` field so peer-owned conflicts are visible |
| `_shared-memory/cross-agent/inbox/` | Per-lane messaging; cross-machine after sync |
| `_shared-memory/fleet-updates.jsonl` | Broadcast channel; carries `[LINK-UNLINK]` directives |
| Tailscale overlay (sinister-os M5) | Direct IP reachability test (ping for "alive" flag) |
| Sinister Vault (`:5078`) | Reserved for `transport=vault` (large-blob path) |

## The 4-piece system

1. `automations/sinister-link.ps1` — state machine (Status / Pair /
   GenerateInvite / AcceptInvite / Sync / Unlink / Health / ListInvites).
2. `automations/sinister-link-poller.ps1` + `install-sinister-link-poller.ps1`
   — every-60s background sync; writes `sinister-link-health.json` (per-
   machine ephemeral; not committed).
3. `automations/mesh-coordinator.ps1` extended with `owner_machine` field +
   `ListPeer` action + PEER-flag in `Check` output.
4. `automations/eve-launcher/eve.py` `_sinister_link_page()` + main_menu.py
   header line + `L) Sinister LINK` menu key.

## State files

- `_shared-memory/sinister-link-state.json` — committed; shape:
  ```
  { v, local_machine, local_display,
    peer: { name, display, tailscale_ip },
    transport, paired_at_utc, last_sync_utc, psk_hash, invite_id_used }
  ```
- `_shared-memory/sinister-link-health.json` — gitignored; per-machine
  ephemeral; updated every 60s by the poller.
- `_shared-memory/sinister-link-invites/<id>.json` — committed; tracks
  issued invites (PSK is hashed, never stored cleartext).

## Pairing flow (6 lines)

**Operator (eleno) generates invite:**
1. EVE.exe -> `L) Sinister LINK` -> `P) Generate invite` (60min default).
2. Operator copies the printed base64 invite and sends to Leo OOB (text/email).

**Leo accepts invite on his EVE.exe:**
3. EVE.exe -> `L) Sinister LINK` -> `C) Accept invite Code` -> pastes code.
4. Leo's machine writes `sinister-link-state.json` pointing at operator's
   machine; runs `Sync` to pull operator's existing heartbeats/locks/inbox.

**Both poll every 60s:**
5. `SinisterLinkPoll` scheduled task (installer ships separately) runs
   `sinister-link.ps1 -Action Sync` which does `git fetch origin --prune` +
   updates `last_sync_utc` + writes health snapshot with peer reachability.
6. EVE.exe header re-reads state every render: `Sinister LINK :: linked to
   leo (last sync 45s ago)` (green) or `STALE 12m` (red) if peer not seen.

## Header render states (operator-visible)

```
unlinked              : Sinister LINK :: unlinked  (press L to pair with peer)              [WARN/orange]
linking (no sync yet) : Sinister LINK :: linked to leo  (no sync yet)                       [PURPLE]
linked (fresh)        : Sinister LINK :: linked to leo  (last sync 45s ago)                 [OK/green]
linked (stale)        : Sinister LINK :: linked to leo (STALE 12m)  (L for diagnostics)     [WARN/orange]
```

## Transport choice — WHY git is default

- **git** (default): Existing `sanctum-auto-push` already pushes every 30
  min + on session-end. Zero new infra. Latency 30s-30min. Cost: $0/month.
- **vault**: Sinister Vault `:5078` (1TB). Use for sub-minute sync or
  large-blob exchange (e.g. binary artifacts, M5 firmware blobs). Requires
  Mode A (Leo runs own daemon) OR Mode B (Tailscale to operator's daemon)
  per `docs/LEO-VAULT-SETUP.md`.
- **tailscale-direct**: Reserved field for future; not yet implemented.
  Would push state via Tailscale-direct HTTP (sub-second latency) once
  the M5 sinister-os mesh ACL is fully wired for Leo.

The `transport` field is recorded at pairing time and propagated via the
state file. Switching transports = re-pair.

## Double-work prevention (the real product)

Both peers see the same `_shared-memory/mesh-locks/<focus>.json` files
after `sanctum-auto-push` cycles. Each lock now carries `owner_machine`.
When Leo wants to edit `automations/eve-launcher/eve.py`:

```
$ powershell -File automations/mesh-coordinator.ps1 -Action Check -Focus automations/eve-launcher/eve.py
LOCKED [PEER]: 'automations/eve-launcher/eve.py' by sanctum-sinister-link@desktop-lto4lus until 2026-05-25T01:55:30Z (hint: Building Sinister LINK header + sub-page)
```

The `[PEER]` flag tells Leo "operator is on this — pick a different
slice". The `ListPeer` action lists every lock the peer machine owns.
The same logic runs the other direction.

Mesh locks have a TTL (default 30 min); a hung agent's lock auto-expires.
Sweep runs every 10 min via `SinisterMeshCoordSweep`.

## Security model

- PSK (pre-shared key) is generated at invite time, hashed (SHA-256) into
  the state file, NEVER logged in cleartext.
- Invite codes carry the PSK in base64 JSON; they expire (default 60min).
- The PSK is currently advisory — there's no signed sync yet. The trust
  boundary is Tailscale's ACL + GitHub's repo access. Future iteration:
  use the PSK to HMAC-sign state file mutations.
- Operator can `-Action Unlink` at any time; broadcast goes via
  `fleet-update.ps1` so peer's lane agents see `[LINK-UNLINK]` in their
  cold-start poll.

## Smoke evidence (verified 2026-05-25)

7 PASS:
1. `Status` (unlinked) -> exit 0, prints `state: unlinked`.
2. `GenerateInvite -ExpiresMin 60` -> emits valid base64 invite, persists
   redacted record in `_shared-memory/sinister-link-invites/`.
3. `AcceptInvite -InviteCode <synth>` -> exit 0, writes state file.
4. `Status` (post-accept) -> exit 0, prints `state: linked`, `peer name`,
   `transport`, `last sync: (never)`.
5. Synthetic peer-owned mesh-lock + `mesh-coordinator.ps1 -Action ListPeer`
   -> lists peer's lock; `Check` returns `LOCKED [PEER]: ... exit 1`.
6. `Sync` -> exit 0, writes health snapshot with peer-reachability +
   warnings (no agent branch on origin yet / peer not pingable).
7. `Unlink` -> exit 0, clears state, broadcast posted to fleet-updates.

Python: `eve.py PARSE OK`, `main_menu.py PARSE OK`, `main_menu.py --smoke
OK`, all 4 header states render (`unlinked` WARN, `linking` PURPLE,
`linked` OK, `STALE` WARN with red brackets).

## Composes with

- `mesh-coordination-and-resource-lifecycle-2026-05-24` — cross-machine
  extension of locks
- `gradual-growth-memory-push-eve-exe-ready-2026-05-24` — operator sees
  the LINK state next render
- `agent-autonomy-push-and-completion-2026-05-23` — sanctum-auto-push is
  the carrier
- `eve-ui-uniformity-doctrine-2026-05-24` — sub-page header+body+footer
  canonical layout
- `no-bullshit-tested-before-claimed-doctrine-2026-05-23` — `shipped`
  claim backed by 7-of-7 smoke evidence above
- `leo-auto-setup-doctrine-2026-05-25` — Setup Wizard can prompt Leo to
  paste operator's invite as final onboarding step

## Open queued (operator hands)

1. Run `powershell -File automations\install-sinister-link-poller.ps1` to
   register the 60s `SinisterLinkPoll` scheduled task on operator's machine.
2. Generate first real invite to send Leo: `powershell -File automations\
   sinister-link.ps1 -Action GenerateInvite -ExpiresMin 60`.
3. Send Leo the invite code OOB (text/Signal). On Leo's first EVE.exe
   launch he sees `Sinister LINK :: unlinked (press L to pair)` in the
   header — he hits `L`, `C`, pastes the code.
4. Both peers run their installer too (operator on operator's box, Leo
   on his) so polling is symmetric.
