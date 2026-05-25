#!/usr/bin/env python3
# Author: RKOJ-ELENO :: 2026-05-25
# utterance_sweep_ack.py -- batch-ack legacy status=new operator utterances
# whose intent is now covered by hard-canonical doctrine blocks in CLAUDE.md.
#
# Scope: ONLY universally-absorbed utterances (loop / swarm / pause / mode-flip
# / "keep working" continuation directives). Phone / keybox / snap-API / lane-
# specific rows are LEFT in status=new for their respective lane owners per
# sanctum-scope-discipline.
#
# Idempotent: re-running with same ack-map does nothing (status already
# acknowledged).

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

SANCTUM_ROOT = Path(r"D:\Sinister Sanctum")
JSONL = SANCTUM_ROOT / "_shared-memory" / "operator-utterances.jsonl"
LOCK = SANCTUM_ROOT / "_shared-memory" / ".operator-utterances.lock"

# Map of {ts_utc: (status, deliverable_text)}. Only universal-doctrine-covered
# rows are listed. Lane-specific rows (phone/keybox/snap) stay status=new.
ACK_MAP: dict[str, tuple[str, str]] = {
    # Loop continuation directives -- now covered by loop-relentless-pursuit-doctrine-2026-05-25.
    "2026-05-24T12:25:00Z": (
        "acknowledged",
        "Covered by CLAUDE.md hard-canonical LOOP MODE = RELENTLESS (rules 1-11). Loop-relentless watchdog schtask fires every 5min; agents pursue queue until empty.",
    ),
    "2026-05-24T12:53:00Z": (
        "acknowledged",
        "Same coverage: loop-relentless-pursuit-doctrine-2026-05-25.md + safe-quality-loops-doctrine-2026-05-24.md.",
    ),
    "2026-05-24T13:19:35Z": (
        "acknowledged",
        "Cross-lane help covered by mesh-coordinator + cross-agent-inbox flow; sanctum lane is the orchestration target (per sanctum-scope-discipline).",
    ),
    "2026-05-24T14:00:24Z": (
        "acknowledged",
        "Efficiency loop continuous via forever-improve.ps1 + safe-quality-loops 12 guardrails; cross-lane help via mesh-coord.",
    ),
    "2026-05-24T14:25:43Z": (
        "acknowledged",
        "Cross-lane help is canonical loop behavior per loop-relentless rule 8 (RELENTLESS PURSUIT) + sanctum is master orchestration lane.",
    ),
    "2026-05-24T14:36:56Z": (
        "acknowledged",
        "Pause + document: PROGRESS rows per-lane append-only; brain entries indexed in _INDEX.md; no-bullshit doctrine rule 1 (precise verbs) + rule 7 (concise summaries) cover this.",
    ),
    "2026-05-24T15:36:01Z": (
        "acknowledged",
        "Swarm default ON: agent-prefs.json default_modes.swarm + projects.json fleet_default_modes.swarm + start-sinister-session.ps1 defSwarm=true. Doctrine: loop-swarm-default-on-doctrine-2026-05-25.md.",
    ),
    "2026-05-24T15:40:57Z": (
        "acknowledged",
        "Sinister OS preparation in flight as a separate project lane (projects/sinister-os/). Not sanctum scope; routed to sinister-os lane owner.",
    ),
    "2026-05-24T18:05:13Z": (
        "acknowledged",
        "Mode-flip is a fleet primitive: SINISTER_FORCE_MODE_FLIP env + start-sinister-session.ps1 mode prompts; sinister-os already opted-in. Covered by doctrine.",
    ),
}


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _acquire_lock(timeout_s: int = 10) -> bool:
    start = time.time()
    while time.time() - start < timeout_s:
        try:
            LOCK.touch(exist_ok=False)
            return True
        except FileExistsError:
            time.sleep(0.1)
    return False


def _release_lock() -> None:
    try:
        LOCK.unlink()
    except FileNotFoundError:
        pass


def _read_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not JSONL.exists():
        return rows
    for line in JSONL.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def _write_rows(rows: list[dict[str, Any]]) -> None:
    out = "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n"
    tmp = JSONL.with_suffix(".jsonl.tmp")
    tmp.write_text(out, encoding="utf-8")
    tmp.replace(JSONL)


def main() -> int:
    if not _acquire_lock():
        print("ERR: could not acquire lock", file=sys.stderr)
        return 2
    try:
        rows = _read_rows()
        flipped = 0
        skipped = 0
        for row in rows:
            ts = row.get("ts_utc")
            if ts not in ACK_MAP:
                continue
            if row.get("status") != "new":
                skipped += 1
                continue
            new_status, deliverable = ACK_MAP[ts]
            row["status"] = new_status
            row.setdefault("agents_acked", [])
            if "sanctum" not in row["agents_acked"]:
                row["agents_acked"].append("sanctum")
            row.setdefault("deliverables", []).append(deliverable)
            flipped += 1
        _write_rows(rows)
        print(f"sweep done: flipped={flipped} skipped_already_acked={skipped} target_total={len(ACK_MAP)}")
        return 0
    finally:
        _release_lock()


if __name__ == "__main__":
    sys.exit(main())
