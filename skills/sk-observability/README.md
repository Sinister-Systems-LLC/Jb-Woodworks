# sk-observability — fleet tracing + metrics + structured logs (Ruflo fork)

> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19 :: forked from ruvnet/ruflo (MIT) ruflo-observability plugin
> **Status:** candidate (pending operator thumb per case-study `_shared-memory/case-studies/2026-05-19-sk-observability.md`)
> **Upstream snapshot:** `_shared-memory/external-imports/ruflo/plugins/ruflo-observability/`

## What it is

OpenTelemetry-compatible structured logging with correlation IDs, distributed tracing with parent-child span hierarchies, and metrics collection (counters / gauges / histograms). Correlates swarm agent activity with application-level telemetry; detects anomalies in latency / error rates / resource usage. Skill `observe-trace <task-id>` collects spans + builds a trace tree.

## Why Sanctum needs it

Sanctum has 13 MCP bots + RKOJ daemon + Vault daemon + 5+ parallel Claude sessions + auto-push + Custodian. **Today's observability surface is grep over `_logs/`.** When something drifts (a bot stops responding, the vault returns 507, the auto-push log writes failures every 30 min), there's no single pane to see it.

ruflo-observability closes that gap **without** the heavy SaaS lift of LangSmith / Phoenix:

- **Local-first** — runs as MCP plugin; no external API. Operator doesn't add another monthly bill.
- **Trace per agent task** — every Task / SendMessage / Monitor call from Claude Code becomes a span; correlation ID flows through the inbox so cross-agent calls link automatically.
- **Anomaly detection** — built-in detectors for latency / error / resource spikes mean fleet-monitor (currently just heartbeat freshness) gets a real diagnostic layer.
- **Pairs with Sanctum's existing patterns** — RKOJ's `/api/sse/changes` already emits SSE events; observability can subscribe and ingest as spans automatically.

## How Sanctum uses it (post operator-thumb)

1. RKOJ Console gains an "Observability" tab — flame graph of recent agent runs, top-N slowest tools, error rate by bot.
2. The existing `fleet-monitor` scheduled task augments from "is heartbeat fresh?" to "are span latencies trending up / are error counts spiking / are token usage anomalies emerging?"
3. Codex peer-review traces feed into observability so we can see the full review-chain latency + cost.
4. Brain entries gain optional `metric:` annotations (e.g. "average call duration ≤ 200 ms") that observability reads for SLO checks.

## Dependencies

- Ruflo MCP registered.
- OpenTelemetry collector (auto-spawned by ruflo).
- Local storage: span/metric data at `D:\sinister-vault\repos\sanctum-observability\` (Vault tier 1).

## License + attribution

- Upstream: MIT.
- Sanctum fork: MIT.
- Snapshot: `_shared-memory/external-imports/ruflo/plugins/ruflo-observability/`.

## See also

- `_shared-memory/case-studies/2026-05-19-sk-observability.md` — verdict file
- `automations/window-manager/server.py` — RKOJ surfaces that emit events ruflo-observability can ingest
- `bots/agents/_shared/runlog.py` — the existing sinister-runlog/v1 format; observability layer above
- `_shared-memory/heartbeats/` — current state-of-fleet surface; gets upgraded with anomaly detection
