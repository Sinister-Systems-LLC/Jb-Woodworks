# Sinister Utils

> **Author:** RKOJ-ELENO :: 2026-05-23
> **License:** AGPL-3.0-or-later
> **Doctrine:** `_shared-memory/knowledge/powershell-out-file-bom-bites-python-readers-2026-05-23.md`

Tiny defensive-I/O helpers used across the Sinister Python stack. Codifies the consumer-side fixes from the BOM-bites-readers brain entry into shared functions so every reader can `from sinister_utils.io import load_json_tolerant` instead of re-implementing the pattern.

## What's here (v0.1.0)

| Function | Purpose |
|---|---|
| `load_json_tolerant(path, default=None)` | Open a JSON file with `utf-8-sig` (BOM-safe) + narrow except + warning log + caller-supplied default. Returns `None` on any failure unless `default` is given. Never raises. |
| `load_text_tolerant(path, default="")` | Same shape for plain text. BOM-stripped via `utf-8-sig`. |
| `write_json_no_bom(path, data, *, indent=2)` | Atomic JSON write with **no BOM** (UTF-8 strict, no `﻿` prefix). Uses `[System.Text.UTF8Encoding](False)`-equivalent semantics via Python's default `open(..., encoding="utf-8")` + explicit byte-write. |
| `write_text_no_bom(path, text)` | Same shape for plain text. |

## Install

```bash
cd "D:/Sinister Sanctum/tools/sinister-utils"
pip install -e .
```

## Usage

```python
from sinister_utils.io import load_json_tolerant, write_json_no_bom

# Read — survives BOM-prefixed files written by PS 5.1 Out-File
data = load_json_tolerant("D:/Sinister Sanctum/automations/session-templates/projects.json", default={})
projects = data.get("projects", [])

# Write — guarantees no BOM in the output bytes
write_json_no_bom("/tmp/out.json", {"key": "value"})
```

## Why this exists

Per the BOM-bites-readers doctrine, EVERY Python reader of a launcher-written file in the fleet should consume the BOM defensively. Without this helper, each reader independently re-implements `open(..., encoding="utf-8-sig")` or — worse — uses `encoding="utf-8"` and silently swallows `JSONDecodeError("Unexpected UTF-8 BOM")` in a `try/except Exception:`. The empirical anchor: RKOJ Workstation's Resume picker was silently empty for an unknown number of sessions because of this exact bug.

`load_json_tolerant` enforces three properties simultaneously:
1. **BOM-tolerant** — `encoding="utf-8-sig"` consumes a leading BOM if present, no-op otherwise.
2. **Narrow except** — only catches `OSError`, `UnicodeDecodeError`, `json.JSONDecodeError`. Programmer errors (NameError, TypeError) propagate.
3. **Logged on swallow** — every catch path emits a `logging.warning(...)` so the silent-disappear failure mode becomes a loud log line.

## Composability

- `_shared-memory/knowledge/powershell-out-file-bom-bites-python-readers-2026-05-23.md` (the doctrine)
- `tools/forge-memory-bridge/` — defensive readers can drop the helper in
- `projects/rkoj/source/sinister_rkoj_qt/state.py` — adopted v1.6.89 (consumer-side fix)
- `projects/sinister-mind/source/mind/server.py` — adopted v0.4.0
- Any PS1 producer that writes JSON — pair the helper with `[System.IO.File]::WriteAllText(..., [System.Text.UTF8Encoding]::new($false))` on the writer side
