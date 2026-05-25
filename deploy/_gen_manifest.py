# Author: RKOJ-ELENO :: 2026-05-25
"""One-shot MANIFEST.txt generator. Lists every file in deploy/ with size + sha256."""
from __future__ import annotations
import hashlib, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "MANIFEST.txt"
SKIP_NAMES = {"MANIFEST.txt", "_gen_manifest.py"}
SKIP_DIRS = {"__pycache__"}

def sha256_of(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

rows = []
for p in sorted(HERE.rglob("*")):
    if not p.is_file():
        continue
    if p.name in SKIP_NAMES:
        continue
    if any(part in SKIP_DIRS for part in p.relative_to(HERE).parts):
        continue
    rel = p.relative_to(HERE).as_posix()
    size = p.stat().st_size
    digest = sha256_of(p)
    rows.append((rel, size, digest))

lines = [
    "# Sinister Sanctum :: deploy/ MANIFEST",
    "# Author: RKOJ-ELENO :: 2026-05-25",
    "# Format: <sha256>  <size_bytes>  <relative_path>",
    "",
]
for rel, size, digest in rows:
    lines.append(f"{digest}  {size:>10}  {rel}")
lines.append("")
lines.append(f"# total files: {len(rows)}")
lines.append(f"# total bytes: {sum(r[1] for r in rows)}")

OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"wrote {OUT} ({len(rows)} files)")
