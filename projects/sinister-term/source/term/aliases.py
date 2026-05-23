# Sinister Term :: aliases.py
# Author: RKOJ-ELENO :: 2026-05-23
# License: AGPL-3.0-or-later
#
# RKOJ-ELENO :: 2026-05-23 :: alias builtin — bash/zsh-style shorthand.
# Persisted at ~/.sterm/aliases.json as a flat {name: expansion} dict.
# Expansion is applied on the FIRST word only (matches bash semantics).

from __future__ import annotations

import json
import shlex
from pathlib import Path


ALIAS_DIR = Path.home() / ".sterm"
ALIAS_FILE = ALIAS_DIR / "aliases.json"


def load_aliases() -> dict[str, str]:
    """Return the persisted alias map, or {} on any failure."""
    try:
        if ALIAS_FILE.exists():
            data = json.loads(ALIAS_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return {str(k): str(v) for k, v in data.items()}
    except Exception:
        pass
    return {}


def save_aliases(aliases: dict[str, str]) -> None:
    ALIAS_DIR.mkdir(parents=True, exist_ok=True)
    ALIAS_FILE.write_text(json.dumps(aliases, indent=2, sort_keys=True), encoding="utf-8")


def expand_line(line: str, aliases: dict[str, str]) -> str:
    """If the first whitespace-token of `line` matches an alias, swap it in.
    Preserves the rest of the line verbatim. Returns `line` unchanged when
    no alias hits or input is empty.
    """
    stripped = line.lstrip()
    if not stripped or stripped.startswith("/"):
        return line
    # Split off the first token; rest is preserved verbatim (no re-quote).
    try:
        first = shlex.split(stripped)[0]
    except ValueError:
        return line
    if first in aliases:
        rest = stripped[len(first):]
        return aliases[first] + rest
    return line
