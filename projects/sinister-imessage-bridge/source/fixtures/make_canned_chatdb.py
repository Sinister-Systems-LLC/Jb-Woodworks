"""Canned chat.db fixture builder. RKOJ-ELENO :: 2026-05-24.

Generates a SQLite database that mirrors the public macOS chat.db schema
(message / chat / handle / chat_message_join / chat_handle_join / attachment)
with N sample messages across M handles. Used by every test in tests/ so
the suite runs cross-platform with no farm + no real Apple data.

Schema source: public macOS reverse-engineering corpus (commits at
github.com/yortz/iMessageDB, github.com/PeterKaminski09/baleen-imessage,
official Apple docs at developer.apple.com/library/archive/documentation).
Tracks macOS 14 (Sonoma) baseline. P1's chat-db-schema.md captures any
delta observed against the real farm.
"""
from __future__ import annotations

import argparse
import sqlite3
import time
from pathlib import Path

# Apple epoch (2001-01-01 UTC) vs Unix epoch (1970-01-01 UTC)
APPLE_EPOCH_OFFSET = 978_307_200

# Baseline message timestamp = "now" minus this many seconds, per sample row
# (most-recent first; sample[0] is newest)
SAMPLE_AGES_SEC = [60, 180, 600, 1_800, 3_600, 7_200, 86_400, 172_800, 259_200, 432_000]


def unix_to_apple_ns(unix_s: float) -> int:
    """Convert Unix epoch seconds → Apple-epoch nanoseconds (chat.db format)."""
    return int((unix_s - APPLE_EPOCH_OFFSET) * 1_000_000_000)


def build(db_path: Path) -> None:
    """Create a fresh canned chat.db at db_path with sample data."""
    if db_path.exists():
        db_path.unlink()
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()

    # --- Schema (baseline subset; real chat.db has ~30+ tables, these 7 cover P1-P3)
    cur.executescript("""
        CREATE TABLE handle (
            ROWID INTEGER PRIMARY KEY AUTOINCREMENT,
            id TEXT,                       -- phone E.164 or email
            service TEXT,                  -- 'iMessage' or 'SMS'
            country TEXT,
            uncanonicalized_id TEXT
        );
        CREATE TABLE chat (
            ROWID INTEGER PRIMARY KEY AUTOINCREMENT,
            guid TEXT,
            chat_identifier TEXT,          -- usually the handle.id for 1:1
            service_name TEXT,
            display_name TEXT,
            is_archived INTEGER DEFAULT 0,
            last_read_message_timestamp INTEGER DEFAULT 0
        );
        CREATE TABLE message (
            ROWID INTEGER PRIMARY KEY AUTOINCREMENT,
            guid TEXT,
            text TEXT,
            handle_id INTEGER,
            service TEXT,
            date INTEGER,                  -- Apple-epoch nanoseconds
            is_from_me INTEGER DEFAULT 0,
            is_read INTEGER DEFAULT 0,
            is_delivered INTEGER DEFAULT 0,
            is_sent INTEGER DEFAULT 0,
            cache_has_attachments INTEGER DEFAULT 0,
            attributedBody BLOB,
            FOREIGN KEY (handle_id) REFERENCES handle(ROWID)
        );
        CREATE TABLE chat_handle_join (
            chat_id INTEGER,
            handle_id INTEGER,
            PRIMARY KEY (chat_id, handle_id),
            FOREIGN KEY (chat_id) REFERENCES chat(ROWID),
            FOREIGN KEY (handle_id) REFERENCES handle(ROWID)
        );
        CREATE TABLE chat_message_join (
            chat_id INTEGER,
            message_id INTEGER,
            message_date INTEGER,
            PRIMARY KEY (chat_id, message_id),
            FOREIGN KEY (chat_id) REFERENCES chat(ROWID),
            FOREIGN KEY (message_id) REFERENCES message(ROWID)
        );
        CREATE TABLE attachment (
            ROWID INTEGER PRIMARY KEY AUTOINCREMENT,
            guid TEXT,
            filename TEXT,
            mime_type TEXT,
            total_bytes INTEGER
        );
        CREATE TABLE chat_recoverable_message_join (
            chat_id INTEGER,
            message_id INTEGER,
            PRIMARY KEY (chat_id, message_id)
        );

        CREATE INDEX message_date_idx ON message(date);
        CREATE INDEX message_handle_idx ON message(handle_id);
        CREATE INDEX cmj_chat_idx ON chat_message_join(chat_id);
        CREATE INDEX cmj_msg_idx ON chat_message_join(message_id);
    """)

    # --- Sample handles (3 contacts: 2 iMessage + 1 SMS)
    handles = [
        (1, "+15551112222", "iMessage"),
        (2, "+15553334444", "iMessage"),
        (3, "+15555556666", "SMS"),
    ]
    cur.executemany(
        "INSERT INTO handle (ROWID, id, service, country) VALUES (?, ?, ?, 'us')",
        handles,
    )

    # --- One chat per handle (1:1 threads)
    chats = [
        (1, "iMessage;-;+15551112222", "+15551112222", "iMessage", None),
        (2, "iMessage;-;+15553334444", "+15553334444", "iMessage", None),
        (3, "SMS;-;+15555556666",      "+15555556666", "SMS",      None),
    ]
    cur.executemany(
        "INSERT INTO chat (ROWID, guid, chat_identifier, service_name, display_name) "
        "VALUES (?, ?, ?, ?, ?)",
        chats,
    )
    cur.executemany(
        "INSERT INTO chat_handle_join (chat_id, handle_id) VALUES (?, ?)",
        [(c[0], c[0]) for c in chats],
    )

    # --- Sample messages, alternating inbound + outbound across the 3 handles
    now_unix = time.time()
    rows = []
    for i, age in enumerate(SAMPLE_AGES_SEC):
        ts_unix = now_unix - age
        ts_apple_ns = unix_to_apple_ns(ts_unix)
        handle_id = (i % 3) + 1
        is_from_me = i % 2  # alternate
        body = f"canned sample msg #{i + 1} (from {'me' if is_from_me else handles[handle_id - 1][1]})"
        service = handles[handle_id - 1][2]
        rows.append((
            i + 1,                          # ROWID
            f"GUID-{i + 1:08x}",            # guid
            body,                           # text
            handle_id,
            service,
            ts_apple_ns,
            is_from_me,
            1,                              # is_read
            1,                              # is_delivered
            1 if is_from_me else 0,         # is_sent
        ))
    cur.executemany(
        "INSERT INTO message (ROWID, guid, text, handle_id, service, date, "
        "is_from_me, is_read, is_delivered, is_sent) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        rows,
    )
    # join messages to chats
    cur.executemany(
        "INSERT INTO chat_message_join (chat_id, message_id, message_date) "
        "VALUES (?, ?, ?)",
        [(r[3], r[0], r[5]) for r in rows],
    )

    # --- Update each chat's last_read_message_timestamp to the newest msg
    cur.execute("""
        UPDATE chat SET last_read_message_timestamp = (
            SELECT MAX(message_date) FROM chat_message_join WHERE chat_id = chat.ROWID
        )
    """)

    conn.commit()
    conn.close()


def main() -> int:
    p = argparse.ArgumentParser(description="Build a canned chat.db fixture.")
    p.add_argument("--out", default="canned-chat.db", help="output file path")
    args = p.parse_args()
    out = Path(args.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    build(out)
    print(f"[fixtures] built canned chat.db at {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
