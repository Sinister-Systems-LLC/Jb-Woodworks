# sk-aidefence — AI safety + PII + prompt-injection defense (Ruflo fork)

> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19 :: forked from ruvnet/ruflo (MIT) ruflo-aidefence plugin
> **Status:** candidate (pending operator thumb per case-study `_shared-memory/case-studies/2026-05-19-sk-aidefence.md`)
> **Upstream snapshot:** `_shared-memory/external-imports/ruflo/plugins/ruflo-aidefence/`

## What it is

AI safety scanning + PII detection + prompt-injection defense + adaptive threat learning. Plus a runtime hardening pairing (Ruflo 3.6.25+): loader-hijack denylist (rejects `LD_PRELOAD` / `NODE_OPTIONS` / `DYLD_*` at terminal_create boundary), file mode 0600 / dir mode 0700 enforcement on session+terminal+memory stores, AES-256-GCM encryption-at-rest with magic-byte sniff.

## Why Sanctum needs it

Sanctum runs `--dangerously-skip-permissions` on every spawn (operator-authorized via the launcher). That means Claude can shell out, read sensitive files, push to git. The `auditor` bot does drift detection + secret pattern matching — that's good for at-rest scanning. ruflo-aidefence adds the **runtime input** gate:

- **Prompt injection detection** — every inbound inbox message + every cold-start phrase is scanned before the agent acts. Operator's three Desktop launchers (Sinister / LetsText / JOKR) inject phrases; aidefence ensures those aren't compromised.
- **PII detection (14 types)** — pairs with the `secrets-redaction-policy.md` in the parent hub. Auto-redacts emails / SSNs / API keys / Yurikey roster patterns in logs before they hit `_shared-memory/`.
- **Adaptive learning** — confirmed threats train the detector. Pairs with the Sanctum brain (`knowledge/`) — discovered injection patterns become brain entries.
- **Runtime hardening** — loader-hijack denylist closes RCE vectors specific to Claude Code's terminal_create flow. Critical when `--dangerously-skip-permissions` is the default.

## How Sanctum uses it (post operator-thumb)

1. `auditor` bot grows a "live scan" mode: each inbox message + each launcher cold-start phrase passes through aidefence first.
2. PII detector wraps the codex-companion peer-review pipeline — never sends sensitive content to OpenAI even on legitimate review.
3. `_shared-memory/auto-push.log` gets a PII-redaction pass before any git commit + push.
4. Operator sets `CLAUDE_FLOW_ENCRYPT_AT_REST=1` (per docs/ENV-VARIABLES.md addition) → memory.db + sessions + terminal-history go AES-256-GCM at rest.

## Dependencies

- Ruflo MCP registered.
- Ruflo 3.6.25+ (auto-managed by `ruflo@latest`).
- Optional: `CLAUDE_FLOW_ENCRYPT_AT_REST=1` for at-rest encryption.

## License + attribution

- Upstream: MIT.
- Sanctum fork: MIT.
- Snapshot: `_shared-memory/external-imports/ruflo/plugins/ruflo-aidefence/`.

## See also

- `_shared-memory/case-studies/2026-05-19-sk-aidefence.md` — verdict file
- `bots/agents/auditor/` — the existing at-rest secret-scan bot; aidefence adds runtime
- `tools/codex-companion/codex.py` — peer-review pipeline that gets a PII-redact wrapper
- `_shared-memory/knowledge/codex-companion-usage.md` — the standing rule that triggers Codex; aidefence makes it safer
- `docs/ENV-VARIABLES.md` — add `CLAUDE_FLOW_ENCRYPT_AT_REST` once fork lands
