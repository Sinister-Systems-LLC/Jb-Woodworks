# Author: RKOJ-ELENO :: 2026-05-24
# Quick post-Phase-2/3 broken-ref audit. Looks for refs to OLD paths that should
# now point to new locations. Read-only.

import os, re, json
from datetime import datetime, timezone

ROOT = r"D:\Sinister Sanctum"
OUT  = r"D:\Sinister Sanctum\_shared-memory\audits\broken-refs-after-phase-23-2026-05-24.json"

EXCLUDE_DIRS = {".git", "__pycache__", "node_modules", "build", "dist", ".venv", "venv", ".pytest_cache", ".mypy_cache", ".ruff_cache", "_archive"}
EXCLUDE_REL_PREFIXES = (os.path.join(".claude", "worktrees"),)
EXTS = {".md", ".py", ".ps1", ".bat", ".json", ".yaml", ".yml", ".toml", ".cmd", ".txt", ".sh"}
MAX_FILE_BYTES = 5 * 1024 * 1024

# Old paths that should NO LONGER appear as live references (moved to new location)
PATTERNS = [
    ("D:\\LetsText (-> D:\\Personal\\LetsText)",         re.compile(r"D:[\\/]+LetsText\b", re.IGNORECASE)),
    ("D:\\Research (-> D:\\Personal\\Research)",         re.compile(r"D:[\\/]+Research\b", re.IGNORECASE)),
    ("D:\\Seagate (-> D:\\Personal\\Seagate)",           re.compile(r"D:[\\/]+Seagate\b", re.IGNORECASE)),
    ("D:\\jbw-deploy (-> D:\\Personal\\jbw-deploy)",     re.compile(r"D:[\\/]+jbw-deploy\b", re.IGNORECASE)),
    ("D:\\jbw-proxy (-> D:\\Personal\\jbw-proxy)",       re.compile(r"D:[\\/]+jbw-proxy\b", re.IGNORECASE)),
    ("D:\\jbw-standalone (-> D:\\Personal\\jbw-standalone)", re.compile(r"D:[\\/]+jbw-standalone\b", re.IGNORECASE)),
    ("D:\\jbw-wt (-> D:\\Personal\\jbw-wt)",             re.compile(r"D:[\\/]+jbw-wt\b", re.IGNORECASE)),
    ("D:\\jbw-wt2 (-> D:\\Personal\\jbw-wt2)",           re.compile(r"D:[\\/]+jbw-wt2\b", re.IGNORECASE)),
    ("D:\\rkoj-eve-picker-wt (-> Sanctum/worktrees/rkoj-eve-picker)", re.compile(r"D:[\\/]+rkoj-eve-picker-wt\b", re.IGNORECASE)),
    ("D:\\eve-build-iter33 (-> Sanctum/builds/eve-iter33)", re.compile(r"D:[\\/]+eve-build-iter33\b", re.IGNORECASE)),
    ("D:\\sinister-vault (-> Sanctum/_vault)",           re.compile(r"D:[\\/]+sinister-vault\b", re.IGNORECASE)),
    ("D:\\Sinister-Term-WT (-> Sanctum/worktrees/sinister-term-wt)", re.compile(r"D:[\\/]+Sinister-Term-WT\b", re.IGNORECASE)),
    ("D:\\d\\Sinister (-> Backups/d-misnamed/Sinister)", re.compile(r"D:[\\/]+d[\\/]+Sinister", re.IGNORECASE)),
    ("D:\\_backups\\ (-> D:\\Backups\\_backups-merged)", re.compile(r"D:[\\/]+_backups[\\/]+", re.IGNORECASE)),
    ("D:\\tmp\\ (-> Sanctum/tmp)",                       re.compile(r"D:[\\/]+tmp[\\/]+", re.IGNORECASE)),
]

results = {label: {"count": 0, "hits": []} for label, _ in PATTERNS}
files_scanned = 0
files_with_hits = 0
start = datetime.now(timezone.utc)

def should_skip(rel):
    return any(rel.startswith(p) for p in EXCLUDE_REL_PREFIXES)

for dirpath, dirnames, filenames in os.walk(ROOT):
    dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
    rel = os.path.relpath(dirpath, ROOT)
    if rel != "." and should_skip(rel):
        dirnames[:] = []
        continue
    for fn in filenames:
        ext = os.path.splitext(fn)[1].lower()
        if ext not in EXTS:
            continue
        full = os.path.join(dirpath, fn)
        try:
            sz = os.path.getsize(full)
            if sz > MAX_FILE_BYTES:
                continue
            with open(full, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception:
            continue
        files_scanned += 1
        file_had_hit = False
        for label, pat in PATTERNS:
            for m in pat.finditer(content):
                results[label]["count"] += 1
                if len(results[label]["hits"]) < 30:
                    line_no = content[:m.start()].count("\n") + 1
                    line = content.split("\n")[line_no - 1][:160]
                    results[label]["hits"].append({
                        "file": os.path.relpath(full, ROOT),
                        "line": line_no,
                        "text": line.strip(),
                    })
                file_had_hit = True
        if file_had_hit:
            files_with_hits += 1

elapsed = (datetime.now(timezone.utc) - start).total_seconds()
out = {
    "scanned_at": datetime.now(timezone.utc).isoformat(),
    "scan_root": ROOT,
    "files_scanned": files_scanned,
    "files_with_hits": files_with_hits,
    "elapsed_seconds": round(elapsed, 2),
    "summary": {label: {"count": r["count"], "hit_count": len(r["hits"])} for label, r in results.items()},
    "details": results,
}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2)
print(f"Wrote: {OUT}")
print(f"Files scanned: {files_scanned}  |  with hits: {files_with_hits}  |  elapsed: {elapsed:.1f}s")
print()
print("Hits per pattern (count = total occurrences):")
for label, r in results.items():
    print(f"  {r['count']:6d}  {label}")
