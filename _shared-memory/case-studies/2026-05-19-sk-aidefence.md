# Case study :: sk-aidefence (forked from ruvnet/ruflo)

> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19T13:30Z
> **Tags:** review, external, ruflo, sk-aidefence, security, pii, prompt-injection, candidate

## 1. What it is

`ruflo-aidefence` provides AI safety scanning (prompt-injection / jailbreak / adversarial content), PII detection (emails / SSNs / API keys / sensitive patterns), adaptive threat learning (confirmed threats train defenses), and threat classification with confidence scores. Plus the **runtime hardening pairing** in ruflo 3.6.25+: loader-hijack denylist (rejects `LD_PRELOAD` / `LD_LIBRARY_PATH` / `LD_AUDIT` / `DYLD_INSERT_LIBRARIES` / `DYLD_LIBRARY_PATH` / `DYLD_FALLBACK_LIBRARY_PATH` / `DYLD_FORCE_FLAT_NAMESPACE` / `NODE_OPTIONS` / `NODE_PATH` at the `terminal_create` MCP boundary — these are functionally RCE vectors); file mode 0600 + dir mode 0700 on session/terminal/memory stores via `fs-secure.writeFileRestricted`; AES-256-GCM encryption-at-rest opt-in via `CLAUDE_FLOW_ENCRYPT_AT_REST=1` with magic-byte (`RFE1`) backward-compat sniff.

Sanctum fork at `skills/sk-aidefence/`; upstream at `_shared-memory/external-imports/ruflo/plugins/ruflo-aidefence/`.

## 2. Strengths

- **Closes the `--dangerously-skip-permissions` gap.** Every Sanctum launcher spawn runs Claude with no permission prompts (operator authorized). Aidefence adds a runtime input gate so that's not the only safety layer.
- **Loader-hijack denylist is critical.** `NODE_OPTIONS` injection is a documented RCE; ruflo 3.6.25+ closes it at the MCP boundary. Without this, a malicious inbox message that triggers a `terminal_create` could inject `NODE_OPTIONS=--require ./evil.js` and get arbitrary code execution.
- **File-mode 0600 / dir-mode 0700** is exactly the discipline Sanctum's `_vault/` directory wants (operator-private). Today auth-keys.json may be 0644-ish; aidefence enforces tighter.
- **PII detection pairs perfectly with `secrets-redaction-policy.md`** (parent-private). Same intent, real-time. Yurikey / capsolver / sk-ant-* patterns get scrubbed before being logged or federated.
- **Adaptive learning loops into the brain.** Confirmed injection patterns become brain entries. Sanctum gets smarter at recognizing attacks over time.
- **AES-256-GCM at-rest** is a free win when paired with `SINISTER_VAULT_PASSPHRASE`. Codec layer doesn't currently encrypt memory.db; this would.

## 3. Weaknesses + risks

- **False positives on legitimate operator content.** Yurikey strings appear in legitimate Sanctum docs (e.g., the case-study writeups themselves). If the PII detector is too eager, it may redact content that's already operator-authored.
- **Adaptive learning is a feedback loop.** Confirmed threats train; misclassified false positives also train. Without a human-review gate, the detector can drift toward over-blocking.
- **Loader-hijack denylist may break legitimate tooling.** Some build pipelines use `NODE_OPTIONS=--max-old-space-size=...` legitimately. Need to whitelist Sanctum's own build scripts.
- **At-rest encryption breaks ad-hoc tooling.** If operator greps `memory.db` directly today, post-encryption that file is opaque. Adds a step.
- **Performance overhead.** Every inbound inbox message + every cold-start phrase scanned = added latency. Negligible per-call but cumulative on busy days.
- **No formal security audit.** MIT-licensed defensive code that itself hasn't been pen-tested. Sanctum trusts the maintainers.

## 4. Better-than-found proposal (~60 LOC outline)

1. **Sanctum-aware allowlist (~20 LOC)** — extends aidefence's denylist with a per-Sanctum allowlist for legitimate operator-authored content patterns (Yurikey roster references in case-studies, sk-ant-* in env-vars cheat sheet, etc.). Tagged at the file level so docs/ paths get more leeway than inbox messages.
2. **Brain integration (~15 LOC)** — confirmed-threat callback writes to `_shared-memory/knowledge/threat-<UTC>.md` instead of a private store. Brain compounds; operator can audit.
3. **Codex pipeline PII wrapper (~15 LOC)** — wraps `codex-companion/codex.py` so that submission content passes through aidefence PII scrub before hitting OpenAI. Prevents accidental secret exfil even on legitimate review.
4. **Build-script `NODE_OPTIONS` allowlist (~10 LOC)** — extends the loader-hijack denylist with a whitelist of Sanctum's own `automations/window-manager/build-sanctum-console.sh` patterns. Sanctum-specific tooling keeps working.

Net: ~60 LOC. Aidefence stays canonical; Sanctum-side glue tunes for the actual workload.

## 5. Recommendation

**KEEP-WITH-CHANGES.** The `--dangerously-skip-permissions` posture means Sanctum needs every defense layer it can get. Loader-hijack denylist alone is enough to justify the fork; PII + adaptive learning are bonus.

Sequence on thumbs-up:
1. Land the allowlist + brain integration adapters (smallest, validates the workflow).
2. Test on a known false-positive corpus (case-study writeups + env-vars cheat sheet).
3. Wire the Codex PII wrapper once smoke is green.
4. Enable `CLAUDE_FLOW_ENCRYPT_AT_REST=1` last (operator decision per `docs/ENV-VARIABLES.md`).

Codex peer-review: **deep tier** (touches security boundary, > 50 LOC, auth-adjacent). Standing rule mandates this.

---

## Operator decision

(blank — operator drops 👍 / 👎 / free text)
