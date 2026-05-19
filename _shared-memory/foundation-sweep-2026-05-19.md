# Foundation sweep — 2026-05-19

> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

Read-only audit of "all files have everything they need" per the operator's working directive. One run; check whether every Sanctum-side path referenced by config/docs resolves on disk.

## Project-level CLAUDE.md / SESSION-START.md presence (from `projects.json`)

| Project | claude_md | session_start | root |
|---|---|---|---|
| Sanctum | ✓ (created this sweep) | ✓ | ✓ |
| Snap EMU | ✓ | ✓ | ✓ |
| TikTok EMU | ✓ | ✓ | ✓ |
| Panel | ✓ | (blank) | ✓ |
| Kernel APK | ✗ MISSING | (blank) | ✓ |
| Sinister Bumble EMU | ✗ MISSING | (blank) | ✓ |

Outcomes:
- **Sanctum root CLAUDE.md** — created this session at `D:\Sinister Sanctum\CLAUDE.md` (master's lane; was the only missing file owned by master).
- **Kernel APK + Bumble EMU CLAUDE.md** — paths point at `projects/<slug>/source/CLAUDE.md`, which is product-repo source under junction. Per lane discipline, master does NOT create these — the per-project agent owns them. Flag to operator: if Kernel APK / Bumble agents are spawned without a CLAUDE.md at their root, they fall back to launcher cold-start phrase + SESSION-START walk.
- **Blank session_start fields** — Panel / Kernel APK / Bumble have no SESSION-START.md set in `projects.json`. Not a defect per se (launcher gracefully skips notepad if blank), but the cold-start protocol for those project agents lands purely on the master's preamble. Worth backfilling when those agents next ship.

## Runtime infrastructure (from the 11:17 + 12:55 runtime audits, cross-checked this session)

| System | State | Notes |
|---|---|---|
| MCP servers in `~/.claude/.mcp.json` | 19 of 20 expected | Vault MCP missing. Fix doc: `tools/sinister-vault/INSTALL-MCP.md` (shipped this session). |
| SinisterCustodian scheduled task | Ready | Not blocking. |
| SinisterSanctumAutoPush task | NOT registered | Verifier shipped: `automations/verify-auto-push.ps1` (live-runs FAIL on this gap). Operator-clicked reinstall needed. |
| RKOJ auto-start task | NOT registered | Operator-clicked: `install-console-task.ps1`. |
| SinisterVault auto-start task | NOT registered | Operator-clicked: `tools/sinister-vault/wire-everything.ps1`. |
| RKOJ on :5077 | source-mode only (no EXE listener) | Source `desktop_app.py` runs; EXE binary present at `dist/RKOJ/RKOJ.exe` (8.6 MB) but not launched. |
| Vault daemon on :5078 | live (PID 49000, uptime > 100 min) | Quota: 4.49 KB / 1 TB. |
| Gitea on :3000 | offline | Docker stack not running. Bring up via `tools/sanctum-git/Sanctum-Git-Start.bat`. |
| Today's hub :7099, header :7088 | live | From earlier 2026-05-19 sprint; both python http.server processes. |
| ANTHROPIC_API_KEY | unset | Blocks Scribe/Curator/Chatbot. Set per `docs/ENV-VARIABLES.md`. |
| OPENAI_API_KEY | set | Codex peer-review healthy; 5 reviews in log. |
| SINISTER_VAULT_PASSPHRASE | unset | At-rest encryption disabled until set. |
| LEO_ANTHROPIC_API_KEY | unset | Only matters when leo's account is active. |
| `agent-prefs.json` schema split | 2 files, 2 schemas | `automations/session-templates/agent-prefs.json` (project-key) + `_shared-memory/agent-prefs.json` (display-name). Resolved by launcher v8 (Phase G — deferred). |

## Catalog → reality cross-check (this session)

| Catalog | Rows | Resolved | Broken |
|---|---|---|---|
| `tools/_INDEX.md` | 11 | 11 ✓ | 0 |
| `skills/_INDEX.md` | (now split: 1 folder + 10 code-library) | 11 ✓ | 0 (reshape this session) |
| `bots/` agents | 13 (12 documented + vault) | 12 reachable, 1 (vault) unwired | 1 — vault MCP entry missing from `.mcp.json` |
| `inventions/` | 8 | 8 ✓ | 0 |
| `_shared-memory/knowledge/_INDEX.md` | 30 (was 29 + ruflo-mcp added this session) | 30 ✓ | 0 |
| `_shared-memory/external-imports/CANDIDATES.md` | 7 (NEW catalog this session) | 7 ✓ | 0 |
| `_shared-memory/case-studies/` | 5 | 5 ✓ | 0 |
| `_shared-memory/codex-reviews/` | 5 | 5 ✓ | 0 |
| `_shared-memory/PROGRESS/` | 6 agent logs | 6 ✓ — all logged within 24h | 0 |
| `_shared-memory/heartbeats/` | 5 (3 liveness JSON + 2 build-stamps) | 5 ✓ | 0 |

## Files shipped this session ("foundation sweep" deliverable)

| Path | Purpose |
|---|---|
| `CLAUDE.md` | Sanctum-root cold-start pointer (was missing) |
| `_shared-memory/external-imports/README.md` | inflow-loop spec |
| `_shared-memory/external-imports/CANDIDATES.md` | master list of external imports |
| `_shared-memory/external-imports/.gitkeep` | git scaffold |
| `_shared-memory/knowledge/ruflo-mcp-integration.md` | brain entry for Ruflo (status: workaround) |
| `_shared-memory/foundation-sweep-2026-05-19.md` | this file |
| `tools/sinister-vault/INSTALL-MCP.md` | operator-click guide for wiring Vault MCP into `.mcp.json` |
| `docs/ENV-VARIABLES.md` | every env var Sanctum reads + the exact set command |
| `automations/verify-auto-push.ps1` | read-only probe of SinisterSanctumAutoPush task state |
| `skills/_INDEX.md` | reshaped — split folder-skills vs code-libraries; added Source + Imported columns |
| `_shared-memory/knowledge/_INDEX.md` | row added for ruflo-mcp-integration |

## What still needs operator clicks

Mirrored from `_shared-memory/OPERATOR-ACTION-QUEUE.md`. None of these can be done by master agents (lane discipline).

1. **Vault MCP**: run `tools/sinister-vault/wire-everything.ps1`, merge staged entry into `~/.claude/.mcp.json`, restart Claude Code.
2. **Auto-push task**: re-register `SinisterSanctumAutoPush` (verify with `automations/verify-auto-push.ps1`).
3. **RKOJ + Vault auto-start tasks**: run respective install-task.ps1 scripts.
4. **Ruflo MCP** (after Phase 0 verification): `claude mcp add ruflo -- npx ruflo@latest mcp start` + restart.
5. **ANTHROPIC_API_KEY, SINISTER_VAULT_PASSPHRASE** env vars per `docs/ENV-VARIABLES.md`.
6. **LICENSE pick** from `LICENSE-CANDIDATES.md` (currently placeholder; private repo gives breathing room).
7. **Restart Claude Code** so any newly-registered MCP servers load.

## Recommended order

1. Restart Claude Code (gives sinister-bus + the 12 bots actual MCP tool access this session — biggest single unlock).
2. Run `automations/verify-auto-push.ps1` to confirm the task gap.
3. Run `tools/sinister-vault/wire-everything.ps1` to wire Vault MCP.
4. Set `ANTHROPIC_API_KEY` + `SINISTER_VAULT_PASSPHRASE` per `docs/ENV-VARIABLES.md`.
5. After Phase 0 verified, run `claude mcp add ruflo ...` and restart again — master then runs Phase C forks behind the operator-thumb gate.
6. Continue with the launcher v8 + foundation gaps + Anthropic Cookbook brain entries in subsequent sessions.

## See also

- Plan: `C:\Users\Zonia\.claude\plans\review-everything-and-create-cryptic-rose.md`
- Operator queue: `_shared-memory/OPERATOR-ACTION-QUEUE.md`
- Standing rules: `_shared-memory/DIRECTIVES.md`
- Brain: `_shared-memory/knowledge/_INDEX.md`
- External imports: `_shared-memory/external-imports/CANDIDATES.md`
