# Sentinel agent

**Role:** Date-based alarms. Yurikey expiry, operator-action deadlines, recurring reminders.

**Tier:** 1 (pure Python). Zero LLM cost.

## Tools

| Tool | Args | Returns |
|---|---|---|
| `sentinel.list_alarms` | `include_past: bool=False` | `[{id, name, due, days_until, severity, message, tags, is_urgent, is_critical}]` |
| `sentinel.check_urgent` | `window_days: int=7` | alarms due within N days |
| `sentinel.add` | `name, due_iso, severity, message, tags` | `{ok, id}` |
| `sentinel.remove` | `alarm_id` | `{ok}` |
| `sentinel.snooze` | `alarm_id, until_iso` | `{ok}` |
| `sentinel.health` | (none) | `{ok, alarm_count, next_due}` |

## State

- `alarms.json` — alarm storage. Atomic writes (temp + rename).
- Auto-seeded on first run with operator-canonical alarms:
  - `yurikey51-root-expiry` (2026-05-24, critical)
  - `phone-pi-reauth` (2026-05-19, high)
  - 1-week reminder

## Run standalone

```powershell
cd 'D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\agents\sentinel'
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python server.py
```

## Register with Claude Code

Add to `~/.claude/.mcp.json`:

```json
"sentinel": {
  "command": "python",
  "args": ["server.py"],
  "cwd": "D:\\Sinister\\Sinister Skills\\12_LLM_ORCHESTRATION\\agents\\sentinel"
}
```

Restart Claude Code. Tools appear as `sentinel.list_alarms()`, etc.

## Health check

```powershell
# After registration, in operator's Claude session:
# Call sentinel.health()
```

## Integrations

- **Scribe** (Phase 8e): calls `sentinel.check_urgent()` for daily-digest urgent section
- **sinister-bus** (Phase 8g): routes operator's "what's expiring?" queries here
- **Eve federation** (optional): if `EVE_NOTIFY_TELEGRAM_ENABLED=true`, Sentinel can call `eve.notify.telegram` for critical alarms

## Crash safety

- All writes atomic (temp + rename)
- `alarms.json` corruption → backed up + restored from defaults
- Append-only `runtime-state/token-usage.jsonl` for call tracking
