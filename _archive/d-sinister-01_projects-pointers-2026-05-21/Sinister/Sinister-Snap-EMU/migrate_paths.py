#!/usr/bin/env python3
"""migrate_paths.py — rewrite hardcoded Desktop paths to D: paths inside the
new canonical copy at `D:\\Sinister\\01_Projects\\Sinister\\Sinister-Snap-EMU\\source\\`.

Single-use migration helper. Walks the D: tree, replaces three forms of the
old path with the new path, atomically writes each file.

NEVER touches the Desktop source (`C:\\Users\\Zonia\\Desktop\\Sinister Snap EMU.API\\`).

Run modes:
  python migrate_paths.py --dry-run    # report what WOULD change, no writes
  python migrate_paths.py               # do the rewrite + log every change
"""
import argparse
import hashlib
import os
import pathlib
import sys

# This script lives at D:\Sinister\01_Projects\Sinister\Sinister-Snap-EMU\
# Target is the sibling source/ directory.
SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
TARGET_ROOT = SCRIPT_DIR / "source"

# Three forms of the old path → new path
REPLACEMENTS = [
    # Windows backslash form
    (r"C:\Users\Zonia\Desktop\Sinister Snap EMU.API",
     r"D:\Sinister\01_Projects\Sinister\Sinister-Snap-EMU\source"),
    # Windows forward-slash form (Python often uses this for cross-platform code)
    ("C:/Users/Zonia/Desktop/Sinister Snap EMU.API",
     "D:/Sinister/01_Projects/Sinister/Sinister-Snap-EMU/source"),
    # WSL mount form
    ("/mnt/c/Users/Zonia/Desktop/Sinister Snap EMU.API",
     "/mnt/d/Sinister/01_Projects/Sinister/Sinister-Snap-EMU/source"),
]

# Extensions to rewrite (text files only — never touch binaries)
TEXT_EXTS = {
    ".py", ".sh", ".bat", ".ps1", ".cmd",
    ".md", ".txt", ".json", ".yaml", ".yml",
    ".js", ".ts", ".cjs", ".mjs",
    ".html", ".css", ".xml",
    ".cfg", ".ini", ".toml", ".env",
    ".gitignore", ".gitattributes",
}

# Dirs to skip entirely
SKIP_DIRS = {
    ".git",                # internal pack/objects — don't touch
    "node_modules",        # JS deps — also don't touch
    "__pycache__",         # Python bytecode (excluded by robocopy already, but defensive)
    ".understand-anything", # snapshots (excluded by robocopy already, but defensive)
    "harvests",            # capture JSONs may include literal historic paths (operator's paper trail)
}


def should_rewrite(path: pathlib.Path) -> bool:
    """True if file is a text type we should rewrite."""
    if not path.is_file():
        return False
    # Skip if any ancestor dir is in SKIP_DIRS
    for ancestor in path.parents:
        if ancestor.name in SKIP_DIRS:
            return False
    # By extension, OR by name for extensionless config-ish files
    if path.suffix.lower() in TEXT_EXTS:
        return True
    if path.name in (".gitignore", ".gitattributes", "Dockerfile", "Makefile"):
        return True
    return False


def rewrite_file(path: pathlib.Path, dry_run: bool, log_lines: list):
    try:
        original = path.read_bytes()
    except Exception as e:
        log_lines.append(f"SKIP_READ_ERR {path}: {e}")
        return 0
    # Try utf-8 first, fall back to latin-1 (which is byte-preserving)
    try:
        text = original.decode("utf-8")
        was_utf8 = True
    except UnicodeDecodeError:
        try:
            text = original.decode("utf-16")
            was_utf8 = False
        except UnicodeDecodeError:
            log_lines.append(f"SKIP_BINARY {path}")
            return 0
    new_text = text
    total_count = 0
    for old, new in REPLACEMENTS:
        n = new_text.count(old)
        if n:
            total_count += n
            new_text = new_text.replace(old, new)
    if total_count == 0:
        return 0
    if dry_run:
        log_lines.append(f"WOULD_REWRITE n={total_count} {path}")
        return total_count
    # Atomic write: tempfile in same dir + rename
    tmp = path.with_name(path.name + ".migrate_paths.tmp")
    try:
        if was_utf8:
            tmp.write_bytes(new_text.encode("utf-8"))
        else:
            tmp.write_bytes(new_text.encode("utf-16"))
        os.replace(tmp, path)
        log_lines.append(f"REWROTE n={total_count} {path}")
    except Exception as e:
        log_lines.append(f"WRITE_ERR {path}: {e}")
        if tmp.exists():
            try: tmp.unlink()
            except Exception: pass
        return 0
    return total_count


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="Report what would change; do not write any files")
    ap.add_argument("--log", default=str(SCRIPT_DIR / "migrate_paths.log"),
                    help="Path to write the change log (default: alongside script)")
    args = ap.parse_args()

    if not TARGET_ROOT.is_dir():
        print(f"ERR: target root not found: {TARGET_ROOT}", file=sys.stderr)
        sys.exit(2)

    print(f"[+] migrate_paths.py {'(DRY RUN)' if args.dry_run else '(LIVE)'}")
    print(f"    target: {TARGET_ROOT}")
    print(f"    log:    {args.log}")

    log_lines = []
    files_changed = 0
    total_replacements = 0
    files_scanned = 0

    for root, dirs, files in os.walk(TARGET_ROOT):
        # Prune skip dirs
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fn in files:
            fp = pathlib.Path(root) / fn
            if not should_rewrite(fp):
                continue
            files_scanned += 1
            n = rewrite_file(fp, args.dry_run, log_lines)
            if n > 0:
                files_changed += 1
                total_replacements += n

    summary = (
        f"\nSummary: scanned={files_scanned} files_changed={files_changed} "
        f"total_replacements={total_replacements}"
    )
    print(summary)
    log_lines.append(summary)
    pathlib.Path(args.log).write_text("\n".join(log_lines), encoding="utf-8")
    print(f"[+] log written: {args.log}")


if __name__ == "__main__":
    main()
