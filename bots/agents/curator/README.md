# Curator agent

Tier 3 code-library extraction scout. Walks recent source files across all projects
listed in `_manifest.json`, identifies helper functions appearing in 2+ projects,
asks Haiku to rank them, writes a proposal into `11_CODE_LIBRARY/_proposals/`.

**Cost:** ~$0.05 per scan (Haiku, prompt-cached system message).

## Tools

| Tool | What |
|---|---|
| `curator.scan_candidates(top_k=10, recent_days=30)` | Walk sources, return ranked recommendations |
| `curator.assess_file(path)` | Pure-Python file-local definition lister (no LLM) |
| `curator.write_proposal(out_path=None)` | Render `11_CODE_LIBRARY/_proposals/curator-<stamp>.md` |
| `curator.list_origins()` | Source roots being scanned |
| `curator.health()` | API key + source-root count |

## How it works

1. **Deterministic walk** — regex-extracts top-level `def`/`function`/`fun` names
   from `.py / .ts / .kt / .java / .sh / .ps1 / .bat / .rs / .go` files modified in
   the last 30 days.
2. **Cross-project filter** — keeps only names that appear in 2+ source roots.
3. **Boilerplate skip** — discards `main` / `test` / `setup` / `__init__` / 1-3 letter names / leading-underscore privates.
4. **Haiku rank** — sends top 30 to `claude-haiku-4-5` with a strict system prompt that requires JSON output, domain bucket suggestion, and `by-language/<lang>/<file>.<ext>` target path.
5. **Proposal markdown** — written to `11_CODE_LIBRARY/_proposals/curator-<utc>.md`.

Operator review step is intentional — Curator never auto-copies code into the library.

## Setup

```powershell
[Environment]::SetEnvironmentVariable('ANTHROPIC_API_KEY','sk-ant-...','User')
```

Restart Claude Code so the agent inherits the env var.

## Environment

- `ANTHROPIC_API_KEY` — required.
- `SINISTER_HUB_ROOT` — defaults to `D:\Sinister\Sinister Skills`.
- `CURATOR_MODEL` — defaults to `claude-haiku-4-5-20251001`.
