<!--
Author: RKOJ-ELENO :: 2026-05-24
Lane: sinister-os
Companion to: compose.dev.yml
-->

# Panel Dev / Live HMR Overlay

## Synopsis

The base `docker-compose.yml` ships a baked, immutable `panel` placeholder on port **3081** for the kiosk surface. That is fine for production, but the operator's directive (verbatim 2026-05-24) was:

> "i want you to build the OS in such a way that i can live work on things with an agent to change ui work etc without having to reboot or things like that"

`compose.dev.yml` is the answer: an additive overlay that brings up a second container, `panel-dev`, on port **3082** with the Sinister Panel Next.js source bind-mounted from the sister `sinister-panel` lane. Hot Module Reload (HMR) means an agent (or the operator) can edit a `.tsx` file on the host and the browser re-renders the changed component in ~500 ms — no container restart, no rebuild, no reboot.

The placeholder `panel` service on :3081 keeps running untouched. Both can be live at the same time.

## Bring-up

```bash
cd projects/sinister-os/source/docker-stack
docker compose -f docker-compose.yml -f compose.dev.yml up -d panel-dev
docker compose -f docker-compose.yml -f compose.dev.yml logs -f panel-dev
```

**What to expect:**

1. **First run:** `npm install` runs inside the container against the bind-mounted source. Expect 60-120 s of "added N packages" output before the dev server starts. Subsequent runs reuse the `panel-dev-node-modules` named volume, so they start in ~5 s.
2. **Dev server up:** the log line `▲ Next.js 15.x.x ... Local: http://0.0.0.0:3082` confirms the listener.
3. **Browse:** `http://localhost:3082` → the live dashboard.
4. **Edit:** save any file under `D:\Sinister Sanctum\projects\sinister-panel\source\Andrew Panel\Sinister Panel\panel\dashboard\` → the browser auto-refreshes the changed module.

## File-watch caveat on Windows bind-mounts

Docker Desktop on Windows runs the engine inside a Linux VM. Native Linux `inotify` events do not cross the Windows → Linux VM boundary reliably for files modified by Windows-side editors. The overlay sets:

- `WATCHPACK_POLLING=true` — webpack's file-watcher (used by Next.js dev) polls instead of relying on inotify
- `CHOKIDAR_USEPOLLING=true` — same fix for any library that uses chokidar

Polling adds a small CPU baseline (~1-2% of one core) and a 300-500 ms detection latency. That is the trade-off for cross-platform reliability.

If you ever see a save that does NOT trigger a reload:

- Some editors (notably old VS Code on slow disks) write to a temp file and atomically rename. Save-and-touch (`echo "" >> file.tsx` then undo) usually wakes the watcher.
- Worst case: hard-refresh the browser (Ctrl+Shift+R) — the source is still re-imported from disk on the next request.

## Pointing the kiosk at the dev server (live preview)

The operator-baked Panel kiosk launches a Chromium kiosk window pointed at port 3081 by default. To switch the kiosk to live-preview the dev server during a UI work session, change the kiosk URL flag in `airootfs` (or pass it at launch):

```bash
# In airootfs/usr/local/bin/sinister-panel-kiosk.sh (or equivalent launcher):
chromium --kiosk http://localhost:3082    # was :3081
```

The kiosk is just a frameless browser — repointing the URL is the entire change. Restore to `:3081` when the UI work session is done so the baked version is what shows on the next OS boot.

## What this does NOT do

- **Does NOT replace the production `panel` service.** :3081 is still the baked placeholder rendered by the inline `server.js` heredoc in `docker-compose.yml`. `panel-dev` on :3082 is the live-edit surface.
- **Does NOT auto-bake into the next ISO build.** Once UI work is finished, the operator (or a baker agent) still needs to copy the relevant build output into `iso-build/airootfs/srv/sinister-panel/` for it to ship with a Mesh OS image.
- **Does NOT mutate the source repo's `node_modules`.** The container installs into a named Docker volume (`panel-dev-node-modules`), not the Windows-side `node_modules` directory. That keeps Windows-native installs (if any) and Linux-native installs from clobbering each other.
- **Does NOT survive `docker compose down -v`.** That flag wipes named volumes, including `panel-dev-node-modules`. Next `up` will re-run `npm install` (60-120 s).
- **Agents editing `.tsx` see changes in roughly 500 ms after save.** Not instant — there is a polling delay and a Next.js recompile step. Acceptable for live UI iteration; not appropriate for keystroke-by-keystroke games or animation timing tests.

## Bring-down

```bash
# Stop the container, keep the named volume (fast restart later):
docker compose -f docker-compose.yml -f compose.dev.yml stop panel-dev

# Stop and remove the container (keep volume):
docker compose -f docker-compose.yml -f compose.dev.yml rm -f panel-dev

# Nuke everything including the node_modules volume (next up re-installs):
docker compose -f docker-compose.yml -f compose.dev.yml down -v
```

## Composition with the hardened overlay

`compose.hardened.yml` applies ghost-server hardening (no-new-privileges, cap_drop, read_only roots, resource caps) to the production services. `panel-dev` is intentionally NOT hardened — dev servers need to write to disk, fork processes, and rebuild on the fly. Run them in **separate** invocations:

```bash
# Production stack (hardened):
docker compose -f docker-compose.yml -f compose.hardened.yml up -d

# Dev panel (additive, unhardened):
docker compose -f docker-compose.yml -f compose.dev.yml up -d panel-dev
```

Compose is happy to run both because the dev overlay only ADDS `panel-dev`; it does not redefine any service the hardening overlay touches.
