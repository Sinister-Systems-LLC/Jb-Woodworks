# chat.db schema — observed reference

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Status:** baseline from public corpus + Apple docs. Real-farm fingerprint appends here on P1 PASS.

The macOS Messages.app SQLite database. Per-account, located at `~/Library/Messages/chat.db`. WAL-journaled. Owned by Messages.app process — we read it ONLY via `mode=ro` SQLite URI.

## Baseline tables (macOS 14 Sonoma reference)

The 7 tables our P1 verifier requires (`recv_worker.poll.BASELINE_TABLES`):

| Table | Role | Key columns |
|---|---|---|
| `message` | The actual messages | `ROWID`, `text`, `handle_id`, `service`, `date`, `is_from_me`, `is_read`, `is_delivered`, `is_sent`, `attributedBody`, `cache_has_attachments` |
| `chat` | Threads | `ROWID`, `guid`, `chat_identifier`, `service_name`, `display_name`, `is_archived`, `last_read_message_timestamp` |
| `handle` | Contacts/IDs | `ROWID`, `id` (phone E.164 or email), `service`, `country`, `uncanonicalized_id` |
| `chat_message_join` | M:N message↔chat | `chat_id`, `message_id`, `message_date` |
| `chat_handle_join` | M:N chat↔handle | `chat_id`, `handle_id` |
| `attachment` | File attachments | `ROWID`, `guid`, `filename`, `mime_type`, `total_bytes` |
| `chat_recoverable_message_join` | "Recently deleted" buffer | `chat_id`, `message_id` |

Sonoma+ additionally exposes (verified-extras, not required by P1):
- `unsynced_removed_items` — deletions pending iCloud sync
- `chat_message_join_deleted_messages` — soft-delete marker rows
- `message_summary_info` — body parser metadata
- `message_processing_task` — async post-processing queue
- `kvtable` — opaque key-value cache

## Timestamps — Apple epoch quirk

`message.date` and `chat.last_read_message_timestamp` are **nanoseconds since 2001-01-01 UTC**, NOT Unix epoch.

```
unix_seconds = (apple_ns / 1_000_000_000) + 978_307_200
apple_ns     = (unix_seconds - 978_307_200) * 1_000_000_000
```

`978_307_200` = Unix seconds between 1970-01-01 and 2001-01-01.

Older macOS (10.13 and earlier) used **seconds** instead of nanoseconds. Detect by magnitude: if `date < 10**12`, it's seconds, multiply by `10**9` before applying the offset. Codified in `recv_worker.poll.apple_ns_to_unix` (defensive on read).

## Body — `text` vs `attributedBody`

- `text` (TEXT) — plain string. Empty for messages composed in Messages.app from macOS 13+ (Sonoma rewrote the composer to write only `attributedBody`).
- `attributedBody` (BLOB) — `NSAttributedString` serialized as a "typedstream" archive. To extract the plain string, parse the typedstream (libraries: `imessage-exporter`, `pytypedstream`). Pure-stdlib parsing is ~150 LOC.

P0 strategy: rely on `text` until P1 confirms it's populated. If P1 observes empty `text` + populated `attributedBody`, P2 adds a typedstream decoder.

## Service column

`message.service` and `handle.service` carry:
- `iMessage` — encrypted Apple Messages
- `SMS` — cellular SMS routed through iPhone Continuity
- `RCS` — coming soon (macOS 15+) — not yet seen in production farms

`chat.service_name` mirrors but historically lagged behind by a few macOS releases. Trust `message.service` over `chat.service_name`.

## Common queries

### Conversation count + most-recent activity
```sql
SELECT COUNT(*) AS thread_count,
       datetime(MAX(last_read_message_timestamp)/1000000000 + 978307200, 'unixepoch', 'localtime') AS most_recent
FROM chat;
```

### Last 5 inbound messages (metadata only — no body)
```sql
SELECT m.ROWID, datetime(m.date/1000000000 + 978307200, 'unixepoch', 'localtime') AS sent_at,
       m.is_from_me, m.service, h.id AS handle_id, length(m.text) AS body_len
FROM message m LEFT JOIN handle h ON m.handle_id = h.ROWID
WHERE m.is_from_me = 0
ORDER BY m.date DESC LIMIT 5;
```

### Per-thread message count (top 10)
```sql
SELECT c.ROWID, c.chat_identifier, c.display_name, COUNT(cmj.message_id) AS n
FROM chat c LEFT JOIN chat_message_join cmj ON c.ROWID = cmj.chat_id
GROUP BY c.ROWID ORDER BY n DESC LIMIT 10;
```

### iMessage vs SMS split
```sql
SELECT service, COUNT(*) AS n FROM message GROUP BY service ORDER BY n DESC;
```

### Newest N messages with body (P3+ only — pulls content)
```sql
SELECT m.ROWID, datetime(m.date/1000000000 + 978307200, 'unixepoch', 'localtime') AS sent_at,
       m.is_from_me, m.service, h.id AS handle_id, m.text
FROM message m LEFT JOIN handle h ON m.handle_id = h.ROWID
WHERE m.ROWID > ?  -- since_rowid
ORDER BY m.ROWID ASC LIMIT 50;
```

## WAL + read safety

`chat.db` ships with WAL journaling (`journal_mode=WAL`). Multiple readers + one writer (Messages.app). Our pattern:
- Open via `mode=ro` URI: `sqlite3.connect("file:/path/to/chat.db?mode=ro", uri=True, timeout=5)`
- `timeout=5` — if Messages.app holds the write lock too long, our query waits up to 5s before raising `sqlite3.OperationalError`
- NEVER `BEGIN EXCLUSIVE` / `VACUUM` / `PRAGMA journal_mode=DELETE` — those would force a checkpoint that may corrupt the DB
- NEVER touch `chat.db-wal` or `chat.db-shm` directly — sqlite owns those

If a query OperationalErrors out, the bridge daemon catches it, backs off 1s, and re-tries up to 3 times before surfacing as `farm_chatdb_locked` in `/status`.

## Observed schema deltas (appended by EVE per farm)

Format per observation:
```
## <farm-slug> — macOS <ver> — observed <UTC>
- Tables present: <count>
- Baseline 7 present: yes / no (missing: ...)
- Notable extras: <list>
- Anomalies: <list>
```

(P1 PASS adds the first row here.)
