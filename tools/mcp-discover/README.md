# mcp-discover

> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

Recurring discovery loop over the official MCP Registry (`registry.modelcontextprotocol.io`). Polls the public catalog, diffs vs the operator's registered servers in `~/.claude.json`, writes a candidate report to `_shared-memory/external-imports/mcp-candidates.md`.

**Pure-read.** This tool never edits `.claude.json`, never runs `claude mcp add`, never installs anything. Operator scans the report; if a candidate fits, operator runs the standard `claude mcp add <name> ...` flow after the case-study gate.

## Why this exists

Sanctum's plan ("work forever") needs a steady inflow of new capabilities. The MCP Registry has thousands of public servers; today Sanctum has 21 registered (12 Sinister bots + 7 externals + ruflo + vault). Without a discovery loop, the fleet plateaus at whatever the operator hand-discovered. With this tool running weekly, the operator gets a fresh list of new candidates without manual hunting.

## Run

```powershell
# Default: 100 entries, no filter
python "D:\Sinister Sanctum\tools\mcp-discover\discover.py"

# Cap + filter
python "D:\Sinister Sanctum\tools\mcp-discover\discover.py" --limit 50 --keyword github

# Custom output path
python "D:\Sinister Sanctum\tools\mcp-discover\discover.py" --out "D:\Sinister Sanctum\_shared-memory\mcp-this-week.md"
```

Or one-click: `C:\Users\Zonia\Desktop\Sanctum-MCP-Discover.bat`.

## Output

`_shared-memory/external-imports/mcp-candidates.md` (overwritten each run; git history keeps the timeline):

```markdown
# MCP Registry — candidate servers

Pulled 100 entries from https://registry.modelcontextprotocol.io/v0/servers (limit=100).

Already registered in ~/.claude.json: 21 server(s).

| Status | Short name | Full name | Description | Repo |
|---|---|---|---|---|
| candidate | playwright | ms-playwright/playwright-mcp | Browser automation ... | link |
| REGISTERED | ruflo | ruvnet/ruflo | Multi-agent ... | link |
| candidate | postgres | modelcontextprotocol/postgres | Postgres MCP server ... | link |
...
```

## Dependencies

- Python 3.10+ with `httpx` (already on system Python per Vault MCP wire-up).
- Network egress to `registry.modelcontextprotocol.io`.
- Read access to `~/.claude.json`.

## Schedule (weekly)

For a recurring discovery loop, register a weekly scheduled task:

```powershell
schtasks /Create /TN SanctumMCPDiscover `
  /SC WEEKLY /D MON /ST 09:00 `
  /TR "python \"D:\Sinister Sanctum\tools\mcp-discover\discover.py\"" `
  /F
```

Or add to `_shared-memory/schedule.json` (RKOJ scheduler — `script` kind, cron `0 9 * * 1`).

## API contract

- Endpoint probed: `GET /v0/servers` (verified 2026-05-19; returns `{servers: [{server: {name, description, ...}}], metadata: {nextCursor}}`).
- Paginates via `cursor` query param until `limit` hit or no `nextCursor`.
- 10-second timeout per request.
- Failure mode: log + exit 1; report not overwritten on registry failure.

## Lane discipline

This tool NEVER:
- Modifies `~/.claude.json`.
- Calls `claude mcp add` / `claude mcp remove`.
- Touches `_vault/`.
- Pushes git.
- Spawns subprocesses other than `httpx.Client` for the registry GETs.

## See also

- `_shared-memory/external-imports/CANDIDATES.md` — manually-curated master list (this script is the auto-generated complement)
- `_shared-memory/DIRECTIVES.md:7-19` — case-study workflow gate for adding new MCPs
- `_shared-memory/knowledge/mcp-registry-integration.md` — brain entry (planned; ship on first non-trivial discovery)
- `tools/sanctum-self-heal/` — companion drift detector (different cadence + scope)
