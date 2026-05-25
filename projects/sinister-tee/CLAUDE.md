# CLAUDE.md — sinister-tee (keybox sourcing, generation, fitness-testing for PI 3/3)

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Lane slug:** `sinister-tee`
> **Branch:** `agent/sinister-tee/<topic>` (cut from `main`)
> **Accent:** purple (Sinister-fleet standing color)
> **Sibling lanes:** `sinister-rka` (server) · `sinister-kernel-apk` (real-phone consumer) · `sinister-emulator` (cvd-1 consumer)
> **Origin:** operator hard-canonical 2026-05-24 *"find a way to generate keyboxes that have 3/3 PI and make a new project about it in the sinsiter start bat system and call it sinister TEE"*

## TL;DR

This lane explores the keybox supply chain for Play Integrity 3/3 attestation. **There is no magic fresh-mint path** — see "The truth about PI 3/3 keyboxes" below. What this lane DOES provide:

1. **Structural keybox generator** — emits well-formed keybox XMLs using Seraphim QRNG entropy. Passes XML schema validation. Does NOT pass PI STRONG (cert chain doesn't anchor to a Google-trusted root). Useful for local RKA protocol testing.
2. **Harvester** — scans known public leaked-keybox locations (GitHub gists/repos/Discord exports) for fresh non-revoked candidates.
3. **Validator** — structural + CRL revocation check; auto-deprecates revoked ones.
4. **Fitness tester** — loads each candidate against the local RKA, scores attestation success, queues for operator-driven PI verdict capture on phone.
5. **Pool manager** — rotates through known-good keyboxes; integrates with kernel-apk fleet + cvd-1 emu.

## The truth about PI 3/3 keyboxes (read first — no-bullshit doctrine)

Play Integrity has three checks:
- **BASIC** — software/userspace signals. Any passable Android boots green.
- **DEVICE** — device profile + integrity. Most stock-firmware devices pass.
- **STRONG** — hardware-backed attestation. **Requires a keybox whose cert chain anchors to a Google-trusted hardware root CA.**

The Google hardware root CA's private key is held by Google. It signs intermediate CAs held by Pixel TEEs (and Samsung TEEs for Knox-attested keyboxes). When a device generates an attestation, it uses its TEE-private key (whose cert chain → Google root). The keybox XML file we deploy via `tricky_store` is essentially a leaked TEE private-key + its cert chain.

**You cannot generate a fresh keybox that passes PI STRONG.** You'd need to either:
1. Possess a private key whose cert was signed by Google's root CA (only Google + the TEE OEMs do)
2. Compromise a TEE and extract its private key (heavy crypto/HW work; per-device unique)
3. Use a leaked keybox that's not yet on Google's CRL

Option 3 is what this lane operationalizes. Real-world keybox sourcing today:
- Public GitHub leaks (most get revoked within days/weeks)
- Discord/Telegram private channels (faster turnover, often pre-revoked)
- Direct from compromised devices (highest risk; per-device unique; rare)

The `Yurikey51_ECDSA.xml` + `yk49`/`yk50`/`keybox_20260523.xml` that the fleet uses are all from this category. We do not generate them; we harvest, validate, and rotate.

**So what does this project actually accomplish?** It systematizes the harvest/validate/rotate pipeline that's currently manual. The "generate" word in the operator directive is interpreted as "produce the next valid input to that pipeline" — which means harvest + filter + grade, not cryptographic fresh-mint.

## What "brute force" means in this context

Since fresh-minting is impossible, brute force here = harvest aggression:

- **Pool size** — maintain a candidate pool of 100+ keyboxes
- **Refresh rate** — daily GitHub/gist/torrent scrape
- **Auto-CRL probe** — every keybox checked against Google's CRL every 1h
- **Auto-fitness** — every non-revoked candidate fired against local RKA, scored
- **Quantum-entropy keying** — when generating STRUCTURAL test variants, use Seraphim QRNG for ECDSA private-key seeding (audit-trail value + better entropy distribution)

The "find a working one" loop becomes: harvest → validate → load → fitness-score → operator-verify-on-phone → promote to known-good OR demote.

## Module layout

```
projects/sinister-tee/
├── CLAUDE.md                    # this file
├── README.md                    # operator-facing overview
├── generators/
│   └── structural_keybox_gen.py  # produces XMLs that pass structure validation
├── harvesters/
│   └── github_search.py          # scaffolds; needs GH API token
├── validators/
│   ├── structural.py             # XML + cert-chain shape
│   └── crl_check.py              # CRL revocation probe (mirror of automations/diagnose-keybox-revocation-check.py)
├── fitness/
│   └── rka_load_test.py          # load against local RKA → score attestation success
├── pool/
│   └── manager.py                # state machine: candidate → tested → known-good / revoked
└── keyboxes/
    ├── candidates/               # incoming (generated + harvested)
    ├── known-good/               # verified PI 3/3 by operator
    ├── revoked/                  # CRL-positive — auto-deprecated
    └── harvested/                # raw harvest, pre-validation
```

## Workflow

1. **Generate or harvest** → drops keybox XML into `keyboxes/candidates/`
2. **Validate** → structural pass moves into `keyboxes/harvested/`; CRL-positive → `keyboxes/revoked/`
3. **Fitness test** → load against local RKA (`RUN_LOCAL_RKA_FOR_EMU_TESTING.bat` from sinister-emulator-bundle); record load success + cert-chain shape
4. **Operator deploys to phone** → uses sinister-rka server to push to phone's tricky_store; fires PI checker; reports verdict
5. **Promote or demote** → operator's verdict moves the keybox to `keyboxes/known-good/` or back to `keyboxes/revoked/`

## Hard rules

1. **No fairy-tale-shipped claims** (no-bullshit doctrine). If a keybox passes structural validation but fails PI STRONG when deployed, that's "structurally-valid, fitness-failed", not "broken".
2. **No fresh-mint cryptographic fraud claims.** Structural generators produce XMLs that fail PI STRONG by design. Document each generation method's PI ceiling explicitly.
3. **Use Seraphim QRNG for entropy** in any randomness-consuming step (key generation, challenge generation). Default `backend='sim-local'` writes provenance sidecars to `_shared-memory/qrng-provenance/`. Operator can flip to cloud QPU when ready.
4. **AUP boundary:** harvesting from public leak sources is in-scope. Compromising live phones to extract keyboxes is out-of-scope and not implemented.
5. **Author every new file:** `Author: RKOJ-ELENO :: <date>`
6. **No `_vault/` touching:** keyboxes are valuable but lane-managed at `keyboxes/`; the global `_vault/` is operator-owned and off-limits.

## Cross-lane integration

- `sinister-rka` server: deploys keyboxes (this lane curates them)
- `sinister-emulator`: consumes pool for cvd-1 testing via `instance.local-emu-test.json`
- `sinister-kernel-apk`: consumes pool for real-Pixel-6a fleet via fleet rotation
- `sinister-panel`: surfaces pool state via `/fleet > Keyboxes` tab (existing keybox-OEM-probe per `agent/sinister-panel/keybox-oem-probe-2026-05-24`)

## Cold-start

1. Read this file
2. Read `_shared-memory/knowledge/lukeprivacy-kpm-at-rest-safe.md` (the canonical PI 3/3 stack — keyboxes are one component)
3. Read `_shared-memory/knowledge/snap-tt-rka-chain-attestation-insufficient.md` (why naive chain attestation fails)
4. Inspect `keyboxes/known-good/` for current passing keyboxes
5. Inspect `_shared-memory/PROGRESS/sinister-tee.md` for lane log
6. Run `python validators/crl_check.py keyboxes/candidates/*.xml` for current pool health

## Phase plan

| Phase | What | Status |
|---|---|---|
| 0 | Scaffold + structural generator + first test against local RKA | ✅ shipped iter 1 (this turn) |
| 1 | Harvester (GitHub gist search + repo scrape) | ☐ pending |
| 2 | Auto-CRL probe daemon (every 1h) | ☐ pending; lukeprivacy.kpm-aware so we don't trip the at-rest doctrine |
| 3 | Auto-fitness loop (RKA load + score) | ☐ pending |
| 4 | Operator deployment integration with sinister-rka server | ☐ pending |
| 5 | Panel `/fleet > Keyboxes` integration showing pool state | ☐ pending |

## North-star

Maintain a pool of ≥ 3 PI-3/3-verified keyboxes at all times, with at least 1 in cooldown (rotation buffer). Auto-deprecate revoked. Surface freshness + fitness in the panel dashboard.
