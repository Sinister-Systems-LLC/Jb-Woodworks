#!/usr/bin/env python3
"""classify-change.py — diff → verdict {hot, target_unit, reason, severity}.

Author: RKOJ-ELENO :: 2026-05-24
Status: SCAFFOLDED. Parse-clean; not installed.

Reads a unified diff on stdin, takes filename as argv[1], and emits a JSON verdict.
Allowlists per file determine what can hot-reload vs what triggers a reboot banner.

Conservative default: unknown key → reboot required (safer to over-prompt than miss).
"""

from __future__ import annotations

import json
import re
import sys

THEME_HOT_KEYS = {"accent", "radius", "font", "density", "primary", "background"}
EVE_HOT_KEYS = {"voice.wake_word", "allowlist", "model", "max_concurrent"}
EVE_COLD_KEYS = {"socket_path", "run_as_user", "data_dir"}
MESH_HOT_KEYS = {"advertise_routes", "exit_node", "accept_dns"}
MESH_COLD_KEYS = {"private_key", "interface_name"}

# filename -> (hot_keys, cold_keys, target_unit)
FILE_POLICY = {
    "theme.toml":  (THEME_HOT_KEYS, set(),         "sinister-panel.service"),
    "eve.toml":    (EVE_HOT_KEYS,   EVE_COLD_KEYS, "sinister-eve.service"),
    "mesh.toml":   (MESH_HOT_KEYS,  MESH_COLD_KEYS, "tailscaled.service"),
}

# Match `key = value` lines in a diff, captures key name (handles dotted keys + TOML tables).
DIFF_KEY_RE = re.compile(r"^[+-](?!\+\+|--)\s*([a-zA-Z_][\w.]*)\s*=", re.MULTILINE)


def extract_changed_keys(diff: str) -> set[str]:
    """Pull every key= line that appears in the diff (added or removed)."""
    return {m.group(1) for m in DIFF_KEY_RE.finditer(diff)}


def classify(diff: str, filename: str) -> dict:
    hot_keys, cold_keys, target_unit = FILE_POLICY.get(filename, (set(), set(), None))
    changed = extract_changed_keys(diff)

    if not changed:
        return {
            "hot": False, "target_unit": target_unit,
            "reason": "diff-unparseable", "severity": "info",
        }

    cold_hits = changed & cold_keys
    if cold_hits:
        return {
            "hot": False, "target_unit": target_unit,
            "reason": f"cold keys changed: {sorted(cold_hits)}", "severity": "warn",
        }

    hot_hits = changed & hot_keys
    unknown = changed - hot_keys - cold_keys
    if unknown:
        return {
            "hot": False, "target_unit": target_unit,
            "reason": f"unknown keys (conservative reboot): {sorted(unknown)}",
            "severity": "info",
        }

    if hot_hits:
        return {
            "hot": True, "target_unit": target_unit,
            "reason": f"hot keys changed: {sorted(hot_hits)}", "severity": "info",
        }

    return {
        "hot": False, "target_unit": target_unit,
        "reason": "no actionable change", "severity": "info",
    }


def main() -> None:
    filename = sys.argv[1] if len(sys.argv) > 1 else "unknown"
    diff = sys.stdin.read()
    verdict = classify(diff, filename)
    print(json.dumps(verdict))


if __name__ == "__main__":
    main()
