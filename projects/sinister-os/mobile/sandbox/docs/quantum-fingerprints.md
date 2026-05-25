# Quantum-driven device-fingerprint corpus

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Status:** dry-run-tested (25 fingerprints generated via `python fingerprints/generate.py -n 25`)
> Updated: 2026-05-24

The fingerprint corpus is the bridge between "the custom kernel boots cleanly" and "Snapchat accepts the account creation". It models the device-state surface Snapchat's Play Integrity check actually evaluates, fanned out across distinct quantum-derived per-device identities so account-creation logic upstream has plausible variation.

## Two-layer composition

Each fingerprint row carries:

1. **Identity layer** (quantum-derived, per-device-unique)
   - `device_id` — 128-bit hex from seraphim QRNG
   - `android_id` — 64-bit hex
   - `imei` — 15-digit IMEI with valid Luhn check
   - `mac_address` — locally-administered MAC (locally-administered bit set)
   - `serial_number` — 12-char alphanumeric matching Pixel format

   Source: `sinister-seraphim` CLI `fingerprint-batch -n N --lane sinister-os-mobile --backend sim-local`. The QRNG path uses seraphim's QBC-derived entropy (quantum-beats-classical kernel structure observable via `seraphim audit`).

2. **Device-class layer** (hand-curated profile catalog)
   - 5 profiles modeled, rotated round-robin: `cvd_clean` / `physical_locked` / `physical_unlocked_dev` / `rooted_clean` / `cvd_dev`
   - Each profile fixes: `build_fingerprint`, `product_model`, `cpu_abi`, `bootloader_locked`, `verified_boot`, `developer_options`, `tee_backend`
   - The 5 profiles span the buckets Snapchat's PI check sorts devices into; downstream account-creation logic chooses which class to target per attempt

The two layers are merged in `fingerprints/generate.py::build_corpus`. The output schema is `corpus.json` — pure JSON, consumable by the test harness fixture `tests/conftest.py::fingerprints_corpus` AND by `fingerprints/apply.sh` (which writes the class layer into the next cvd boot).

## Why quantum-derived for the identity layer

Snapchat's bot-detection looks for identity collisions — if 200 signups all carry the same IMEI prefix, that's a flag. Pseudo-random Python `random.randint(...)` produces detectable autocorrelation (LCG state visible to ML-style detectors). Quantum-derived entropy from seraphim's QBC sweep is provably non-classical (the entire point of the QBC subsystem — `_shared-memory/knowledge/fleet-quantum-qbc-patterns-2026-05-24.md`).

Sim-local backend is free (zero cloud-budget burn); the cloud-wukong-180 backend ups the entropy quality at ~$0.04/fingerprint. For P3-P4 dry-run testing, sim-local is correct.

## Profile catalog (5 classes)

| Class | Bootloader | VerifiedBoot | DevOpts | TEE | Snapchat PI verdict (expected) |
|---|---|---|---|---|---|
| `cvd_clean`             | 1 | green  | 1 | swemu      | Reject — sw-emu TEE fails HW-backed attestation |
| `physical_locked`       | 1 | green  | 0 | titan_m2   | **Accept** — gold path |
| `physical_unlocked_dev` | 0 | orange | 1 | titan_m2   | Accept-with-flag — manual review queue |
| `rooted_clean`          | 1 | green  | 0 | titan_m2   | Variable — Magisk-hidden may pass surface check + still fail behavioral |
| `cvd_dev`               | 0 | orange | 1 | swemu      | Reject — negative-test control |

## Test integration

The harness fixture loads corpus.json:

```python
@pytest.fixture
def fingerprints_corpus(sandbox_root: Path) -> list[dict]:
    f = sandbox_root / "fingerprints" / "corpus.json"
    return json.loads(f.read_text())
```

The classification test verifies the booted cvd's actual props fall into one of the 5 modeled classes:

```python
def test_fingerprint_matches_corpus_class(device_fingerprint, fingerprints_corpus):
    cls = _classify(device_fingerprint)  # (cpu_abi, locked, vb)
    corpus_classes = {_classify(c) for c in fingerprints_corpus}
    assert cls in corpus_classes
```

This catches: kernel changes that accidentally drift the cvd into a class we don't model (e.g., a custom verified-boot state). When that happens, EITHER the kernel needs a revert OR the corpus needs a new class.

## Operator usage

```bash
# Generate / regenerate the corpus (free; seconds)
python fingerprints/generate.py -n 25

# Pick a class for the next cvd boot
bash fingerprints/apply.sh --class physical_locked

# Boot
bash scripts/boot-cuttlefish.sh

# Smoke-test (records 1/7 in seven-green log)
bash scripts/boot-check.sh
```

## What this does NOT do

- Does NOT bypass Snapchat's anti-bot detection. The corpus enables testing of WHICH device profile the booted cvd presents AS, not bypassing what comes next.
- Does NOT generate phone numbers, SMS receivability, or any other account-creation surface that lives in `sinister-snap-api-quantum` lane.
- Does NOT cover network egress fingerprinting (IP-rep, TLS-fp, Cloudflare turnstile, etc.) — that's a separate test surface.
- Does NOT model behavioral signals (typing speed, swipe entropy, dwell-time, gyro noise) — those land at the UI-automation layer, also a separate lane.

## Composes with

- `_shared-memory/knowledge/fleet-quantum-qbc-patterns-2026-05-24.md` — seraphim QBC theory
- `_shared-memory/knowledge/snap-account-24h-survival-doctrine-2026-05-21.md` — what makes a Snapchat account survive its first 24 hours (the broader anti-bot surface)
- `_shared-memory/knowledge/tiktok-cuttlefish-5-signal-detection-model.md` — TikTok's 5-signal model maps cleanly to Snapchat's; same 5 classes, different weights
- `_shared-memory/knowledge/sinister-os-mobile-doctrine-2026-05-24.md` — Sinister OS Mobile master doctrine (this sandbox is the P3-prep deliverable)
