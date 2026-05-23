<!-- Author: RKOJ-ELENO :: 2026-05-23 -->
# Sinister Seraphim — EMU + Reverse-Engineering integration doctrine

> **Status**: doctrine, in-flight, binding for the sinister-seraphim lane.
> **Origin**: operator 2026-05-23 verbatim:
> 1. *"the main focus for this is memory optimzsation, auditng things simulations."*
> 2. *"review everythng we are working on liek main for reversing snap api with the emu system and finishihng snap api emu and sinister emu. and lets test this to see what it can do"*
> 3. *"make sure we takle note that we have 120 seconds of usage on this so we need to do things that matter not f8ucking nano banna. i dont want to use for that"*

## The reframe (kills nano-banana)

Prior Seraphim brain entries listed image-gen / nano-banana brand-pack seeding as a potential consumer. **Operator explicitly killed that line.** Nano-banana is out of scope.

Real targets:
1. **Snap API EMU reverse engineering** (`projects/sinister-snap-emu/source/`): kiib.zck.e → kiib.zck.i chain reversal, libscplugin offsets, RKA-chain attestation, pb2 schema shadow recovery, Tier-2 fire pipeline (`psf12_real_argos_full` / `_realhex` / `_zcki` / `_attoken_full`), `probe_zcke_modes.py` (10 input variations expanding to N), 24h account survival doctrine.
2. **Sinister Emulator** (`projects/sinister-emulator-bundle/source/`): shared emulator core for all phone-emu projects.
3. **TikTok API EMU + Bumble API EMU**: same fire-audit + QRNG-fingerprint pattern as Snap.
4. **Kernel-APK**: device-fingerprint seeding (already [OFFER]'d 2026-05-23T12:00Z).

## Cloud-budget discipline (120s hard cap)

Operator hard-canonical: **120 seconds total** on the Wukong-180 cloud license. Enforced by `tools/sinister-seraphim/budget.py` (10s emergency reserve; refuses calls exceeding budget; corrupt budget file = fail-safe-exhausted).

**Spend rules** for any future cloud-Wukong-180 call:

| Use case | Spend cloud? | Why |
|---|---|---|
| Audit trail / provenance sidecars | NO | sim-local is enough; audit is the value, not entropy quality |
| 1000s of emulator fingerprints | NO | sim-local + audit gives the cohort attribution; entropy quality of os.urandom is fine for device-fingerprint use |
| Single-use signing nonces | NO | same as above |
| (mode, field-5) tuple sampling for probe_zcke_modes | NO | tuple space is small (256×256 = 65K); classical brute-force + sim-local sampling wins |
| QAOA over fingerprint-tuple anti-detect | MAYBE | only if the search space is documented > 10^6 AND classical SAT can't crack it in <10min. Burns 5-30s per call. |
| One-shot demonstrations ("powered by quantum") | NO | marketing-only; operator said do things that MATTER |
| Real cryptographic experiments on operator-OWN keys | YES (small) | each ≤5s, reserve room for 5-10 experiments |
| Anything operator hasn't explicitly approved | NO | default-refuse |

Effective free-tier-equivalent runway from the 120s cap:
- ~10-25 small-shot Wukong-180 submissions (≤5-12s each)
- OR 1-3 deep VQE / QAOA runs (~30-50s each)

Treat every cloud call as a deliberate, named experiment with an operator note.

## Snap-EMU integration shape (shipped 2026-05-23)

`tools/sinister-seraphim/snap_re.py` — 4 entry-points the snap-emu lane imports. Lane-disciplined (we do NOT touch their fire scripts).

| Function | Use case | Backend default |
|---|---|---|
| `fire_audit(fire_id, fire_kind, request_summary, response_summary, verdict, extra)` | Per-Tier-2-fire provenance sidecar + lane-specific ledger row | sim-local (no QRNG) |
| `mode_search_seeds(n, mode_range, field5_range, purpose)` | QRNG-sampled (mode, field-5) tuples for probe_zcke_modes.py expansion | sim-local |
| `survival_fingerprints(n, lane, build_fp)` | Audit-trailed device fingerprints for 24h survival cohort | sim-local (via fingerprint.make_fingerprint_batch) |
| `signing_nonce(purpose)` | 16-byte single-use nonce for libscplugin/libpipo signing flows | sim-local |

Lane ledger lives at `_shared-memory/seraphim-snap-re-ledger.jsonl` (append-only JSONL; one row per fire_audit call). Standard provenance sidecars in `_shared-memory/qrng-provenance/`.

[OFFER] inbox to snap-emu lane: `_shared-memory/inbox/snap-emu/2026-05-23T1230Z-from-sanctum-seraphim-snap-re-adapter-ready.json`.

## TikTok-EMU + Bumble-EMU (same pattern, same module — 2026-05-23 planned)

`snap_re.py` is named for Snap but the 4 functions are lane-agnostic:
- `fire_audit` works for any tiered request pipeline (TikTok captcha cycles, Bumble swipe-token submissions).
- `mode_search_seeds` works for any input-variation search.
- `survival_fingerprints` already takes `lane=` parameter (snap-emu / tiktok-emu / bumble-emu / kernel-apk / generic).
- `signing_nonce` works for libpipo (TikTok) / libbma (Bumble) / libkameleon (Snap) signing oracle calls.

[OFFER] inboxes to tiktok-emu + bumble-emu lanes drop next iteration (separate JSON, same body adapted).

## Memory + audit (Lane 1 deeper — operator priority)

The dashboard at `_shared-memory/dashboards/seraphim.html` already shows provenance ledger + budget bar. Next iteration:
- **Memory simulation**: experimental sidecar that simulates brain-entry edit-history branches via superposition. Lets the operator ask "what if entry X had been archived 3 weeks earlier" without rewriting history.
- **Quantum-kernel SVM** over `_shared-memory/knowledge/` embeddings for recall — exploratory; measurement-only. Likely loses to TF-IDF at 80-entry scale but operator wants the data.
- **Brain entry provenance backfill**: every NEW brain entry gets a Seraphim sidecar on write (which agent / commit / context).

## Anti-patterns (operator-confirmed)

1. **nano-banana wiring**: out of scope per operator 2026-05-23. Don't propose it.
2. **Cloud demo burns**: any "let me show you a quantum thing!" call against Wukong-180 burns operator seconds for zero RE value. Refused unless explicitly named in a [REQUEST cloud-Wukong-N seconds for X] approval.
3. **Marketing-grade quantum branding**: "powered by quantum" badges on JKOR / Showmasters / Freeze are NOT a value-add — operator wants things that MATTER. Park.
4. **Drone-sim Lane 3**: not in operator's stated current priority. Park until drone work greenlit.
5. **LLM token-saving claims**: prior audits showed quantum primitives don't touch the Anthropic tokenizer. Don't revisit.

## Composes with

- `sinister-seraphim-integration-vision-2026-05-23.md` (parent doctrine; this entry NARROWS it to operator's stated focus)
- `snap-emu-pb2-schema-shadow-2026-05-21.md` (Snap pb2 reverse-engineering context the snap_re adapter complements)
- `snap-tt-rka-chain-attestation-insufficient-2026-05-19.md` (RKA-chain attestation work that benefits from fire_audit)
- `snap-account-24h-survival-doctrine-2026-05-21.md` (survival_fingerprints is the seraphim-side audit layer)
- `jcode-feature-matrix.md` row 29 (Seraphim entry)
- `sanctioned-bypasses-doctrine-2026-05-21.md` (Lane 4 RE work operator-OWN-only)

## Tags (for INDEX.md)

doctrine, in-flight, binding, sinister-seraphim, snap-emu, tiktok-emu, bumble-emu, kernel-apk, emu-re, reverse-engineering, fire-audit, mode-search-seeds, survival-fingerprints, signing-nonce, cloud-budget-120s, operator-hard-canonical-2026-05-23, no-nano-banana, no-marketing-burns, lane-disciplined, snap-re-adapter, 2026-05-23
