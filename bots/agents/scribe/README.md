# Scribe agent

Tier 3 daily-digest writer. Reads peer-agent state (Sentinel alarms, Watcher queue,
Auditor findings, token-usage log) and renders `07_DASHBOARD/daily-digest.md`.

**Cost:** ~$0.02 per digest (Claude Haiku 4.5 with prompt caching on the system prompt).

## Tools

| Tool | Purpose |
|---|---|
| `scribe.generate_digest(preview=False)` | Render today's digest. Writes `07_DASHBOARD/daily-digest.md`. |
| `scribe.weekly_summary(preview=False)` | 7-day rollup to `07_DASHBOARD/weekly/<iso-week>.md`. |
| `scribe.list_inputs()` | Show the raw inputs Scribe would feed Haiku — zero token cost. |
| `scribe.health()` | API key + peer-agent state-file presence. |

## Setup

```powershell
# Set ANTHROPIC_API_KEY (user-level so all agents see it):
[Environment]::SetEnvironmentVariable('ANTHROPIC_API_KEY','sk-ant-...','User')
```

After restart Claude Code picks up the new env var.

## Output shape

The system prompt enforces these H2 sections in order:

```
# Daily digest - YYYY-MM-DD
## Urgent (operator action this week)
## What changed
## Audit findings
## Cost
## What to work on next
```

## Prompt caching

The system prompt is cached with `cache_control: ephemeral`. First call writes the
cache (~5k tokens at $0.001/1k), subsequent calls within 5 min read it (~$0.00008/1k).

Typical daily digest: ~800 output + ~300 user input + ~5k cached system =
**~$0.012-$0.025**.

## Safety

- Atomic write (`.tmp.<rand>` + os.replace) — power-out safe.
- Previous digest archived to `history/daily-digest-<utc-stamp>.md` before overwrite.
- System prompt forbids inventing items or emitting secrets verbatim.

## Environment

- `ANTHROPIC_API_KEY` — required.
- `SINISTER_HUB_ROOT` — defaults to `D:\Sinister\Sinister Skills`.
- `SCRIBE_MODEL` — defaults to `claude-haiku-4-5-20251001`.
