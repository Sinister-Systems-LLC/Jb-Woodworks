# Sinister Sanctum :: sinister-swarm :: smoke tests
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pytest

from sinister_swarm import (
    dm,
    broadcast,
    list_active,
    watch_file,
    mark_done,
    wait_for,
    detect_my_slug,
    set_sanctum_root,
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


def test_dm_drops_inbox_file(tmp_root: Path) -> None:
    rec = dm("forge", "test message", subject="hello")
    assert rec["to"] == "forge"
    assert rec["from"] == "sanctum"
    assert rec["message"] == "test message"
    inbox_dir = tmp_root / "_shared-memory" / "inbox" / "forge"
    files = list(inbox_dir.glob("*.json"))
    assert len(files) == 1
    on_disk = json.loads(files[0].read_text(encoding="utf-8"))
    assert on_disk["subject"] == "hello"


def test_broadcast_drops_only_for_active_heartbeats(tmp_root: Path) -> None:
    hb_dir = tmp_root / "_shared-memory" / "heartbeats"
    # Active: forge + term + panel
    for slug in ("forge", "sinister-term", "panel"):
        (hb_dir / f"{slug}.json").write_text(json.dumps({"agent": slug, "slug": slug}))
    # Stale heartbeat (older than 15 min)
    stale = hb_dir / "apk.json"
    stale.write_text(json.dumps({"agent": "apk", "slug": "apk"}))
    os.utime(stale, (time.time() - 3600, time.time() - 3600))

    drops = broadcast("fleet pause incoming", subject="pause", use_mcp=False)
    slugs = {d["to"] for d in drops}
    # apk should be excluded (stale); sanctum should be excluded (self)
    assert "forge" in slugs
    assert "sinister-term" in slugs
    assert "panel" in slugs
    assert "apk" not in slugs
    assert "sanctum" not in slugs


def test_list_active_filters_by_age(tmp_root: Path) -> None:
    hb_dir = tmp_root / "_shared-memory" / "heartbeats"
    fresh = hb_dir / "forge.json"
    fresh.write_text(json.dumps({"agent": "forge", "slug": "forge"}))
    stale = hb_dir / "old.json"
    stale.write_text(json.dumps({"agent": "old", "slug": "old"}))
    os.utime(stale, (time.time() - 7200, time.time() - 7200))
    active = list_active(stale_minutes=15)
    slugs = {e["slug"] for e in active}
    assert "forge" in slugs
    assert "old" not in slugs


def test_watch_file_records_baseline_and_event(tmp_root: Path) -> None:
    target = tmp_root / "watched.txt"
    target.write_text("initial")
    handle = watch_file(target, poll_seconds=0.01, blocking=False)
    assert handle.path == target
    state_path = (
        tmp_root / "_shared-memory" / "swarm-watch" / "sanctum"
    )
    assert state_path.exists()
    # Mutate the file + check the next baseline-record reads new hash
    target.write_text("mutated")
    handle2 = watch_file(target, poll_seconds=0.01, blocking=False)
    files = list(state_path.glob("*.json"))
    assert len(files) >= 1
    state = json.loads(files[0].read_text(encoding="utf-8"))
    assert state["hash"] != ""


def test_mark_done_and_wait_for_round_trip(tmp_root: Path) -> None:
    mark_done("R8", result="mermaid_render.py shipped", from_slug="forge")
    rec = wait_for("forge", "R8", timeout_s=2.0, poll_seconds=0.1)
    assert rec is not None
    assert rec["from"] == "forge"
    assert rec["task"] == "R8"
    assert rec["result"] == "mermaid_render.py shipped"


def test_wait_for_timeout(tmp_root: Path) -> None:
    rec = wait_for("nonexistent", "nope", timeout_s=0.3, poll_seconds=0.1)
    assert rec is None
