<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
# Sinister OS :: Sanctum integration manifest

**Status:** living document. Updated 2026-05-24 by sanctum lane.
**Operator verbatim 2026-05-24T20:38Z:** *"link all of this into the sinister os im making as we will be switching over operations to there soon"*

## 2026-05-24T22:10Z — Mobile consolidation

**Operator verbatim 2026-05-24T22:10Z:** *"combine project sinister os and sinister os mobile."*

The Pixel 6a custom-Android lane (formerly `projects/sinister-os-mobile/`) was consolidated into this project as a sub-lane at `projects/sinister-os/mobile/`. Sinister OS is now a single project with two metal targets:

- **PC sub-lane** — Linux desktop replacement (this directory, `source/`, `docs/`, `plans/`, `research/`, `memory/`, `build/`). Branch `agent/sinister-os/*`.
- **Mobile sub-lane** — Pixel 6a custom Android (`mobile/`, with its own `CLAUDE.md` / `SESSION-START.md` / `plans/` / `research/` / `sandbox/` / `source/`). Branch `agent/sinister-os-mobile/*` (preserved post-consolidation).

Shared by both sub-lanes (single slug `sinister-os`): heartbeat, PROGRESS log, inbox, resume-points, picker entry. The mobile sub-lane retains its own CLAUDE.md (Pixel 6a hard rules, emulator-first discipline, GApps / AVB / signed-boot operator-decisions) — that file inherits from this one as well as from Sanctum master CLAUDE.md.

Composes with the migration table below: when porting to Sinister OS the PC, the mobile sub-lane ports separately via per-row mobile addendum once P3 (cuttlefish) lands — see `mobile/plans/master-plan-2026-05-24.md` § 12.


**Purpose.** When fleet operations migrate from Windows-on-D: (current host) to Sinister OS (Linux PC replacement), every Sanctum primitive listed below ports over. Each row identifies: the Sanctum source, the Sinister OS landing path, the porting work required, and a smoke-test that proves the port works.

## Migration scope (sanctum primitives → sinister-os)

| # | Primitive (Sanctum source) | Sinister OS landing path | Port work | Smoke test |
|---|---|---|---|---|
| 1 | **Overseer agent** (`automations/overseer-agent.ps1`) | `source/system/sanctum-overseer/` (systemd service or daemon) | Rewrite PS1 → bash or Python. Replace `Get-Process claude` with `pgrep claude`. Replace Windows-style paths with `$XDG_DATA_HOME/sanctum/heartbeats`. | `sanctum-overseer scan` returns clean table; `sanctum-overseer reap` drains stale leases. |
| 2 | **Launcher** (`automations/start-sinister-session.ps1`) | `source/system/sanctum-launcher/` (bash + tmux or wezterm spawn) | Rewrite PS1 → bash; replace mintty with native terminal; honor SINISTER_* env vars unchanged. | `sanctum-launch sanctum` opens a new pane with the cold-start phrase. |
| 3 | **EVE.exe picker** (`automations/eve-launcher/eve.py`) | `source/system/sanctum-picker/` (already Python — minimal port) | Replace Win32 console calls with curses/textual. PyInstaller → native binary or pyz. | `sanctum-pick` shows picker with correct mcp:N bots:N counts. |
| 4 | **Claude-account rotation** (`automations/claude-accounts.ps1`) | `source/system/sanctum-accounts/` | PS1 → Python (auth.py). Same JSON schema (`claude-accounts.json`). Add the open round-robin v2 fields when operator confirms telemetry source (Q pending). | `sanctum-accounts status` matches Sanctum behavior; rotation works across ≥2 enabled slots. |
| 5 | **Fleet-update channel** (`automations/fleet-update.ps1` + `_shared-memory/fleet-updates.jsonl`) | `source/system/sanctum-bus/` | Same JSONL append pattern; cross-machine via vault Tailscale sync. Per-agent slug filtering preserved. | `sanctum-bus list --slug sanctum` shows recent updates. |
| 6 | **Window-position monitor** (`automations/window-position-monitor.ps1`) | `source/system/sanctum-wm-monitor/` (Linux wm-specific) | Win32 GetWindowRect → X11 `xdotool` or Wayland `swaymsg -t get_tree`. Per-WM driver pattern. JSON schema unchanged (`_shared-memory/window-positions/<key>.json`). | After close+reopen, mintty/foot/kitty lands at saved position. |
| 7 | **Fleet-autostart at logon** (`automations/fleet-autostart.ps1` + `automations/register-fleet-autostart-task.ps1` + Startup-folder .bat) | `etc/systemd/user/sanctum-fleet-autostart.service` (systemd user unit) | schtasks → systemd user service with `WantedBy=default.target`. Steps inside (Docker, vault, MCPs, auto-push) translate directly. | `systemctl --user start sanctum-fleet-autostart; systemctl --user status` shows green. |
| 8 | **Auto-push daemon** (`automations/sanctum-auto-push.ps1`) | `source/system/sanctum-auto-push/` (cron or systemd timer 30min) | bash equivalent of the 30-min push loop; existing per-branch logic preserved. | Edit on main → 30 min later, GitHub commit appears. |
| 9 | **Detect-similar-agents** (`automations/detect-similar-agents.ps1`) | `source/system/sanctum-peers/` | Same heartbeat scan logic in bash/Python. Output JSON unchanged so the launcher can inject without code change. | `sanctum-peers --project sanctum --as-json` returns valid JSON of active peers. |
| 10 | **Shared memory** (`_shared-memory/`) | `$XDG_DATA_HOME/sanctum/_shared-memory/` (symlinked into `~/sanctum-data` for vault-sync) | No code change — directory move only. Vault daemon syncs across machines as today. | `ls $XDG_DATA_HOME/sanctum/_shared-memory/heartbeats/` shows current agent heartbeats. |
| 11 | **Brain** (`_shared-memory/knowledge/`) | Same as #10 — moves with shared-memory | None | `grep -r safe-quality-loops $XDG_DATA_HOME/sanctum/_shared-memory/knowledge/` returns the doctrine. |
| 12 | **Quality monotonic loop** (`automations/quality-monotonic-loop.ps1`) | `source/system/sanctum-quality/` | PS1 → Python; score-tracking JSONL schema unchanged. | `sanctum-quality run --iters 3` produces a quality-loop-log entry. |
| 13 | **Forever-improve** (`automations/forever-improve.ps1`) | `source/system/sanctum-forever-improve/` | PS1 → Python; uses Anthropic SDK directly. | `sanctum-forever-improve review --target <path>` produces a finding row. |
| 14 | **Sinister Generator wrapper** (`tools/nano-banana/`) | `source/system/sanctum-generator/` | Python (already cross-platform); only need to update output paths to XDG. | `sanctum-gen banner --brief "test"` produces a PNG under XDG_DATA_HOME. |
| 15 | **Cross-machine non-interference doctrine** (`_shared-memory/knowledge/cross-machine-non-interference-doctrine-2026-05-24.md`) | Same as #11 — moves with brain | None — doctrine is OS-agnostic. The slug-namespacing + per-machine `claude-accounts.json` discipline applies identically on Linux. | n/a (doctrine, not code) |
| 16 | **Memory audit findings** (`_shared-memory/knowledge/memory-audit-jcode-rufus-obsidian-understand-2026-05-24.md`) | Same as #11 | None | n/a |
| 17 | **Handterm fork brief** (`_shared-memory/cross-agent/2026-05-24T2025Z-sanctum-to-sinister-term-handterm-fork-brief.md`) | When sinister-term ships the fork, it lives at `projects/sinister-term/source/` and integrates into Sinister OS via #2 (the launcher spawns sinister-term as the default terminal on the OS). | When sinister-term port lands, register as default terminal in `sanctum-launcher` config. | `sanctum-launch sanctum --terminal sinister-term` opens with full sinister-term feature set. |
| 18 | **Safe quality loops doctrine** (`_shared-memory/knowledge/safe-quality-loops-doctrine-2026-05-24.md`) | Same as #11 | None | n/a |
| 19 | **Operator-utterance tracking** (`_shared-memory/operator-utterances.jsonl` + log/ack scripts) | `source/system/sanctum-utter/` | PS1 → Python; JSONL schema unchanged. | `sanctum-utter list --status new --slug sanctum` shows unacked rows. |
| 20 | **Bot fleet** (`_sinister-skills/12_LLM_ORCHESTRATION/agents/`) | `source/system/sanctum-bots/` (or junction-equivalent) | Bots are already mostly Python — minimal port. MCP server registration in `~/.claude/.mcp.json` becomes `$XDG_CONFIG_HOME/claude/mcp.json`. | `claude --list-mcp` shows all 22 servers + 14 bots online. |

## Open dependencies (resolve BEFORE OS migration)

1. **Round-robin v2 telemetry** — sanctum has 4 clarifying questions outstanding (telemetry source / hot-swap mechanism / burn-down thresholds / preference-learning store). Resolve in current Sanctum before porting #4 to OS — otherwise port re-does wrong design.
2. **EVE.exe banner `mcp:2` BOM bug** — root cause found (sanctum-to-sanctum-B coord note 2026-05-24T20:25Z). Fix BEFORE port so the port copies the corrected count function. Two-character change to `tools/eve-picker/eve_picker_lib.py` line 164.
3. **Round-robin slot enablement** — only 1 of 4 Claude account slots enabled. At least 1 more needs `SetKey` before rotation can be smoke-tested on either platform.
4. **Sister-B's in-flight launcher edits** — sanctum lane is holding off launcher edits while sister-B is in the file. Resolve sister-B's slice (per-stage progress bars + account-viewer + add-agent button) before porting #2.

## Composition with Sinister OS architecture

- **Sinister OS** is a Linux PC OS that replaces Windows as the operator's primary workstation. Per `projects/sinister-os/README.md`, EVE-controlled + per-app sandbox + Sinister branding.
- **Sanctum** remains the orchestration brain. On Sinister OS, Sanctum lives at `~/sanctum/` (or wherever the OS image places it) and runs as a systemd user-scope service.
- **Migration mode** — when ops switches over, Sanctum keeps running on Windows in parallel for 1-2 weeks (warm-failover). Brain + heartbeats + PROGRESS sync via vault between both hosts. Cut-over happens when Sinister OS Sanctum's `overseer scan` shows healthy + complete bot fleet for 7 consecutive days.

## Cross-references

- `_shared-memory/knowledge/_INDEX.md` — brain index (all doctrines listed here)
- `_shared-memory/knowledge/cross-machine-non-interference-doctrine-2026-05-24.md` — what to keep per-machine vs shared
- `_shared-memory/knowledge/safe-quality-loops-doctrine-2026-05-24.md` — universal loop discipline
- `_shared-memory/knowledge/overseer-agent-doctrine-2026-05-24.md` — overseer state machine
- `_shared-memory/knowledge/memory-audit-jcode-rufus-obsidian-understand-2026-05-24.md` — memory architecture comparison
- `_shared-memory/cross-agent/2026-05-24T2025Z-sanctum-to-sinister-term-handterm-fork-brief.md` — sinister-term port plan for handterm features

Updated: 2026-05-24
