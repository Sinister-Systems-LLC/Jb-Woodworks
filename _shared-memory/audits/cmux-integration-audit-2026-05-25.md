# Audit :: cmux integration mining for Sinister Term

> **Author:** RKOJ-ELENO :: 2026-05-25
> **Lane:** sinister-term
> **Operator trigger:** 2026-05-25T~12:32Z — *"review cmux and see what we can use that for i think it may give us some great code to start on and intergreate."*
> **Audit method:** WebFetch on manaflow-ai/cmux docs/*.md (no clone).

## What cmux is

`manaflow-ai/cmux` (https://github.com/manaflow-ai/cmux) — **GPL-3.0-or-later**, **81% Swift / 10% Python / 4% TS / 2% Go**, 19.3k stars. **Native macOS terminal app** (Ghostty-fork) for parallel AI coding agents. Cross-platform value for us lives in its **protocols, schemas, and Python/TS sidecars** — not the Swift UI.

> Caveat: Hummer98/cmux-team, ph3on1x/claude-cmux-skill, EtanHey/cmuxlayer are SKILLS that wrap cmux, not cmux itself.

## License verdict

**GPL-3.0-or-later → AGPL-3.0** is **one-way compatible** (AGPL absorbs GPL). Sinister Term is AGPL-3.0 (per CLAUDE.md). **Safe to vendor verbatim**, but every ported file MUST carry:

1. Original cmux copyright header retained
2. AGPL upgrade notice
3. `Author: RKOJ-ELENO :: <date>` line

**Do NOT vendor into any future MIT/Apache sibling project.** Prefer **clean-room re-implementation from the docs/*.md specs** (prose, not GPL'd code) where possible — keeps license options open.

## 5 features to mine (ranked by integration value)

| # | Feature | cmux source | Sinister Term dest | Status |
|---|---|---|---|---|
| 1 | **Event bus with resumable seq + jsonl persistence** (boot_id, after_seq, gap detection, 4096 ring, 16 MiB rotation, slow_consumer backpressure) | `docs/events.md` schema | NEW `term/event_bus.py` consumed by `ipc.py` + persisted to `_shared-memory/heartbeats/sinister-term-events.jsonl` | **STARTER — this audit ships it** |
| 2 | **Feed approval-card panel** (permission / ExitPlanMode / AskUserQuestion with 120s hook ceiling, workstream.jsonl, ring buffer 2000) | `docs/feed.md` + `FeedCoordinator` | NEW `term/feed_panel.py` rendering inside `glass_overlay.py` | queued |
| 3 | **Agent-hook session restore** (sessions.json per agent: session_id, cwd, pid, sanitized launch cmd → native resume on relaunch) | `docs/agent-hooks.md` + `~/.cmuxterm/<agent>-hook-sessions.json` | EXTEND `term/swarm.py` + NEW `term/agent_hooks.py` writing to `_shared-memory/heartbeats/<slug>-sessions.json` | queued |
| 4 | **CLI socket contract** (Unix-socket / `CMUX_SOCKET_PATH` env, HMAC challenge auth, password env, newline-delimited JSON, no-socket help contract) | `docs/cli-contract.md` + `CLI/CLISocketPathResolver.swift` | HARDEN existing `term/ipc.py` (port 5081 → add auth, no-socket help, env-overridable path) | queued |
| 5 | **OSC-based notification ingestion** (cmux scans terminal OSC sequences for "agent waiting" → blue ring + sidebar light) | `docs/notifications.md` + cmux notify wrapper | NEW `term/osc_scanner.py` feeding `name_pill.py` / `glass_overlay.py` ring state | queued |

## Architectural patterns worth copying

- **Out-of-process sidecar via JSON-RPC v2 over stdio** (`remote-daemon-spec.md`): release-pinned binary, SHA-256 manifest verify, `hello` handshake with capability negotiation. Directly applicable to a Sinister Term remote-mode for fleet agents on other workstations.
- **Event sourcing with monotonic seq + boot_id + gap=true semantics**: every state mutation = event; replay is the source of truth. Maps onto our existing `fleet-updates.jsonl` and would unify `crash_recovery.py` + `swarm.py` + `concise_log.py`.
- **Env-var precedence chain for IPC** (`CMUX_SOCKET_PATH` → deprecated alias → CLI flag) + **HMAC-SHA256 challenge** before forwarding commands — far stronger than our current port-5081 trust model.

## Recommended starter integration (shipped THIS session)

**`term/event_bus.py`** — clean-room from `docs/events.md`. Specifically:

- `Event{seq, boot_id, ts, name, category, payload}` dataclass
- `events.jsonl` append-only writer at `_shared-memory/heartbeats/sinister-term-events.jsonl` with 16 MiB rotation
- In-memory 4096-ring + 16 KiB frame cap
- `subscribe(after_seq, names=[...], categories=[...])` async generator with `gap: true` on overflow
- Wire `app.py` keystroke loop, `swarm.py` peer events, and `crash_recovery.safe_loop` exit/restart into it (deferred to next iter — substrate must land first)

**Why first:** zero UI surface (so no PH-test regressions), it is the substrate every other ported feature (Feed panel, agent-hook restore, OSC notifications) consumes, and the spec is fully written (no Swift reading required).

## Sources

- https://github.com/manaflow-ai/cmux (main)
- https://raw.githubusercontent.com/manaflow-ai/cmux/main/docs/events.md
- https://raw.githubusercontent.com/manaflow-ai/cmux/main/docs/feed.md
- https://raw.githubusercontent.com/manaflow-ai/cmux/main/docs/agent-hooks.md
- https://raw.githubusercontent.com/manaflow-ai/cmux/main/docs/cli-contract.md
- https://raw.githubusercontent.com/manaflow-ai/cmux/main/docs/notifications.md
- https://raw.githubusercontent.com/manaflow-ai/cmux/main/docs/remote-daemon-spec.md
- https://raw.githubusercontent.com/manaflow-ai/cmux/main/docs/agent-browser-port-spec.md

## Composes with

- `_shared-memory/knowledge/research-import-pipeline.md` — external repo intake doctrine
- `_shared-memory/knowledge/we-have-the-source-read-it-doctrine-2026-05-25.md` — read source directly (applied: WebFetch raw github not clone)
- `_shared-memory/knowledge/sinister-generator-fleet-wide-conservative-2026-05-23.md` — conservative external mining
- AGPL-3.0 license discipline (CLAUDE.md lane rules)
