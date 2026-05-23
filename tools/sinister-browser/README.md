# Sinister Browser

> **Author:** RKOJ-ELENO :: 2026-05-23
> **License:** AGPL-3.0-or-later
> **Matrix:** jcode-feature-matrix.md row 26 (browser-bridge)
> **Status:** Layer A probe shipped (v0.1.0); Layer B/C/D deferred per `_shared-memory/knowledge/browser-bridge-integration-shape-2026-05-23.md`.

## What this is

Sinister wrapper around upstream [firefox-agent-bridge](https://github.com/1jehuang/firefox-agent-bridge) (MIT). We do NOT clone the Rust source. We talk to the running upstream bridge over its WebSocket interface (`ws://127.0.0.1:8766`) and document the integration shape so future layers can be added incrementally.

See `_shared-memory/knowledge/browser-bridge-integration-shape-2026-05-23.md` for the full integration doctrine.

## Layer A — probe (v0.1.0)

Connectivity check. Tells you whether the upstream bridge is installed + Firefox is running + the extension is connected.

```bash
sinister-browser probe
# or, without install:
python -m sinister_browser probe
```

Exit codes:

| Code | Meaning |
|---|---|
| 0 | bridge alive — TCP listener on :8766 + WebSocket handshake completes |
| 2 | bridge not installed / Firefox not running — TCP connect refused/timeout |
| 3 | bridge installed but unreachable — TCP connected but no valid WebSocket handshake response (something else on the port, or the bridge is broken) |

Options:

```bash
sinister-browser probe --host 127.0.0.1 --port 8766 --timeout 3.0
```

stdlib-only. No `websockets` / `websocket-client` dep — does a minimal HTTP Upgrade handshake by hand.

## What's not in v0.1.0

- Layer B (`api.py`) — pythonic action surface mirroring the ~25 upstream actions (`navigate` / `click` / `type` / `fillForm` / `getContent` / `screenshot` / `evaluate` / ...). Adds proper WebSocket framing (RFC 6455 client). Deferred until operator wants live browser-as-tool flows.
- Layer C — Forge `/browser` slash + Term `/jcode-browser` alias.
- Layer D — `skills/sinister-browser/SKILL.md` mirror.

## Install

```bash
cd "D:/Sinister Sanctum/tools/sinister-browser"
pip install -e .
```

## Composability

- `tools/sinister-login/` — credential surface for Layer B's `evaluate` action.
- `tools/sinister-usage/` — Layer A probe counts as a "configured but inactive" provider in `sinister usage matrix`.
- `projects/sinister-forge/` — Layer C lands here (`forge/commands.py` slash table).
- `projects/rkoj/` — optional `/api/browser/screenshot` REST endpoint mirroring `/api/diagrams` shape.

## What stays operator-gated

- Upstream XPI install (operator clicks "Install Add-on From File...")
- `HKCU\Software\Mozilla\NativeMessagingHosts\firefox_agent_bridge` registry write (R3 reversibility)
- `FAB_AUTOLOGIN_REQUIRE_FINGERPRINT=true` env var (Yurikey-required-for-autologin)

Sinister Browser NEVER writes the registry or installs the XPI — the operator owns those surfaces.
