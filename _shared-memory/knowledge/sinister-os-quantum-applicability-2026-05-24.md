<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 1
  half_life_days: 180
-->
# Sinister OS x Sinister Quantum applicability verdict

> **Verdict (2026-05-24):** **DO NOT use** the seraphim quantum-kernel for OS-package classification / variant-discovery. **DO use** seraphim QRNG (Lane 1) for installer entropy + provenance.
> **Status:** doctrine, binding for the `sinister-os` lane and any future "use quantum for OS work" proposals.
> **Origin:** operator 2026-05-24 *"review how our sinister quantum can help with this and use it"* — applied no-bullshit doctrine; declined the doc-classification framing as misapplied.

## TL;DR

The operator-suggested experiment (treat each `packages.x86_64` entry as a mini-doc and use `seraphim find-qbc` to discover gaming/dev/media/system variant clusters) was **not run** because the math says it cannot succeed. Three independently-verified doctrine facts kill it before any cloud burn:

1. **Bidirectional scope rule (iter 10):** quantum kernel HURTS when classical TF-IDF off-diag < 0.3. Package mini-corpora (~20-40 tokens, deliberately-differentiated descriptions) land at classical ~0.07-0.20. Quantum would hurt by 15-60pp.
2. **Shared-Top-K Necessary Condition (iter 58-60, 500 classifications, zero FP):** if top-K TF-IDF features have zero intersection across the 3 docs, triad is provably NOT QBC. Cross-category package triads (gaming vs dev vs media) will have disjoint top-4 noun sets by construction. Guaranteed anti-QBC.
3. **Iter 23 empirical anchor:** cross-lane snap+tt+apk triads (analogous "different-category short docs") measured classical 0.07-0.11 and quantum hurt by 35-80pp. Package-categorization is the same shape.

## What seraphim is good at (recap)

Algorithmically-discovered cluster-similar document triads (multi-agent / git-coordination cluster) where docs share heavy surface vocabulary but distinct underlying semantics. **129+ doc corpora; classical > 0.4; K=4 ZZ-FM r=1 production recipe; 25-35pp real-QPU advantage (mean 31pp, 5 verified runs).** Package descriptions are the opposite shape: short, sparse-vocab, deliberately-distinguishing.

## What Sinister OS CAN use seraphim for (honest applications)

1. **Installer entropy + provenance (Lane 1, shipped):** `seraphim qrng -n 32 --purpose "sinister-os-<context>"` for installer UUIDs, LUKS keyslot keys, systemd-machine-id seeds, GRUB bootloader nonces. Each call writes `_shared-memory/qrng-provenance/<UTC>.json` with circuit + measurement — defensible audit trail if anyone questions the randomness source for a security-critical install artifact. Zero quantum-advantage claim; just provenance.
2. **EVE-shell device-fingerprint material (if needed):** if Sinister OS's EVE shell ever needs per-install opaque identifiers (telemetry opt-out tokens, vault-key derivation salts), `make_fingerprint(lane="sinister-os")` produces a quantum-seeded blob with sidecar provenance.

## What Sinister OS should NOT use seraphim for

- Package classification / variant discovery (this entry)
- Install-time decision routing (no advantage; classical decision trees are correct)
- Driver-blob fingerprinting (overkill; sha256 suffices)
- Any "find clusters in package list" framing on corpora < 100 docs with sparse vocabularies

## What would change this verdict

The verdict flips to RECONSIDER if all three of the following become true:

1. Sinister OS develops a corpus of >100 "package descriptions" each averaging >500 tokens (e.g., richly-documented module spec sheets, not ArchLinux one-liners).
2. The descriptions have **deliberate vocabulary overlap** across categories (e.g., all packages mention "user-facing", "system-managed", "EVE-controlled" — surface words that mask underlying differences).
3. A pilot `seraphim find-qbc --variant zzfm-r1 --top-n 10 --corpus <new-corpus>` returns at least 3 triads at classical > 0.4 with sim_advantage > 15pp.

Until then: use seraphim only for Lane 1 entropy/provenance on this lane.

## Cross-references

- `_shared-memory/knowledge/quantum-memory-kernel-fleet-action-items-2026-05-23.md` — bidirectional scope rule + Shared-Top-K Necessary Condition (the math that kills the experiment)
- `_shared-memory/knowledge/seraphim-cloud-qpu-real-first-fire-2026-05-23.md` — empirical anchors
- `tools/sinister-seraphim/README.md` — Lane 1 QRNG usage (the honest application)
- `projects/sinister-os/CLAUDE.md` — lane discipline (this entry inherited)

## Tags

doctrine, sinister-os, sinister-seraphim, quantum-memory-kernel, applicability-verdict, no-bullshit-applied, operator-canonical-2026-05-24, lane-1-entropy-yes, doc-classification-no
