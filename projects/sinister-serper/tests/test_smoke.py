# Author: RKOJ-ELENO :: 2026-05-27
"""Smoke test — imports + keypool round-trip + client stub."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path


def test_imports():
    import sinister_serper
    from sinister_serper import client, keypool, rotator  # noqa: F401
    assert sinister_serper.__version__


def test_client_stub():
    from sinister_serper.client import SerperClient
    out = SerperClient().search("hello", num=5)
    assert out["_stub"] is True
    assert out["q"] == "hello"


def test_keypool_round_trip():
    from sinister_serper.keypool import KeyPool, KeyRecord
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
    # Only k1 active after retirement
    assert pool2.next().key == "k1"


if __name__ == "__main__":
    test_imports()
    test_client_stub()
    test_keypool_round_trip()
    print("ALL SMOKE PASS")
