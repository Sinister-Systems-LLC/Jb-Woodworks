#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
plugin_manifest.py -- Sinister plugin-manifest validator + helper CLI.

Shared validator for plugin manifests consumed by Sinister Term, Sinister Memory,
and any other lane that loads cross-lane plugins. Modeled on oh-my-pi's
packages/coding-agent/src/extensibility/plugins/types.ts:27-95.

The canonical JSON Schema lives at:
    D:/Sinister Sanctum/_shared-memory/schemas/plugin-manifest.schema.json
The canonical example lives at:
    D:/Sinister Sanctum/_shared-memory/schemas/example-plugin-manifest.json

This validator deliberately uses stdlib only (json + re + argparse + pathlib).
It implements a focused subset of draft-07 validation -- enough for the rules
above plus the extra business rules in `validate_business_rules`. It is NOT a
full draft-07 implementation.

Usage:
    python automations/plugin_manifest.py validate <path>
    python automations/plugin_manifest.py validate-all <dir>
    python automations/plugin_manifest.py describe <path>
    python automations/plugin_manifest.py example
    python automations/plugin_manifest.py --help

Exit codes:
    0  success / valid
    2  validation failure
    3  IO or argument error

Author: RKOJ-ELENO :: 2026-05-26
License: AGPL-3.0-or-later

  This file is part of the Sinister Sanctum.

  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU Affero General Public License as published
  by the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
  GNU Affero General Public License for more details.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
SANCTUM_ROOT = SCRIPT_DIR.parent
SCHEMA_PATH = SANCTUM_ROOT / "_shared-memory" / "schemas" / "plugin-manifest.schema.json"
EXAMPLE_PATH = SANCTUM_ROOT / "_shared-memory" / "schemas" / "example-plugin-manifest.json"

KNOWN_LANES = {
    "sterm",
    "memory",
    "panel",
    "dashboard",
    "sanctum",
    "eve-exe",
    "os",
    "kernel-apk",
    "snap-api",
    "jokester",
    "overseer",
    "letstext",
    "all",  # wildcard
}

NAME_RE = re.compile(r"^[a-z][a-z0-9-]*$")
SEMVER_RE = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-((?:0|[1-9][0-9]*|[0-9]*[a-zA-Z-][0-9a-zA-Z-]*)"
    r"(?:\.(?:0|[1-9][0-9]*|[0-9]*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)

ALLOWED_SETTING_TYPES = {"string", "number", "boolean", "enum"}
ALLOWED_TOP_LEVEL_KEYS = {
    "name",
    "version",
    "description",
    "author",
    "lanes",
    "entry_points",
    "settings_schema",
    "features",
    "dependencies",
    "requires_lanes",
    "min_sinister_version",
}
ALLOWED_ENTRY_POINT_KEYS = {"commands", "hooks", "extensions", "tools"}
ALLOWED_DEPENDENCY_KEYS = {"python", "node"}

# ---------------------------------------------------------------------------
# Validation core
# ---------------------------------------------------------------------------


class ValidationResult:
    """Collects errors and warnings during a single-manifest validation pass."""

    __slots__ = ("errors", "warnings", "path")

    def __init__(self, path: Path | None = None) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.path: Path | None = path

    def err(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    @property
    def ok(self) -> bool:
        return not self.errors


def _is_str(v: Any) -> bool:
    return isinstance(v, str)


def _is_obj(v: Any) -> bool:
    return isinstance(v, dict)


def _is_arr(v: Any) -> bool:
    return isinstance(v, list)


def _is_bool(v: Any) -> bool:
    return isinstance(v, bool)


def validate_schema(data: Any, result: ValidationResult) -> None:
    """Walk the manifest enforcing the schema's structural rules by hand."""
    if not _is_obj(data):
        result.err("manifest root must be a JSON object")
        return

    # --- additionalProperties: false at top level
    extra = set(data.keys()) - ALLOWED_TOP_LEVEL_KEYS
    if extra:
        result.err(f"unknown top-level keys: {sorted(extra)}")

    # --- required keys
    for k in ("name", "version", "entry_points"):
        if k not in data:
            result.err(f"missing required field: {k!r}")

    # --- name
    if "name" in data:
        name = data["name"]
        if not _is_str(name):
            result.err("'name' must be a string")
        else:
            if not (2 <= len(name) <= 64):
                result.err(f"'name' length {len(name)} not in 2..64")
            if not NAME_RE.match(name):
                result.err(
                    f"'name' {name!r} does not match kebab-case regex "
                    f"^[a-z][a-z0-9-]*$"
                )

    # --- version
    if "version" in data:
        ver = data["version"]
        if not _is_str(ver):
            result.err("'version' must be a string")
        elif not SEMVER_RE.match(ver):
            result.err(f"'version' {ver!r} is not valid semver")

    # --- description
    if "description" in data:
        desc = data["description"]
        if not _is_str(desc):
            result.err("'description' must be a string")
        elif len(desc) > 200:
            result.err(f"'description' is {len(desc)} chars (max 200)")

    # --- author
    if "author" in data and not _is_str(data["author"]):
        result.err("'author' must be a string")

    # --- lanes
    if "lanes" in data:
        lanes = data["lanes"]
        if not _is_arr(lanes):
            result.err("'lanes' must be an array")
        else:
            for i, lane in enumerate(lanes):
                if not _is_str(lane):
                    result.err(f"'lanes[{i}]' must be a string")

    # --- entry_points
    if "entry_points" in data:
        ep = data["entry_points"]
        if not _is_obj(ep):
            result.err("'entry_points' must be an object")
        else:
            ep_extra = set(ep.keys()) - ALLOWED_ENTRY_POINT_KEYS
            if ep_extra:
                result.err(f"unknown entry_points keys: {sorted(ep_extra)}")
            for arr_key in ("commands", "extensions", "tools"):
                if arr_key in ep:
                    if not _is_arr(ep[arr_key]):
                        result.err(f"'entry_points.{arr_key}' must be an array")
                    else:
                        for i, item in enumerate(ep[arr_key]):
                            if not _is_str(item):
                                result.err(
                                    f"'entry_points.{arr_key}[{i}]' must be a string"
                                )
            if "hooks" in ep and not _is_obj(ep["hooks"]):
                result.err("'entry_points.hooks' must be an object")

    # --- settings_schema
    if "settings_schema" in data:
        ss = data["settings_schema"]
        if not _is_obj(ss):
            result.err("'settings_schema' must be an object")
        else:
            for setting_name, desc in ss.items():
                prefix = f"settings_schema.{setting_name}"
                if not _is_obj(desc):
                    result.err(f"'{prefix}' must be an object")
                    continue
                if "type" not in desc:
                    result.err(f"'{prefix}' missing 'type'")
                    continue
                t = desc["type"]
                if t not in ALLOWED_SETTING_TYPES:
                    result.err(
                        f"'{prefix}.type' = {t!r}; must be one of "
                        f"{sorted(ALLOWED_SETTING_TYPES)}"
                    )
                if "env" in desc and not _is_str(desc["env"]):
                    result.err(f"'{prefix}.env' must be a string")
                if "secret" in desc and not _is_bool(desc["secret"]):
                    result.err(f"'{prefix}.secret' must be a boolean")
                if "enum_values" in desc and not _is_arr(desc["enum_values"]):
                    result.err(f"'{prefix}.enum_values' must be an array")
                if "description" in desc and not _is_str(desc["description"]):
                    result.err(f"'{prefix}.description' must be a string")

    # --- features
    if "features" in data:
        feats = data["features"]
        if not _is_obj(feats):
            result.err("'features' must be an object")
        else:
            for fname, fdesc in feats.items():
                prefix = f"features.{fname}"
                if not _is_obj(fdesc):
                    result.err(f"'{prefix}' must be an object")
                    continue
                if "default" not in fdesc:
                    result.err(f"'{prefix}' missing required 'default'")
                elif not _is_bool(fdesc["default"]):
                    result.err(f"'{prefix}.default' must be a boolean")
                if "description" in fdesc and not _is_str(fdesc["description"]):
                    result.err(f"'{prefix}.description' must be a string")

    # --- dependencies
    if "dependencies" in data:
        deps = data["dependencies"]
        if not _is_obj(deps):
            result.err("'dependencies' must be an object")
        else:
            extra_eco = set(deps.keys()) - ALLOWED_DEPENDENCY_KEYS
            if extra_eco:
                result.err(f"unknown dependencies ecosystems: {sorted(extra_eco)}")
            for eco in ("python", "node"):
                if eco in deps and not _is_obj(deps[eco]):
                    result.err(f"'dependencies.{eco}' must be an object")

    # --- requires_lanes
    if "requires_lanes" in data:
        rl = data["requires_lanes"]
        if not _is_arr(rl):
            result.err("'requires_lanes' must be an array")
        else:
            for i, lane in enumerate(rl):
                if not _is_str(lane):
                    result.err(f"'requires_lanes[{i}]' must be a string")

    # --- min_sinister_version
    if "min_sinister_version" in data:
        msv = data["min_sinister_version"]
        if not _is_str(msv):
            result.err("'min_sinister_version' must be a string")
        elif not SEMVER_RE.match(msv):
            result.err(f"'min_sinister_version' {msv!r} is not valid semver")


def validate_business_rules(data: Any, result: ValidationResult) -> None:
    """Cross-field rules that go beyond the structural schema."""
    if not _is_obj(data):
        return

    # Rule 2: settings_schema enum requires enum_values
    ss = data.get("settings_schema")
    if _is_obj(ss):
        for setting_name, desc in ss.items():
            if not _is_obj(desc):
                continue
            if desc.get("type") == "enum":
                ev = desc.get("enum_values")
                if not _is_arr(ev) or len(ev) == 0:
                    result.err(
                        f"settings_schema.{setting_name}: type=enum requires "
                        f"non-empty 'enum_values' array"
                    )

    # Rule 3: entry_points.commands paths must end in .py
    ep = data.get("entry_points")
    if _is_obj(ep):
        cmds = ep.get("commands")
        if _is_arr(cmds):
            for i, p in enumerate(cmds):
                if _is_str(p) and not p.endswith(".py"):
                    result.err(
                        f"entry_points.commands[{i}] = {p!r}; "
                        f"Sinister is Python-first, command paths must end in .py"
                    )

    # Rule 4: requires_lanes unknown slugs -> WARN (non-fatal)
    rl = data.get("requires_lanes")
    if _is_arr(rl):
        for lane in rl:
            if _is_str(lane) and lane not in KNOWN_LANES:
                result.warn(
                    f"requires_lanes references unknown lane slug {lane!r}; "
                    f"known: {sorted(KNOWN_LANES)}"
                )


def validate_manifest(data: Any, path: Path | None = None) -> ValidationResult:
    """Run schema + business rules against a parsed manifest object."""
    result = ValidationResult(path)
    validate_schema(data, result)
    validate_business_rules(data, result)
    return result


def load_manifest(path: Path) -> Any:
    """Read + json-parse a manifest file. Raises on failure."""
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# CLI plumbing
# ---------------------------------------------------------------------------


def _print_result(result: ValidationResult) -> None:
    label = str(result.path) if result.path else "<manifest>"
    if result.ok and not result.warnings:
        print(f"OK   {label}")
        return
    if result.ok:
        print(f"OK   {label} (with warnings)")
    else:
        print(f"FAIL {label}")
    for e in result.errors:
        print(f"  ERROR   {e}")
    for w in result.warnings:
        print(f"  WARN    {w}")


def cmd_validate(args: argparse.Namespace) -> int:
    path = Path(args.path)
    if not path.is_file():
        print(f"ERROR: not a file: {path}", file=sys.stderr)
        return 3
    try:
        data = load_manifest(path)
    except json.JSONDecodeError as e:
        print(f"FAIL {path}")
        print(f"  ERROR   invalid JSON: {e}")
        return 2
    except OSError as e:
        print(f"ERROR: cannot read {path}: {e}", file=sys.stderr)
        return 3
    result = validate_manifest(data, path)
    _print_result(result)
    return 0 if result.ok else 2


def cmd_validate_all(args: argparse.Namespace) -> int:
    root = Path(args.dir)
    if not root.is_dir():
        print(f"ERROR: not a directory: {root}", file=sys.stderr)
        return 3
    manifests = sorted(root.rglob("plugin-manifest.json"))
    if not manifests:
        print(f"(no plugin-manifest.json files under {root})")
        return 0
    pass_count = 0
    fail_count = 0
    name_to_paths: dict[str, list[Path]] = defaultdict(list)
    for p in manifests:
        try:
            data = load_manifest(p)
        except json.JSONDecodeError as e:
            fail_count += 1
            print(f"FAIL {p}")
            print(f"  ERROR   invalid JSON: {e}")
            continue
        result = validate_manifest(data, p)
        _print_result(result)
        if result.ok:
            pass_count += 1
        else:
            fail_count += 1
        if _is_obj(data):
            n = data.get("name")
            if _is_str(n):
                name_to_paths[n].append(p)

    # Rule 1: duplicate-name check across the tree
    dup_fail = 0
    for n, paths in name_to_paths.items():
        if len(paths) > 1:
            dup_fail += 1
            print(f"FAIL duplicate name {n!r} found in:")
            for p in paths:
                print(f"  - {p}")

    print()
    print(
        f"summary: pass={pass_count} fail={fail_count} duplicate_names={dup_fail}"
    )
    return 0 if (fail_count == 0 and dup_fail == 0) else 2


def cmd_describe(args: argparse.Namespace) -> int:
    path = Path(args.path)
    if not path.is_file():
        print(f"ERROR: not a file: {path}", file=sys.stderr)
        return 3
    try:
        data = load_manifest(path)
    except json.JSONDecodeError as e:
        print(f"ERROR: invalid JSON: {e}", file=sys.stderr)
        return 3
    if not _is_obj(data):
        print("ERROR: manifest root is not an object", file=sys.stderr)
        return 3

    name = data.get("name", "<unnamed>")
    version = data.get("version", "<no-version>")
    desc = data.get("description", "")
    author = data.get("author", "<unknown>")
    lanes = data.get("lanes", []) or []
    ep = data.get("entry_points", {}) or {}
    cmds = ep.get("commands", []) or []
    hooks = ep.get("hooks", {}) or {}
    exts = ep.get("extensions", []) or []
    tools = ep.get("tools", []) or []
    settings = data.get("settings_schema", {}) or {}
    features = data.get("features", {}) or {}
    req_lanes = data.get("requires_lanes", []) or []
    min_ver = data.get("min_sinister_version", "")

    print(f"name              : {name}")
    print(f"version           : {version}")
    print(f"author            : {author}")
    if desc:
        print(f"description       : {desc}")
    print(f"lanes             : {', '.join(lanes) if lanes else '(none)'}")
    print(f"n_commands        : {len(cmds)}")
    print(f"n_hooks           : {len(hooks)}")
    print(f"n_extensions      : {len(exts)}")
    print(f"n_tools           : {len(tools)}")
    print(f"n_settings        : {len(settings)}")
    print(f"n_features        : {len(features)}")
    if req_lanes:
        print(f"requires_lanes    : {', '.join(req_lanes)}")
    if min_ver:
        print(f"min_sinister_ver  : {min_ver}")
    return 0


def cmd_example(args: argparse.Namespace) -> int:
    if not EXAMPLE_PATH.is_file():
        # Fallback: emit an in-memory example if the on-disk one is missing.
        fallback = {
            "name": "fortune-builtin",
            "version": "0.1.0",
            "description": "Adds /fortune slash-command returning a daily fortune cookie",
            "author": "RKOJ-ELENO",
            "lanes": ["sterm"],
            "entry_points": {"commands": ["cmd_fortune.py"]},
        }
        print(json.dumps(fallback, indent=2))
        return 0
    with EXAMPLE_PATH.open("r", encoding="utf-8") as fh:
        text = fh.read()
    sys.stdout.write(text)
    if not text.endswith("\n"):
        sys.stdout.write("\n")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="plugin_manifest.py",
        description=(
            "Sinister plugin-manifest validator + helper. "
            "Schema lives at _shared-memory/schemas/plugin-manifest.schema.json. "
            "Author: RKOJ-ELENO :: 2026-05-26."
        ),
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    sp_validate = sub.add_parser(
        "validate",
        help="Validate a single plugin-manifest.json (exit 0 ok / 2 invalid).",
    )
    sp_validate.add_argument("path", help="Path to manifest JSON.")
    sp_validate.set_defaults(func=cmd_validate)

    sp_va = sub.add_parser(
        "validate-all",
        help="Recursively validate every plugin-manifest.json under DIR.",
    )
    sp_va.add_argument("dir", help="Directory to walk.")
    sp_va.set_defaults(func=cmd_validate_all)

    sp_describe = sub.add_parser(
        "describe", help="Human-readable summary of a manifest."
    )
    sp_describe.add_argument("path", help="Path to manifest JSON.")
    sp_describe.set_defaults(func=cmd_describe)

    sp_example = sub.add_parser(
        "example", help="Print the canonical example manifest to stdout."
    )
    sp_example.set_defaults(func=cmd_example)

    return p


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
