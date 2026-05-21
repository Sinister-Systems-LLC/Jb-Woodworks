# Sinister Sanctum :: forge-memory-bridge :: smoke tests
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
"""Smoke test the disk-first store: write, recall, list, graph, consolidate, delete."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from forge_memory_bridge import (
    write,
    recall,
    ls,
    graph,
    consolidate,
    delete,
    set_root,
    SCHEMA_VERSION,
)


@pytest.fixture
def tmp_root(tmp_path: Path) -> Path:
    set_root(tmp_path)
    return tmp_path


def test_write_returns_record(tmp_root: Path) -> None:
    rec = write("sanctum", "cold-start", "Read SESSION-START in order", tags=["doctrine"])
    assert rec["schema_version"] == SCHEMA_VERSION
    assert rec["namespace"] == "sanctum"
    assert rec["key"] == "cold-start"
    assert rec["writes"] == 1
    assert rec["confidence"] == 1.0
    assert "doctrine" in rec["tags"]
    # round-trips on disk
    path = tmp_root / "sanctum" / "cold-start.json"
    assert path.exists()
    on_disk = json.loads(path.read_text(encoding="utf-8"))
    assert on_disk["key"] == "cold-start"


def test_write_upsert_increments_writes_and_confidence(tmp_root: Path) -> None:
    write("sanctum", "binding-rule", "v1")
    rec2 = write("sanctum", "binding-rule", "v2-stronger")
    assert rec2["writes"] == 2
    assert rec2["confidence"] > 1.0 - 1e-6 or rec2["confidence"] == 1.0
    assert rec2["value"] == "v2-stronger"


def test_write_no_upsert_collision_raises(tmp_root: Path) -> None:
    write("sanctum", "binding-rule", "v1")
    with pytest.raises(FileExistsError):
        write("sanctum", "binding-rule", "v2", upsert=False)


def test_recall_keyword_finds_match(tmp_root: Path) -> None:
    write("sanctum", "k1", "claude code session contracts", tags=["binding"])
    write("sanctum", "k2", "panel wave seven dashboard", tags=["panel"])
    write("forge", "k3", "textual python tui memory pane", tags=["forge"])
    hits = recall("python textual tui")
    assert len(hits) >= 1
    assert hits[0]["key"] == "k3"
    assert hits[0]["_recall_score"] > 0


def test_recall_namespace_filter(tmp_root: Path) -> None:
    write("sanctum", "k1", "alpha beta gamma")
    write("forge", "k2", "alpha beta gamma")
    hits = recall("alpha", namespace="forge")
    assert all(h["namespace"] == "forge" for h in hits)


def test_list_filters_by_tags(tmp_root: Path) -> None:
    write("sanctum", "k1", "x", tags=["doctrine", "binding"])
    write("sanctum", "k2", "y", tags=["doctrine"])
    write("sanctum", "k3", "z", tags=["binding"])
    matches = ls(tags=["doctrine", "binding"])
    keys = [r["key"] for r in matches]
    assert "k1" in keys and "k2" not in keys and "k3" not in keys


def test_graph_emits_mermaid_with_edges(tmp_root: Path) -> None:
    write("sanctum", "a", "x", tags=["alpha", "beta"])
    write("sanctum", "b", "y", tags=["alpha"])
    write("sanctum", "c", "z", tags=["beta"])
    mmd = graph(namespace="sanctum")
    assert mmd.startswith("flowchart LR")
    # 3 nodes
    assert mmd.count("[") >= 3
    # a-b share alpha; a-c share beta => 2 edges expected
    assert mmd.count("---") >= 2


def test_consolidate_dedupes_same_content_hash(tmp_root: Path) -> None:
    # Same value under two different keys creates duplicate content_hash
    write("sanctum", "doctrine-v1", "binding rule X")
    write("sanctum", "doctrine-v2", "binding rule X")
    summary = consolidate(namespace="sanctum", dry_run=False)
    assert summary["scanned"] == 2
    assert summary["duplicates_found"] == 1
    assert summary["merged"] == 1
    remaining = ls(namespace="sanctum")
    assert len(remaining) == 1


def test_delete_removes_record_and_index_entry(tmp_root: Path) -> None:
    write("sanctum", "k1", "value")
    assert delete("sanctum", "k1") is True
    assert delete("sanctum", "k1") is False
    assert ls(namespace="sanctum") == []
