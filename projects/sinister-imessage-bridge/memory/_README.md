# memory/ — Sinister iMessage Bridge lane memory

> **Author:** RKOJ-ELENO :: 2026-05-24

Per-lane memory for the iMessage bridge. Cross-session learnings specific to this lane (farm IDs, AppleScript quirks, chat.db schema discoveries, anti-abuse rate limits). Fleet-wide doctrine still goes to `_shared-memory/knowledge/`.

## Files

- `decisions.md` — architectural decisions with date + rationale (e.g., AppleScript-vs-IMCore-vs-shortcut decision; per-thread vs per-contact opt-in policy).
- `gotchas.md` — every "I tried X, it broke because Y, fix is Z" learning (e.g., AppleScript permission flow on macOS Sonoma+ / chat.db SQLite WAL journaling).
- `farm-inventory.md` — connected farm hosts, Apple IDs in use, chat.db paths, SSH key handles in vault.
- `contact-policy.md` — per-contact opt-in / auto-respond rule registry (operator-managed; lane only appends with explicit OK).
- `chat-db-schema.md` — observed schema of `~/Library/Messages/chat.db` per macOS version (chat / message / handle / chat_message_join / etc).
