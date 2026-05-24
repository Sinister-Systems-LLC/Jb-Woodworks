"""Read-path tests against the canned chat.db. RKOJ-ELENO :: 2026-05-24."""
from __future__ import annotations

from pathlib import Path

from recv_worker.poll import (
    BASELINE_TABLES,
    fetch_threads,
    poll_new,
    schema_fingerprint,
    verify_baseline_schema,
)


def test_schema_fingerprint_includes_baseline(canned_chatdb: Path) -> None:
    observed = set(schema_fingerprint(canned_chatdb))
    assert BASELINE_TABLES <= observed, f"missing baseline tables: {BASELINE_TABLES - observed}"


def test_verify_baseline_schema_pass(canned_chatdb: Path) -> None:
    result = verify_baseline_schema(canned_chatdb)
    assert result["pass"]
    assert result["missing"] == []


def test_poll_returns_all_messages_when_since_zero(canned_chatdb: Path) -> None:
    rows = poll_new(canned_chatdb, since_rowid=0, limit=100)
    assert len(rows) == 10, "canned fixture should have 10 sample messages"
    for r in rows:
        assert {"rowid", "sent_unix", "is_from_me", "service", "handle", "body"} <= r.keys()


def test_poll_respects_since(canned_chatdb: Path) -> None:
    rows = poll_new(canned_chatdb, since_rowid=7, limit=100)
    assert len(rows) == 3
    assert all(r["rowid"] > 7 for r in rows)


def test_fetch_threads_groups_by_chat(canned_chatdb: Path) -> None:
    threads = fetch_threads(canned_chatdb, limit_per_thread=50)
    assert len(threads) == 3, "canned fixture has 3 handles → 3 chats"
    total_msgs = sum(len(t["messages"]) for t in threads)
    assert total_msgs == 10


def test_threads_sorted_by_last_read_desc(canned_chatdb: Path) -> None:
    threads = fetch_threads(canned_chatdb, limit_per_thread=1)
    last_reads = [t["last_read_unix"] for t in threads]
    assert last_reads == sorted(last_reads, reverse=True)


def test_no_message_bodies_redacted(canned_chatdb: Path) -> None:
    threads = fetch_threads(canned_chatdb, limit_per_thread=50)
    for t in threads:
        for m in t["messages"]:
            assert m["body"] is not None
            assert m["body"].startswith("canned sample msg")
