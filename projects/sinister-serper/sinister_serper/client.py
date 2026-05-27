# Author: RKOJ-ELENO :: 2026-05-27
"""SerperClient — single-call surface that hides key-rotation from callers.

P0 SCAFFOLD ONLY — does not perform live Serper calls yet. Smoke ($ python
-m sinister_serper.client --smoke) returns a stub payload so the chatbot
backend integration can be wired against a known shape today; rotator + real
HTTP land in iter-1 once email-gen is available.
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any

SERPER_BASE = "https://google.serper.dev"


class SerperClient:
    """Public API surface. Methods mirror Serper.dev REST endpoints.

    iter-1 TODO: wire to keypool.next() + requests.post(SERPER_BASE/<route>,
    headers={"X-API-KEY": key}, json={"q": q, ...}). Decrement key credits
    by Serper's `X-Credits-Remaining` response header.
    """

    def __init__(self, keypool: Any | None = None):
        # iter-1: keypool defaults to KeyPool.from_vault() when None.
        self.keypool = keypool

    def search(self, q: str, **kwargs: Any) -> dict[str, Any]:
        return {
            "_stub": True,
            "route": "/search",
            "q": q,
            "kwargs": kwargs,
            "note": "P0 scaffold — replace with real call in iter-1",
        }

    def news(self, q: str, **kwargs: Any) -> dict[str, Any]:
        return {"_stub": True, "route": "/news", "q": q, "kwargs": kwargs}

    def images(self, q: str, **kwargs: Any) -> dict[str, Any]:
        return {"_stub": True, "route": "/images", "q": q, "kwargs": kwargs}

    def places(self, q: str, **kwargs: Any) -> dict[str, Any]:
        return {"_stub": True, "route": "/places", "q": q, "kwargs": kwargs}


def _smoke() -> int:
    c = SerperClient()
    out = c.search("hello world", num=3)
    assert out["_stub"] is True
    assert out["q"] == "hello world"
    assert out["kwargs"] == {"num": 3}
    print(json.dumps(out, indent=2))
    print("SMOKE PASS")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="sinister_serper.client")
    p.add_argument("--smoke", action="store_true", help="run scaffold smoke")
    args = p.parse_args(argv)
    if args.smoke:
        return _smoke()
    p.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
