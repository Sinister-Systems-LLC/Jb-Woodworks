# pip-editable install can hide MCP cwd-emptiness (audit anti-trap)

> **Author:** RKOJ-ELENO :: 2026-05-23
> **Status:** doctrine, audit-pattern, validated
> **Empirical anchor:** Sanctum resume audit 2026-05-23T08:15Z — flagged 3 "broken MCP / install" rows in OPERATOR-ACTION-QUEUE.md that were actually false alarms.

## The trap

A prior audit pass (2026-05-23T03:05Z, captured in `mcp-junction-fix-pattern-2026-05-23.md`) flagged `sinister_apk_mcp` as "module folder at the junction target is EMPTY (no .py files). The package was either archived or the source got cleared. The MCP entry in .mcp.json is effectively dead until operator either restores the source OR removes the entry."

That conclusion was wrong. The MCP was live. The audit inspected only the `cwd` value in `~/.claude/.mcp.json` and the filesystem at that path. It missed the second resolution mechanism: **`python -m sinister_apk_mcp` does an `import sinister_apk_mcp` against `sys.path`**, and pip-editable installs add arbitrary on-disk locations to `sys.path` via `.pth` files in `site-packages`. The cwd can be the wrong/empty folder and the import still succeeds.

Same pattern surfaced twice more in the same queue:
- `sinister-term` flagged "resolves to D:\Sinister-Term-WT (worktree path)" → `pip show` confirmed canonical install at `D:\Sinister Sanctum\projects\sinister-term\source`. Audit had compared a worktree's egg-info to repo state without checking the live pip resolution.
- `sinister-review` flagged "harness blocked auto-install" → `pip show` confirmed editable install at canonical path. Auto-install had succeeded in a later iteration; the queue row was stale.

## The fix (audit procedure)

When auditing whether a Python-launched MCP server or tool is actually broken, **never** stop at the cwd / source-folder check. Always cross-reference pip:

```bash
pip show <package-name>        # confirms install + editable location
pip list | grep -i <slug>      # catches differently-named siblings
```

`pip show` reports `Editable project location:` for pip-editable installs — that's the resolution path Python actually uses, not the cwd in the MCP entry. If `pip show` returns the package, the import is live regardless of what the cwd points at. The empty cwd folder is then either: (a) cosmetic / archival residue (harmless), or (b) a legitimate "the launcher's relative-path file ops will fail" issue (separate problem, narrower fix).

## Reusable pattern

**audit-pip-before-declaring-mcp-dead** — for any "MCP X is broken because Y on disk" claim, run `pip show <module>` before believing it. If the module is editable-installed, the MCP launches even when the cwd points at nothing.

## Anti-patterns

- **Inspecting only `cwd` / filesystem at the MCP entry's path** — misses pip editable installs that resolve via sys.path.
- **Trusting prior audit conclusions in the operator queue without re-verifying** — install state changes between sessions; "broken" can flip to "fine" without a queue update.
- **Removing `.mcp.json` entries when the folder is empty** — the entry may still be working; the empty folder may be unrelated archival residue.
- **Re-running `pip install -e <path>` "just in case"** — if `pip show` already returns the package at the right location, the re-install is a noop that risks corrupting metadata.

## Composes with

- `mcp-junction-fix-pattern-2026-05-23.md` — the cwd-side fix doctrine. This entry is the import-side complement.
- `sanctioned-bypasses-doctrine-2026-05-21.md` — confirms `.mcp.json` is operator-gated; this entry reduces the need to touch it.
- `OPERATOR-ACTION-QUEUE.md` — three rows cleared 2026-05-23T08:20Z via this audit pattern.

## Empirical residue (from the Sanctum audit)

18 Sinister/EVE packages confirmed pip-editable-installed via `pip list | grep -i sinister`:

| Package | Editable location | Note |
|---|---|---|
| eve_mcp | `C:\Users\Zonia\Desktop\Sinister Library Of Alexandria\eve mcp\eve-server` | Pre-monorepo |
| sinister_apk_mcp | `C:\Users\Zonia\Desktop\Sinister-Snap-APK-\mcp-server` | Pre-monorepo (audit subject) |
| sinister_mcp | `C:\Users\Zonia\Desktop\Snap Signer\mcp-server` | Pre-monorepo |
| sinister_tiktok_mcp | `C:\Users\Zonia\Desktop\Sinister Tiktok EMU.API\mcp-server` | Pre-monorepo |
| sinister-{cli, diagnose, login, model, review, swarm, usage} | `D:\Sinister Sanctum\tools\...` | Canonical |
| sinister-{forge, mind, term} | `D:\Sinister Sanctum\projects\.../source` | Canonical |
| sinister-jcode-shim | `D:\Sinister Sanctum\tools\sinister-jcode-shim` | Canonical |
| forge-memory-bridge, memory-graph-render, nano-banana, sanctum-backup | `D:\Sinister Sanctum\tools\...` | Canonical |

Four Desktop-located editable installs are pre-monorepo residue — harmless but worth migrating to canonical locations on the next round of housekeeping (would also let the queue's "is the source backed up?" worry go away).
