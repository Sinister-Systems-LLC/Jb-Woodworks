# Author: RKOJ-ELENO :: 2026-05-27
"""KeyPool — JSON-on-disk pool of Serper.dev API keys with credit accounting.

P0 SCAFFOLD — supports load/save/list/round-robin; retirement + concurrency
locking land in iter-1.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

DEFAULT_POOL_PATH = Path(
    os.environ.get("SINISTER_SERPER_POOL", "_vault/serper/keys.json")
)
RETIRE_THRESHOLD = 50  # credits remaining


@dataclass
class KeyRecord:
    key: str
    email: str
    credits_remaining: int
    created_utc: str
    last_used_utc: str | None = None
    retired: bool = False


class KeyPool:
    def __init__(self, path: Path = DEFAULT_POOL_PATH):
        self.path = path
        self.records: list[KeyRecord] = []
        self._cursor = 0

    @classmethod
    def from_vault(cls, path: Path | None = None) -> "KeyPool":
        p = cls(path or DEFAULT_POOL_PATH)
        p.load()
        return p

    def load(self) -> None:
        if not self.path.exists():
            self.records = []
            return
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        self.records = [KeyRecord(**r) for r in raw]

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps([asdict(r) for r in self.records], indent=2),
            encoding="utf-8",
        )

    def add(self, rec: KeyRecord) -> None:
        self.records.append(rec)

    def next(self) -> KeyRecord | None:
        """Round-robin over non-retired records with credits >= RETIRE_THRESHOLD."""
        active = [r for r in self.records if not r.retired and r.credits_remaining >= RETIRE_THRESHOLD]
        if not active:
            return None
        rec = active[self._cursor % len(active)]
        self._cursor += 1
        return rec

    def retire_below(self, threshold: int = RETIRE_THRESHOLD) -> int:
        n = 0
        for r in self.records:
            if not r.retired and r.credits_remaining < threshold:
                r.retired = True
                n += 1
        return n

    def list_dict(self) -> list[dict[str, Any]]:
        return [asdict(r) for r in self.records]


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="sinister_serper.keypool")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    sub.add_parser("smoke")
    args = p.parse_args(argv)
    if args.cmd == "list":
        pool = KeyPool.from_vault()
        print(json.dumps(pool.list_dict(), indent=2))
        return 0
    if args.cmd == "smoke":
        # Self-contained smoke — no disk writes outside tmp.
        import tempfile
        tmp = Path(tempfile.mkdtemp()) / "keys.json"
        pool = KeyPool(tmp)
        pool.add(KeyRecord(key="k1", email="a@x", credits_remaining=2500, created_utc="2026-05-27"))
        pool.add(KeyRecord(key="k2", email="b@x", credits_remaining=10, created_utc="2026-05-27"))
        pool.save()
        pool2 = KeyPool(tmp)
        pool2.load()
        assert len(pool2.records) == 2
        assert pool2.next().key == "k1"
        assert pool2.retire_below() == 1
        assert pool2.next().key == "k1"  # k2 retired, only k1 active
        print("SMOKE PASS")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
