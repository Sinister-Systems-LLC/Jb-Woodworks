> **Author:** RKOJ-ELENO :: 2026-05-24

# Quality-of-life feature catalog — Sinister OS

> **Operator directive (verbatim 2026-05-24):** *"things like soft reboot or clearing caches without full restart or fucking with my agents all things like this"*
>
> **Scope:** the QoL surface for daily operator use. Companion docs: [ghost-server-hardening.md](ghost-server-hardening.md) for the security baseline, [live-dev-workflow.md](live-dev-workflow.md) for HMR-without-reboot, [geo-mesh-routing.md](geo-mesh-routing.md) for remote access.

## Status legend

- **SHIPPED** — file exists on disk, verified working (curl 200 / exit code / measurable receipt this turn)
- **SCAFFOLDED** — file exists, parses clean, NOT smoke-tested end-to-end
- **PROPOSED** — design only; nothing on disk yet

## Feature table

| # | Feature | Status | Surface | Reference |
|---|---|---|---|---|
| 1 | Soft-reboot (clear caches, keep agents alive) | SCAFFOLDED (`eve` CLI shipping this turn) | `eve clean` | [`source/docker-stack/eve`](../source/docker-stack/eve), [`source/docker-stack/eve.md`](../source/docker-stack/eve.md) |
| 2 | Agent isolation per lane | SHIPPED | per-lane git worktree, `agent/<slug>/<topic>` branches | [Sanctum CLAUDE.md Rule 9](../../../CLAUDE.md), `automations/sanctum-auto-push.ps1` |
| 3 | `eve` CLI surface | SCAFFOLDED (shipping this turn) | `eve install \| restart \| clean \| theme \| hotkey \| logs \| status` | [`source/docker-stack/eve.md`](../source/docker-stack/eve.md) |
| 4 | Per-service log rotation | SHIPPED | Docker `logging.max-size` cap (5–20 MB × 3 files) | [HARDENING.md § logging row](../source/docker-stack/HARDENING.md) |
| 5 | Hotkey bindings (system-wide) | PROPOSED | Hyprland `bind=` lines → `eve.sock` → eve daemon | this doc § Hotkeys |
| 6 | Theme inheritance (Panel → OS shell → mobile) | SHIPPED (doctrine binding) | `sinister-theme-tokens.css` single source of truth | [knowledge/sinister-ui-canonical-dashboard-skeleton-inheritance-2026-05-24.md](../../../_shared-memory/knowledge/sinister-ui-canonical-dashboard-skeleton-inheritance-2026-05-24.md) |
| 7 | Live UI editing (no reboot) | SCAFFOLDED (`PANEL-DEV.md` shipping this turn) | `panel-dev` HMR service on :3082 | [`source/docker-stack/PANEL-DEV.md`](../source/docker-stack/PANEL-DEV.md), [live-dev-workflow.md](live-dev-workflow.md) |

## 1. Soft-reboot (`eve clean`)

**Problem.** Restarting Docker / the host wipes container caches AND breaks any running agent sessions. The operator wants cache clearing that does NOT touch agent state.

**Design.**

```
eve clean              # default: prune Docker dangling images + builder cache + Yjs LevelDB checkpoints older than 7d
eve clean --hard       # also: restart non-agent services (excludes panel + ollama + vault-api)
eve clean --layer ui   # only: clear Next.js .next build cache + Chromium kiosk cache; keep services running
```

What it never touches:
- Running EVE / Claude sessions
- `_shared-memory/` (the shared brain)
- `_vault/` (operator-owned secrets)
- Volumes named `*_data` (persistent state)

Reference: [`source/docker-stack/eve`](../source/docker-stack/eve) (CLI entrypoint, shipping this turn) + [`source/docker-stack/eve.md`](../source/docker-stack/eve.md) (full sub-command reference, shipping this turn).

## 2. Agent isolation per lane

**Pattern.** Each lane (sinister-os, sanctum, panel, apk, …) runs on its own branch `agent/<slug>/<topic>`. The `sanctum-auto-push` daemon is the only writer to `main` — per-lane sessions push their own branches freely (operator hard-canonical 2026-05-23).

**Why it matters for QoL.** Two operators can edit in similar areas of the same project without overwriting each other because:
- Each lane has its own working tree (or branch checkout)
- Yjs CRDT relay (`yjs-server` on :1234) provides character-level merge for live editing in the Panel
- `sanctum-auto-push.ps1` runs `git fetch --all --prune` every 30 min — branches stay in sync across machines

## 3. The `eve` CLI surface

| Sub-command | Purpose | Status |
|---|---|---|
| `eve install` | Bring up Docker stack via `docker compose -p sinister-mesh up -d` | SCAFFOLDED |
| `eve restart <service>` | Restart one service without touching others | SCAFFOLDED |
| `eve clean [--hard \| --layer X]` | Soft-reboot (see § 1) | SCAFFOLDED |
| `eve theme <name>` | Apply a named theme overlay; reloads only the Panel CSS | PROPOSED |
| `eve hotkey list \| add \| remove` | Manage compositor hotkey bindings | PROPOSED |
| `eve logs <service> [--follow]` | Tail one service's rotated log | SCAFFOLDED |
| `eve status` | Show the 10/10 service-health table + active VPN nodes | SCAFFOLDED |

Detailed reference: [`source/docker-stack/eve.md`](../source/docker-stack/eve.md) (shipping this turn).

## 4. Per-service log rotation

Every service in [`docker-compose.yml`](../source/docker-stack/docker-compose.yml) inherits the rotation rule from [`compose.hardened.yml`](../source/docker-stack/compose.hardened.yml):

```yaml
logging:
  driver: json-file
  options:
    max-size: "10m"   # 5m for chatty services, 20m for ollama
    max-file: "3"
```

Cap: ~30 MB per service. With 13 services in the stack, worst-case log footprint is ~390 MB before rotation kicks in. See [HARDENING.md `logging.max-size` row](../source/docker-stack/HARDENING.md) for the full security context.

## 5. Hotkeys (PROPOSED — not built)

**Future binding ladder:**

```
hardware key
    -> compositor (Hyprland) bind= rule
        -> POST /hotkey/<name> on /run/sinister/eve.sock
            -> eve daemon resolves <name> -> action
                -> auto-yes for the curated allowlist (apt, systemctl, nmcli, etc.)
                -> operator confirm hotkey for the rest
```

Initial proposed bindings (operator can edit `~/.config/sinister/hotkeys.toml`):

| Combo | Action | Curation |
|---|---|---|
| `SUPER + grave` | Toggle Panel kiosk fullscreen | auto-yes |
| `SUPER + SHIFT + R` | `eve clean` (soft-reboot) | auto-yes |
| `SUPER + SHIFT + Q` | `eve restart <focused-service>` | confirm |
| `SUPER + V` | Open voice surface (`sinister-voice`) | auto-yes |
| `SUPER + L` | Lock screen + freeze EVE socket | auto-yes |

Xorg fallback uses `xbindkeys` with the same socket target.

## 6. Theme inheritance

**Single source of truth:** [`source/docker-stack/config/theme/sinister-theme-tokens.css`](../source/docker-stack/config/theme/sinister-theme-tokens.css).

The Panel, the OS shell (Hyprland status bar + waybar), and the mobile app (`projects/sinister-kernel-apk/`) all consume the same CSS custom properties (`--sinister-bg`, `--sinister-accent-purple`, `--sinister-glass-blur`, etc.). Updating one token updates every surface.

Binding doctrine: [`_shared-memory/knowledge/sinister-ui-canonical-dashboard-skeleton-inheritance-2026-05-24.md`](../../../_shared-memory/knowledge/sinister-ui-canonical-dashboard-skeleton-inheritance-2026-05-24.md).

## 7. Live UI editing (no reboot)

The `panel-dev` service mounts the Panel source read-write into a Next.js dev container. Agents edit `.tsx`, operator sees the change in the kiosk in ~500ms. Windows file-watch quirk handled via `WATCHPACK_POLLING=true`.

See [live-dev-workflow.md](live-dev-workflow.md) for the full walkthrough and the [`source/docker-stack/PANEL-DEV.md`](../source/docker-stack/PANEL-DEV.md) bring-up doc (shipping this turn).

## Honest deferred (not yet started)

- Voice surface (`sinister-voice` always-on wake-word)
- Per-app proxy routing (composes with [geo-mesh-routing.md § 3-layer anonymity](geo-mesh-routing.md))
- Per-theme cold-load benchmarks (need to measure CSS-token swap cost on the kiosk)
- `eve theme` reload-without-reboot pipeline (depends on Panel HMR going live first)
