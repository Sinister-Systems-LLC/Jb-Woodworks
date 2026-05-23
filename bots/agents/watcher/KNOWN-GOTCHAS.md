# Watcher-specific gotchas

- **Only key files are scanned** (SESSION-START, CLAUDE.md, README, RESUME-HERE, AUTONOMY-LOG, SESSION-LOG, PROJECT-STATUS, WHAT-FAILED). Full source-tree drift is robocopy's job.
- **mtime alone is unreliable** -- sha256 always wins. Some editors update mtime without changing bytes.
- **Source-missing isn't an error** -- if a project's source path moved, you get a `source_missing` entry; operator decides whether to update `_manifest.json` or fix the path.
