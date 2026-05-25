# Sinister Term :: tests/test_event_bus.py
# Author: RKOJ-ELENO :: 2026-05-25
# License: AGPL-3.0-or-later
#
# Cover the cmux-spec event bus contract: monotonic seq, category whitelist,
# 16 KiB payload cap, jsonl persistence + rotation, ring overflow gap, and
# subscribe filters. Spec source: cmux docs/events.md.

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest


# Ensure term package importable from the tests dir
_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


from term.event_bus import (  # noqa: E402
    EventBus,
    Event,
    MAX_PAYLOAD_BYTES,
    RING_CAPACITY,
    VALID_CATEGORIES,
)


@pytest.fixture
def bus(tmp_path: Path) -> EventBus:
    jsonl = tmp_path / "events.jsonl"
    return EventBus(jsonl, ring_capacity=64, rotation_threshold=4096)


def test_publish_assigns_monotonic_seq(bus: EventBus):
    e1 = bus.publish("a", "lifecycle")
    e2 = bus.publish("b", "lifecycle")
    e3 = bus.publish("c", "lifecycle")
    assert e1.seq == 1
    assert e2.seq == 2
    assert e3.seq == 3
    assert bus.current_seq == 3


def test_publish_writes_jsonl(bus: EventBus, tmp_path: Path):
    bus.publish("hello", "agent", {"k": "v"})
    line = bus.jsonl_path.read_text(encoding="utf-8").strip()
    parsed = json.loads(line)
    assert parsed["name"] == "hello"
    assert parsed["category"] == "agent"
    assert parsed["payload"] == {"k": "v"}
    assert parsed["seq"] == 1


def test_invalid_category_rejected(bus: EventBus):
    with pytest.raises(ValueError):
        bus.publish("x", "bogus_category")
    # Valid categories all accept
    for cat in sorted(VALID_CATEGORIES):
        bus.publish("ping", cat)


def test_oversized_payload_rejected(bus: EventBus):
    huge = "x" * (MAX_PAYLOAD_BYTES + 10)
    with pytest.raises(ValueError):
        bus.publish("big", "lifecycle", {"blob": huge})


def test_subscribe_yields_all_after_zero(bus: EventBus):
    bus.publish("a", "lifecycle")
    bus.publish("b", "agent")
    bus.publish("c", "terminal")
    got = [e.name for e in bus.subscribe(after_seq=0)]
    assert got == ["a", "b", "c"]


def test_subscribe_filters_by_name_and_category(bus: EventBus):
    bus.publish("a", "lifecycle")
    bus.publish("b", "agent")
    bus.publish("c", "agent")
    bus.publish("d", "terminal")
    by_cat = [e.name for e in bus.subscribe(categories=["agent"])]
    assert by_cat == ["b", "c"]
    by_name = [e.name for e in bus.subscribe(names=["a", "d"])]
    assert by_name == ["a", "d"]


def test_subscribe_after_seq_skips_older(bus: EventBus):
    bus.publish("a", "lifecycle")
    bus.publish("b", "lifecycle")
    bus.publish("c", "lifecycle")
    got = [e.name for e in bus.subscribe(after_seq=2)]
    assert got == ["c"]


def test_subscribe_emits_gap_when_consumer_falls_behind(tmp_path: Path):
    b = EventBus(tmp_path / "evt.jsonl", ring_capacity=8, rotation_threshold=1024)
    for i in range(20):
        b.publish(f"e{i}", "lifecycle")
    # subscriber asks for events after seq 1 but ring only kept last 8
    events = list(b.subscribe(after_seq=1))
    # First yielded event must be the synthetic gap marker
    assert events[0].name == "bus_gap"
    assert events[0].payload.get("gap") is True
    assert events[0].payload.get("dropped_count") > 0
    # Then real events follow
    assert all(e.seq > 1 for e in events[1:])


def test_replay_from_disk_returns_all(bus: EventBus):
    for i in range(5):
        bus.publish(f"e{i}", "lifecycle")
    replayed = [e.name for e in bus.replay_from_disk(after_seq=0)]
    assert replayed == ["e0", "e1", "e2", "e3", "e4"]


def test_replay_from_disk_filters_by_after_seq(bus: EventBus):
    for i in range(5):
        bus.publish(f"e{i}", "lifecycle")
    replayed = [e.seq for e in bus.replay_from_disk(after_seq=3)]
    assert replayed == [4, 5]


def test_listener_fires_on_publish(bus: EventBus):
    seen: list[Event] = []
    unsub = bus.add_listener(lambda ev: seen.append(ev))
    bus.publish("x", "ui")
    bus.publish("y", "ui")
    assert [e.name for e in seen] == ["x", "y"]
    unsub()
    bus.publish("z", "ui")
    assert [e.name for e in seen] == ["x", "y"]  # unsub took effect


def test_listener_exception_does_not_crash_bus(bus: EventBus):
    def bad(ev: Event):
        raise RuntimeError("oops")
    bus.add_listener(bad)
    # Must not raise
    e = bus.publish("survive", "lifecycle")
    assert e.seq == 1


def test_rotation_happens_at_threshold(tmp_path: Path):
    # 512 is the floor enforced by EventBus; pick exactly that so 4-5 events trigger.
    b = EventBus(
        tmp_path / "events.jsonl",
        ring_capacity=64,
        rotation_threshold=512,
    )
    for i in range(30):
        b.publish("x", "lifecycle", {"i": i, "pad": "z" * 20})
    rotated = sorted(tmp_path.glob("events.*.jsonl"))
    assert len(rotated) >= 1, f"no rotation occurred; files: {sorted(tmp_path.iterdir())}"


def test_event_jsonl_round_trip(bus: EventBus):
    e = bus.publish("trip", "network", {"host": "127.0.0.1"})
    line = e.to_jsonl()
    parsed = Event.from_jsonl(line)
    assert parsed == e


def test_boot_id_changes_per_instance(tmp_path: Path):
    b1 = EventBus(tmp_path / "a.jsonl")
    b2 = EventBus(tmp_path / "b.jsonl")
    assert b1.boot_id != b2.boot_id


def test_ring_capacity_constant_is_4096():
    # cmux docs/events.md guarantee — keep the spec value explicit
    assert RING_CAPACITY == 4096


def test_max_payload_bytes_is_16_kib():
    # cmux docs/events.md guarantee
    assert MAX_PAYLOAD_BYTES == 16 * 1024
