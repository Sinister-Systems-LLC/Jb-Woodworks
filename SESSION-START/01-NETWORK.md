# 01-NETWORK — 19-MCP-server discovery + shortcuts

After `Sinister-Bots-Activation.bat` ran + Claude Code restarted, you have 19
MCP servers registered. Call `sinister-bus.list_network` for a live inventory.

## The fleet (13 Sinister Bots)

| Bot | Tier | Cost | Default use |
|---|---|---|---|
| sentinel | 1 | $0 | date alarms (Yurikey, deadlines) |
| translator | 1 | $0 | MCP-tool catalog search |
| librarian | 2 | $0 | RAG over 8,500+ .md archive |
| watcher | 1 | $0 | source-drift detection |
| auditor | 1 | $0 | secrets + dedup + freshness |
| sinister-bus | 1 | $0 | orchestrator + runlog + codec + vault + garden |
| triage | 2 | $0 | file classifier |
| scribe | 3 | ~$0.02 | daily-digest writer |
| curator | 3 | ~$0.05 | code-library scout |
| custodian | 1 | $0 | active backup to `D:\_backups\` |
| stealth-browser | 1 | $0 | undetected Chromium (nodriver) |
| researcher | 2 | $0 | scrape -> Ollama summarize chain |
| vault | 1 | $0 | collaborative storage — repos / sync / snapshots / accounts (ready to register; run `install-fleet.ps1`) |

## Base MCP servers (operator's pre-existing)

eve (51), letstext-admin (44), letstext (27), sinister-panel (13), sinister-apk (12), sinister-snap (12), sinister-tiktok (12). Total: 171 tools.

## Bot-callable shortcuts (no operator-bat-click needed)

`sinister-bus.run_script(name)` with whitelist:

- `check-hetzner-state` — service probes + git-ahead
- `verify-backups` — Custodian health
- `memory-garden` — per-bot aliveness snapshot
- `aggregate-gotchas` — rebuild SANDBOX-GOTCHAS.md
- `prepare-for-migration-dryrun` — preview LLC migration

Returns `{ok, exit_code, stdout_tail, manifest_path}`. Audit log at `runtime-state/script-runner-log.jsonl`.

For the structured manifest after a `run_script` call: `bus.runlog_latest(name)`.

## Discovery

- `sinister-bus.list_network` — 19 servers + kinds + tool counts
- `sinister-bus.find <query>` — substring match across names + kinds
- `translator.find_tool <query>` — search 268+ tool names

## Aliveness

- `sinister-bus.memory_garden` — per-bot facts/calls/embeddings table
- `sinister-bus.pending_actions` — aggregated operator next-actions from all runlogs
- `sinister-bus.codec_status` — codec dictionary stats
- `sinister-bus.vault_status` — at-rest vault availability

## Operator-only (NOT bot-callable; sandbox blocks or destructive)

- `install-task.ps1` — register SinisterCustodian scheduled task
- `Deploy-Hetzner.bat` — push to production
- `migrate-projects.ps1` (non-dryrun) — creates Windows junctions
- `secret-scrub.ps1` — long-running source-tree scan
- ANTHROPIC_API_KEY / SINISTER_VAULT_PASSPHRASE env vars
- LICENSE selection
- git push to remote
