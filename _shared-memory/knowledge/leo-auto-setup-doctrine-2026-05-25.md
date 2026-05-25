<!-- decay:
  category: preference
  confidence: 0.9
  reinforcements: 0
  half_life_days: 365
-->
# Leo Auto-Setup Doctrine (drop EVE.exe + Sanctum folder, agent handles the rest)

**Author:** RKOJ-ELENO :: 2026-05-25

## Operator hard-canonical (verbatim 2026-05-25 ~00:35Z)

*"i need the exe to auto setup when i place on leos computer and all you need is
the exe and the sinsiter sanctum folder. when its doing setup it also needs to
first thing spawn a Sinister Setup Wizard agent that is prompted with the task
of making sure leo gets setup. document all issues you run into and their fixes
and report back"*

## The two-file drop contract

Leo's machine needs **exactly two artifacts** to be bring-up-ready:

1. `EVE.exe` (bundled launcher; PyInstaller-built; sits anywhere on disk)
2. `D:\Sinister Sanctum\` folder (cloned from GitHub `z0nian/Sinister Sanctum`
   to `D:\Sinister Sanctum\` -- the path is canonical because every doctrine,
   script, and project root references it)

Leo double-clicks `EVE.exe`. The first-run flow takes over.

## First-run flow (auto-triggered by EVE.exe before picker renders)

```
EVE.exe
  -> _maybe_run_first_run_wizard()  (eve.py line ~556)
     -> ~/.eve/first_run_marker.lock exists?
        YES  -> skip, render picker
        NO   -> run eve-first-run-check.ps1
                  exit 0 -> drop marker, render picker
                  exit 1 -> run eve-first-run-wizard.ps1 (hard-block first-run)
                  exit 2 -> run eve-first-run-wizard.ps1 (soft warns)
                  -> wizard runs grant-claude-autonomy.ps1 (9 steps idempotent)
                  -> wizard creates _shared-memory/* dirs
                  -> wizard drops ~/.sanctum-autonomy-granted + ~/.eve/first_run_marker.lock
                  -> wizard calls spawn-setup-wizard.ps1
                     -> resolves claude CLI on PATH; HALTs with Node/npm instructions if missing
                     -> pre-runs `claude login` interactively if no OAuth + no API key
                     -> constructs Wizard primer prompt
                     -> writes _shared-memory/setup/wizard-spawn-<utc>.sh
                     -> spawns mintty + bash + `claude --dangerously-skip-permissions <prompt>`
                     -> logs spawn to spawned-windows.jsonl
              -> render picker after wizard returns
```

## The Sinister Setup Wizard agent (the real Claude session)

After the .ps1 wizard finishes the automated steps, it spawns a REAL Claude
session in a mintty window with primer prompt (constructed in
`spawn-setup-wizard.ps1`). That session is "the Sinister Setup Wizard" and
walks Leo through 8 checklist items, one per turn:

1. Verify Anthropic OAuth login (claude CLI logged in).
2. Run `eve-first-run-check.ps1 -Format text` + surface remaining gaps.
3. Set git `user.name` + `user.email` for Leo.
4. Create working branch `agent/leo/onboard-bring-up`.
5. Offer Tailscale + vault join (point at `docs/LEO-VAULT-SETUP.md`); optional.
6. Smoke test a small shell command and verify execution.
7. Create first heartbeat at `_shared-memory/heartbeats/leo.json`.
8. Append a 5-line onboarding report to
   `_shared-memory/setup/leo-onboarding-report-<utc>.md`.

Loop policy: `loop=on`. One item per turn; asks confirmation at each gate;
never deletes / kills anything without explicit Leo confirmation; asks for
permission before writes outside `_shared-memory/setup/` +
`_shared-memory/heartbeats/`.

## Exit code contract (eve-first-run-check.ps1)

| Exit | Meaning | Wizard fires? |
|---|---|---|
| 0 | All checks PASS, marker present, claude CLI + OAuth working | NO |
| 1 | Hard-block: missing claude CLI / git / shared-memory / auth / Sanctum root | YES (mandatory) |
| 2 | Soft-warn: missing API key / network / vault / Python | YES (recommended) |

Hard-block list (any one triggers exit 1):
- `sanctum-root-missing-or-incomplete` (no CLAUDE.md / automations / _shared-memory)
- `git-for-windows-missing` (no mintty / git-bash / bash on canonical paths)
- `claude-cli-missing` (no claude.exe or claude on PATH)
- `shared-memory-uninitialized` (no _shared-memory/ tree)
- `no-auth` (no OAuth creds AND no ANTHROPIC_API_KEY env)
- `force-flag-set` (operator passed `-Force` to re-run setup)

## CLI knobs

```powershell
# Detect first-run
powershell -File automations\eve-first-run-check.ps1 -Format text
powershell -File automations\eve-first-run-check.ps1 -Format json
powershell -File automations\eve-first-run-check.ps1 -SimulateFreshMachine  # test wizard would fire
powershell -File automations\eve-first-run-check.ps1 -Force                  # force exit 1

# Run wizard (interactive)
powershell -File automations\eve-first-run-wizard.ps1
powershell -File automations\eve-first-run-wizard.ps1 -DryRun                # no writes
powershell -File automations\eve-first-run-wizard.ps1 -NoHelperSpawn         # skip Claude agent spawn
powershell -File automations\eve-first-run-wizard.ps1 -NonInteractive        # CI / unattended

# Spawn the Setup Wizard agent directly (skipping detector)
powershell -File automations\spawn-setup-wizard.ps1
powershell -File automations\spawn-setup-wizard.ps1 -DryRun                  # print would-do, no spawn
powershell -File automations\spawn-setup-wizard.ps1 -OperatorName Leo        # override name
powershell -File automations\spawn-setup-wizard.ps1 -NoLogin                 # skip OAuth pre-step

# Re-run wizard on already-set-up machine
EVE.exe --force-setup-wizard
```

## Markers

Two markers gate first-run:

1. `~/.sanctum-autonomy-granted` -- global marker; set by `grant-claude-autonomy.ps1`
   AND by the wizard. Survives EVE.exe rebuilds.
2. `~/.eve/first_run_marker.lock` -- EVE-specific marker dropped by `eve.py`
   when `_maybe_run_first_run_wizard()` returns successfully OR when detector
   says ready. Allows wizard to be skipped on subsequent EVE launches even if
   the global marker is missing (drift protection).

`EVE.exe --force-setup-wizard` ignores both markers.

## Logs

Every wizard run writes a log to
`_shared-memory/setup/leo-first-run-<utc>.log`. Each spawn of the Setup
Wizard Claude agent writes to
`_shared-memory/setup/wizard-spawns-<yyyymmdd>.log` (one line per spawn).
The mintty launch script for each spawn lives at
`_shared-memory/setup/wizard-spawn-<utc>.sh` (kept for forensics).

## Files in play

| File | Purpose | Author / Date |
|---|---|---|
| `automations/eve-first-run-check.ps1` | detector (probe + 3-tier exit) | RKOJ-ELENO 2026-05-25 v2 |
| `automations/eve-first-run-wizard.ps1` | automated setup wizard | RKOJ-ELENO 2026-05-25 v2 |
| `automations/spawn-setup-wizard.ps1` | spawns the Claude Setup Wizard agent | RKOJ-ELENO 2026-05-25 |
| `automations/grant-claude-autonomy.ps1` | 9-step idempotent autonomy grant | RKOJ-ELENO 2026-05-23 v2 |
| `automations/eve-launcher/eve.py` | first-run gate in `main()` + `_maybe_run_first_run_wizard()` | (existing; line ~556) |
| `_shared-memory/setup/` | log + launch.sh + onboarding report dir | (auto-created) |
| `_shared-memory/knowledge/leo-first-run-issues-and-fixes-2026-05-25.md` | issues log | RKOJ-ELENO 2026-05-25 |

## MCP + Docker + Bots + Autonomy (v3 expansion, 2026-05-25)

Operator hard-canonical (verbatim 2026-05-25 ~01:35Z): *"make sure in the exe auto setup for leo we make sure mcp setup. all bots docker installed and ready for use all shit like that we do. the autonomy grant all taht"*.

The fresh-machine flow MUST also surface + auto-fix:

### Detector additions (`eve-first-run-check.ps1` v3)

Added 13 new checks (all soft-warn; wizard auto-fixes each):

| Check | What it verifies | Auto-fix |
|---|---|---|
| `docker_cli_present` | `docker` command on PATH | `winget install Docker.DockerDesktop` (operator confirms) |
| `docker_daemon_reachable` | `docker info` returns Server version | Start Docker Desktop |
| `mcp_config_present` | `~/.claude/.mcp.json` exists | Wizard copies `automations/templates/leo-mcp-config.json` |
| `mcp_servers_connected` | `claude mcp list` shows >=1 Connected | Restart Claude Code after seeding config |
| `task_auto_push` | `SinisterSanctumAutoPush` schtask registered | `install-leo-scheduled-tasks.ps1` |
| `task_oauth_health` | `SinisterOAuthHealthPoll` schtask registered | `install-leo-scheduled-tasks.ps1` |
| `task_link_poll` | `SinisterLinkPoll` schtask registered | `install-leo-scheduled-tasks.ps1` |
| `task_account_watchdog` | `SinisterAccountWatchdog` schtask registered | `install-leo-scheduled-tasks.ps1` |
| `bypass_permissions_on` | `bypassPermissions=true` + `--dangerously-skip` in allow-list + `defaultMode=bypassPermissions` | `grant-claude-autonomy.ps1` Step 6 |
| `understand_anything_on` | Plugin enabled in `~/.claude/settings.json` (cold-start step 0 prereq) | `grant-claude-autonomy.ps1` Step 9 |
| `eve_exe_mirrored` | `~/.eve/EVE.exe` present | `verify-eve-features.ps1 -SyncMirror` |
| `git_user_configured` | `git config --global user.name + user.email` set | Wizard prompts Leo |
| `vault_daemon_reachable` | TCP :5078 listening | Optional Tailscale + vault join (LEO-VAULT-SETUP.md) |

### Wizard additions (`eve-first-run-wizard.ps1` v3)

Added Steps 6a (MCP seed), 6b (Docker + bots), 6c (scheduled tasks) before agent spawn. Each step runs the corresponding installer in -DryRun first; real install is operator-confirm via the Setup Wizard agent.

### New tools

| Tool | Purpose |
|---|---|
| `automations/templates/leo-mcp-config.json` | 16-server template; `${SINISTER_SANCTUM_ROOT}` placeholder substituted on seed. Includes 12 Sinister bots + 4 npm-based MCPs (playwright, context7, sequential-thinking, memory). API-key fields marked `FILL-IN-WITH-USER-ENV`. |
| `automations/install-leo-bots.ps1` | Wraps `docker compose pull`/`build`/`ps` for every known compose stack (ollama + sanctum-git). Auto-discovers known stacks, supports `-DryRun`/`-VerifyOnly`/`-NoBuild`/`-Stack`. Logs to `_shared-memory/setup/leo-bots-install-<utc>.log`. |
| `automations/install-leo-scheduled-tasks.ps1` | Wraps every `install-*.ps1` task installer (7 tasks). Supports `-DryRun`/`-UninstallAll`/`-Only`/`-Skip`. Logs to `_shared-memory/setup/leo-tasks-install-<utc>.log`. |

### Setup Wizard agent primer expansion

Expanded from 8 to 13 checklist items adding: Docker presence (item 5), bot pull (6), MCP seed + `claude mcp list` verify (7), scheduled task install (8), autonomy grant verify (9). Original Tailscale/smoke/heartbeat/report items become 10-13.

## Composes with

- `sanctioned-bypasses-doctrine-2026-05-21.md` (`--dangerously-skip-permissions` always-on)
- `agent-identity-eve.md` (the agent persona is EVE; Setup Wizard is an EVE sub-persona)
- `non-interactive-auth-doctrine-2026-05-23.md` (pre-resolving OAuth before spawn)
- `do-not-revert-operator-canonical-protections-2026-05-23.md` (don't remove the first-run gate)
- `eve-ui-uniformity-doctrine-2026-05-24.md` (any sub-pages in the wizard use canonical layout)
- `mesh-coordination-and-resource-lifecycle-2026-05-24.md` (lock before editing eve.py)
