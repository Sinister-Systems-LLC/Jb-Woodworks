# Author: RKOJ-ELENO :: 2026-05-21
# D-drive path reference auditor for Sanctum reorg planning.
# Read-only scan.
import os
import re
import json
import time
from datetime import datetime, timezone

ROOT = r"D:\Sinister Sanctum"
OUT = r"D:\Sinister Sanctum\_shared-memory\audits\d-drive-path-refs-2026-05-21.json"
MAX_REFS = 2000
MAX_FILE_BYTES = 5 * 1024 * 1024
TIME_BUDGET_SEC = 270  # ~4.5 min, leaving room for write

EXCLUDE_DIRS = {
    ".git", ".swarm", "__pycache__", "node_modules", "build", "dist",
    ".pytest_cache", ".venv", "venv", ".mypy_cache", ".ruff_cache",
}
EXCLUDE_REL_PREFIXES = (
    os.path.join(".claude", "worktrees"),
)

EXTS = {".md", ".py", ".ps1", ".bat", ".json", ".yaml", ".yml", ".toml", ".cmd", ".txt"}

PATTERNS = [
    # (label, compiled regex, flags-applied)
    ("D:\\Sinister\\Sinister Skills", re.compile(r"D:[\\/]+Sinister[\\/]+Sinister Skills", re.IGNORECASE)),
    ("D:\\Sinister\\ (not Sanctum)", re.compile(r"D:[\\/]+Sinister[\\/]+(?!Sanctum)", re.IGNORECASE)),
    ("D:\\sinister-vault\\", re.compile(r"D:[\\/]+sinister-vault[\\/]*", re.IGNORECASE)),
    ("D:\\Sinister-Term-WT\\", re.compile(r"D:[\\/]+Sinister-Term-WT[\\/]*", re.IGNORECASE)),
    ("D:\\_backups\\", re.compile(r"D:[\\/]+_backups[\\/]*", re.IGNORECASE)),
    ("D:\\Sinister LLC\\", re.compile(r"D:[\\/]+Sinister LLC[\\/]*", re.IGNORECASE)),
    ("substring:Sinister Skills", re.compile(r"Sinister Skills", re.IGNORECASE)),
    ("substring:sinister-vault", re.compile(r"sinister-vault", re.IGNORECASE)),
]

def is_junction(path):
    try:
        if os.path.islink(path):
            return True
        # Windows junction detection
        try:
            st = os.lstat(path)
            # FILE_ATTRIBUTE_REPARSE_POINT = 0x400
            if hasattr(st, "st_file_attributes") and (st.st_file_attributes & 0x400):
                return True
        except OSError:
            pass
    except OSError:
        return False
    return False

def main():
    t0 = time.time()
    refs = []
    summary = {}  # label -> {"count": int, "files": set}
    file_ref_counts = {}  # rel -> {"count": int, "patterns": set}
    files_scanned = 0
    truncated = False
    time_flag = False
    delta_after_cap = 0

    for label, _ in PATTERNS:
        summary[label] = {"count": 0, "files": set()}

    for dirpath, dirnames, filenames in os.walk(ROOT):
        # Time check
        if time.time() - t0 > TIME_BUDGET_SEC:
            time_flag = True
            break

        # Prune excluded dirs (in-place)
        pruned = []
        for d in dirnames:
            if d in EXCLUDE_DIRS:
                continue
            full = os.path.join(dirpath, d)
            rel = os.path.relpath(full, ROOT)
            if any(rel.startswith(p) for p in EXCLUDE_REL_PREFIXES):
                continue
            if is_junction(full):
                continue
            pruned.append(d)
        dirnames[:] = pruned

        for fn in filenames:
            ext = os.path.splitext(fn)[1].lower()
            if ext not in EXTS:
                continue
            full = os.path.join(dirpath, fn)
            try:
                if is_junction(full):
                    continue
                sz = os.path.getsize(full)
                if sz > MAX_FILE_BYTES:
                    continue
            except OSError:
                continue

            rel = os.path.relpath(full, ROOT).replace("\\", "/")
            try:
                with open(full, "r", encoding="utf-8", errors="replace") as f:
                    lines = f.readlines()
            except OSError:
                continue

            files_scanned += 1
            file_had_match = False
            for lineno, line in enumerate(lines, 1):
                if len(line) > 2000:
                    line_to_check = line[:2000]
                else:
                    line_to_check = line
                for label, rx in PATTERNS:
                    for m in rx.finditer(line_to_check):
                        match_str = m.group(0)
                        summary[label]["count"] += 1
                        summary[label]["files"].add(rel)
                        if not truncated:
                            if len(refs) < MAX_REFS:
                                refs.append({
                                    "file": rel,
                                    "line": lineno,
                                    "pattern": label,
                                    "match": match_str.strip(),
                                })
                            else:
                                truncated = True
                        if truncated:
                            delta_after_cap += 1
                        fc = file_ref_counts.setdefault(rel, {"count": 0, "patterns": set()})
                        fc["count"] += 1
                        fc["patterns"].add(label)
                        file_had_match = True
            # end lines

    # Build high_impact (top 20 by ref_count)
    high_impact = sorted(
        ({"path": p, "ref_count": v["count"], "patterns": sorted(v["patterns"])}
         for p, v in file_ref_counts.items()),
        key=lambda x: x["ref_count"], reverse=True
    )[:20]

    # Total refs (true total, even when capped)
    total_refs = sum(v["count"] for v in summary.values())

    out = {
        "scanned_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "scan_root": ROOT,
        "total_files_scanned": files_scanned,
        "total_refs_found": total_refs,
        "truncated": truncated,
        "truncated_delta": delta_after_cap if truncated else 0,
        "time_budget_hit": time_flag,
        "elapsed_seconds": round(time.time() - t0, 2),
        "summary_by_pattern": {
            label: {"count": data["count"], "files": len(data["files"])}
            for label, data in summary.items()
        },
        "high_impact_files": high_impact,
        "refs": refs,
        "note": ("TRUNCATED at 2000 refs; see truncated_delta for additional matches not enumerated"
                 if truncated else None),
        "authorship": "RKOJ-ELENO :: 2026-05-21",
    }

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    print(f"files_scanned={files_scanned} total_refs={total_refs} truncated={truncated} elapsed={out['elapsed_seconds']}s")

if __name__ == "__main__":
    main()
