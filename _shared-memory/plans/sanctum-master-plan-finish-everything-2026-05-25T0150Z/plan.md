# Sanctum master plan -- finish everything (operator hard-canonical 2026-05-25 ~01:50Z)

**Author:** RKOJ-ELENO :: 2026-05-25
**Lane:** sanctum (master orchestrator)
**Strategy:** maximum parallelism via 5 active sub-agents; consolidate on each notification.

## Operator stack this session (decoded)

1. Real-usage progress bars (no fake cap) -- SHIPPED
2. Sinister Sleight P0 -- SHIPPED
3. OAuth pivot from API keys -- SHIPPED
4. Auto-detect 429 + auto-rotate + health poller -- SHIPPED
5. Claude Login wizard with isolated sandbox -- SHIPPED
6. EVE.exe Accounts page + multi-action menu -- SHIPPED
7. Token analytics in Accounts -- SHIPPED
8. Sinister Overseer (scaffold + contradiction + analyzer compile + expand) -- SHIPPED
9. Kill Fleet -> Agents page rename -- SHIPPED
10. Leo auto-setup + Setup Wizard agent -- SHIPPED (extension in flight)
11. Single-repo push policy + Sinister Panel consolidation -- SHIPPED
12. Sinister LINK cross-machine system -- SHIPPED
13. Frequent-detailed-commits doctrine -- SHIPPED
14. Final EVE.exe rebuild after all eve.py edits -- IN FLIGHT (Helper Alpha)
15. GitHub push to Sinister-Sanctum -- IN FLIGHT (Helper Beta)
16. Leo handoff readiness verify -- IN FLIGHT (Helper Gamma)
17. Overseer first-fire audit on Sinister Term -- IN FLIGHT (sub-agent)
18. Leo MCP + Docker + bots + autonomy extension -- IN FLIGHT (sub-agent)
19. Coordinate with Sinister Sessions + Sinister Memory (no double work) -- SHIPPED (broadcast)
20. Open one ready-to-go resume-point -- SHIPPED

## 5 sub-agents in flight (parallel)

| # | Slug / agentId | Owns | Releases mesh-lock when... |
|---|---|---|---|
| 1 | aa159bed1c (Leo MCP+Docker) | install-leo-bots.ps1, install-leo-scheduled-tasks.ps1, templates/leo-mcp-config.json, expanded eve-first-run-check + wizard | shipped + smoke PASS |
| 2 | aa0992c81 (Overseer audit Sinister Term) | overseer-audit-sinister-term-2026-05-25.md + applied TRIVIAL/LOW fixes + MEDIUM+ queue rows | audit verdict + lessons brain entry |
| 3 | aa16b34142 (Helper Alpha) | EVE.exe FINAL rebuild + 24-check smoke matrix | matrix logged + PASS/FAIL surfaced |
| 4 | a92a3d55bf (Helper Beta) | batched stage+commit+push to origin/agent/sinister-os-mobile/p0-spec-2026-05-24 + verify remote | per-batch commit pushed + remote HEAD == local HEAD |
| 5 | ad2481217a (Helper Gamma) | leo-handoff-readiness verdict (READY / CAVEATS / NOT-READY) | verdict file written + OPERATOR-ACTION-QUEUE row + fleet-update HIGH push |

## Coordination rules (binding for all 5)

1. **Mesh-coord lock BEFORE editing any shared file** (`eve.py`, `claude-accounts.json`, `projects.json`, `CLAUDE.md`, `_INDEX.md`). Helper Alpha is the FINAL eve.py edit (rebuild only -- no functional changes).
2. **Frequent-detailed-commits doctrine** -- per-deliverable commit with Shipped/Smoke/Refs sections (per `_shared-memory/knowledge/frequent-detailed-commits-per-agent-2026-05-25.md`).
3. **Cross-agent inbox for handoffs** -- Helper Gamma drops to Helper Beta if pending-file diff is non-empty.
4. **No duplicate work with Sinister Sessions / Sinister Memory** -- per the coord broadcast at `_shared-memory/cross-agent/2026-05-25T0030Z-sanctum-to-sessions-memory-coord-broadcast.md`.

## My (master Sanctum) remaining work

1. Wait for sub-agent notifications (background watcher armed).
2. On each notification: verify the ship + mark task complete + update PROGRESS.
3. After ALL 5 land: final consolidated report to operator with:
   - PASS/FAIL summary per helper
   - GitHub branch URL + commit SHAs
   - Leo handoff verdict
   - Open operator-action items (close+reopen EVE.exe, generate first LINK invite, run install-* scripts once, etc.)
4. Push final fleet-update HIGH with "ALL SESSION SHIPS CONSOLIDATED" summary.
5. Update resume-point with final state.

## Operator-action items expected at session end (preview)

(Will be confirmed by helpers)

- [ ] Close + reopen any running EVE.exe windows to load the new bundle (LINK header + Agents page + Token analytics + Real-usage bars + Claude Login menu)
- [ ] Run `powershell -File automations/install-sinister-link-poller.ps1` once on this machine
- [ ] Run `powershell -File automations/install-oauth-health-poller.ps1` once on this machine
- [ ] Generate first LINK invite for Leo: EVE.exe Accounts L key -> Pair -> send code OOB
- [ ] Decision: 5 push-policy carve-out approvals (sinister-panel/.git, sinister-chatbot/.git, sinister-snap-emu/.git, sinister-tiktok-emu/.git)
- [ ] Decision: 3 Sleight P1 (yfinance vs Polygon, Alpaca paper account, kill-switch ack)
- [ ] Decision: 3 Overseer attach approvals (eve-compliance / chatbot / sleight from "prepared" to "active")
- [ ] Send Leo: repo URL + "double-click EVE.exe" instruction (Gamma will confirm readiness)

## Exit criterion

ALL 5 sub-agents complete + all 9 TaskList items completed/closed + final fleet-update pushed + operator briefed.
