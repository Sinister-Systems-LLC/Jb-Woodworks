#!/usr/bin/env python3
"""hgly_status.py — one-call status reader for the Sinister Hieroglyphics lane.

Author: RKOJ-ELENO :: 2026-05-25

Emits a unified status JSON (or human-readable text) covering: hgly package
version, corpus file count + total bytes + glyph coverage, recent commits,
trainer state, loop history, sim live-ness. Designed to be invoked from
EVE.exe (Phase 10 integration) or from any agent that needs to display
the lane's health in one shot.

Usage:
  python automations/hgly_status.py              # human text
  python automations/hgly_status.py --json       # JSON
  python automations/hgly_status.py --compact    # one-line summary

Exit code is always 0 (this is a reader; failure to compute one section
just nulls that field).
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

SANCTUM = Path(os.environ.get("SINISTER_SANCTUM_ROOT", r"D:\Sinister Sanctum"))
HGLY_DIR = SANCTUM / "projects" / "sinister-hieroglyphics"
CORPUS_DIR = SANCTUM / "_shared-memory" / "hgly-corpus"
LOOP_LOG = SANCTUM / "_shared-memory" / "quality-loop-log.jsonl"
TRAINER_STATE = SANCTUM / "_shared-memory" / "hgly-trainer-state.json"
SEEDER = SANCTUM / "automations" / "hgly_corpus_seed.py"

_NO_WIN = 0x08000000 if os.name == "nt" else 0


def _utcnow_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def hgly_version() -> str | None:
    try:
        init = HGLY_DIR / "src" / "hgly" / "__init__.py"
        for ln in init.read_text(encoding="utf-8").splitlines():
            if ln.startswith("__version__"):
                # __version__ = "x.y.z"
                return ln.split("=", 1)[1].strip().strip('"').strip("'")
    except Exception:
        pass
    return None


def corpus_stats() -> dict:
    """Read corpus_seed stats command output. Already JSON."""
    if not SEEDER.exists():
        return {"file_count": 0, "available": False}
    try:
        r = subprocess.run(
            [sys.executable, str(SEEDER), "stats"],
            capture_output=True, text=True, timeout=20,
            creationflags=_NO_WIN,
        )
        if r.returncode != 0:
            return {"file_count": 0, "available": False, "error": r.stderr[:200]}
        return json.loads(r.stdout)
    except Exception as e:
        return {"file_count": 0, "available": False, "error": str(e)}


def recent_hgly_commits(limit: int = 5) -> list[str]:
    """Tail of recent hgly-tagged commits."""
    try:
        r = subprocess.run(
            ["git", "-C", str(SANCTUM), "log", f"-{limit}", "--oneline",
             "--grep=hgly", "--all"],
            capture_output=True, text=True, timeout=10,
            creationflags=_NO_WIN,
        )
        if r.returncode != 0: return []
        return [l for l in r.stdout.splitlines() if l.strip()]
    except Exception:
        return []


def trainer_state() -> dict:
    if not TRAINER_STATE.exists():
        return {"exists": False}
    try:
        return {"exists": True, **json.loads(TRAINER_STATE.read_text(encoding="utf-8"))}
    except Exception:
        return {"exists": True, "parse_error": True}


def recent_loop_ticks(lane: str | None = None, limit: int = 5) -> list[dict]:
    if not LOOP_LOG.exists(): return []
    rows = []
    try:
        with LOOP_LOG.open(encoding="utf-8", errors="replace") as fh:
            for ln in fh:
                ln = ln.strip()
                if not ln: continue
                try: r = json.loads(ln)
                except Exception: continue
                if lane and r.get("lane") != lane: continue
                rows.append(r)
    except Exception:
        return []
    return rows[-limit:]


def test_suite_status() -> dict:
    """Walk projects/sinister-hieroglyphics/tests/ and count test_*.py files."""
    tdir = HGLY_DIR / "tests"
    if not tdir.exists(): return {"available": False}
    files = sorted(tdir.glob("test_*.py"))
    return {
        "available": True,
        "test_modules": [f.stem for f in files],
        "count": len(files),
    }


def python_sim_bridge_live() -> bool:
    """Quick TCP probe for the desktop python_simulator router port 7000."""
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.25)
        rc = s.connect_ex(("127.0.0.1", 7000))
        s.close()
        return rc == 0
    except Exception:
        return False


def collect() -> dict:
    """Single status dict assembled from all readers."""
    cs = corpus_stats()
    return {
        "ts_utc": _utcnow_iso(),
        "hgly": {
            "version": hgly_version(),
            "project_dir": str(HGLY_DIR),
            "tests": test_suite_status(),
        },
        "corpus": {
            "file_count": cs.get("file_count", 0),
            "total_bytes": cs.get("total_bytes", 0),
            "mean_bytes_per_program": cs.get("mean_bytes_per_program"),
            "glyphs_covered": cs.get("glyphs_covered", 0),
            "glyph_vocabulary_size": cs.get("glyph_vocabulary_size", 64),
            "coverage_pct": cs.get("coverage_pct", 0),
        },
        "trainer": trainer_state(),
        "loop_ticks_recent": recent_loop_ticks(limit=5),
        "python_sim_live": python_sim_bridge_live(),
        "recent_commits": recent_hgly_commits(limit=5),
    }


def render_text(d: dict) -> str:
    lines = []
    h = d["hgly"]; c = d["corpus"]
    lines.append(f"=== Sinister Hieroglyphics :: {d['ts_utc']} ===")
    lines.append(f"  package        v{h['version']}  ({h['tests']['count']} test modules)")
    lines.append(f"  corpus         {c['file_count']} programs / {c['total_bytes']} bytes")
    lines.append(f"  glyph coverage {c['glyphs_covered']}/{c['glyph_vocabulary_size']} ({c['coverage_pct']}%)")
    t = d["trainer"]
    if t.get("exists"):
        lines.append(f"  trainer        iter={t.get('iter', '?')} best={t.get('best_score', '?')}")
    else:
        lines.append(f"  trainer        scaffolded (no state yet)")
    lines.append(f"  python_sim     {'LIVE on :7000' if d['python_sim_live'] else 'not running (synth fallback)'}")
    ticks = d.get("loop_ticks_recent") or []
    if ticks:
        lines.append(f"  loop ticks ({len(ticks)} recent):")
        for r in ticks[-3:]:
            lines.append(f"    {r.get('ts_utc', '?')} lane={r.get('lane', '?')} "
                         f"iter={r.get('iter', '?')} score={r.get('score', '?')} "
                         f"action={r.get('action', '?')}")
    commits = d.get("recent_commits") or []
    if commits:
        lines.append(f"  recent commits:")
        for c_ln in commits[:5]:
            lines.append(f"    {c_ln[:100]}")
    return "\n".join(lines)


def render_compact(d: dict) -> str:
    c = d["corpus"]
    return (f"hgly v{d['hgly']['version']}  "
            f"corpus={c['file_count']}/{c['total_bytes']}b  "
            f"glyphs={c['glyphs_covered']}/{c['glyph_vocabulary_size']}  "
            f"sim={'LIVE' if d['python_sim_live'] else 'synth'}")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--json", dest="json_out", action="store_true")
    p.add_argument("--compact", action="store_true")
    args = p.parse_args()
    d = collect()
    if args.json_out:
        print(json.dumps(d, indent=2, default=str))
    elif args.compact:
        print(render_compact(d))
    else:
        print(render_text(d))
    return 0


if __name__ == "__main__":
    sys.exit(main())
