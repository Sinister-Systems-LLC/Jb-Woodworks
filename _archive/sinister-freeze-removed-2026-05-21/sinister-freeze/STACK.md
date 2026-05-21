# Sinister Freeze :: Tech-Stack Decision-of-Record

> **Author:** RKOJ-ELENO :: 2026-05-21
> **Source:** `_shared-memory/plans/sinister-freeze-2026-05-21/deep-research.md` §6
> **Status:** ✅ locked for MVP; V2+ migration points noted

## TL;DR

**FastAPI on `:5079` + SQLite (v0) → Postgres on Hetzner (v2) + PWA (React + Vite + Tailwind, Sanctum purple) + `sinister-freeze` CLI + Telegram bot + Claude API (Sonnet 4.6 / Haiku 4.5) + Whisper local + GPT-4o vision (optional).** Local-first on Joe's PC v0; multi-tenant cloud v2.

## Backend

### Pick: **FastAPI** (NOT Flask)

| Decision | Rationale |
|---|---|
| FastAPI | Joe will hit it from 3+ clients (desktop PWA, Telegram bot, iPhone PWA). FastAPI async I/O delivers 15-20k req/s vs Flask 2-3k [19]. Built-in Pydantic validation. Auto-OpenAPI. Fan-out to Anthropic + Cox + FB Graph + IG Graph + Gmail concurrent. |
| Port `:5079` | Adjacent to Sinister Vault `:5078`. Fits the Sanctum services map. |
| Keep Flask | Only for the existing Forge bridge at `:5078` (already shipped commit `1e5817a`). Don't migrate. Freeze is its own service. |
| Workers | Single-worker v0 (Joe's PC). Uvicorn standalone. Scale to gunicorn + uvicorn workers v2 on Hetzner. |
| Background jobs | `apscheduler` for nightly briefs / cron-style. RQ + Redis if queue depth becomes real (V2+). |

## Frontend

### Pick: **PWA-first** (React + Vite + Tailwind + Sanctum purple) + **`sinister-freeze` CLI**

| Decision | Rationale |
|---|---|
| PWA | One codebase, two surfaces (iPhone + desktop Chromium). Installs as app on both. No Electron bloat. Microsoft Store distribution path if needed [32]. |
| React + Vite + Tailwind | Sanctum precedent (Panel). Fast dev iteration. Tailwind utility classes match Sinister purple system. |
| Sanctum purple system | `#7A3DD4` primary + black background + dim cyan secondary. Cascadia Code for code; Mona Sans for UI body. Vault Boy iconography. |
| `sinister-freeze` CLI | Mirrors `sterm` UX. Power-user surface: voice memo upload, manual brief generation, quick lookups, debug. Python+prompt_toolkit (proven by sterm PH1-PH6). |
| React Native | **Deferred to V2.** PWA delivers 80% of native UX; native only needed for true push (V2 multi-tenant). |
| Electron | **Rejected.** Bloat (Chromium bundle 200MB+) for no benefit over PWA-in-Chromium-shell. |

## Database

| Stage | DB | Where | Migration trigger |
|---|---|---|---|
| **v0** | SQLite | `~/.sinister-freeze/freeze.db` on Joe's PC | — |
| **v1** | SQLite + write-through to Sinister Vault `:5078` daemon | Joe's PC + nightly backup to Sanctum vault | Joe has 2+ devices to sync |
| **v2** | Postgres (mirrors Sinister Panel pattern) | Hetzner | Multi-tenant rows w/ `dealer_id` + `salesperson_id` |

**Schema versioning:** every table carries `schema_version` field per `forever-expanding-modular-architecture-doctrine.md`. Migrations via Alembic.

## AI providers

| Use case | Model | Why |
|---|---|---|
| Email + DM drafts (high-touch) | **Claude Sonnet 4.6** | Concierge tone fits luxury; reliable instruction-follow; sane cost per turn |
| DM triage (Hot/Tire-Kicker/Fan/Spam) | **Claude Haiku 4.5** | Cheap + fast; classification doesn't need Opus depth |
| Post-drive voice-memo → structured CRM row | **Whisper (local) + Claude Sonnet 4.6** | Whisper local = privacy; Sonnet for structure |
| Photo analysis (damage detect, listing-quality score) | **GPT-4o vision** (optional; toggle-off if Joe wants no third-party) | OpenAI vision currently best-in-class for car damage; can swap to Claude-vision when parity lands |
| Allocation-strategy notebook (V2 deep reasoning) | **Claude Opus 4.7** | Multi-client history + Ferrari-allocation reasoning benefits from depth |

**Routing:** `automations/agent-host-routing.md` gets a `sinister-freeze` row (Sonnet primary, Haiku triage fallback).

## Comms layer (channel adapters)

| Channel | Library | Auth | Send-gate |
|---|---|---|---|
| Telegram bot | `python-telegram-bot` | Bot token in vault | Joe-side: full; Frost outbound: Joe-confirmed first |
| Gmail | `google-auth-oauthlib` + Gmail API | Joe's OAuth (read-only v0; send-with-Joe-click v1) | Always Joe-confirmed before send (JOE-SAFETY) |
| Instagram | Meta Graph (Joe's personal Business or Creator account) | Long-lived token in vault | 24h messaging window honored; 200 DM/hr cap |
| Facebook Marketplace | Meta Graph (same as IG) | Same | Same |
| TikTok | TikTok Business API (limited) + manual paste fallback | Token in vault | Joe pastes for now (TikTok API send is weak) |
| SMS (V2) | Twilio | API key in vault | TCPA-strict: written consent per number; opt-in confirmed |

## Auth

| Stage | Mechanism |
|---|---|
| **v0** | Single-user (Joe's PC, local SQLite, no auth — Windows account is the gate) |
| **v1** | Local FastAPI + cookie-session (Joe's PC + iPhone over Tailscale to Joe's PC) |
| **v2** | OAuth + magic-link (multi-tenant: Joe + Ferrari of Winter Park colleagues) |

## Voice (post-test-drive memos)

- **Whisper local** (faster-whisper Python pkg) — runs on Joe's PC; no audio leaves
- 30-second baseline transcription target on commodity GPU/CPU
- Output: structured Claude prompt → CRM row + draft follow-up

## Imaging (photo prep, listing set generation)

- **GPT-4o vision** for analysis (object detect, damage detect, photo-quality score)
- **Stable Diffusion XL** or **Pillow + rembg** local for background swap + plate blur (no third-party for actual generation)
- 18-shot listing set takes 60-90 seconds per car (vs 30+ minute manual today)

## Infrastructure

| Stage | Where | Notes |
|---|---|---|
| **v0** | Joe's PC | Single-user; Windows; FastAPI single-worker; SQLite |
| **v1** | Joe's PC + iPhone over Tailscale | Phone PWA hits Joe-PC FastAPI through Tailscale tunnel |
| **v2** | Hetzner (mirrors Sinister Panel pattern) | Multi-tenant; Postgres; nginx; Caddy TLS |

## Composes with

- `PLAN.md` — phases use this stack
- `FEATURES.md` — every feature targets MVP/V1/V2 tier per stack readiness
- `PERSONA-FROST.md` — UX layer sits on top of this stack
- `COMPLIANCE.md` — TCPA/CAN-SPAM/Meta enforcement at the bridge layer of every channel adapter
- `automations/agent-host-routing.md` — provider routing row for `sinister-freeze`
- `tools/forge-memory-bridge/` — Freeze's memory namespace (`freeze`) backed by this bridge
- `tools/sinister-vault/` — secrets storage (Telegram token, IG token, Twilio key, Joe's Gmail OAuth refresh token)
- `tools/sinister-browser-bridge/` — eventual IG/FB DM bridge when Meta Graph API insufficient (per `agent-browser-bridge-pattern.md`)

## Open decision queues

- **Stable Diffusion XL vs OpenAI DALL-E 3** for the generative image work? — leaning SDXL local (data sovereignty); evaluate post-MVP
- **Cox API access** for VIN history + cross-dealer inventory (feature #40)? — operator must confirm Cox developer account
- **Twilio vs MessageBird** for V2 SMS? — Twilio per industry precedent + better TCPA documentation
