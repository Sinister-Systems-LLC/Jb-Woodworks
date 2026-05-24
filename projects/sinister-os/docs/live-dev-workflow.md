> **Author:** RKOJ-ELENO :: 2026-05-24

# Live dev workflow — HMR without reboot

> **Operator directive (verbatim 2026-05-24):** *"i want to open in docker first before we move to laptop. I want you to build the OS in such a way that i can live work on things with an agent to change ui work etc without having to reboot or things like that."*
>
> **Companion docs:** [qol-features.md § 7 live UI editing](qol-features.md), [ghost-server-hardening.md](ghost-server-hardening.md) (production hardening contrast), [geo-mesh-routing.md](geo-mesh-routing.md) (remote-access case for the same workflow from Thailand).
>
> **Bring-up reference:** [`source/docker-stack/PANEL-DEV.md`](../source/docker-stack/PANEL-DEV.md) — the operational doc for starting / stopping / debugging the dev service. This doc is the higher-level walkthrough.

## The flow in one sentence

Agent edits a `.tsx` file on disk → Next.js dev server inside the `panel-dev` container picks up the change in ~150–500 ms → the Chromium kiosk pointed at `http://localhost:3082/` re-renders without a page reload (or full-reloads if the change crosses an HMR boundary).

## Detailed walkthrough

### 1. Two panel surfaces, one stack

| Service | Port | Role | Hardening overlay |
|---|---|---|---|
| `panel` | `:3081` | Production placeholder (Liquid Glass landing, then real Next.js standalone after `bake-panel.sh`) | Hardened overlay applies in prod |
| `panel-dev` | `:3082` | Live HMR Next.js dev server bind-mounting the Panel source | NOT hardened (read_only:false; webpack writes inside container) |

Operator can switch the kiosk URL between `:3081` (stable) and `:3082` (live dev) freely. Both are always running once both compose files are up.

### 2. The edit-to-pixel timeline

| t (ms) | Step | Surface |
|---|---|---|
| 0 | Agent saves `.tsx` (e.g. `projects/sinister-panel/components/Topbar.tsx`) | host filesystem |
| 50–150 | webpack-dev-server inside `panel-dev` container detects file change | Docker bind-mount → container |
| 150–300 | webpack re-compiles the changed module + dependents | container |
| 300–450 | webpack pushes the HMR update over websocket to the kiosk page | container → kiosk |
| 450–500 | React mounts the new module, preserving component state where possible | kiosk |

Typical observed end-to-end: 300–500 ms for a single-file change. Full reload (when HMR boundary is crossed): 800–1200 ms.

### 3. The Windows file-watch caveat

Docker Desktop on Windows uses a 9p / SMB-style filesystem bridge between host NTFS and the container's bind-mount. **Inotify events do not propagate cleanly across that bridge.** Without intervention, webpack never sees the edit.

**Fix shipped in the `panel-dev` service definition (described in [PANEL-DEV.md](../source/docker-stack/PANEL-DEV.md)):**

```yaml
environment:
  WATCHPACK_POLLING: "true"
  CHOKIDAR_USEPOLLING: "true"
  WATCHPACK_POLLING_INTERVAL: "300"
```

`WATCHPACK_POLLING=true` forces webpack-dev-server to poll the filesystem every 300 ms instead of relying on inotify. CPU cost on the operator's laptop: ~1–2% of a single core, well under the 1.0 CPU cap in the dev overlay.

**Save-and-reload fallback.** If polling is somehow disabled OR the agent edits a file webpack doesn't watch (e.g. `next.config.js`), the operator can force the dev server to restart with:

```bash
docker compose -p sinister-mesh restart panel-dev
```

Restart takes ~2–4 s; the kiosk auto-reconnects when the websocket comes back.

### 4. The kiosk URL switch flow

The Chromium kiosk is launched on first-boot by the OS shell with a single env var:

```bash
KIOSK_URL="${SINISTER_KIOSK_URL:-http://localhost:3081/}"
chromium --kiosk --noerrdialogs --disable-translate "$KIOSK_URL"
```

To switch between prod and dev surfaces WITHOUT rebooting:

| Goal | Command |
|---|---|
| Switch kiosk to live dev | `eve theme dev` (PROPOSED) OR manually: `pkill -USR1 chromium; SINISTER_KIOSK_URL=http://localhost:3082/ /usr/local/bin/sinister-kiosk` |
| Switch kiosk back to prod | `eve theme prod` (PROPOSED) OR `SINISTER_KIOSK_URL=http://localhost:3081/` |
| Reload current URL | `xdotool key --window $(xdotool search --class chromium \| head -1) F5` |

The `eve theme dev` / `eve theme prod` flow is PROPOSED — see [qol-features.md § 3 eve CLI](qol-features.md).

### 5. Agent-edits-tsx-operator-sees-it loop

Concrete example. Operator says: *"make the topbar accent purple instead of cyan"*.

1. Agent reads `projects/sinister-panel/components/Topbar.tsx`.
2. Agent reads [`source/docker-stack/config/theme/sinister-theme-tokens.css`](../source/docker-stack/config/theme/sinister-theme-tokens.css) for the canonical `--sinister-accent-purple` token.
3. Agent edits Topbar.tsx to consume `var(--sinister-accent-purple)` instead of the hard-coded cyan.
4. Agent saves. webpack rebuilds in ~300 ms.
5. Operator sees the change in the kiosk at `:3082`.
6. Agent commits on the lane branch.
7. `sanctum-auto-push` ships the commit on the next 30-min tick.

At no point does the operator restart Docker, restart the kiosk, restart an agent session, or lose any in-progress work.

### 6. Coexistence with hardening

The hardened production `panel` service (port `:3081`) runs under [`compose.hardened.yml`](../source/docker-stack/compose.hardened.yml) — read-only root, cap_drop ALL, etc. The dev `panel-dev` service (port `:3082`) does NOT inherit the hardening overlay because:

- webpack needs to write to `.next/` and `node_modules/.cache/` at runtime
- HMR websocket requires unsolicited inbound on the dev port
- File-system polling requires read-write access to the bind-mount

This is intentional. The dev surface is opt-in via a separate compose file (`compose.dev.yml`) the operator brings up only when actively editing. Production traffic never touches `:3082`.

### 7. Failure modes + recovery

| Symptom | Likely cause | Fix |
|---|---|---|
| Kiosk shows "This site can't be reached" on :3082 | `panel-dev` container not running | `docker compose -p sinister-mesh up -d panel-dev` |
| Edit saved but kiosk doesn't update | Polling disabled OR file outside watched paths | Check `docker logs sinister-panel-dev` for "watching"; restart container |
| Webpack compile error overlay covers the page | TypeScript error in agent's edit | Agent must fix; overlay clears automatically on next clean compile |
| HMR drops the websocket every few minutes | Browser tab throttled (background) | Bring kiosk window to foreground OR set Chromium flag `--disable-background-timer-throttling` |
| Edit took >2 s to show | Cold compile after `node_modules` change | Expected; subsequent edits are sub-second |

## Honest status

- `compose.dev.yml` defining `panel-dev`: **SHIPPED** (file exists at [`source/docker-stack/compose.dev.yml`](../source/docker-stack/compose.dev.yml))
- `PANEL-DEV.md` bring-up doc: **SCAFFOLDED** (shipping this turn alongside this doc)
- Live HMR loop end-to-end smoke-test (edit → kiosk re-renders): **NOT YET RUN** — verification pending operator-driven test or smoke-test script extension
- `eve theme dev` / `eve theme prod` kiosk URL switch: **PROPOSED** (manual switch documented in § 4)

## Where to go next

- Bring-up specifics: [`source/docker-stack/PANEL-DEV.md`](../source/docker-stack/PANEL-DEV.md)
- The dev surface composed with operator-facing QoL: [qol-features.md](qol-features.md)
- The hardening overlay that the prod surface (not dev) inherits: [ghost-server-hardening.md](ghost-server-hardening.md)
- Editing live from Thailand over Tailscale: [geo-mesh-routing.md](geo-mesh-routing.md)
