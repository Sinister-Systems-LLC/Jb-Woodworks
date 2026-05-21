# Agent-Browser-Bridge Pattern (Forge PH15 doctrine)

> **Author:** RKOJ-ELENO :: 2026-05-21
> **Origin:** Sanctum Audit Agent TOP-5 #4 + Sinister Forge PLAN.md PH15. Documents the **WebSocket-host + browser-extension** architecture for when an agent needs to drive a real browser (DOM-level, not headless-Chromium-screenshot).

## When to use this pattern

The agent needs to:
- Drive a logged-in web session (e.g. Bumble web, IG DM inbox, Facebook Marketplace seller console)
- Read/write DOM state the page is computing client-side (React/Vue/Svelte SPAs)
- Stay logged in across multiple invocations without re-authenticating
- Avoid headless-browser fingerprint flags (Cloudflare / Akamai bot detection)
- Operate on the operator's OWN session, on the operator's OWN device

When NOT to use:
- Public scraping (use `requests` / Playwright headless)
- Single-page extraction (use Playwright + selectors directly)
- High-throughput parallel work (the extension is single-session per browser)

## Architecture (three components)

```
┌──────────────────────────────┐        ┌───────────────────────────────┐
│  Agent (Claude Code session) │        │  Operator's logged-in Firefox │
│  - calls bridge.send(cmd)    │  WS    │  (or Chromium/Edge)           │
│  - awaits bridge.recv()      │ <───>  │  + Sinister-Bridge extension  │
└──────────────┬───────────────┘ :7066  │  - listens on tab.* events    │
               │                        │  - injects content scripts     │
               │ HTTP/WS                │  - posts DOM mutations back    │
               v                        └─────────────────┬─────────────┘
┌──────────────────────────────┐                          │
│  bridge-host (Python/Node)   │ <────────────────────────┘
│  - WebSocket server :7066    │
│  - command queue + dedupe    │
│  - per-tab session affinity  │
└──────────────────────────────┘
```

### Component 1 — bridge-host (server)

Lives in `tools/sinister-browser-bridge/` (planned; not yet built). Responsibilities:
- WebSocket server bound to `127.0.0.1:7066` (local-only by default)
- Auth via `Authorization: Bearer <token>` (token regenerated per session, stored at `_shared-memory/sinister-browser-bridge-token.txt`)
- Maintains a queue of pending commands per browser tab
- Returns results to the calling agent via response WebSocket
- Logs every command + result to `_shared-memory/sinister-browser-bridge/transcripts/<UTC>-<tab>.jsonl` for replay + audit
- Reference: `tools/sinister-vault/INSTALL-MCP.md` for the auth-token pattern

### Component 2 — Browser extension (Manifest V3 web-ext)

Lives in `tools/sinister-browser-bridge/extension/` (planned). Responsibilities:
- Installs into Firefox via `about:debugging` (dev) or AMO (signed-prod)
- Background service worker connects to `ws://127.0.0.1:7066` on browser launch
- Listens for commands from the host (e.g. `click_selector`, `read_dom`, `fill_input`, `screenshot_visible`, `scroll_to`)
- Injects content scripts per-tab to execute DOM operations
- Posts results back via the same WebSocket
- All commands are explicitly enumerated — NO arbitrary JS injection (security)
- Per-domain allowlist enforced at the extension level (only operator-approved sites)

### Component 3 — Agent-side client library

Lives in `tools/sinister-browser-bridge/client/` (planned). Two surfaces:
- Python: `from sinister_browser_bridge import Bridge; b = Bridge(); b.send_to_tab(tab_id, "click", selector="#submit")`
- CLI: `sinister-browser-bridge click --tab <id> --selector "#submit"`

The agent calls these; the agent does NOT directly talk to the browser. Bridge-host is the only WebSocket peer.

## Why this beats Playwright-headless

| Concern | Playwright-headless | Agent-Browser-Bridge |
|---|---|---|
| Login persistence | Cookie jar must be saved/loaded; brittle to session-cookie rotation | Operator's real browser session; persists across reboots |
| Bot detection | Cloudflare / Akamai catch the headless fingerprint | Real Firefox profile; same fingerprint operator already uses |
| 2FA flows | Have to script TOTP entry | Operator handles 2FA in their own browser; bridge resumes after |
| Audit trail | Console logs | JSONL transcript per tab w/ full command + result |
| Lateral risk | A compromise = full Chromium DevTools control | Compromise limited to enumerated commands + allowlisted domains |
| Resource cost | Spinning up a full Chromium per task | Single browser open; per-tab session |

## Security posture

- **Local-only by default**: WebSocket binds `127.0.0.1`. Remote access requires explicit Tailscale tunneling.
- **Bearer-token auth**: regenerated per session.
- **Enumerated commands only**: extension never executes arbitrary JS; only the (~12) commands defined in the manifest.
- **Per-domain allowlist**: each tab's domain must be in `bridge-allowed-domains.json` operator-managed.
- **Transcript audit**: every command + result logged + grep-auditable.
- **No password storage**: bridge never sees the operator's credentials — operator logs in via the browser normally.

## Composes with

- **Forge PH15** (was: clone firefox-agent-bridge) — this doc replaces the clone-and-run plan; document-only per Sanctum Audit Agent TOP-5 #4 recommendation.
- **`projects/sinister-bumble-emu/`** — Bumble-web sessions that need real-session driving go through this bridge.
- **`projects/sinister-freeze/`** — once Joe-mode lands, Freeze's IG DM / FB Marketplace / TT DM connectors use this bridge for in-browser actions (read DMs, send drafts after Joe-approves).
- **`tools/sinister-vault/`** — auth token stored in Vault; per-session rotation enforced.
- **`automations/session-contracts.md`** — CONTRACT 3 AUP-RESPECT applies: only operator's OWN sessions, only operator-approved sites.

## When to revisit

- A new bot-detection technique defeats the real-browser approach → document mitigation + add to extension
- The agent needs to drive 5+ tabs in parallel → reconsider per-tab session affinity (move to per-tab worker)
- Operator wants a Chromium variant (Edge / Brave) → port the extension (Manifest V3 is largely portable)

## Status

📋 **Doc-only** as of 2026-05-21. Cloning + building `tools/sinister-browser-bridge/` deferred until a real use-case opens (Bumble-web lane re-opens, or Freeze v1 needs IG DM bridge).
