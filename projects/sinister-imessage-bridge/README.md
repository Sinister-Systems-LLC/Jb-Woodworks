# Sinister iMessage Bridge

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Lane:** `sinister-imessage-bridge` :: branch `agent/sinister-imessage-bridge/<topic>` :: purple accent
> **Status:** 🔵 P0 (scaffold landed; awaiting operator to connect the farm)
> **License:** GPL-3.0-or-later

## What this is

Sinister iMessage Bridge is the fleet's iMessage automation lane — sending, receiving, and indexing iMessages through an operator-controlled Mac farm. Once the operator connects the farm, EVE can:

- Read inbound iMessage threads (per-contact, per-group)
- Send iMessages via AppleScript / `imessage`-cli / private framework calls
- Cross-route iMessage events into the Sinister bus (so other lanes can react)
- Index conversation history for the brain / Mind graph
- Bridge to the operator's other Sinister apps (Vault → conversation backup, Forge → reply suggestions, Showmasters → client messaging)

## Operator directive (verbatim 2026-05-24)

> *"prepare a project fodler in the sanctum from the imessage pbridge and proejct and add it to the bat and eve exe start files. i will soon connect the farm so you can begin testing on it to get our systems working"*

## Quick map

| Subfolder | Role |
|---|---|
| **`plans/`** | master plan + phase plans (filled when operator connects the farm) |
| **`memory/`** | per-lane memory (decisions, gotchas, farm IDs) |
| **`docs/`** | architecture, AppleScript surface, private-framework notes |
| **`source/`** | the bridge daemon + send/receive workers + cross-lane connectors |

## Phased delivery (preview)

| Phase | Description | Status |
|---|---|---|
| **P0** | Project scaffold + lane discipline + brain entry | ✅ 2026-05-24 |
| **P1** | Operator connects the farm; lane spawns first session; first read of `chat.db` confirmed | ⏳ Awaiting farm |
| **P2** | Send-iMessage CLI proven via AppleScript on operator's owned account | ⏳ Blocked on P1 |
| **P3** | Bridge daemon — polls inbound, posts to sinister-bus, surfaces to UI | ⏳ Blocked on P2 |
| **P4** | Cross-lane connectors (Vault backup / Forge reply suggestions / Showmasters client outreach) | ⏳ Blocked on P3 |

## Surfaces this lane will touch

- **macOS `~/Library/Messages/chat.db`** (SQLite, per-account, read-only access via `osascript` or sandbox-aware path).
- **AppleScript** (`tell application "Messages" to send "<text>" to buddy "<phone>"`) — the canonical send path until private-framework recon ships.
- **iMessage private framework** (`/System/Library/PrivateFrameworks/IMCore.framework/`) — reverse-engineered SPI; reserved for P3+ if AppleScript proves insufficient.
- **Sinister bus** (cross-lane messaging) — iMessage events become `org.sinister.Bus` DBus signals on Sinister OS, sanctum-inbox messages until then.

## What EVE does on this lane

- Reads operator's iMessage farm `chat.db` (per-account, in operator-managed VM or remote Mac).
- Drafts replies via Forge memory recall (when context warrants).
- Posts cross-lane events when iMessages match operator-curated patterns.
- Never sends without explicit per-thread operator OK during P1-P3. P4 introduces operator-curated auto-respond rules.

## What EVE does NOT do

- Touch the operator's main Apple ID without explicit auth.
- Send iMessages outside operator-approved contact lists.
- Persist iMessage content outside the operator-controlled vault (no third-party cloud).
- Touch the farm's filesystem without operator-gated `farm-write` flag.

## Operator action to unlock P1

1. Connect the farm (Mac + Apple ID + iMessage signed in).
2. Tell EVE: "farm is online — token in vault, host at <hostname>".
3. Open `agent/sinister-imessage-bridge/p1-readonly-2026-MM-DD` and run the first `chat.db` read.

## Fleet integration

When P3 lands:
- Cross-lane signal: `org.sinister.Bus.iMessageReceived(thread_id, sender, body, attachments)` — any lane can subscribe.
- Sinister Vault: nightly backup of `chat.db` to the vault.
- Sinister Mind: per-contact node + edge for message frequency.
- Sinister Forge: reply suggestions via Forge memory recall.
- Showmasters: client-thread automation (per Showmasters operator approval).
