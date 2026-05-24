"""Poll-based chat.db reader (P1) + thread aggregation (P2/P3).

RKOJ-ELENO :: 2026-05-24 :: phases P1-P2

Runs against any chat.db file path — the canned fixture for tests, or a
real chat.db copied from the farm. Does NOT take any write locks; opens
the DB read-only via SQLite URI mode.

The FSEvents-based live tail belongs to P3 (recv_worker/tail.py — stub
present, real implementation lands when the farm is connected).
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

APPLE_EPOCH_OFFSET = 978_307_200


@contextmanager
def open_ro(db_path: Path) -> Iterator[sqlite3.Connection]:
    """Open chat.db read-only via URI mode (no write locks)."""
    uri = f"file:{db_path.as_posix()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True, timeout=5)
    try:
        yield conn
    finally:
        conn.close()


def apple_ns_to_unix(date_ns: int) -> float:
    return (date_ns / 1_000_000_000) + APPLE_EPOCH_OFFSET


def poll_new(db_path: Path, since_rowid: int = 0, limit: int = 50) -> list[dict]:
    """Return new messages with ROWID > since_rowid (oldest first, capped at limit).

    Each message dict: rowid, sent_unix, is_from_me, service, handle, body.
    """
    with open_ro(db_path) as conn:
        rows = conn.execute(
            """
            SELECT m.ROWID, m.date, m.is_from_me, m.service, h.id, m.text
            FROM message m LEFT JOIN handle h ON m.handle_id = h.ROWID
            WHERE m.ROWID > ?
            ORDER BY m.ROWID ASC
            LIMIT ?
            """,
            (since_rowid, limit),
        ).fetchall()
    return [
        {
            "rowid": rowid,
            "sent_unix": apple_ns_to_unix(date),
            "is_from_me": bool(is_from_me),
            "service": service,
            "handle": handle,
            "body": body,
        }
        for (rowid, date, is_from_me, service, handle, body) in rows
    ]


def fetch_threads(db_path: Path, limit_per_thread: int = 50) -> list[dict]:
    """Return all threads with their last `limit_per_thread` messages."""
    with open_ro(db_path) as conn:
        chats = conn.execute(
            """
            SELECT c.ROWID, c.chat_identifier, c.display_name, c.service_name,
                   COALESCE(c.last_read_message_timestamp, 0) AS last_read_ts
            FROM chat c
            ORDER BY last_read_ts DESC
            """
        ).fetchall()
        threads = []
        for chat_id, ident, display, service, last_read_ts in chats:
            msgs = conn.execute(
                """
                SELECT m.ROWID, m.date, m.is_from_me, m.text, h.id
                FROM chat_message_join cmj
                JOIN message m ON cmj.message_id = m.ROWID
                LEFT JOIN handle h ON m.handle_id = h.ROWID
                WHERE cmj.chat_id = ?
                ORDER BY m.date DESC
                LIMIT ?
                """,
                (chat_id, limit_per_thread),
            ).fetchall()
            threads.append({
                "chat_id": chat_id,
                "chat_identifier": ident,
                "display_name": display,
                "service": service,
                "last_read_unix": apple_ns_to_unix(last_read_ts) if last_read_ts else 0,
                "messages": [
                    {
                        "rowid": rowid,
                        "sent_unix": apple_ns_to_unix(date),
                        "is_from_me": bool(is_from_me),
                        "body": body,
                        "handle": handle,
                    }
                    for (rowid, date, is_from_me, body, handle) in msgs
                ],
            })
    return threads


def schema_fingerprint(db_path: Path) -> list[str]:
    """Return sorted list of table names — used by P1 §4 fingerprint check."""
    with open_ro(db_path) as conn:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
    return [r[0] for r in rows]


BASELINE_TABLES = {
    "attachment",
    "chat",
    "chat_handle_join",
    "chat_message_join",
    "chat_recoverable_message_join",
    "handle",
    "message",
}


def verify_baseline_schema(db_path: Path) -> dict:
    """P1 §4: verify the baseline 7 tables are present."""
    observed = set(schema_fingerprint(db_path))
    missing = BASELINE_TABLES - observed
    extra = observed - BASELINE_TABLES
    return {
        "pass": not missing,
        "observed": sorted(observed),
        "missing": sorted(missing),
        "extra": sorted(extra),
    }
