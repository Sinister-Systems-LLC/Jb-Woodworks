# CLAUDE.md — Sinister iMessage Bridge

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Lane:** `sinister-imessage-bridge` :: branch `agent/sinister-imessage-bridge/<short-topic>` :: purple accent
> **Lane heartbeat:** `_shared-memory/heartbeats/sinister-imessage-bridge.json`
> **PROGRESS log:** `_shared-memory/PROGRESS/Sinister iMessage Bridge.md` (created on first commit)

Lane discipline for any EVE session opened with the working directory at `D:\Sinister Sanctum\projects\sinister-imessage-bridge\`. Inherits from `D:\Sinister Sanctum\CLAUDE.md` — read that first, then this file.

## What this lane owns

- `projects/sinister-imessage-bridge/` — all of it
- `_shared-memory/PROGRESS/Sinister iMessage Bridge.md`
- `_shared-memory/heartbeats/sinister-imessage-bridge.json`
- Brain rows tagged `sinister-imessage-bridge` in `_shared-memory/knowledge/_INDEX.md`
- Branches matching `agent/sinister-imessage-bridge/*`

## What this lane NEVER touches

- The operator's primary Apple ID account configuration without explicit auth
- iMessage content of non-operator-approved contacts
- `~/.claude/.mcp.json` (operator-owned)
- `main` branch direct pushes (routes through `sanctum-auto-push` daemon)
- Other lanes' `source/` folders

## Hard rules for this lane

1. **Farm-only execution.** Every chat.db read / AppleScript send runs on the operator's Mac farm, NOT on the operator's primary daily-driver Mac or any cloud Mac that isn't operator-controlled.
2. **No outbound sends without per-thread OK during P1-P3.** P4 introduces operator-curated auto-respond rules, NOT P1-P3.
3. **No content exfil.** iMessage content stays in `Sinister Vault` + brain (where indexed). No third-party cloud, no public-facing logs.
4. **Per-contact operator opt-in.** Auto-respond rules are per-contact, opt-in by the operator (NOT default-on for the whole farm).
5. **Doctrine self-audit per Sanctum's no-bullshit doctrine.** Every claim of "received" / "sent" / "indexed" carries a chat.db query + AppleScript receipt + count in PROGRESS.

## Farm-connection assumptions (operator-supplied at P1 unlock)

When operator says "farm is online", they will provide:
- Hostname or Tailscale name of the Mac (e.g., `mac-farm-1`)
- SSH key path in vault (e.g., `_vault/farm-ssh/mac-farm-1.pem`)
- Apple ID associated with the farm
- Path to `chat.db` on the farm (default: `~/Library/Messages/chat.db`)
- Whether the farm has the operator's primary Apple ID OR a dedicated bridge Apple ID

EVE should never assume these; always read from the agreed-vault location at runtime.

## Branch hygiene

- `agent/sinister-imessage-bridge/p0-scaffold-2026-05-24` — current (scaffold)
- `agent/sinister-imessage-bridge/p1-readonly-<date>` — opens when operator connects the farm
- `agent/sinister-imessage-bridge/p2-send-<date>` — opens when P2 gated open
- `agent/sinister-imessage-bridge/p3-bridge-daemon-<date>` — opens when P3 gated open
- `agent/sinister-imessage-bridge/p4-cross-lane-<date>` — opens when P4 gated open

## First-turn checklist for a fresh EVE on this lane

1. Read `README.md` (this folder) for orientation.
2. Read this `CLAUDE.md` for lane discipline.
3. Confirm current phase status (initially P0 — scaffold only; no farm connected).
4. Heartbeat + inbox poll per Sanctum Rule 9.
5. If operator says "farm is online", read connection details from `_vault/farm-ssh/` (operator-gated) and proceed to P1 work.
6. If no farm yet, write a placeholder PROGRESS row and return to picker.
