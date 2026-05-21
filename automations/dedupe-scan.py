#!/usr/bin/env python3
# Author: RKOJ-ELENO :: 2026-05-21
"""Sanctum dedupe scanner — Phase 1 + Phase 2."""
import os
import sys
import hashlib
import json
import time
from collections import defaultdict

ROOT = r"D:\Sinister Sanctum"
EXCLUDE_DIRS = {
    ".git", "node_modules", "__pycache__", "build", "dist",
    ".swarm", ".pytest_cache", ".mypy_cache", ".ruff_cache",
}
EXCLUDE_PATH_PARTS = {
    os.path.join(".claude", "worktrees"),
}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
HARD_TIMEOUT = 60 * 9  # 9 minutes (leave buffer for report writing)

def should_skip_dir(dirpath: str) -> bool:
    base = os.path.basename(dirpath)
    if base in EXCLUDE_DIRS:
        return True
    # exclude .claude/worktrees specifically
    if os.path.sep + ".claude" + os.path.sep + "worktrees" in dirpath:
        return True
    # skip junction/symlink (projects/<X>/source/ etc.)
    try:
        if os.path.islink(dirpath):
            return True
        # Windows: detect junction via reparse point attribute
        import stat
        st = os.lstat(dirpath)
        if hasattr(st, "st_file_attributes"):
            FILE_ATTRIBUTE_REPARSE_POINT = 0x400
            if st.st_file_attributes & FILE_ATTRIBUTE_REPARSE_POINT:
                return True
    except OSError:
        return True
    return False

def sha256_of_file(path: str) -> str:
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            while True:
                chunk = f.read(1024 * 1024)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()
    except (OSError, PermissionError):
        return ""

def main():
    start = time.time()
    by_hash: dict[str, list[tuple[str, int]]] = defaultdict(list)
    by_name: dict[str, list[str]] = defaultdict(list)
    total_files = 0
    total_bytes = 0
    skipped_large = 0
    skipped_err = 0
    timed_out = False

    for dirpath, dirnames, filenames in os.walk(ROOT):
        # filter dirs in place
        dirnames[:] = [
            d for d in dirnames
            if not should_skip_dir(os.path.join(dirpath, d))
        ]
        for fn in filenames:
            if time.time() - start > HARD_TIMEOUT:
                timed_out = True
                break
            full = os.path.join(dirpath, fn)
            try:
                if os.path.islink(full):
                    continue
                st = os.stat(full)
                if not os.path.isfile(full):
                    continue
                sz = st.st_size
            except OSError:
                skipped_err += 1
                continue
            total_files += 1
            total_bytes += sz
            by_name[fn].append(full)
            if sz > MAX_FILE_SIZE:
                skipped_large += 1
                continue
            if sz == 0:
                continue  # skip empty files from dedup grouping
            h = sha256_of_file(full)
            if not h:
                skipped_err += 1
                continue
            by_hash[h].append((full, sz))
        if timed_out:
            break

    # Build duplicate groups
    dup_groups = []
    for h, entries in by_hash.items():
        if len(entries) >= 2:
            sz = entries[0][1]
            wasted = (len(entries) - 1) * sz
            dup_groups.append({
                "hash": h,
                "size": sz,
                "count": len(entries),
                "wasted": wasted,
                "paths": [p for p, _ in entries],
            })

    dup_groups.sort(key=lambda g: g["wasted"], reverse=True)

    # name-only duplicates (different content)
    name_dups = []
    for name, paths in by_name.items():
        if len(paths) < 2:
            continue
        # only those where not all share a single hash
        hashes = set()
        for p in paths:
            for h, entries in by_hash.items():
                if any(x == p for x, _ in entries):
                    hashes.add(h)
                    break
        if len(hashes) > 1:
            name_dups.append({"name": name, "count": len(paths), "paths": paths, "distinct_hashes": len(hashes)})

    name_dups.sort(key=lambda x: x["count"], reverse=True)

    result = {
        "total_files": total_files,
        "total_bytes": total_bytes,
        "skipped_large": skipped_large,
        "skipped_err": skipped_err,
        "elapsed_sec": round(time.time() - start, 1),
        "timed_out": timed_out,
        "dup_groups": dup_groups,
        "name_dups": name_dups[:50],
        "num_dup_groups_over_1kb": sum(1 for g in dup_groups if g["size"] > 1024),
    }

    out = r"D:\Sinister Sanctum\_shared-memory\audits\dedupe-scan-data.json"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(f"Scanned {total_files} files / {total_bytes/1e6:.1f} MB in {result['elapsed_sec']}s")
    print(f"Duplicate groups: {len(dup_groups)} (>{result['num_dup_groups_over_1kb']} over 1KB)")
    print(f"Name-only dups: {len(name_dups)}")
    print(f"Timed out: {timed_out}")
    print(f"Wrote: {out}")

if __name__ == "__main__":
    main()
