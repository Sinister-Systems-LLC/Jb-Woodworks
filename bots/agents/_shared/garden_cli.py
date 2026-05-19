r"""garden_cli - prints the Sinister Bots memory garden as a formatted table.

Run as:
    python -m _shared.garden_cli
or:
    python "D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\agents\_shared\garden_cli.py"

Also writes snapshot files for after-the-fact reading + bot consumption:
    runtime-state/memory-garden-latest.txt   (same as stdout, human-readable)
    runtime-state/memory-garden-latest.json  (structured, bot-readable)

Used by C:\Users\Zonia\Desktop\Memory-Garden.bat.
"""

from __future__ import annotations

import io
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
AGENTS_DIR = HERE.parent
if str(AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(AGENTS_DIR))

os.environ.setdefault("SINISTER_HUB_ROOT", r"D:\Sinister\Sinister Skills")
HUB_ROOT = Path(os.environ["SINISTER_HUB_ROOT"])
SNAPSHOT_TXT = HUB_ROOT / "12_LLM_ORCHESTRATION" / "runtime-state" / "memory-garden-latest.txt"
SNAPSHOT_JSON = HUB_ROOT / "12_LLM_ORCHESTRATION" / "runtime-state" / "memory-garden-latest.json"

try:
    from _shared import bot_memory as bm  # type: ignore
except Exception as e:
    print(f"FATAL: could not import bot_memory: {e}", file=sys.stderr)
    sys.exit(1)


BOTS = [
    "sentinel", "translator", "librarian", "watcher", "auditor", "sinister-bus",
    "triage", "scribe", "curator", "custodian", "stealth-browser", "researcher",
]


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".tmp.{os.urandom(4).hex()}")
    tmp.write_text(content, encoding="utf-8")
    os.replace(tmp, path)


def _atomic_write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".tmp.{os.urandom(4).hex()}")
    tmp.write_text(json.dumps(obj, indent=2, default=str), encoding="utf-8")
    os.replace(tmp, path)


def render(rows: list[dict]) -> str:
    """Render rows as a fixed-width table string (same lines that print to stdout)."""
    buf = io.StringIO()
    buf.write("=== Sinister Bots - Memory Garden ===\n")
    buf.write(f"Generated: {datetime.now(timezone.utc).isoformat()}\n\n")
    buf.write(f"{'BOT':<18} {'FACTS':>5} {'EMBED':>5} {'CALLS':>5} {'SMART':>5}  LAST ABSORBED\n")
    buf.write("-" * 80 + "\n")
    total_facts = 0
    total_calls = 0
    with_facts = 0
    for r in rows:
        if "error" in r:
            buf.write(f"{r['bot']:<18} ERROR: {r['error']}\n")
            continue
        total_facts += r["facts"]
        total_calls += r["calls"]
        if r["facts"] > 0:
            with_facts += 1
        smart = "YES" if r["smart"] else "-"
        last = r["last"][:20] if r["last"] != "-" else "-"
        buf.write(f"{r['bot']:<18} {r['facts']:>5} {r['embed']:>5} {r['calls']:>5} {smart:>5}  {last}\n")
    buf.write("\n")
    buf.write(f"TOTAL   facts={total_facts}   calls={total_calls}   bots_with_facts={with_facts}\n")
    return buf.getvalue()


def main() -> int:
    rows = []
    for n in BOTS:
        try:
            s = bm.memory_stats(n)
            rows.append({
                "bot": n,
                "facts": int(s.get("fact_count", 0) or 0),
                "embed": int(s.get("embedded_fact_count", 0) or 0),
                "calls": int(s.get("lifetime_calls", 0) or 0),
                "smart": bool(s.get("smart_retrieval_active", False)),
                "last":  s.get("last_absorbed") or "-",
            })
        except Exception as e:
            rows.append({"bot": n, "error": str(e)[:120]})

    rows.sort(key=lambda r: -(r.get("facts", 0) or 0))
    table_text = render(rows)

    # Print to stdout
    print(table_text, end="")

    # Persist snapshots so the operator can read after auto-close + bots can ingest
    try:
        _atomic_write_text(SNAPSHOT_TXT, table_text)
        _atomic_write_json(SNAPSHOT_JSON, {
            "generated": datetime.now(timezone.utc).isoformat(),
            "rows": rows,
            "totals": {
                "facts": sum(r.get("facts", 0) or 0 for r in rows),
                "calls": sum(r.get("calls", 0) or 0 for r in rows),
                "bots_with_facts": sum(1 for r in rows if r.get("facts", 0)),
            },
        })
        print(f"Snapshot: {SNAPSHOT_TXT.relative_to(HUB_ROOT)}")
    except Exception as e:
        print(f"WARN: could not write snapshot: {e}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
