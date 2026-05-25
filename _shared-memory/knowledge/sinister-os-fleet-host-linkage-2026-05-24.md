<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
# Sinister OS fleet-host linkage doctrine

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Trigger:** Operator 2026-05-24 20:40Z verbatim — *"link all of this into the sinister os im making as we willl be siwthcin (switching) to it"*
> **Composes with:** `sinister-os-doctrine-2026-05-24`, `sinister-os-mobile-doctrine-2026-05-24`, `sanctum-scope-discipline-2026-05-24`, `mesh-coordination-and-resource-lifecycle-2026-05-24`, `fleet-update-channel-doctrine-2026-05-24`

## Strategic intent

The current Sanctum runtime (Windows 10, `D:\Sinister Sanctum`, PowerShell-driven launcher, mintty terminals, MCP servers, Docker Desktop, vault daemon) is the **bootstrap host** — not the final home. Operator will switch the entire fleet to **Sinister OS** (the custom Linux/Android-derived distribution being built in the `sinister-os` + `sinister-os-mobile` lanes).

Every new automation, every doctrine, every script the fleet ships should be **designed to port** — not Windows-locked.

## What "linked into Sinister OS" means

Three tiers of linkage:

1. **Direct port** — the artifact runs on Sinister OS with no rewrite (e.g. Python scripts using only stdlib + cross-platform third-party libs; bash scripts; Docker images; JSON/JSONL data files).
2. **Trivial adaptation** — the artifact runs after a single mechanical translation (PowerShell `.ps1` → bash `.sh`; `Start-Process` → `nohup … &` or systemd unit; `~/.claude/...` path → `$XDG_CONFIG_HOME/claude/...`).
3. **Architectural re-host** — the artifact's *role* survives but the implementation changes substantively (mintty → kitty / wezterm / Sinister-Term; Windows registry → systemd-machine-id / `/etc`; Task Scheduler → systemd timers; Defender exclusions → none-needed-on-Linux).

## Inventory of fleet artifacts by linkage tier

### Tier 1 — direct port (works as-is)

- `_shared-memory/` (entire tree: PROGRESS, heartbeats, knowledge, plans, resume-points, fleet-updates.jsonl, operator-utterances.jsonl, counter-arguments.jsonl, improvement-log.jsonl, quality-loop-log.jsonl, claude-accounts.json)
- `projects/<lane>/source/` (junctions become symlinks on Linux; git repos clone identically)
- `_vault/` (vault daemon is Python; portable)
- Python wrappers: `tools/nano-banana/`, `automations/eve-launcher/eve.py` (PyInstaller bundle today; on Linux either run `eve.py` directly or rebuild as a Linux ELF binary)
- JSON config files: `projects.json`, `agent-prefs.json`, `claude-accounts.json`, `personal-projects.json`, `agent-modes/*.json`
- Bash scripts already present (`launch.sh` already used; `automations/build-eve-exe.bat` → port to `build-eve-elf.sh`)
- Markdown docs (CLAUDE.md, SESSION-START/*, brain entries, project-level docs)

### Tier 2 — trivial adaptation

- `automations/*.ps1` (≈40 scripts) → translate to bash. Common patterns:
  - `Get-Content -Raw | ConvertFrom-Json` → `jq < file`
  - `Start-Process` → `nohup … >/dev/null 2>&1 &`
  - `Test-Path` → `[ -e ]` / `[ -d ]`
  - `[System.IO.File]::Open(... CreateNew ...)` (sentinel lock) → `flock` or `mkdir` race-trick
  - Sentinel-file locks port directly (just change extension/path)
- Scheduled tasks (`SinisterSanctumAutoPush`, `SinisterVault`, `RKOJ`, `Docker Desktop AutoStart`) → systemd timers + units
- `~/.claude/.mcp.json` → `~/.config/claude/.mcp.json` (path map only)
- Windows path separators → use `os.path.join` / pathlib in Python, `/` in bash
- Sinister Start.bat → `sinister-start.sh` calling the same `start-sinister-session` core

### Tier 3 — architectural re-host

- **Terminal**: mintty (Win-only) → kitty / wezterm / sinister-term (the lane's own terminal)
- **Window position monitor**: Win32 `GetWindowRect` → Wayland `ext-foreign-toplevel` protocol or X11 `XGetWindowAttributes`
- **EVE.exe**: PyInstaller Win EXE → ELF binary OR system-installed `eve` command in `$PATH`
- **Defender exclusions**: irrelevant on Linux (no real-time AV scanning the home dir by default)
- **Docker Desktop**: replaced by native dockerd or podman (`systemctl enable docker.service`)
- **Tailscale**: same daemon, native Linux package (already cross-platform)
- **MCP servers**: most are Python/Node → run on Linux directly; the few Windows-specific ones (none we ship today) would need re-impl
- **GitHub Desktop / file explorer**: replaced by native tools (nautilus / dolphin / nnn)

## Forward-design rules (binding for new work)

When adding new automations / doctrines / scripts:

1. **Pick the most portable language**: Python > Bash > PowerShell. Use PowerShell only for genuine Windows APIs (registry, Win32 GUI). When PS is necessary, also ship the Linux equivalent in `automations/linux/<name>.sh`.
2. **Use cross-platform path helpers**: Python `pathlib.Path` + `os.path.expanduser('~')`; bash `$HOME`. Never hardcode `D:\Sinister Sanctum` — use `$SINISTER_SANCTUM_ROOT` env var with sensible default.
3. **Avoid Windows-only daemons** when designing new services: prefer systemd unit specs first, then Task Scheduler wrappers. (Sinister Vault's daemon model already does this — Python `http.server` works both places.)
4. **Tag artifacts with portability tier** in their header comment: `# Portability: Tier 1 (direct)` / `# Portability: Tier 2 (translates to bash)` / `# Portability: Tier 3 (Linux rewrite needed)`. Makes the Sinister OS port a mechanical sort.
5. **Data formats stay portable**: JSON + JSONL + Markdown. Never Windows-specific serializations (no .reg files for runtime state; no `[xml]::Load` for fleet data).
6. **EVE.exe → eve binary**: when adding new picker keys or menu items, write the logic in pure Python (eve.py) so the same code becomes both `EVE.exe` on Windows and `eve` on Linux via PyInstaller's `--onefile` for each target.
7. **Per-platform conditionals**: when needed, use `if sys.platform == 'win32'` blocks in Python and `case "$(uname)" in` in bash. Never assume Windows is forever.

## Port-readiness checklist (Sinister OS migration prerequisites)

Before flipping the fleet to Sinister OS as primary host:

- [ ] Tier-2 .ps1 → .sh translations for: `start-sinister-session`, `claude-accounts`, `fleet-update`, `log-operator-utterance`, `ack-operator-utterance`, `resume-point-write`, `forever-improve`, `quality-monotonic-loop`, `counter-arg`, `sanctum-auto-push`, `fleet-health`, `verify-fleet-state`, `mesh-coordinator`, `bot-lifecycle`, `heartbeat-sweep`, `detect-similar-agents`, `window-position-monitor`
- [ ] eve.py portable build: Linux PyInstaller ELF (test-run on the cuttlefish sandbox first)
- [ ] systemd units replacing Task Scheduler entries (SinisterSanctumAutoPush, vault, watchdogs)
- [ ] `~/.config/claude/` paths supported as alternates throughout the fleet
- [ ] All MCP servers verified to start under systemd on Linux
- [ ] Vault daemon survives the host switch (data dir under `/var/lib/sinister-vault` or `~/.local/share/sinister-vault`)
- [ ] Brand-locks (nano_banana) verified portable (Python + Gemini API are cross-platform)
- [ ] sinister-term gains feature parity with mintty (colors, fonts, position restore via Wayland protocol)
- [ ] Test full /loop cycle on Sinister OS sandbox before flipping primary
- [ ] Operator-facing Sinister-Start launcher (.sh) tested

## Anti-patterns (do not write these)

- Hardcoding `D:\Sinister Sanctum` in new scripts (use `$SINISTER_SANCTUM_ROOT`)
- New `.bat` files (write `.sh` first, optionally wrap in `.bat` for Windows transition)
- Windows-only Python deps (`pywin32` etc.) without a Linux fallback path
- Storing runtime state in Windows registry (use `_shared-memory/` files instead)
- Assuming PowerShell will run on Sinister OS (PS Core exists for Linux but is not the default; bash IS)
- Designing new GUIs in WinForms / WPF (use TUI in Python / Rust, or web UI served by vault-style daemon)

## How this composes with existing doctrines

- **sanctum-scope-discipline-2026-05-24**: linkage-to-Sinister-OS is high-level architecture = explicitly in-scope for sanctum lane.
- **mesh-coordination-and-resource-lifecycle-2026-05-24**: the mesh-coordinator + bot-lifecycle + heartbeat-sweep scripts MUST be ported to bash for Sinister OS host.
- **fleet-update-channel-doctrine-2026-05-24**: the channel mechanism (jsonl + sentinel lock + lazy poll) is Tier 1 portable. The `fleet-update.ps1` CLI is Tier 2 (becomes `fleet-update.sh`).
- **agent-identity-eve**: EVE persona is host-independent. The EVE.exe binary is host-specific.
- **no-bullshit-tested-before-claimed-doctrine-2026-05-23**: every port artifact must be smoke-tested on Sinister OS sandbox before claiming it works there.

## Status

- **Created:** 2026-05-24 20:40Z (this row)
- **Bound in:** `_shared-memory/knowledge/_INDEX.md` (next iter — operator-pinned)
- **Distributed via:** `fleet-update.ps1 -Action Push -Kind doctrine -Priority normal -TargetSlugs sinister-os,sinister-os-mobile,sanctum,sinister-term`
- **Owner during transition:** sanctum lane (high-level architecture) + sinister-os lane (Linux host) + sinister-os-mobile lane (Android host)
