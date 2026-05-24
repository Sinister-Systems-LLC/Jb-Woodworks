# P4 — Cross-lane integration acceptance plan

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Phase:** P4 (per-lane wiring + operator-curated auto-respond rules)
> **Unlock condition:** P3 (`plans/p3-bridge-daemon-acceptance.md`) is `acceptance-tested` PASS
> **Estimated bench time:** 4–8 h spread across multiple sub-phases (one lane per session)

P4 is the FIRST phase that sends without per-message operator OK. Sub-phases land independently — each subscribing lane is its own acceptance gate.

---

## 0. P4 sub-phase map (each is its own session)

| Sub | Subscribing lane | Effort | Operator-blocking? |
|---|---|---|---|
| P4.1 | **vault** — nightly chat.db backup | small | No (read-only) |
| P4.2 | **mind** — per-contact graph node + edge | small | No (metadata only) |
| P4.3 | **forge** — reply suggestions via Forge memory recall | medium | No (suggestions only, no send) |
| P4.4 | **showmasters** | medium | YES — per-Showmasters operator approval needed |
| P4.5 | **auto-respond rules** — operator-curated, per-contact, single pattern | medium | YES — operator opt-in per rule |

Order rationale: read-only + suggestions ship first (zero send risk); then operator opens auto-respond per-contact.

---

## P4.1 — Vault: nightly chat.db backup

**What:** snapshot the farm's `chat.db` into Sinister Vault every 24h.

**How:**
- Vault MCP `mcp__vault__snapshot` with key `imessage/farm/<host>/chat-<YYYYMMDD>.db`
- bridge_daemon adds a cron-like task (apscheduler `cron` trigger, 03:00 local)
- Snapshot path: `_vault/imessage/<host>/chat-<YYYYMMDD>.db` (gitignored; vault-managed)
- Backup is full-copy not incremental (chat.db is typically <500MB; WAL-aware copy via `sqlite3.backup` API)

**Pass:**
- One snapshot lands per night for 3 consecutive nights
- Vault audit log shows each `commit` event
- Restore-from-backup smoke: pick a snapshot, `sqlite3 ... "SELECT COUNT(*) FROM message"` matches the live count at backup time (±0)

---

## P4.2 — Mind: per-contact graph

**What:** every inbound iMessage updates a node in the Mind graph for the sending contact.

**How:**
- Subscribe to `iMessageReceived` events
- Upsert node `contact:<handle>` with `last_seen`, `msg_count`, `service` fields
- Add edge `(contact:<handle>) -[:MESSAGED]-> (sinister-imessage-bridge)` with `count` weight
- Use the existing Mind graph daemon (assumed Neo4j or similar — confirm at unlock)

**Pass:**
- After 50 inbound messages across 5 distinct handles, the graph shows 5 contact nodes with correct counts
- No body content stored in the graph (counts + timestamps only — content lives in chat.db backup, mind is the index)

---

## P4.3 — Forge: reply suggestions

**What:** when an inbound message lands, Forge proposes 1–3 reply candidates rendered in the dashboard UI side panel. Operator clicks to accept (which routes through `POST /send` with `operator_ok=true`).

**How:**
- bridge_daemon publishes inbound to Forge memory-recall API
- Forge returns N candidates with confidence scores
- Dashboard UI shows them under the message stream
- Click → `POST /send` with `operator_ok=true` (the click IS the operator OK)

**Pass:**
- 10 inbound test messages → ≥7 produce at least one suggestion within 3s
- Operator-accepted suggestion sends correctly (round-trip per P2 §3)
- Operator-ignored suggestion gracefully expires after 60s (no auto-send, no nag)

---

## P4.4 — Showmasters: client-thread routing

**What:** inbound from a known-client handle routes to the Showmasters lane queue.

**OPERATOR GATE:** Showmasters operator must opt in per-client. Lane discipline: this lane (`sinister-imessage-bridge`) does NOT touch Showmasters business logic; it routes events and waits.

**How:**
- `memory/contact-policy.md` adds a `client_route` column mapping `handle → lane`
- bridge_daemon checks the column on inbound; if matched, posts a `cross-agent/<ts>-from-imessage-to-showmasters-clientmsg.json` event
- Showmasters reads its inbox per Sanctum Rule 9 and handles

**Pass:**
- One Showmasters client test thread → 5 inbounds → 5 inbox messages land in `_shared-memory/inbox/showmasters/` within 5s each
- Showmasters operator confirms the routing matches their workflow

---

## P4.5 — Auto-respond rules

**What:** the FIRST sends without per-message operator OK. Each rule is per-contact, per-pattern, operator-opt-in.

**Rule schema (in `memory/contact-policy.md`):**

```markdown
| handle | pattern (regex) | action | template | operator_signed |
|---|---|---|---|---|
| +15551234567 | ^pong$ | reply_template | "ping" | yes (2026-MM-DD) |
```

**Constraints (binding):**
- One rule per (handle, pattern). Conflict → operator-resolves before either fires.
- Max 1 auto-reply per inbound (no chains, no loops).
- Rate-limit per (handle, rule): max 5/hr.
- Operator gets a `cross-agent/<ts>-from-imessage-autoresponded.json` notification on every fire (silent fires forbidden).
- Operator can kill-switch all auto-respond rules via `POST /autorespond/disable` (sets a flag; bridge_daemon checks before every send).

**Pass:**
- One rule active for one contact
- 3 trigger messages → 3 auto-replies sent + 3 notifications land in sanctum inbox
- Kill-switch test: `POST /autorespond/disable` → next trigger does NOT send + notification reads `autorespond_disabled`
- 24h soak: no rule fires more than 5×/hr; no chain-loops observed

---

## P4 acceptance summary

P4 is `acceptance-tested` when:
- [ ] At least one of P4.1, P4.2, P4.3 has landed and is producing daily evidence in PROGRESS for 7 consecutive days
- [ ] P4.5 has ONE active operator-signed rule running cleanly for 7 days with kill-switch verified
- [ ] No "false positive" incidents (auto-reply to wrong contact / wrong pattern / wrong template) over the 7-day soak
- [ ] Brain entry `_shared-memory/knowledge/imessage-bridge-p4-cross-lane-2026-MM-DD.md` summarizing the per-lane integration patterns + indexed

---

## Safety + reversibility wall (P4-specific)

| Risk | Mitigation |
|---|---|
| Auto-respond chain loop (bot replies trigger bot replies) | RATE_GAP_SEC=5 from P2 + per-rule rate-limit + max 1 auto-reply per inbound + `is_from_me=1` filter (never auto-reply to self) |
| Operator wants to disable everything fast | Kill-switch endpoint `POST /autorespond/disable` settable from dashboard one click; flag checked before every auto-send |
| Wrong-contact send (rule misfires) | Operator-signed column in `contact-policy.md`; bridge_daemon refuses unsigned rules at boot |
| Vault backup contains sensitive content | Vault is operator-controlled, encrypted-at-rest; no third-party cloud; daily audit-log review by operator |
| Cross-lane event explosion (subscribers fire too much) | per-subscriber rate-limit at the bus layer; subscribers with sustained >100 events/hr get a warning row in operator queue |

---

## After P4 PASS — sustaining mode

Lane shifts to maintenance:
- New auto-respond rules added per operator request (each is an operator-signed `contact-policy.md` row + restart)
- Cross-lane integrations expand as new lanes come online
- Quarterly forever-improve review per Sanctum doctrine
- Monthly snapshot of `memory/decisions.md` + `gotchas.md` into the brain for cross-lane reuse
