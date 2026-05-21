# Sinister Sanctum :: sinister-swarm :: smoke tests
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
from __future__ import annotations
import json, os, time
from pathlib import Path
import pytest
from sinister_swarm import (
    dm, broadcast, list_active, watch_file, mark_done, wait_for,
    detect_my_slug, set_sanctum_root,
)


@pytest.fixture
def tmp_root(tmp_path: Path, monkeypatch):
    set_sanctum_root(tmp_path)
    (tmp_path / "_shared-memory" / "heartbeats").mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("SINISTER_AGENT_SLUG", "sanctum")
    return tmp_path


def test_detect_my_slug_env_var(monkeypatch):
    monkeypatch.setenv("SINISTER_AGENT_SLUG", "forge")
    assert detect_my_slug() == "forge"
    monkeypatch.delenv("SINISTER_AGENT_SLUG", raising=False)
    monkeypatch.setenv("SINISTER_AGENT_NAME", "Sinister Term")
    assert detect_my_slug() == "sinister-term"


def test_dm_drops_inbox_file(tmp_root: Path):
    rec = dm("forge", "test message", subject="hello")
    assert rec["to"] == "forge"
    assert rec["from"] == "sanctum"
    inbox = tmp_root / "_shared-memory" / "inbox" / "forge"
    files = list(inbox.glob("*.json"))
    assert len(files) == 1


def test_broadcast_only_active(tmp_root: Path):
    hb = tmp_root / "_shared-memory" / "heartbeats"
    for slug in ("forge", "panel"):
        (hb / f"{slug}.json").write_text(json.dumps({"slug": slug}))
    stale = hb / "apk.json"
    stale.write_text(json.dumps({"slug": "apk"}))
    os.utime(stale, (time.time() - 3600, time.time() - 3600))
    drops = broadcast("test", use_mcp=False)
    slugs = {d["to"] for d in drops}
    assert "forge" in slugs and "panel" in slugs and "apk" not in slugs


def test_list_active_filters_age(tmp_root: Path):
    hb = tmp_root / "_shared-memory" / "heartbeats"
    (hb / "forge.json").write_text(json.dumps({"slug": "forge"}))
    old = hb / "old.json"
    old.write_text(json.dumps({"slug": "old"}))
    os.utime(old, (time.time() - 7200, time.time() - 7200))
    active = list_active(stale_minutes=15)
    slugs = {e["slug"] for e in active}
    assert "forge" in slugs and "old" not in slugs


def test_watch_file_baseline(tmp_root: Path):
    target = tmp_root / "watched.txt"
    target.write_text("initial")
    handle = watch_file(target, poll_seconds=0.01, blocking=False)
    assert handle.path == target
    state_dir = tmp_root / "_shared-memory" / "swarm-watch" / "sanctum"
    assert state_dir.exists()


def test_mark_done_and_wait_for(tmp_root: Path):
    mark_done("R8", result="shipped", from_slug="forge")
    rec = wait_for("forge", "R8", timeout_s=2.0, poll_seconds=0.1)
    assert rec is not None
    assert rec["task"] == "R8"
    assert rec["result"] == "shipped"


def test_wait_for_timeout(tmp_root: Path):
    rec = wait_for("nonexistent", "nope", timeout_s=0.3, poll_seconds=0.1)
    assert rec is None
