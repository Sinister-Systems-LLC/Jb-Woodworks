# Case study :: sk-federation (forked from ruvnet/ruflo)

> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19T13:30Z
> **Tags:** review, external, ruflo, sk-federation, multi-machine, candidate

## 1. What it is

`ruflo-federation` is the comms layer for multi-machine multi-agent AI. Zero-trust cross-installation federation: mTLS + ed25519 identity proofing, PII pipeline (14-type detection, per-trust-level policies BLOCK/REDACT/HASH/PASS, adaptive confidence calibration), 5-tier trust model (UNTRUSTED → VERIFIED → ATTESTED → TRUSTED → PRIVILEGED with behavioral scoring), compliance modes (HIPAA / SOC2 / GDPR audit trails), HMAC-signed message envelopes with dual AI Defence gates, Byzantine BFT consensus for state mutations, budget circuit breaker (ADR-097) with `maxHops` (default 8) + `maxTokens` + `maxUsd` caps plus constant-string error codes (`HOP_LIMIT_EXCEEDED` / `BUDGET_EXCEEDED`) to defang runaway delegation.

Sanctum fork at `skills/sk-federation/`; upstream at `_shared-memory/external-imports/ruflo/plugins/ruflo-federation/`.

## 2. Strengths

- **Direct match to Sanctum's operator+Leo multi-machine collaboration vision** (per `WORKSTATION.md` + Sinister Vault rollout). The Vault gives shared storage; this gives the comms layer.
- **Budget circuit breaker is the killer feature.** "Work forever" without per-call cost caps is how API bills explode. ADR-097's hop+token+usd caps are exactly what Sanctum's existing `cross-agent-coordination` patterns are missing.
- **PII pipeline pairs with Sanctum's existing `secrets-redaction-policy.md`** (parent-private). Same intent, finer granularity. Yurikey roster / snap.sinijkr credentials / auth-keys can be marked BLOCK at the comms boundary so they never accidentally federate.
- **Compliance audit trails come standard.** If Sanctum ever needs to demonstrate provenance (which lane shipped which artifact when), HIPAA/SOC2/GDPR-grade trails are over-spec but free.
- **MIT license + thoughtful API design.** Trust scoring is observable — operator can grep `_shared-memory/federation/<machine-id>.json` to audit.

## 3. Weaknesses + risks

- **Single-machine for now.** Operator + Leo on different machines isn't the day-1 use case (they share via Syncthing today). Federation pays off when the second machine actually exists. Today this is forward investment.
- **Key management overhead.** ed25519 keypairs need rotation, revocation, distribution. Lane discipline says master never touches `_vault/`; federation adds a second class of operator-managed secrets (per-machine keys). One more thing to lose.
- **HIPAA/SOC2/GDPR modes** are over-spec for current Sanctum workloads. They add audit-log overhead even when not "compliance mode" — minor but real.
- **Byzantine BFT consensus is heavy.** Operator + Leo (n=2) doesn't need BFT; majority quorum suffices. For 2-machine setups, BFT is theatre. Plugin doesn't expose a "skip BFT" mode trivially.
- **Cross-machine clock drift** — without NTP discipline, signed envelopes with TTL stamps can reject as expired. Sanctum doesn't currently enforce NTP.

## 4. Better-than-found proposal (~70 LOC outline)

1. **2-machine setup template (`tools/sanctum-federation-setup/`) ~30 LOC** — operator runs once, generates keypair, writes `_shared-memory/federation/<machine-id>.json` (gitignored), publishes the public key to a shared Vault repo so Leo can authorize. Captures Sanctum's specific 2-party scope.
2. **Budget defaults bridge ~20 LOC** — wraps `/federation send` to apply Sanctum's $1/spawn + $5/day operator-set ceiling. Override per-call but default is conservative.
3. **PII denylist seeded from `secrets-redaction-policy.md` ~10 LOC** — parses the parent-hub policy + builds a Yurikey / capsolver / snap.sinijkr / sk-ant-* denylist that federation enforces at outbound gate.
4. **NTP gate ~10 LOC** — federation startup checks system clock vs `time.windows.com`; refuses to send if skew > 5 s. One-time, gates the comms loop.

Net: ~70 LOC adapters. Federation upstream stays vendor; Sanctum-side glue captures operator's specific scope.

## 5. Recommendation

**KEEP-WITH-CHANGES, but parked until 2-machine.** The capability is high-value when Leo's machine is online; today it's forward investment. Operator can:

- **A (recommended)**: Land the README + case-study now; defer the actual fork wiring to when Leo onboards. Documentation cost: zero. Code cost: deferred.
- **B**: Land the full fork now, exercise it on the single machine via loopback for smoke testing. Costs ~70 LOC of adapter work now, ~0 incremental when Leo comes online.

I lean toward **A** — Sanctum has higher-leverage forks (swarm + vector-memory + observability) that pay off immediately. Federation waits.

---

## Operator decision

(blank — operator drops 👍 / 👎 / free text. Recommendation: "park, revisit when Leo is online" is also a valid thumbs-up alternative.)
