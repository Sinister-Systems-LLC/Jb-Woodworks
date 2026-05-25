# keybox/ — Android attestation keybox handling

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Operator directive (verbatim 2026-05-24T16:15:42Z):** *"C:\Users\Zonia\Desktop\keybox_20260523.xml use this keybox and check pi"*
> **Status:** dry-run-tested (parsing + verification work on Windows without cvd)

## What this directory holds

Code + manifest for handling Android attestation keyboxes used to satisfy Play Integrity (PI) checks. The keybox XML files contain real EC/RSA private keys + cert chains rooting in OEM TEE CAs (Samsung, Google, Qualcomm, etc.).

**Binding rules:**

1. **No keybox file lives inside this repo.** Operator provides keyboxes by absolute path at runtime. The repo carries ONLY a manifest (filename + sha256 + metadata).
2. **No private key material in any committed file.** `parse_keybox.py` strips PrivateKey blocks before logging or returning structured data. The harness uses keys only inside in-process memory.
3. **Manifest entries are append-only.** A keybox is recorded once (sha256 hash + DeviceID + cert chain summary); subsequent verifications match the hash. If the operator rotates the keybox, append a new row + mark the old as `superseded`.

## Files

| File | Role |
|---|---|
| `README.md` | this file |
| `manifest.json` | declared keyboxes (no key material) — see schema below |
| `parse_keybox.py` | XML parser — extracts metadata + structured cert chain (PrivateKey blocks dropped) |
| `verify_keybox.py` | reads operator path + asserts SHA256 matches manifest + parses + emits canonical metadata |

## Manifest schema

```json
{
  "schema_version": "sinister.keybox-manifest.v1",
  "keyboxes": [
    {
      "filename": "keybox_20260523.xml",
      "sha256": "58243fe6...",
      "first_seen_utc": "2026-05-24T16:15Z",
      "operator_provided_path_hint": "C:\\Users\\Zonia\\Desktop\\keybox_20260523.xml",
      "device_id": "Samsung_c5faa186-2a74-4c12-a5a0-22f396e63aa7",
      "key_algorithm": "ecdsa",
      "key_curve": "secp256r1",
      "cert_chain_length": 3,
      "chain_root_issuer_cn": "TEE",
      "chain_root_issuer_serial_hex": "dd1f8db3bf97e0c3be84d91b466bfef5",
      "status": "active",
      "notes": "Samsung device keybox. For sandbox PI testing only — do not deploy on operator's primary device."
    }
  ]
}
```

## Operator handoff procedure

When operator drops a new keybox:

1. Operator says "use keybox at <path>" + provides the file (typically on Desktop or in operator-controlled vault)
2. Harness runs `python sandbox/keybox/verify_keybox.py --path <path>` ONE TIME
3. If keybox is new (no matching sha256 in manifest), verify_keybox.py prints a SUGGESTED MANIFEST ROW + asks operator to confirm via `--accept-new`
4. On confirm, the row appends to `manifest.json`; subsequent verifications are silent

## What this directory does NOT do

- Does NOT modify the keybox file
- Does NOT export private keys to disk
- Does NOT push keyboxes to git (the manifest is the only thing committed; .gitignore covers raw `*.xml` here defensively)
- Does NOT decide which keybox is best for a given test — that's the scenario runner's job (see `sandbox/scripts/run-scenario.sh` when it lands)
- Does NOT integrate with Play Integrity itself (the keybox is INPUT to a separate PI injector that runs on the booted cvd; the injector is operator-supplied at P3+, typically PIFork or similar Magisk module)

## PI testing flow (full integration, P3+)

The keybox is consumed by a Magisk module on the booted cvd. The flow:

```
operator keybox.xml (Desktop)
        │
        ▼ verify_keybox.py
sandbox/keybox/manifest.json (committed; sha256 only)
        │
        ▼ scenario runner picks a keybox row
cvd boot with PIFork Magisk module + keybox volume-mounted from operator path
        │
        ▼ Snapchat APK invokes PI
PIFork intercepts the PI handshake, signs with the keybox's private key,
returns the cert chain — Snapchat sees a 'meets-device-integrity' verdict
        │
        ▼ test_play_integrity.py asserts the verdict
```

The flow above DEPENDS on:
- Real cvd running (operator-action: Linux+KVM host)
- PIFork Magisk module installed in the cvd image (operator-action: PIFork source + build)
- The keybox not being globally blocklisted by Google (operator manages keybox rotation)

This sandbox handles the INPUTS to that flow + verifies a keybox is structurally valid + reachable. It does NOT do the PIFork install for you.

## Composes with

- `sandbox/docs/anti-brick-safety.md` (Gate 5 — TEE delta modeled; keybox injection is the modeling vector)
- `sandbox/docs/quantum-fingerprints.md` (the fingerprint corpus + the keybox together define one full PI-survivable identity)
- `_shared-memory/knowledge/snap-tt-rka-chain-attestation-insufficient.md` (background: why attestation chain alone isn't always enough)
- Brain entry pending: `imessage-bridge-not-this` — kidding, this is the os-mobile sandbox; will be referenced from the next sandbox brain update

## Updated: 2026-05-24
