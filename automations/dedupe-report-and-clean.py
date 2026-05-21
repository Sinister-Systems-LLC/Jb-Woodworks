#!/usr/bin/env python3
# Author: RKOJ-ELENO :: 2026-05-21
"""Phase 2 (report) + Phase 3 (safe removals)."""
import os
import json
import time
import re
from datetime import datetime

DATA = r"D:\Sinister Sanctum\_shared-memory\audits\dedupe-scan-data.json"
REPORT = r"D:\Sinister Sanctum\_shared-memory\audits\dedupe-2026-05-21.md"

# protected path prefixes (case-insensitive)
PROTECTED = [
    r"_vault",
    r"_shared-memory\inbox",
    r"_shared-memory\heartbeats",
    r"_shared-memory\cross-agent",
    r"_shared-memory\PROGRESS",
]

# safe-remove patterns (regex on path)
SAFE_PATTERNS = [
    re.compile(r"__pycache__[\\/].*\.pyc$", re.IGNORECASE),
    re.compile(r"\.pytest_cache[\\/]", re.IGNORECASE),
    re.compile(r"\.mypy_cache[\\/]", re.IGNORECASE),
    re.compile(r"\.ruff_cache[\\/]", re.IGNORECASE),
    re.compile(r"\.tmp$", re.IGNORECASE),
    re.compile(r"\.bak$", re.IGNORECASE),
]
LOG_PATTERN = re.compile(r"\.log$", re.IGNORECASE)
SEVEN_DAYS = 7 * 86400

def is_protected(path: str) -> bool:
    pl = path.lower()
    for p in PROTECTED:
        if p.lower() in pl:
            return True
    return False

def is_safe_remove(path: str, mtime: float) -> bool:
    for pat in SAFE_PATTERNS:
        if pat.search(path):
            return True
    if LOG_PATTERN.search(path):
        if (time.time() - mtime) > SEVEN_DAYS:
            return True
    return False

def canonical_priority(path: str) -> tuple:
    """Lower tuple = preferred (kept)."""
    pl = path.lower()
    has_tools = 0 if (os.sep + "tools" + os.sep) in pl else 1
    has_shared_mem = 1 if (os.sep + "_shared-memory" + os.sep) in pl else 0
    # tools/ over _shared-memory/ → tools wins (lower)
    pri1 = has_tools  # 0 = has tools
    pri2 = has_shared_mem  # 0 = NOT shared-memory (preferred)
    depth = path.count(os.sep)
    has_projects = 0 if (os.sep + "projects" + os.sep) in pl else 1
    return (pri1, pri2, depth, has_projects, path.lower())

def pick_canonical(paths: list[str]) -> str:
    return sorted(paths, key=canonical_priority)[0]

def human(n: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if n < 1024:
            return f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}TB"

def main():
    with open(DATA, "r", encoding="utf-8") as f:
        data = json.load(f)

    groups = data["dup_groups"]
    name_dups = data["name_dups"]

    # categorize each duplicate group
    safe_deletions = []   # list of paths to delete
    review_groups = []    # groups for operator review

    for g in groups:
        paths = g["paths"]
        # skip if any path protected
        if any(is_protected(p) for p in paths):
            review_groups.append({"reason": "protected", **g})
            continue
        # pick canonical
        canonical = pick_canonical(paths)
        dups = [p for p in paths if p != canonical]
        # check each dup for safe-removal eligibility
        safe_this_group = []
        unsafe_this_group = []
        for d in dups:
            try:
                mt = os.path.getmtime(d)
            except OSError:
                mt = time.time()
            if is_safe_remove(d, mt):
                safe_this_group.append(d)
            else:
                unsafe_this_group.append(d)
        if safe_this_group:
            safe_deletions.extend(safe_this_group)
        if unsafe_this_group:
            review_groups.append({
                "reason": "needs-review",
                "canonical": canonical,
                "duplicates_remaining": unsafe_this_group,
                **{k: v for k, v in g.items() if k != "paths"},
            })

    # Phase 3 — execute safe deletions
    deleted = 0
    freed = 0
    errors = []
    for path in safe_deletions:
        try:
            sz = os.path.getsize(path)
            os.remove(path)
            deleted += 1
            freed += sz
        except OSError as e:
            errors.append(f"{path}: {e}")

    # Top 20 by wasted bytes
    top20 = sorted(groups, key=lambda g: g["wasted"], reverse=True)[:20]

    # Build report
    lines = []
    lines.append("# Sanctum Dedupe Sweep — 2026-05-21")
    lines.append("")
    lines.append("Author: RKOJ-ELENO :: 2026-05-21")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- **Total files scanned:** {data['total_files']:,}")
    lines.append(f"- **Total bytes:** {human(data['total_bytes'])} ({data['total_bytes']:,} B)")
    lines.append(f"- **Hash-duplicate groups:** {len(groups)} ({data['num_dup_groups_over_1kb']} with size >1KB)")
    lines.append(f"- **Name-only duplicates (different content):** {len(data['name_dups'])}")
    lines.append(f"- **Scan elapsed:** {data['elapsed_sec']}s")
    lines.append(f"- **Scan timed out (9min cap):** {data['timed_out']} — report is partial if true")
    lines.append(f"- **Skipped (>50MB):** {data['skipped_large']}")
    lines.append(f"- **Read errors:** {data['skipped_err']}")
    lines.append("")
    lines.append("## Phase 3 — Safe Removals (executed)")
    lines.append("")
    lines.append(f"- **Files deleted:** {deleted}")
    lines.append(f"- **Bytes freed:** {human(freed)}")
    lines.append(f"- **Errors:** {len(errors)}")
    if errors[:10]:
        lines.append("")
        lines.append("Sample errors:")
        for e in errors[:10]:
            lines.append(f"- `{e}`")
    lines.append("")
    lines.append("Categories removed (canonical kept, duplicates removed):")
    lines.append("- `__pycache__/*.pyc`")
    lines.append("- `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`")
    lines.append("- `.log` files older than 7 days")
    lines.append("- `.tmp`, `.bak` files")
    lines.append("")
    lines.append("## Top 20 Hash-Duplicate Groups by Wasted Bytes")
    lines.append("")
    lines.append("| # | Size | Count | Wasted | Sample Path |")
    lines.append("|---|------|-------|--------|-------------|")
    for i, g in enumerate(top20, 1):
        sample = g["paths"][0]
        lines.append(f"| {i} | {human(g['size'])} | {g['count']} | {human(g['wasted'])} | `{sample}` |")
    lines.append("")
    lines.append("## Groups Needing Operator Review (NOT auto-deleted)")
    lines.append("")
    lines.append(f"Total: {len(review_groups)} groups. Top 30 by wasted bytes:")
    lines.append("")
    review_sorted = sorted(review_groups, key=lambda g: g.get("wasted", 0), reverse=True)[:30]
    for i, g in enumerate(review_sorted, 1):
        reason = g.get("reason", "")
        wasted = human(g.get("wasted", 0))
        count = g.get("count", 0)
        lines.append(f"### {i}. [{reason}] {wasted} wasted across {count} files")
        if "canonical" in g:
            lines.append(f"- **Keep:** `{g['canonical']}`")
            lines.append("- **Review for removal:**")
            for p in g.get("duplicates_remaining", []):
                lines.append(f"  - `{p}`")
        else:
            for p in g.get("paths", []):
                lines.append(f"- `{p}`")
        lines.append("")
    lines.append("## Same-Name Different-Content (Top 30)")
    lines.append("")
    lines.append("These are NOT duplicates by content — same filename, different hashes. Operator review only.")
    lines.append("")
    for i, nd in enumerate(name_dups[:30], 1):
        lines.append(f"### {i}. `{nd['name']}` — {nd['count']} copies, {nd['distinct_hashes']} distinct contents")
        for p in nd["paths"][:10]:
            lines.append(f"- `{p}`")
        if len(nd["paths"]) > 10:
            lines.append(f"- ... +{len(nd['paths']) - 10} more")
        lines.append("")

    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Deleted: {deleted} files, freed {human(freed)}")
    print(f"Review groups: {len(review_groups)}")
    print(f"Report: {REPORT}")
    # write summary for caller
    summary = {
        "deleted": deleted,
        "freed_bytes": freed,
        "review_groups": len(review_groups),
        "errors": len(errors),
    }
    with open(r"D:\Sinister Sanctum\_shared-memory\audits\dedupe-summary.json", "w") as f:
        json.dump(summary, f, indent=2)

if __name__ == "__main__":
    main()
