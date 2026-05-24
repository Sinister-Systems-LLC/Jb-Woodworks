# farm-inventory — registered Mac farms

> **Author:** RKOJ-ELENO :: 2026-05-24
> Append at top on first-seen. Operator-redacted handle of the Apple ID only.

## Active farms

| Slug | Host | macOS | apple_id (redacted) | chat.db path | is_primary | first_seen | last_verified |
|---|---|---|---|---|---|---|---|
| _none yet_ | — | — | — | — | — | — | — |

## Decommissioned farms

| Slug | Host | reason | decommissioned |
|---|---|---|---|
| _none yet_ | — | — | — |

## Schema notes

- **`slug`** — short kebab-case (e.g., `mac-farm-1`, `mac-mini-pro-23`). Used as path component in vault and PROGRESS rows.
- **`host`** — Tailscale hostname OR LAN IP. Real connection target; resolved via `_vault/farm-ssh/<slug>.meta.json`.
- **`macOS`** — observed at first_seen. Update `last_verified` row when OS upgrades.
- **`apple_id (redacted)`** — operator-readable redaction (e.g., `b****@apple.com`). NEVER store the full Apple ID here. Full string lives ONLY in `_vault/farm-ssh/<slug>.meta.json` under operator control.
- **`chat.db path`** — typically `~/Library/Messages/chat.db`. Custom paths (e.g., on a non-standard user) noted here.
- **`is_primary`** — `true` if this is the operator's PRIMARY Apple ID. `true` → bridge enforces READ-ONLY forever (no send work at any phase). `false` only after operator explicitly authorizes a dedicated bridge Apple ID.
- **`first_seen`** — UTC date the bridge first connected to this farm.
- **`last_verified`** — UTC date the bridge last successfully ran the P1 smoke (`§2-§5` of `plans/p1-readonly-acceptance.md`).

## Procedure when a new farm comes online

1. Operator drops `_vault/farm-ssh/<slug>.meta.json` (operator-managed; lane does NOT write here):
   ```json
   {
     "host": "mac-farm-1.tail-xxxxxx.ts.net",
     "user": "imessage-bridge",
     "key_path": "_vault/farm-ssh/mac-farm-1.pem",
     "apple_id": "<full apple id>",
     "apple_id_redacted": "b****@apple.com",
     "chat_db_path": "/Users/imessage-bridge/Library/Messages/chat.db",
     "is_primary": false,
     "macos_at_setup": "14.5"
   }
   ```
2. EVE runs P1 smoke (`plans/p1-readonly-acceptance.md` §2-§5).
3. On PASS, append a row to the **Active farms** table here (operator-redacted Apple ID only; full string stays in vault).
4. EVE writes a brain entry `_shared-memory/knowledge/imessage-bridge-farm-<slug>-2026-MM-DD.md`.

## Operator gates

- A farm with `is_primary=true` NEVER unlocks P2 send work. EVE refuses with `{"reason": "farm.is_primary=true"}`.
- A farm with `is_primary=false` unlocks P2 only after operator explicitly authorizes the dedicated bridge Apple ID (separate row added to `_shared-memory/OPERATOR-ACTION-QUEUE.md` and resolved).
- Decommissioning a farm: move the row to **Decommissioned**, then operator rotates the SSH key + revokes the bridge access on the Mac.
