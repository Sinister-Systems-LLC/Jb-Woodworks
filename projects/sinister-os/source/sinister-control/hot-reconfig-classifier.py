#!/usr/bin/env python3
# Author: RKOJ-ELENO :: 2026-05-25
# Sinister OS — hot-reconfig classifier
#
# Decides whether a /etc/sinister/*.toml change is hot-applyable or requires
# a reboot. Inputs are pre/post snapshots of one or more TOML files; the
# classifier returns either:
#   - hot       (reload running services; no reboot)
#   - service   (systemctl restart <unit>; no reboot)
#   - reboot    (kernel/initramfs/bootloader/sysctl-immutable surface touched)
#
# Wired into:
#   - reboot-required.sh  (called when verdict=reboot)
#   - eve apply config <file>  (decides reload strategy)
#
# Usage:
#   hot-reconfig-classifier.py --pre /tmp/cfg.before.toml --post /etc/sinister/cfg.toml
#   hot-reconfig-classifier.py --pre-dir /tmp/snap-before --post-dir /etc/sinister
#
# Exit codes mirror verdicts: 0=hot, 10=service, 20=reboot, 2=usage, 3=error

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # type: ignore

REBOOT_KEYS = {
    "kernel.cmdline",
    "kernel.modules.builtin",
    "boot.bootloader",
    "boot.initramfs",
    "boot.secureboot",
    "fs.root.device",
    "fs.root.options",
    "sysctl.immutable",
    "selinux.policy",
    "apparmor.profile.builtin",
    "audit.kernel",
    "ima.policy",
    "net.bridge.module",
}

SERVICE_PREFIXES = {
    "service.",
    "daemon.",
    "agent.",
    "mesh.",
    "vault.",
    "panel.",
    "eve.",
}

# Keys that match a SERVICE_PREFIXES prefix but are safe to hot-reload (no
# service restart needed). The operator directive "actively change things like
# UI look ... without a reboot" depends on accent/theme tokens being here.
HOT_OVERRIDE = {
    "panel.accent",
    "panel.theme",
    "panel.layout.density",
    "panel.layout.sidebar",
    "eve.accent",
    "mesh.banner.message",
}


def flatten(d: dict, prefix: str = "") -> dict:
    out = {}
    for k, v in d.items():
        key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            out.update(flatten(v, key))
        else:
            out[key] = v
    return out


def load(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("rb") as f:
        return flatten(tomllib.load(f))


def diff(pre: dict, post: dict) -> dict:
    added = {k: post[k] for k in post if k not in pre}
    removed = {k: pre[k] for k in pre if k not in post}
    changed = {k: (pre[k], post[k]) for k in pre if k in post and pre[k] != post[k]}
    return {"added": added, "removed": removed, "changed": changed}


def classify(d: dict) -> tuple[str, list[str]]:
    """Return (verdict, hits) where verdict in {hot, service, reboot}."""
    touched = set(d["added"]) | set(d["removed"]) | set(d["changed"])
    hits: list[str] = []
    needs_reboot = False
    needs_service = False
    for key in touched:
        if key in REBOOT_KEYS:
            hits.append(f"reboot:{key}")
            needs_reboot = True
            continue
        if key in HOT_OVERRIDE:
            hits.append(f"hot:{key}")
            continue
        if any(key.startswith(p) for p in SERVICE_PREFIXES):
            hits.append(f"service:{key}")
            needs_service = True
            continue
        hits.append(f"hot:{key}")
    if needs_reboot:
        return "reboot", hits
    if needs_service:
        return "service", hits
    return "hot", hits


def collect(p: Path) -> dict:
    if p.is_dir():
        merged: dict = {}
        for child in sorted(p.glob("*.toml")):
            merged.update(load(child))
        return merged
    return load(p)


VERDICT_EXIT = {"hot": 0, "service": 10, "reboot": 20}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pre")
    ap.add_argument("--post")
    ap.add_argument("--pre-dir")
    ap.add_argument("--post-dir")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if (args.pre and not args.post) or (args.post and not args.pre):
        print("hot-reconfig: --pre and --post must be paired", file=sys.stderr)
        return 2
    if (args.pre_dir and not args.post_dir) or (args.post_dir and not args.pre_dir):
        print("hot-reconfig: --pre-dir and --post-dir must be paired", file=sys.stderr)
        return 2
    if not (args.pre or args.pre_dir):
        print("usage: hot-reconfig-classifier.py --pre X --post Y | --pre-dir A --post-dir B", file=sys.stderr)
        return 2

    pre_src = Path(args.pre or args.pre_dir)
    post_src = Path(args.post or args.post_dir)

    try:
        pre = collect(pre_src)
        post = collect(post_src)
    except Exception as e:  # noqa: BLE001
        print(f"hot-reconfig: parse error: {e}", file=sys.stderr)
        return 3

    d = diff(pre, post)
    verdict, hits = classify(d)

    if args.json:
        print(json.dumps({"verdict": verdict, "diff": d, "hits": hits}, indent=2, default=str))
    else:
        print(f"verdict={verdict}")
        for h in hits:
            print(f"  {h}")

    return VERDICT_EXIT[verdict]


if __name__ == "__main__":
    sys.exit(main())
