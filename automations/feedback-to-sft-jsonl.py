#!/usr/bin/env python3
"""Sinister Chatbot — feedback-to-SFT JSONL exporter (Phase 2 step 1).

Author: RKOJ-ELENO :: 2026-05-24

Reads the `/chatter` test-env feedback ledger at
`data/sinister/chatter-feedback.json` plus the persona registry at
`data/sinister/chatter.json`, emits per-persona OpenAI-compatible SFT JSONL
to `data/sinister/training-corpus/<persona_id>.jsonl`.

Each row:
  {
    "messages": [
      {"role": "system",    "content": <persona.system_prompt or "">},
      {"role": "user",      "content": <feedback.user_text>},
      {"role": "assistant", "content": <feedback.reply_text>}
    ],
    "weight": 1.0 or -1.0,         # good = +1, bad = -1
    "persona_id": "<id>",
    "provider": "openrouter|capitalbot|local|...",
    "model":    "<model-id>",
    "ts_utc":   "<iso8601>"
  }

Bad-thumb rows ride along with weight=-1.0 so a downstream DPO pair-builder
can mine them; pure SFT consumers can filter by weight>=1.0.

Usage:
  python automations/feedback-to-sft-jsonl.py [--data-dir PATH] [--out-dir PATH]
  python automations/feedback-to-sft-jsonl.py --smoke   # synthetic fixture, no real data

Plan reference: projects/sinister-chatbot/leo_dev/docs/CHATBOT-DIRECTION-2026-05-24.md Phase 2.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any


def _persona_index(chatter_json_path: Path) -> dict[str, dict[str, Any]]:
    """Return { persona_id: persona_row } from chatter.json. Empty dict on miss."""
    if not chatter_json_path.exists():
        return {}
    try:
        data = json.loads(chatter_json_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    groups = data.get("groups", []) if isinstance(data, dict) else []
    return {g["id"]: g for g in groups if isinstance(g, dict) and "id" in g}


def export(data_dir: Path, out_dir: Path) -> dict[str, Any]:
    feedback_path = data_dir / "chatter-feedback.json"
    chatter_path = data_dir / "chatter.json"
    if not feedback_path.exists():
        return {"ok": False, "error": f"feedback file not found at {feedback_path}", "rows_in": 0, "rows_out": 0}

    try:
        feedback_data = json.loads(feedback_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        return {"ok": False, "error": f"feedback file unreadable: {e}", "rows_in": 0, "rows_out": 0}

    entries = feedback_data.get("entries", []) if isinstance(feedback_data, dict) else []
    personas = _persona_index(chatter_path)

    out_dir.mkdir(parents=True, exist_ok=True)
    per_persona: dict[str, list[dict[str, Any]]] = {}
    skipped = 0
    for row in entries:
        if not isinstance(row, dict):
            skipped += 1
            continue
        pid = row.get("persona_id") or "_unknown"
        user_text = row.get("user_text")
        reply_text = row.get("reply_text")
        verdict = row.get("verdict")
        if not user_text or not reply_text or verdict not in ("good", "bad"):
            # Rows without the (user_text, reply_text, verdict) triple can't
            # train a supervised LM; skip + count.
            skipped += 1
            continue

        system_prompt = ""
        if pid in personas:
            system_prompt = personas[pid].get("system_prompt") or ""

        weight = 1.0 if verdict == "good" else -1.0
        out_row = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text},
                {"role": "assistant", "content": reply_text},
            ],
            "weight": weight,
            "persona_id": pid,
            "provider": row.get("provider"),
            "model": row.get("model"),
            "ts_utc": row.get("ts_utc"),
        }
        per_persona.setdefault(pid, []).append(out_row)

    written: dict[str, int] = {}
    for pid, rows in per_persona.items():
        # Filesystem-safe slug for the filename.
        slug = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in pid) or "_unknown"
        target = out_dir / f"{slug}.jsonl"
        with target.open("w", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        written[str(target)] = len(rows)

    return {
        "ok": True,
        "rows_in": len(entries),
        "rows_skipped": skipped,
        "rows_out": sum(written.values()),
        "files_written": written,
        "feedback_path": str(feedback_path),
        "out_dir": str(out_dir),
    }


def smoke_test() -> int:
    """Synthetic fixture → export → assert. Returns 0 on PASS, non-zero on FAIL."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "chatter-feedback.json").write_text(json.dumps({
            "entries": [
                {
                    "persona_id": "default",
                    "message_id": "b-1",
                    "verdict": "good",
                    "user_text": "hey",
                    "reply_text": "heyy whats up",
                    "provider": "openrouter",
                    "model": "cognitivecomputations/dolphin-mixtral-8x22b",
                    "ts_utc": "2026-05-24T16:00:00Z",
                },
                {
                    "persona_id": "default",
                    "message_id": "b-2",
                    "verdict": "bad",
                    "user_text": "send pics",
                    "reply_text": "i dont send pics on snap",
                    "provider": "openrouter",
                    "model": "anthropic/claude-3.5-haiku",
                    "ts_utc": "2026-05-24T16:01:00Z",
                },
                {
                    "persona_id": "alt-persona",
                    "message_id": "b-3",
                    "verdict": "good",
                    "user_text": "wyd",
                    "reply_text": "watching tv lol",
                    "ts_utc": "2026-05-24T16:02:00Z",
                },
                # Missing user_text — should skip.
                {
                    "persona_id": "default",
                    "message_id": "b-4",
                    "verdict": "good",
                    "ts_utc": "2026-05-24T16:03:00Z",
                },
            ]
        }), encoding="utf-8")
        (root / "chatter.json").write_text(json.dumps({
            "groups": [
                {"id": "default", "name": "Default", "system_prompt": "you are flirty"},
                {"id": "alt-persona", "name": "Alt", "system_prompt": "you are dry"},
            ]
        }), encoding="utf-8")

        out_dir = root / "training-corpus"
        res = export(root, out_dir)
        if not res.get("ok"):
            print(f"[smoke] FAIL — export returned not-ok: {res}", file=sys.stderr)
            return 1
        if res["rows_in"] != 4:
            print(f"[smoke] FAIL — expected rows_in=4 got {res['rows_in']}", file=sys.stderr)
            return 1
        if res["rows_skipped"] != 1:
            print(f"[smoke] FAIL — expected rows_skipped=1 got {res['rows_skipped']}", file=sys.stderr)
            return 1
        if res["rows_out"] != 3:
            print(f"[smoke] FAIL — expected rows_out=3 got {res['rows_out']}", file=sys.stderr)
            return 1
        # Verify file shapes.
        default_jsonl = out_dir / "default.jsonl"
        if not default_jsonl.exists():
            print(f"[smoke] FAIL — default.jsonl missing", file=sys.stderr)
            return 1
        rows = [json.loads(line) for line in default_jsonl.read_text(encoding="utf-8").splitlines()]
        if len(rows) != 2:
            print(f"[smoke] FAIL — default.jsonl row count {len(rows)} != 2", file=sys.stderr)
            return 1
        if rows[0]["messages"][0]["content"] != "you are flirty":
            print("[smoke] FAIL — system prompt not injected from chatter.json", file=sys.stderr)
            return 1
        if rows[0]["weight"] != 1.0 or rows[1]["weight"] != -1.0:
            print(f"[smoke] FAIL — weight mismatch good=+1/bad=-1 got {rows[0]['weight']}/{rows[1]['weight']}", file=sys.stderr)
            return 1
        print("[smoke] PASS — 4 in, 1 skipped, 3 out, 2 files, weights + system_prompt verified")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Sinister Chatbot — feedback-to-SFT JSONL exporter")
    sanctum_root = Path(__file__).resolve().parent.parent
    default_data = sanctum_root / "projects" / "sinister-chatbot" / "data" / "sinister"
    p.add_argument("--data-dir", default=str(default_data), help="data dir holding chatter-feedback.json + chatter.json")
    p.add_argument("--out-dir", default=None, help="output dir (default: <data-dir>/training-corpus)")
    p.add_argument("--smoke", action="store_true", help="run synthetic fixture self-test and exit")
    p.add_argument("--json", action="store_true", help="emit summary as JSON")
    args = p.parse_args()

    if args.smoke:
        return smoke_test()

    data_dir = Path(args.data_dir)
    out_dir = Path(args.out_dir) if args.out_dir else (data_dir / "training-corpus")
    res = export(data_dir, out_dir)
    if args.json:
        print(json.dumps(res, separators=(",", ":")))
    else:
        if res.get("ok"):
            print(f"[feedback-to-sft-jsonl] rows_in={res['rows_in']} rows_skipped={res['rows_skipped']} rows_out={res['rows_out']}")
            for path, n in res["files_written"].items():
                print(f"  wrote {n} rows -> {path}")
        else:
            print(f"[feedback-to-sft-jsonl] FAIL — {res.get('error')}", file=sys.stderr)
    return 0 if res.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
