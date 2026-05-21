# Sinister Sanctum :: sinister-model :: core API
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later

from __future__ import annotations
import os
import re
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = "sinister.model.v1"
_AUTHOR = "RKOJ-ELENO :: 2026-05-21"
DEFAULT_SANCTUM_ROOT = Path(os.environ.get("SINISTER_SANCTUM_ROOT", r"D:\Sinister Sanctum"))
_root: Path = DEFAULT_SANCTUM_ROOT


def set_sanctum_root(p):
    global _root
    _root = Path(p)


def get_sanctum_root():
    return _root


def _now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _routing_path():
    return _root / "automations" / "agent-host-routing.md"


def _parse_table(text, *, header_signature):
    """Find the first markdown table whose header matches `header_signature` (substring)."""
    lines = text.splitlines()
    rows = []
    in_table = False
    header_cells = None
    for line in lines:
        if not in_table:
            if header_signature in line and "|" in line:
                # next line is the |---|---| separator; line after that starts rows
                header_cells = [c.strip() for c in line.strip("|").split("|")]
                in_table = True
            continue
        # In table
        if "|" not in line:
            break
        if re.match(r"^[\s|:-]+$", line):
            continue  # separator
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) >= 2:
            rows.append(dict(zip(header_cells or [], cells)))
    return rows


def list_models():
    p = _routing_path()
    if not p.exists():
        return []
    text = p.read_text(encoding="utf-8")
    return _parse_table(text, header_signature="Task class")


def current(task_class):
    for row in list_models():
        name = next(iter(row.keys()), "")
        if task_class.lower() in (row.get(name, "") or "").lower():
            return row
    return None


def providers():
    p = _routing_path()
    if not p.exists():
        return []
    text = p.read_text(encoding="utf-8")
    return _parse_table(text, header_signature="Provider |")


def propose_switch(task_class, primary, rationale=None):
    """Append a brain entry suggesting a routing switch. Operator clicks to adopt."""
    brain = _root / "_shared-memory" / "knowledge" / "model-switch-proposals.md"
    brain.parent.mkdir(parents=True, exist_ok=True)
    line = f"\n- [ ] **{_now_iso()}** — switch `{task_class}` primary to `{primary}`"
    if rationale:
        line += f" (rationale: {rationale})"
    if not brain.exists():
        brain.write_text(
            "# Model-switch proposals\n\n"
            "> Author: RKOJ-ELENO :: 2026-05-21\n"
            "> License: AGPL-3.0-or-later\n"
            "> Auto-appended by tools/sinister-model/. Operator clicks `- [ ]` -> `- [x]` to adopt.\n",
            encoding="utf-8",
        )
    with brain.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")
    return {
        "_author": _AUTHOR,
        "schema_version": SCHEMA_VERSION,
        "task_class": task_class,
        "primary": primary,
        "rationale": rationale,
        "ts_utc": _now_iso(),
        "appended_to": str(brain),
    }
