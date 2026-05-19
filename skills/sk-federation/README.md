# sk-federation — cross-installation agent federation (Ruflo fork)

> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19 :: forked from ruvnet/ruflo (MIT) ruflo-federation plugin
> **Status:** candidate (pending operator thumb per case-study `_shared-memory/case-studies/2026-05-19-sk-federation.md`)
> **Upstream snapshot:** `_shared-memory/external-imports/ruflo/plugins/ruflo-federation/`

## What it is

Multi-agent comms across machines — operator + Leo cross-machine collaboration with zero-trust security, PII gating, and compliance-grade audit trails. Five-tier trust model (UNTRUSTED → VERIFIED → ATTESTED → TRUSTED → PRIVILEGED), HMAC-signed envelopes, dual AI Defence gates, Byzantine consensus for state mutations, budget circuit breaker (ADR-097) with `maxHops` / `maxTokens` / `maxUsd` caps.

## Why Sanctum needs it

Sanctum's stated vision (per `WORKSTATION.md` + Sinister Vault rollout) is operator + Leo working on the same files at the same time without stepping on each other. The Vault gives shared storage; ruflo-federation gives the **communication layer** — how Leo's Claude session talks to operator's Claude session, how trust is established between machines, how PII doesn't leak.

Specific gaps closed:

- **Zero-trust handshake** — replaces ad-hoc "share auth-keys.json over Tresorit" with mTLS + ed25519 + trust scoring.
- **PII gate** — 14-type detection blocks Yurikey roster, snap.sinijkr credentials, etc. from federating accidentally. Per-trust-level policies (BLOCK/REDACT/HASH/PASS) match the operator-private rule from DIRECTIVES.
- **Budget circuit breaker** — `maxHops=8` + cost caps prevent runaway delegation loops between operator agent + Leo agent. Critical for "work forever" — without it, a feedback loop can burn $100/hr in API spend.
- **Compliance audit** — HIPAA / SOC2 / GDPR trails come standard; Sanctum can claim provenance even if Leo's lane changes.

## How Sanctum uses it (post operator-thumb)

1. Operator + Leo each install ruflo + ruflo-federation locally.
2. Operator's machine is `TRUSTED` for Leo, Leo's machine is `VERIFIED` for operator (operator stays the privileged source-of-truth).
3. Cross-machine inbox messages go through ruflo-federation transport instead of the file-based inbox (which only works on shared filesystems / Syncthing).
4. The existing `sinister-bus.delegate_to agent_name="<other>"` pattern gets a federation backend — same API, new transport, machine-aware.
5. Vault commits + audit events become federation-aware so operator can see Leo's contributions in real-time with cryptographic provenance.

## Dependencies

- Ruflo MCP registered.
- Each machine generates an ed25519 keypair (one-time, on first launch).
- Per-machine config at `_shared-memory/federation/<machine-id>.json` (gitignored; per-machine state).

## License + attribution

- Upstream: MIT.
- Sanctum fork: MIT.
- Snapshot: `_shared-memory/external-imports/ruflo/plugins/ruflo-federation/`.

## See also

- `_shared-memory/case-studies/2026-05-19-sk-federation.md` — verdict file
- `tools/sinister-vault/` — the Vault tier that pairs with federation comms
- `_shared-memory/knowledge/cross-agent-coordination.md` — same-machine pattern; federation extends it to multi-machine
- `_vault/auth-keys-DELIVER-TO-LEO.txt` — Leo's onboarding key (operator-private)
