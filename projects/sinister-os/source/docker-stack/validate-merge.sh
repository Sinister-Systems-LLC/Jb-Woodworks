#!/usr/bin/env bash
# validate-merge.sh — deep-merge collision checker for Sinister docker-stack overlays
# Author: RKOJ-ELENO :: 2026-05-24
#
# Purpose:
#   `docker compose -f a -f b -f c config` does a deep-merge and silently lets later
#   files shadow earlier files. That's usually intended — but for an OS-shell stack
#   with 5+ overlays (base + hardened + mesh + doh + wg-fallback + panel-shell + ...),
#   silent shadowing is a foot-gun. A later overlay can quietly disable a security
#   setting (`cap_drop`, `read_only`, `user`, sysctls) without anyone noticing.
#
# What this script does:
#   - Loads N compose files via PyYAML (no docker daemon required).
#   - Walks `services.<name>.<key>` for every service and detects keys that appear
#     in 2+ files with DIFFERENT values (i.e. a later overlay shadows an earlier one).
#   - WARN level: scalar shadowing (later wins; explicit override, probably intended).
#   - FAIL level: incompatible network_mode collisions (host vs bridge vs container:X).
#   - FAIL level: cap_drop shadowed by later cap_add of the dropped cap.
#
# Usage:
#   ./validate-merge.sh docker-compose.yml compose.hardened.yml compose.mesh.yml ...
#
# Exit codes:
#   0 = no FAIL findings (may have WARN findings — printed but tolerated).
#   1 = at least one FAIL finding; the merge is unsafe to deploy.
#   2 = invocation error (missing file, yaml parse fail).

set -euo pipefail

readonly SCRIPT_NAME="validate-merge.sh"

if [ "$#" -lt 2 ]; then
    echo "${SCRIPT_NAME}: usage: ./${SCRIPT_NAME} <compose1.yml> <compose2.yml> [compose3.yml ...]" >&2
    echo "${SCRIPT_NAME}: need at least 2 files to validate a merge" >&2
    exit 2
fi

for f in "$@"; do
    if [ ! -r "$f" ]; then
        echo "${SCRIPT_NAME}: cannot read: ${f}" >&2
        exit 2
    fi
done

python3 - "$@" <<'PYEOF'
import sys
import yaml

files = sys.argv[1:]
docs = []

for fp in files:
    try:
        with open(fp) as fh:
            doc = yaml.safe_load(fh)
        if doc is None:
            print(f"WARN  {fp}: empty document (skipped)", file=sys.stderr)
            continue
        docs.append((fp, doc))
    except yaml.YAMLError as e:
        print(f"FAIL  {fp}: yaml parse error: {e}", file=sys.stderr)
        sys.exit(2)

# Collect every service.<name>.<key> = value tuple per file.
# service_keys: { service_name: { key: [ (file, value), ... ] } }
service_keys = {}

for fp, doc in docs:
    services = doc.get("services") or {}
    for svc_name, svc_def in services.items():
        if not isinstance(svc_def, dict):
            continue
        service_keys.setdefault(svc_name, {})
        for key, val in svc_def.items():
            service_keys[svc_name].setdefault(key, []).append((fp, val))

warn_count = 0
fail_count = 0

NETWORK_MODE_FAIL_KEY = "network_mode"
HARDEN_KEYS_THAT_SHOULD_PERSIST = {"read_only", "user", "cap_drop", "security_opt"}

for svc_name, keys in sorted(service_keys.items()):
    for key, occurrences in sorted(keys.items()):
        if len(occurrences) < 2:
            continue
        # Multiple files set this key. Check if values differ.
        first_fp, first_val = occurrences[0]
        differing = [(fp, v) for fp, v in occurrences[1:] if v != first_val]
        if not differing:
            continue

        # FAIL: network_mode collision
        if key == NETWORK_MODE_FAIL_KEY:
            print(f"FAIL  services.{svc_name}.{key} — incompatible values across overlays:")
            for fp, v in occurrences:
                print(f"        {fp}: {v!r}")
            fail_count += 1
            continue

        # FAIL: cap_drop shadowed by cap_add re-introducing the same cap
        if key == "cap_drop":
            # Check the same service's cap_add list for re-additions
            cap_add_occurrences = service_keys.get(svc_name, {}).get("cap_add", [])
            dropped = set()
            for fp, v in occurrences:
                if isinstance(v, list):
                    dropped.update(v)
            re_added = set()
            for fp, v in cap_add_occurrences:
                if isinstance(v, list):
                    re_added.update(v)
            overlap = dropped & re_added
            if overlap:
                print(f"FAIL  services.{svc_name}: caps in cap_drop also re-added via cap_add: {sorted(overlap)}")
                fail_count += 1
                continue

        # FAIL: read_only=true shadowed by read_only=false
        if key == "read_only":
            values = [v for _, v in occurrences]
            if True in values and False in values:
                print(f"FAIL  services.{svc_name}.{key} — toggled true and false across overlays:")
                for fp, v in occurrences:
                    print(f"        {fp}: {v!r}")
                fail_count += 1
                continue

        # Otherwise: WARN
        severity = "WARN"
        if key in HARDEN_KEYS_THAT_SHOULD_PERSIST:
            severity = "WARN-SEC"
        print(f"{severity}  services.{svc_name}.{key} — overridden across overlays:")
        for fp, v in occurrences:
            print(f"        {fp}: {v!r}")
        warn_count += 1

print(f"\n--- summary: {warn_count} WARN, {fail_count} FAIL across {len(docs)} files ---")
sys.exit(1 if fail_count > 0 else 0)
PYEOF
