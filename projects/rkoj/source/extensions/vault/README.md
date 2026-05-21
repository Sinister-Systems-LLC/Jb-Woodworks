# RKOJ extension :: vault

> Author: RKOJ-ELENO :: 2026-05-21

Bridges the RKOJ PyQt6 shell to the **sinister-vault** 1 TB collaborative store running at `http://127.0.0.1:5078`.

## What it adds

| Surface | Effect |
|---|---|
| Sidebar `OPERATIONS` section | New nav row "Vault" with glyph `⛀` |
| KPI strip | New tile "VAULT USED" showing live MB usage (30 s refresh) |
| Workstation tab | Action card "Open Vault :5078" — launches dashboard in default browser |
| Agent pane slash | `/vault status` / `/vault list [path]` / `/vault search <q>` / `/vault push <file>` |

## Requirements

- `tools/sinister-vault/sinister_vault` must be importable (the extension auto-locates it by walking up from `extensions/vault/` to `tools/`).
- If the vault daemon is down or the package is missing, every hook degrades gracefully — KPI shows `--`, slash returns `vault tool not installed`.

## Slash usage

```text
/vault                    # equivalent to /vault status
/vault status             # daemon up/down + current usage + URL
/vault list               # list root entries
/vault list /projects     # list a sub-path
/vault search ssh keys    # full-text search
/vault push C:\path.txt   # upload a local file
```

## Self-contained

Drop this directory into any other PyQt6 host that implements the same three hook signatures (`hook_kpi`, `hook_workstation_action`, `hook_slash`) and it works without modification. No imports from `sinister_rkoj_qt.*`.
