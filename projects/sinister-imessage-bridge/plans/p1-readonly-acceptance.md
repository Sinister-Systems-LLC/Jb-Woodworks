# P1 — Read-only acceptance plan

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Phase:** P1 (read-only chat.db over SSH; no sends)
> **Unlock condition:** operator says "farm is online — host at &lt;hostname&gt;, key in vault"
> **Estimated bench time:** 20–40 min once SSH lands

This plan is the one-step P1 handoff. The moment the operator unblocks the farm, EVE follows the steps below in order and lands a single PROGRESS row containing the verification table.

---

## 0. Pre-flight (no farm needed — can be confirmed today)

| Check | How | Pass condition |
|---|---|---|
| `_vault/farm-ssh/` exists | `ls _vault/farm-ssh/` | Directory present (operator may pre-create empty) |
| Vault MCP reachable | `mcp__vault__health` | Returns `ok` |
| `ssh` binary on path | `where ssh` (Win) / `which ssh` (bash) | Returns a path |
| `sqlite3` binary on path (Win-side) | `where sqlite3` | If missing, install via `winget install --id=SQLite.SQLite` OR rely on remote `sqlite3` only |

Pre-flight result lands in PROGRESS as `scaffolded` rows; nothing here is a `smoke-tested+` claim until the farm responds.

---

## 1. Operator handoff parameters (operator provides)

When farm comes online, operator drops the following — EVE reads from vault, NEVER hardcodes:

| Parameter | Source path | Notes |
|---|---|---|
| Farm hostname / Tailscale name | `_vault/farm-ssh/<host>.meta.json` → `host` | e.g., `mac-farm-1.tail-xxxx.ts.net` |
| SSH user | same file → `user` | Often the macOS shortname of the bridge account |
| SSH key path | `_vault/farm-ssh/<host>.pem` | File mode 0600 enforced by vault daemon |
| Apple ID | same meta → `apple_id` | Used only for logging — never sent in plaintext to any third-party |
| `chat.db` path on farm | same meta → `chat_db_path` | Default: `~/Library/Messages/chat.db` |
| Is this the operator's primary Apple ID? | same meta → `is_primary` | If `true` → restrict to read-only forever; operator must explicitly authorize a dedicated bridge Apple ID before any send work |

EVE acknowledges the handoff by appending one row to `memory/farm-inventory.md` (slug + host + apple_id_redacted + first-seen-ts).

---

## 2. SSH reachability smoke

```bash
# bash on Windows (git-bash); -o BatchMode forces non-interactive
ssh -i "$KEY" -o BatchMode=yes -o ConnectTimeout=10 -o StrictHostKeyChecking=accept-new \
    "$USER@$HOST" 'sw_vers -productVersion && uname -m && date -u +%Y-%m-%dT%H:%MZ'
```

**Pass:** exit 0 + three lines (macOS version / arch / UTC ts).
**Verbs allowed:** `smoke-tested` (SSH reachability proven).
**Fail modes & fixes:**
- `Permission denied (publickey)` → key not added to farm's `~/.ssh/authorized_keys`; operator runs `ssh-copy-id`.
- `Host key verification failed` → first connect; `accept-new` flag above handles it. If still failing, key changed → manual investigate (do NOT auto-trust).
- Tailscale resolves but TCP hangs → farm asleep / not signed in; operator wakes the Mac.

---

## 3. chat.db reachability + Full-Disk-Access (FDA) smoke

macOS sandboxes `~/Library/Messages/`. SSH session inherits the SSH-server process's TCC permissions. On modern macOS (Ventura+), the SSH daemon needs **Full Disk Access** granted via `System Settings → Privacy & Security → Full Disk Access → sshd-keygen-wrapper`.

```bash
ssh -i "$KEY" "$USER@$HOST" \
    'ls -la "$HOME/Library/Messages/chat.db" 2>&1 && stat -f "%z bytes" "$HOME/Library/Messages/chat.db" 2>&1'
```

**Pass:** lists the file + a non-zero byte count.
**Fail mode (FDA not granted):** `ls: ...: Operation not permitted` → operator opens System Settings, toggles FDA for `/usr/libexec/sshd-keygen-wrapper`, may need to restart Remote Login.
**Verb if PASS:** `smoke-tested` (chat.db readable over SSH).

---

## 4. SQLite schema fingerprint (proves it's actually chat.db, not a stub)

Run on the farm; chat.db uses WAL — readers don't need write lock but SQLite snapshot is taken at query open.

```bash
ssh -i "$KEY" "$USER@$HOST" \
    'sqlite3 "$HOME/Library/Messages/chat.db" \
     "SELECT name FROM sqlite_master WHERE type=\"table\" ORDER BY name;"'
```

**Pass:** output includes at minimum `chat`, `message`, `handle`, `chat_message_join`, `chat_handle_join`, `attachment`, `chat_recoverable_message_join`. Modern macOS adds more (`unsynced_removed_items` etc.) — extras are fine; missing ones fail the check.

Persist the observed schema to `memory/chat-db-schema.md` with a heading `## macOS <ver> — observed <ts>` and the raw table list.

---

## 5. Read-only metadata queries (the "PASS" demo for P1)

All four queries below run server-side; only the small result rows traverse SSH.

### 5a. Conversation count + most-recent timestamp

```sql
SELECT
  COUNT(*) AS thread_count,
  datetime(MAX(last_read_message_timestamp)/1000000000 + 978307200, 'unixepoch', 'localtime') AS most_recent_read
FROM chat;
```

**Pass:** `thread_count` ≥ 0; if account is active, expect non-NULL `most_recent_read`.
**Note:** message timestamps are nanoseconds since `2001-01-01 UTC` (Apple epoch). The `+ 978307200` converts to Unix epoch.

### 5b. Last 5 inbound messages across all threads (no body)

```sql
SELECT
  m.ROWID AS msg_id,
  datetime(m.date/1000000000 + 978307200, 'unixepoch', 'localtime') AS sent_at,
  m.is_from_me,
  m.service,
  h.id AS handle_id,
  length(m.text) AS body_len
FROM message m
LEFT JOIN handle h ON m.handle_id = h.ROWID
WHERE m.is_from_me = 0
ORDER BY m.date DESC
LIMIT 5;
```

**Pass:** 0–5 rows return. Operator can eyeball that `handle_id` looks right (phone number / email). NO `text` column selected — we're proving the read-path without ingesting content yet.

### 5c. Per-thread message count (top 10 by volume)

```sql
SELECT
  c.ROWID AS chat_id,
  c.chat_identifier,
  c.display_name,
  COUNT(cmj.message_id) AS msg_count
FROM chat c
LEFT JOIN chat_message_join cmj ON c.ROWID = cmj.chat_id
GROUP BY c.ROWID
ORDER BY msg_count DESC
LIMIT 10;
```

**Pass:** 0–10 rows. Confirms `chat_message_join` is intact.

### 5d. iMessage-vs-SMS split (sanity)

```sql
SELECT service, COUNT(*) AS n
FROM message
GROUP BY service
ORDER BY n DESC;
```

**Pass:** services typically include `iMessage` and `SMS`. Empty result = empty mailbox (valid for a fresh bridge Apple ID).

---

## 6. Acceptance criteria — what makes P1 a PASS

P1 is `smoke-tested` (per no-bullshit doctrine §2) when **all** of the following land in one PROGRESS row, with command + exit code:

- [ ] Step 2 SSH smoke — exit 0, three-line output captured
- [ ] Step 3 FDA + chat.db `ls` — exit 0, non-zero byte count captured
- [ ] Step 4 schema fingerprint — all 7 baseline tables present, full list persisted to `memory/chat-db-schema.md`
- [ ] Step 5a–5d — all four queries exit 0; row counts captured (even zero counts are valid)
- [ ] One row appended to `memory/farm-inventory.md` (slug / host / apple_id_redacted / chat.db path / first-seen-ts)
- [ ] One brain entry added at `_shared-memory/knowledge/imessage-bridge-p1-readonly-2026-MM-DD.md` summarizing the macOS version + observed schema delta vs. this plan's baseline

P1 is `acceptance-tested` (per doctrine §1, the bar above `smoke-tested`) when EVE has tailed a NEW inbound message via the FSEvents helper (P2 prep) AND seen the row appear in the `message` table within 5s of the iPhone confirming delivery. That bar belongs to P2; do NOT claim it as part of P1.

---

## 7. What P1 deliberately does NOT do

- No `text` body selected from any query (proves the read path without ingesting message content)
- No outbound AppleScript (`send` is P2)
- No FSEvents listener (poll-based reads only; live-tail is P2)
- No bus posting (`org.sinister.Bus.iMessageReceived` belongs to P3)
- No content persistence (nothing written to vault or brain beyond the schema fingerprint + farm inventory)

---

## 8. Safety + reversibility wall

| Risk | Mitigation |
|---|---|
| Accidentally modifying chat.db | All queries are `SELECT`-only; sqlite3 opens read-only when no write attempted; WAL-aware |
| Leaking message bodies into logs | No `text` / `subject` / `attributedBody` columns selected in §5 |
| FDA grant gives SSH user broad disk access | Operator already aware (FDA is the only workable path on Ventura+); revocable via System Settings |
| Bridge Apple ID confused with operator's primary | `is_primary` flag in farm meta gates send work; primary = read-only forever unless operator explicitly authorizes |

If any §5 query takes longer than 60s, abort and surface to operator — chat.db is normally <500MB and these queries are indexed.

---

## 9. After P1 PASS — what's next

- Open `agent/sinister-imessage-bridge/p2-send-<date>` branch
- Write `plans/p2-send-acceptance.md` (AppleScript send + per-thread operator OK flow + dry-run mode)
- Open one operator-curated test thread (operator picks the contact — likely a 2nd device the operator owns) for round-trip tests
- Land first `acceptance-tested` ship: send "ping" from EVE → operator's other device → tail confirms `is_from_me=1` row → reply "pong" → tail confirms `is_from_me=0` row within 5s
