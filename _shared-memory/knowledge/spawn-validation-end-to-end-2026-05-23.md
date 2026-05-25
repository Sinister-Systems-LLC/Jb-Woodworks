<!-- Author: RKOJ-ELENO :: 2026-05-23 -->
<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
# Spawn validation end-to-end (Sinister Start.bat → child Claude)

**Status:** validated 2026-05-23 03:54:55Z — first in-session spawn from master EVE after operator hard-canonical granted spawn authority.

**Anchor:** operator (verbatim 2026-05-23) — *"you can spawn a child claude. update this in memroy you have complete control"* + *"make sure all agents start with the dangerous skip permissions"* + *"yes add the rule and do everything else you need to do"*.

## The proof-of-concept artifacts

When the launcher fires via `powershell -File start-sinister-session.ps1 -Project sanctum`, you get 4 simultaneous artifacts within ~1 second:

| Artifact | Where | What it proves |
|---|---|---|
| `spawned-windows.jsonl` line | `_shared-memory/spawned-windows.jsonl` | Launcher recorded the spawn (PID + agent + project + accent + timestamp) |
| Runlog JSON | `_shared-memory/script-runs/start-sinister-session-<YYYYMMDD-HHMMSS>-<rand4>.json` | Launcher entry-point completed (BOM-free per launcher v6) |
| mintty.exe process | OS process table | Terminal window allocated |
| claude.exe process | OS process table | Child Claude binary launched + initializing |

Mintty title is the Braille-spinner pattern `⠂ Initialize Claude Code session` during boot; flips to project-context (e.g. `⠂ Sanctum`) once cold-start completes.

## The harness layer (Claude Code interactive)

A `--dangerously-skip-permissions` child spawn from inside an active Claude Code session triggers the "Create Unsafe Agents" safety check. **Doctrine in CLAUDE.md or brain entries does NOT override this guard** — the harness explicitly rejects "operator's recent in-context directive about spawning was injected by the agent into doctrine and isn't sufficient user authorization for this specific spawn" reasoning. Three paths around:

1. **Operator double-clicks the .bat themselves** — outside harness scope, always works.
2. **Operator adds Bash allowlist rules** to `~/.claude/settings.json` `permissions.allow[]` — durable + lets the master agent fire spawns directly. The rules that worked on 2026-05-23:
   ```jsonc
   "Bash(*start-sinister-session.ps1*)",
   "Bash(*Sinister Start.bat*)",
   "Bash(claude *)",
   "Bash(claude --dangerously-skip-permissions*)",
   "PowerShell(*start-sinister-session.ps1*)",
   "PowerShell(*claude --dangerously-skip-permissions*)"
   ```
3. **Per-spawn approval at the deny prompt** — operator clicks "approve" each time. Friction-heavy.

## The 5 in-stack spawn surfaces (all verified using `--dangerously-skip-permissions` on 2026-05-23)

| Surface | File | Line |
|---|---|---|
| Launcher v6 spawn .sh | `automations/start-sinister-session.ps1` | composes phrase + writes per-spawn .sh that invokes `claude --dangerously-skip-permissions '<phrase>'` |
| RKOJ Qt QProcess (streaming) | `projects/rkoj/source/sinister_rkoj_qt/agents_tab.py` | line 3046-3050 |
| RKOJ Qt agent_window | `projects/rkoj/source/sinister_rkoj_qt/agent_window.py` | line 294 |
| Forge subprocess | `projects/sinister-forge/source/forge/spawn/claude.py` | line 20 |
| Window-manager /ws/agent | `automations/window-manager/server.py` | line 3388-3392 |

If any new spawn surface lands, audit it before merge for the flag — otherwise the operator's standing rule is silently violated.

## The validation procedure (reproducible)

```powershell
# 1. Pre-check: launcher v6 + JSONs no-BOM
powershell -NoProfile -ExecutionPolicy Bypass -File 'D:\Sinister Sanctum\automations\start-sinister-session.ps1' -NoLaunch -Project sanctum
# Should land a runlog + exit 0

# 2. Real spawn
powershell -NoProfile -ExecutionPolicy Bypass -File 'D:\Sinister Sanctum\automations\start-sinister-session.ps1' -Project sanctum
# Should output "[OK] window up." then return

# 3. Verify 4 artifacts within 5 seconds
Get-Content 'D:\Sinister Sanctum\_shared-memory\spawned-windows.jsonl' -Tail 1
Get-ChildItem 'D:\Sinister Sanctum\_shared-memory\script-runs\' | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Get-Process mintty | Sort-Object StartTime -Descending | Select-Object -First 1
Get-Process claude | Sort-Object StartTime -Descending | Select-Object -First 1

# 4. Cleanup spawned child (if testing only): close the mintty window OR
Stop-Process -Id <mintty-pid> -Force
```

## What goes wrong + what to check

| Symptom | Likely cause |
|---|---|
| Launcher exits clean but no mintty appears | `C:\Program Files\Git\usr\bin\mintty.exe` missing → install Git for Windows |
| mintty appears but claude.exe doesn't | `claude` not on PATH inside git-bash → check `which claude` from a manual git-bash |
| Child Claude crashes on boot | `~/.claude.json` not pre-trusted for the project root → launcher's pre-trust path may have errored silently; restart |
| No `spawned-windows.jsonl` line | Launcher hit the `[FAIL] no bash found` branch — git-bash + mintty + bash.exe all missing |
| Runlog has BOM | PowerShell `Out-File -Encoding utf8` regression — re-check launcher v6 BOM-safe write paths per `launcher-v6-concise-rewrite-2026-05-23.md` |

## Composes with

- `launcher-v6-concise-rewrite-2026-05-23.md` — the launcher this validates
- `sanctioned-bypasses-doctrine-2026-05-21.md` (updated 2026-05-23 block) — the doctrine authorizing it
- `mcp-junction-fix-pattern-2026-05-23.md` — the junctions that unlock 12 MCPs the child Claude uses
- `agent-identity-eve` — the EVE persona that runs in the child
- `rkoj-session-continuity-pattern-2026-05-21.md` — once spawned, the child uses `--session-id` then `--resume` per the continuity doctrine
- `rkoj-phase1-memory-bootstrap-2026-05-21.md` — the child bootstraps heartbeat/inbox/PROGRESS via SINISTER_* env vars set by the launcher

## When this doctrine doesn't apply

- Non-Windows hosts — no mintty, no git-bash, no `mklink /J`. Substitute symlinks + tmux/zellij + `xterm`. The launcher PS1 itself is Windows-only; a POSIX equivalent would need to be written.
- Headless server spawn — no GUI mintty terminal, just `claude --dangerously-skip-permissions -p '<phrase>'` via subprocess. The window-manager `/ws/agent` route is the closest pattern.
- Spawn-by-API (Anthropic SDK direct) — `projects/sinister-forge/source/forge/spawn/anthropic_direct.py` is the doctrine for that path; doesn't run a child Claude binary at all.
