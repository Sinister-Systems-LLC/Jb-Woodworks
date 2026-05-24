# dashboard — Sinister iMessage Bridge

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Phase:** P0 (scaffold). Runs locally against the canned chat.db or against the real farm via bridge_daemon.

## Design doctrine

Per CLAUDE.md hard-canonical 2026-05-24 15:44Z — **EXPAND, never fork**:
- Inherits `tokens/globals.css` + `.lg-*` Liquid Glass classes from `../../sinister-dashboard-skeleton/dashboard-skeleton/` via Tailwind 4 `@import` (see `app/globals.css`).
- Inherits TypeScript primitives via `tsconfig.json` `@skeleton/*` path alias when needed.
- **NO `--accent` override.** This lane is a LetsText surface (iMessage = LetsText product), so the skeleton's default iOS-blue `#0A84FF` (literally the iMessage dark-mode bubble color) IS the brand. Per operator directive 2026-05-24 16:08Z: *"this needs the letstext branding and look"*. Other Sinister-fleet surfaces (sanctum / forge / etc) flip to purple `#c084fc`; this one stays iOS-blue.
- If a primitive is missing in the skeleton, ADD IT TO THE SKELETON FIRST then consume here. Never roll a one-off.

## First-time setup

```bash
cd dashboard
npm install
```

Then start the bridge_daemon in another terminal (uses the canned fixture by default):

```bash
cd ../source
python -m bridge_daemon.bridge --chatdb fixtures/canned-chat.db
```

Then start Next.js dev:

```bash
cd ../dashboard
npm run dev
```

Opens at http://127.0.0.1:3171. The `/api/*` rewrites proxy to `http://127.0.0.1:8731`.

To point at a different bridge_daemon URL: `BRIDGE_DAEMON_URL=http://otherhost:8731 npm run dev`.

## Routes

| Path | Role |
|---|---|
| `/` | Status — daemon health, polled every 5s |
| `/threads` | Thread list — all chats in the chat.db, sorted by last-read |
| `/threads/[chatId]` | Single thread — iMessage-style bubble layout |
| `/compose` | Compose form — dry-run + live send (live disabled until P2) |

## Wired to bridge_daemon

| Dashboard call | bridge_daemon endpoint |
|---|---|
| `api.status()` | `GET /status` |
| `api.threads()` | `GET /threads` |
| `api.threadDetail(id)` | `GET /threads/{id}/messages` |
| `api.send(req)` | `POST /send` |

Types live in `lib/types.ts`; keep in sync with `source/bridge_daemon/bridge.py`.

## Per-phase UI gating

- P0 — `/compose` Send button is disabled (only dry-run works). The status page shows `phase: P0-scaffold`.
- P1 — Status page shows `farm_ssh: up` when farm is connected.
- P2 — Compose live send unlocks (changes the `PHASE` constant in `app/compose/page.tsx`).
- P3 — Tail-alive flips true; SSE event stream lights up in the right rail.
- P4 — Auto-respond rules surface in `/compose` as a separate tab.

## Doctrine audit

Run the skeleton's doctrine-audit against this lane:

```bash
npm run doctrine-audit:strict
```

Catches:
- `lucide-react` imports (banned)
- raw hex outside `lib/theme.ts` (one violation expected: the per-lane accent override in `app/globals.css`; whitelist via `// doctrine-audit:allow-hex` if needed)
- banned phrases
- emoji bytes in chrome
- raw `<button>` outside skeleton's `components/ui/`
- pill regression (`<Button rounded-md/lg/xl>`)

## Production parity TODO

When the dashboard moves from P0 dev to always-on operator surface:
- Wrap with NSSM / systemd
- Add Bearer-token auth on `/api/send` proxy (matching bridge_daemon's P4 token gate)
- Container build (single Docker image: dashboard + bridge_daemon co-resident on operator workstation)
- SSE wiring on `/threads/[chatId]` (live message tail, replacing the one-shot fetch)
