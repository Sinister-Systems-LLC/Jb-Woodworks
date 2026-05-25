# Sinister Term :: event_bus.py
# Author: RKOJ-ELENO :: 2026-05-25
# License: AGPL-3.0-or-later
#
# Operator trigger 2026-05-25T~12:32Z: "review cmux and see what we can use
# that for i think it may give us some great code to start on and intergreate."
#
# Clean-room port of the cmux event-bus contract from
#   https://github.com/manaflow-ai/cmux/blob/main/docs/events.md
# (cmux is GPL-3.0-or-later; AGPL-3.0 absorbs GPL — license is compatible.
# This file is implemented from the prose spec, not the Swift source, to
# preserve license flexibility downstream.)
#
# Spec mined:
#   - Event { seq (u64 monotonic), boot_id (uuid per process), ts (ns since
#     epoch), name (snake_case), category (one of: lifecycle / agent /
#     terminal / ui / network), payload (dict, capped 16 KiB serialized) }
#   - jsonl append-only writer with 16 MiB rotation per file
#   - In-memory 4096-entry ring buffer for tail subscribers
#   - subscribe(after_seq, names=[...], categories=[...]) -> generator
#     yielding Event objects; emits a single synthetic event with name
#     "bus_gap" payload {"gap": True, "dropped_count": N} when the subscriber
#     is too slow and falls off the ring (cmux "slow_consumer" semantics).
#   - boot_id changes on every process restart so subscribers can tell
#     resume-vs-cold-start apart.
#
# Substrate for upcoming ports: feed_panel (cmux Feed) consumes lifecycle +
# ui events; agent_hooks (cmux session-restore) consumes agent events;
# osc_scanner (cmux notifications) emits ui events.

from __future__ import annotations

import json
import os
import threading
import time
import uuid
from collections import deque
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable, Iterator, Optional


# -------- spec constants --------

RING_CAPACITY = 4096                 # cmux docs/events.md
MAX_PAYLOAD_BYTES = 16 * 1024        # cmux 16 KiB cap
ROTATION_THRESHOLD = 16 * 1024 * 1024  # cmux 16 MiB jsonl rotation

VALID_CATEGORIES = frozenset({"lifecycle", "agent", "terminal", "ui", "network"})


# -------- data model --------

@dataclass(frozen=True)
class Event:
    seq: int
    boot_id: str
    ts_ns: int
    name: str
    category: str
    payload: dict = field(default_factory=dict)

    def to_jsonl(self) -> str:
        return json.dumps(asdict(self), separators=(",", ":")) + "\n"

    @staticmethod
    def from_jsonl(line: str) -> "Event":
        d = json.loads(line)
        return Event(
            seq=int(d["seq"]),
            boot_id=str(d["boot_id"]),
            ts_ns=int(d["ts_ns"]),
            name=str(d["name"]),
            category=str(d["category"]),
            payload=dict(d.get("payload", {})),
        )


# -------- bus --------

class EventBus:
    """In-process event bus with ring + rotating jsonl persistence.

    Thread-safe (a single lock around publish + ring). Subscribers iterate the
    ring snapshot non-blocking; if their requested after_seq is older than the
    oldest in-ring seq, a synthetic `bus_gap` event is yielded once so the
    consumer can decide to replay from disk.
    """

    def __init__(self, jsonl_path: Path, *,
                 ring_capacity: int = RING_CAPACITY,
                 rotation_threshold: int = ROTATION_THRESHOLD):
        self._jsonl_path = Path(jsonl_path)
        self._jsonl_path.parent.mkdir(parents=True, exist_ok=True)
        self._ring_capacity = max(8, int(ring_capacity))
        self._rotation_threshold = max(512, int(rotation_threshold))
        self._ring: deque[Event] = deque(maxlen=self._ring_capacity)
        self._seq = 0
        self._boot_id = str(uuid.uuid4())
        self._lock = threading.RLock()
        # Each subscriber gets a callable that returns True to stop iteration.
        self._listeners: list[Callable[[Event], None]] = []

    # ---- core publish ----

    def publish(self, name: str, category: str, payload: Optional[dict] = None) -> Event:
        """Publish one event. Returns the published Event.

        Raises ValueError on invalid category or oversized payload.
        """
        if category not in VALID_CATEGORIES:
            raise ValueError(
                f"category {category!r} not in {sorted(VALID_CATEGORIES)}"
            )
        payload = payload or {}
        # Enforce 16 KiB cap on serialized payload (cmux spec)
        serialized_size = len(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
        if serialized_size > MAX_PAYLOAD_BYTES:
            raise ValueError(
                f"payload {serialized_size} bytes exceeds {MAX_PAYLOAD_BYTES} cap"
            )
        with self._lock:
            self._seq += 1
            ev = Event(
                seq=self._seq,
                boot_id=self._boot_id,
                ts_ns=time.time_ns(),
                name=name,
                category=category,
                payload=payload,
            )
            self._ring.append(ev)
            self._append_jsonl(ev)
            listeners_snapshot = list(self._listeners)
        # Listeners fire OUTSIDE the lock so a slow handler can't block publish.
        for fn in listeners_snapshot:
            try:
                fn(ev)
            except Exception:
                # Bus must never crash on a misbehaving listener.
                pass
        return ev

    # ---- subscription ----

    def subscribe(self, *, after_seq: int = 0,
                  names: Optional[list[str]] = None,
                  categories: Optional[list[str]] = None) -> Iterator[Event]:
        """Yield ring snapshot from `after_seq` forward, with cmux gap semantics.

        If `after_seq` is older than the oldest in-ring event, yields a single
        synthetic `bus_gap` Event (category=lifecycle) FIRST so the caller can
        replay from `replay_from_disk` and resume from the next real event.
        """
        wanted_names = set(names) if names else None
        wanted_cats = set(categories) if categories else None
        with self._lock:
            snapshot = list(self._ring)

        if not snapshot:
            return
        oldest = snapshot[0].seq
        if after_seq < oldest - 1 and after_seq != 0:
            yield Event(
                seq=oldest,  # synthetic — same seq as the first available
                boot_id=self._boot_id,
                ts_ns=time.time_ns(),
                name="bus_gap",
                category="lifecycle",
                payload={
                    "gap": True,
                    "requested_after_seq": after_seq,
                    "oldest_available_seq": oldest,
                    "dropped_count": max(0, oldest - 1 - after_seq),
                },
            )
        for ev in snapshot:
            if ev.seq <= after_seq:
                continue
            if wanted_names is not None and ev.name not in wanted_names:
                continue
            if wanted_cats is not None and ev.category not in wanted_cats:
                continue
            yield ev

    def add_listener(self, fn: Callable[[Event], None]) -> Callable[[], None]:
        """Register a fire-on-publish callback. Returns an unsubscribe fn."""
        with self._lock:
            self._listeners.append(fn)
        def _unsub() -> None:
            with self._lock:
                try:
                    self._listeners.remove(fn)
                except ValueError:
                    pass
        return _unsub

    # ---- replay ----

    def replay_from_disk(self, *, after_seq: int = 0,
                         include_rotated: bool = True) -> Iterator[Event]:
        """Read the current jsonl (and rotated siblings if requested) and yield
        Events with seq > after_seq.

        Rotated files have the same stem with a `.NNN` suffix (cmux convention).
        Yields in chronological order.
        """
        paths: list[Path] = []
        if include_rotated:
            stem = self._jsonl_path.stem
            parent = self._jsonl_path.parent
            # gather rotated siblings sorted by suffix index
            rotated = sorted(
                parent.glob(f"{stem}.*.jsonl"),
                key=lambda p: int(p.suffixes[-2].lstrip(".")) if len(p.suffixes) >= 2 and p.suffixes[-2].lstrip(".").isdigit() else 0,
            )
            paths.extend(rotated)
        if self._jsonl_path.exists():
            paths.append(self._jsonl_path)
        for p in paths:
            try:
                with p.open("r", encoding="utf-8") as fh:
                    for line in fh:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            ev = Event.from_jsonl(line)
                        except Exception:
                            continue
                        if ev.seq > after_seq:
                            yield ev
            except OSError:
                continue

    # ---- state ----

    @property
    def boot_id(self) -> str:
        return self._boot_id

    @property
    def current_seq(self) -> int:
        with self._lock:
            return self._seq

    @property
    def ring_size(self) -> int:
        with self._lock:
            return len(self._ring)

    @property
    def jsonl_path(self) -> Path:
        return self._jsonl_path

    # ---- internals ----

    def _append_jsonl(self, ev: Event) -> None:
        """Append + rotate when threshold crossed. Caller holds the lock."""
        line = ev.to_jsonl()
        # Rotate BEFORE writing if file would exceed threshold
        try:
            size = self._jsonl_path.stat().st_size if self._jsonl_path.exists() else 0
        except OSError:
            size = 0
        if size + len(line.encode("utf-8")) > self._rotation_threshold:
            self._rotate()
        try:
            with self._jsonl_path.open("a", encoding="utf-8") as fh:
                fh.write(line)
        except OSError:
            # Disk full or path gone — drop the persisted copy; in-memory
            # ring still has it. Don't crash the bus.
            pass

    def _rotate(self) -> None:
        """Move current jsonl to <stem>.NNN.jsonl with next index."""
        if not self._jsonl_path.exists():
            return
        stem = self._jsonl_path.stem
        parent = self._jsonl_path.parent
        # find max existing rotation index
        idx_max = 0
        for sib in parent.glob(f"{stem}.*.jsonl"):
            try:
                idx = int(sib.suffixes[-2].lstrip("."))
                if idx > idx_max:
                    idx_max = idx
            except (ValueError, IndexError):
                continue
        next_idx = idx_max + 1
        rotated = parent / f"{stem}.{next_idx:03d}.jsonl"
        try:
            self._jsonl_path.rename(rotated)
        except OSError:
            # Locked on Windows? Best-effort: leave current file in place.
            pass


# -------- default singleton --------

_SANCTUM_ROOT = Path(
    os.environ.get("SINISTER_SANCTUM_ROOT") or "D:/Sinister Sanctum"
)
_DEFAULT_JSONL = (
    _SANCTUM_ROOT
    / "_shared-memory"
    / "heartbeats"
    / "sinister-term-events.jsonl"
)

_DEFAULT_BUS: Optional[EventBus] = None
_DEFAULT_BUS_LOCK = threading.Lock()


def default_bus() -> EventBus:
    """Process-wide singleton for the sinister-term lane."""
    global _DEFAULT_BUS
    with _DEFAULT_BUS_LOCK:
        if _DEFAULT_BUS is None:
            _DEFAULT_BUS = EventBus(_DEFAULT_JSONL)
        return _DEFAULT_BUS


def publish(name: str, category: str, payload: Optional[dict] = None) -> Event:
    """Convenience: publish on the default bus."""
    return default_bus().publish(name, category, payload)
