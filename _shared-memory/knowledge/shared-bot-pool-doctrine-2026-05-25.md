---
category: system
half_life_days: 365
created: 2026-05-25
author: RKOJ-ELENO :: 2026-05-25
---

# Shared Bot Pool Doctrine — 2026-05-25

> Operator hard-canonical 2026-05-25 (verbatim):
> "have each bot work for all and as there is more demand per that bot at that
> time to allow for efficient use. use the fucking jcode log system. we have
> the bloody code"

## Problem

Before this doctrine every terminal session / spawned agent opened its own
connection to Ollama and had its own idea of which bots existed. This caused:
- Redundant context loading per session
- No visibility into cross-session demand
- No shared audit trail

## Design: shared daemon vs per-terminal spawn

| Approach | Old | New |
|---|---|---|
| Process per session | one Ollama call per agent | shared pool daemon |
| Port | none (CLI tool only) | 17340 (hardcoded, always same) |
| Demand tracking | none | per-bot + per-caller_slug counter |
| Audit log | `gpu-bot-fleet-log.jsonl` (flat) | `bot-pool-session.jsonl` (jcode JSONL) |
| Scale signal | none | log `scale_up` event when >3 in-flight |
| Fallback | none | direct Ollama call if daemon unreachable |

## Files

| File | Role |
|---|---|
| `automations/sinister_bot_pool.py` | daemon (`--start` / `--stop` / `--status` / `--install-schtask`) |
| `automations/bot_pool_client.py` | thin client library used by every agent |
| `_shared-memory/bot-pool-session.jsonl` | jcode-format JSONL audit log |

## jcode JSONL Log Schema

Derived from `jcode-0.12.4/crates/jcode-import-core/src/lib.rs` (`ClaudeCodeEntry`,
camelCase). Every line is a valid JSON object:

```json
{
  "type": "user|assistant|tool_use",
  "uuid": "<hex>",
  "parentUuid": "<hex or null>",
  "sessionId": "bot-pool-<hex12>",
  "timestamp": "2026-05-25T06:30:00Z",
  "isSidechain": false,
  "content": { ... event payload ... }
}
```

- `type=user` — incoming request
- `type=assistant` — bot response
- `type=tool_use` — system events (daemon start/stop, scale-up signals)

## Bot Types

| Bot | Role | Default model |
|---|---|---|
| librarian | RAG / code search | qwen2.5-coder:7b |
| triage | classify / route | qwen2.5-coder:7b |
| researcher | summarise / digest | qwen2.5-coder:7b |

## Scale-Up Behaviour

When `in_flight > 3` for any bot the daemon logs a `scale_up` event to
`bot-pool-session.jsonl`. Ollama itself handles GPU concurrency; the log entry
is the hook for future multi-GPU expansion (e.g. a second Ollama worker on a
second port).

## Schtask

`python automations/sinister_bot_pool.py --install-schtask` registers
`SinisterBotPool` at ONLOGON, user-level, 30-second delay. No elevation needed.

## Pass Criteria

- [ ] `GET http://127.0.0.1:17340/health` returns `{"healthy": true, ...}` when Ollama is up
- [ ] `POST /query {bot:"librarian", query:"hello", caller_slug:"test"}` returns `response` field
- [ ] `_shared-memory/bot-pool-session.jsonl` grows with one `user` + one `assistant` line per query

## Composes With

- `automations/gpu_bot_fleet.py` — Ollama detection + model catalogue
- `_shared-memory/knowledge/no-bat-no-ps1-do-it-for-me-doctrine-2026-05-25.md`
- `_shared-memory/knowledge/automate-everything-no-operator-admin-2026-05-25.md`
- `_shared-memory/knowledge/we-have-the-source-read-it-doctrine-2026-05-25.md`
