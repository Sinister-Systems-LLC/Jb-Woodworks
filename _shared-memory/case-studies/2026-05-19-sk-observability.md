# Case study :: sk-observability (forked from ruvnet/ruflo)

> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19T13:30Z
> **Tags:** review, external, ruflo, sk-observability, tracing, candidate

## 1. What it is

`ruflo-observability` provides OpenTelemetry-compatible structured logging (correlation IDs, parent-child span hierarchies, counters/gauges/histograms metrics) for multi-agent fleets. Correlates swarm activity with application telemetry; detects anomalies in latency / error rates / resource usage. One agent (`observability-engineer`, sonnet model); one skill (`observe-trace <task-id>` builds a trace tree from spans). Composable with `ruflo-swarm` (which emits the spans) and `ruflo-agentdb` (which can store them for historical recall).

Sanctum fork at `skills/sk-observability/`; upstream at `_shared-memory/external-imports/ruflo/plugins/ruflo-observability/`.

## 2. Strengths

- **Local-first, no SaaS bill.** LangSmith + Phoenix + Helicone are great products but operator's stated stance is "no recurring bills if I can help it." OTel-compatible local collector keeps that promise.
- **Fills the visibility gap that today's `fleet-monitor` can't.** Heartbeats tell you a process is alive; spans tell you what it's doing + how slow + how often it errors. Existing audit at `_shared-memory/heartbeats/` is necessary but not sufficient.
- **Anomaly detection built-in.** Sanctum has no anomaly layer today; ruflo-observability ships one. Latency spikes, error rate climbs, token-usage anomalies all surface without operator-built alerting.
- **Correlates with existing patterns.** RKOJ's `/api/sse/changes` emits SSE events; observability can ingest as spans. The codex peer-review pipeline already logs to `_shared-memory/codex-reviews/`; spans add the timing dimension.
- **MIT, OTel-compatible** — can pivot to a SaaS observability provider later by pointing the OTel collector at it. No lock-in.

## 3. Weaknesses + risks

- **Storage cost.** Spans + metrics accumulate fast. A busy fleet day = 10K-100K spans. Without retention policy, `D:\sinister-vault\repos\sanctum-observability\` grows unbounded. Vault has a 1 TB quota so it'll hit warning before disaster, but it's a real risk.
- **Signal-to-noise without a dashboard.** Spans are raw data; humans need flame graphs / time-series charts. Ruflo doesn't ship a viewer; relies on external (e.g., Jaeger). RKOJ would need a new tab to surface this usefully.
- **OTel ecosystem complexity.** OTel-Collector, semantic conventions, exporters — there's a learning curve. Operator may not want to invest in OTel literacy until anomalies actually hurt.
- **Anomaly detection has false positives.** Without baselining on real Sanctum traffic, the detector will fire on every novel pattern in the first weeks.
- **Codex pipeline wrapping.** PII-sensitive content (auth-keys, Yurikey strings) could leak into spans if span attributes aren't sanitized. Needs paired aidefence integration.

## 4. Better-than-found proposal (~90 LOC outline)

1. **RKOJ Observability tab (~50 LOC)** — new `WINDOW_TOOLS_REGISTRY` entry + template + pane: flame-graph for last 100 agent runs, top-N slowest tools, error rate per bot. Reads spans from agentdb store (if sk-vector-memory also lands) or from a local sqlite cache.
2. **Span ingest from RKOJ SSE (~20 LOC)** — subscribes to `/api/sse/changes`, converts events into OTel spans + writes to local collector.
3. **PII-sanitizer hook (~10 LOC)** — wraps span-attribute writes through aidefence's PII detector (if sk-aidefence also lands); redacts sensitive fields before persist.
4. **Retention policy (~10 LOC scheduler entry)** — `_shared-memory/schedule.json` daily job deletes spans > 30 days old; older summaries roll up into per-day aggregates stored as brain entries.

Net: ~90 LOC, all in Sanctum's own surface (RKOJ + scheduler + brain). Upstream stays vendor; Sanctum-specific glue stays local.

## 5. Recommendation

**KEEP-WITH-CHANGES.** Single biggest unlock for the operator's "I can see the fleet" moment. Pairs strongly with the other forks: needs sk-swarm-coord (span source), benefits from sk-vector-memory (storage backend), is hardened by sk-aidefence (PII gate).

Sequence on thumbs-up:
1. Land the OTel collector + ingest pipe (smallest piece, validates the round-trip).
2. Build the RKOJ Observability tab (visual proof of value).
3. Wire the PII sanitizer once sk-aidefence is approved.
4. Set retention policy + schedule before storage blows out.

Codex peer-review: standard tier (~90 LOC, touches RKOJ which is the workbench, no auth boundary).

---

## Operator decision

(blank — operator drops 👍 / 👎 / free text)
