---
name: d-drive-audit
description: Walk D:\ root + identify off-canonical entries
allowed-tools: [bash, glob_search, read_file]
---
# Active Skill: d-drive-audit

Walk the `D:\` root and identify anything that's not in the operator's
canonical layout. Produce a markdown report so the operator can decide what
to move, archive, or delete.

## Canonical layout (allowed top-level entries)

The operator's canonical `D:\` layout contains exactly these directories:

- `Personal` — operator-private files (do NOT enumerate contents)
- `Sinister Sanctum` — the workstation (this repo)
- `Backups` — snapshots + archives
- `LetsText` — LetsText project root
- `Research` — research notes + scratch

Anything else at the root is OFF-CANONICAL and should be reported.

## Steps

1. **Enumerate `D:\`**:
   ```bash
   ls -la /d/
   ```

2. **Identify off-canonical entries**. For each top-level dir/file that is
   NOT in the canonical list above (also skip standard Windows artifacts:
   `$RECYCLE.BIN`, `System Volume Information`, `pagefile.sys`), capture:
   - Name
   - Type (directory / file)
   - Size (use `du -sh` for dirs, `ls -lh` for files)
   - Last-modified date

3. **Cross-check against active projects**. Some off-canonical entries may
   be legitimate work-in-progress. Read
   `D:/Sinister Sanctum/_shared-memory/WORKSTATION.md` for any references
   to non-canonical paths. Flag those as "active WIP" instead of "off-canonical".

4. **Check for sinister-vault**. The path `D:\sinister-vault\` is the 1 TB
   collaborative store and is EXPECTED but technically off-canonical. Flag
   as "expected: vault".

## Output format

Single markdown table with columns: `Name | Type | Size | Modified | Status`.
Status values: `off-canonical`, `active WIP`, `expected: vault`, `system`.

Below the table, add a one-line summary:
> `<N>` off-canonical entries totaling `<size>`. Recommend operator review.

## Hard rules

- READ-ONLY. Never delete, move, or modify anything on `D:\`.
- Never enumerate inside `D:\Personal\` (operator privacy).
- If `D:\` enumeration fails (permissions / drive offline), report the
  error and stop — do not guess.
