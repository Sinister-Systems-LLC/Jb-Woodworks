# docs/ — design + reference

Permanent design docs for Sinister Sanctum. Read in this order:

| # | Doc | Read when |
|---|---|---|
| 1 | `ARCHITECTURE.md` | First — the 3-layer model + data flows |
| 2 | `SETUP.md` | Fresh machine — bootstrap |
| 3 | `AGENT-BOOTSTRAP.md` | Every bot reads this on cold start |
| 4 | `MCP-NETWORK.md` | Bot ↔ base MCP integration map |
| 5 | `BOT-MEMORY-PROTOCOL.md` | How `<bot>.absorb` / `forget` / smart-retrieval work |
| 6 | `ALIVE-ARCHITECTURE.md` | The 6 properties + why this system feels "alive" |
| 7 | `MEMORY-CODEC-AND-CRYPTO.md` | Token codec dictionary + at-rest Fernet vault |
| 8 | `DEPLOYMENT.md` | Per-project deploy + pre-deploy checklist |
| 9 | `DRIVE-ENCRYPTION.md` | VeraCrypt container plan (operator-decision) |

## Operator quick-references (NOT in docs/; lives in SESSION-START/)

- `SESSION-START/00-RULES.md` — TL;DR rule + delegation table + hard rules
- `SESSION-START/01-NETWORK.md` — 19-MCP-server discovery shortcuts
- `SESSION-START/02-OPERATOR-QUEUE.md` — pending operator items
- `SESSION-START/03-GOTCHAS.md` — sandbox classifier denies + green paths
- `SESSION-START/04-RECOVERY.md` — when things look wrong

## TL;DR

- **How we won:** 9 design docs cover architecture / setup / deploy / bot memory / codec / vault / drive encryption. Each addresses a distinct concern; no overlap.
- **What you need to do:** Read top-to-bottom on first visit; reference by ID afterward.
