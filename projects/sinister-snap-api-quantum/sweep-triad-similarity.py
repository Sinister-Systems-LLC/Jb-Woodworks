"""Sim-only sweep of 3 candidate triads with varying topical similarity.

Author: RKOJ-ELENO :: 2026-05-23

Operator (2026-05-23 evening loop iteration 2): "keep working and do not stop" +
"use the quantum time when ytou need it".

Hypothesis: the encoding-collapse plateau at sim ~0.85-0.90 we observed for
the canonical Snap-RE triad may be partially a property of the document set's
high topical similarity (all 3 documents are Snap-RE focused). Testing with
wider/different triads in sim costs zero budget; if any triad shows sim
off-diag below ~0.5, that's a real-QPU candidate where hardware noise might
not saturate the signal.

Three triads tested:
  DEFAULT_TRIAD: canonical Snap-RE (high topical similarity, verified sim 0.8975)
  WIDE_TRIAD: maximally unrelated domains (quantum / persona / AUP)
  MEDIUM_TRIAD: 3 doctrine entries from different lanes (snap-emu / freeze / arch)

For each triad: compute classical TF-IDF baseline + sim K=4 ANGLE off-diag.
Identify the most-discriminating triad as the real-QPU candidate.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np

try:
    sys.stdout.reconfigure(encoding='utf-8')  # type: ignore[attr-defined]
except Exception:
    pass

SANCTUM_ROOT = Path(os.environ.get('SINISTER_SANCTUM_ROOT', r'D:\Sinister Sanctum'))
SERAPHIM_DIR = SANCTUM_ROOT / 'tools' / 'sinister-seraphim'
if str(SERAPHIM_DIR) not in sys.path:
    sys.path.insert(0, str(SERAPHIM_DIR))

import memory_kernel  # type: ignore  # noqa: E402

TRIADS = {
    'default-snap-re': [
        'snap-tt-rka-chain-attestation-insufficient.md',
        'snap-emu-pb2-schema-shadow.md',
        'snap-account-24h-survival-doctrine-2026-05-21.md',
    ],
    'wide-unrelated': [
        'seraphim-cloud-qpu-real-first-fire-2026-05-23.md',  # quantum computing
        'agent-identity-eve.md',                              # persona/identity
        'apk-classifier-aup-doctrine.md',                     # AUP/legal scope
    ],
    'medium-doctrine': [
        'snap-emu-doctrine-drift-2026-05-23.md',              # snap-emu lane
        'sinister-freeze-project-doctrine.md',                # freeze project
        'forever-expanding-modular-architecture-doctrine.md', # system architecture
    ],
}


def main() -> int:
    print('=' * 76)
    print(' Sinister Seraphim :: SIM-ONLY triad similarity sweep')
    print('=' * 76)
    print(' K=4 ANGLE inversion overlap, CPUQVM (zero cloud burn)')
    print()

    results = {}
    for name, triad in TRIADS.items():
        try:
            r = memory_kernel.run_kernel_audit(
                encoding='angle', k=4, reps=1,
                triad=triad,
                sim_only=True,
            )
        except FileNotFoundError as exc:
            print(f' [{name}] FAIL: missing brain entry: {exc}')
            continue

        cl = r['classical_off_diag_mean']
        sm = r['sim_off_diag_mean']
        results[name] = {
            'triad': triad,
            'classical_off_diag_mean': cl,
            'sim_off_diag_mean': sm,
            'classical_kernel': r['classical_kernel'],
            'sim_kernel': r['sim_kernel'],
        }

        print(f' [{name}]')
        for i, t in enumerate(triad):
            print(f'   [{i}] {t}')
        print(f'   classical off-diag mean: {cl:.4f}')
        print(f'   sim off-diag mean:       {sm:.4f}')
        print(f'   Δ sim - classical:       {sm - cl:+.4f}')
        print()

    print('=' * 76)
    print(' Comparison:')
    print(f'   {"triad":<20s}  {"classical":>10s}  {"sim K=4 ANGLE":>14s}  {"Δ":>10s}')
    for name, r in results.items():
        cl = r['classical_off_diag_mean']
        sm = r['sim_off_diag_mean']
        print(f'   {name:<20s}  {cl:>10.4f}  {sm:>14.4f}  {sm - cl:>+10.4f}')

    print()
    print(' ── Verdict ──')
    if results:
        best = min(results.items(), key=lambda kv: kv[1]['sim_off_diag_mean'])
        worst = max(results.items(), key=lambda kv: kv[1]['sim_off_diag_mean'])
        print(f'   Most-discriminating sim plateau: {best[0]} (sim off-diag = {best[1]["sim_off_diag_mean"]:.4f})')
        print(f'   Highest plateau (least discrim): {worst[0]} (sim off-diag = {worst[1]["sim_off_diag_mean"]:.4f})')
        gap = worst[1]['sim_off_diag_mean'] - best[1]['sim_off_diag_mean']
        print(f'   Gap: {gap:.4f}pp')
        if gap > 0.15:
            print(f'\n   ✅ Triad choice matters. Document-set similarity DOES affect the plateau.')
            print(f'      Real-QPU candidate: {best[0]} — has the lowest sim baseline.')
        else:
            print(f'\n   ⚠️  Triad choice barely moves the plateau. Plateau is intrinsic to K=4 ANGLE encoding,')
            print(f'      not the documents. Real-QPU on different triads would burn budget without insight.')

    print('=' * 76)

    import json
    out = SANCTUM_ROOT / 'projects' / 'sinister-snap-api-quantum' / 'outputs' / 'triad-similarity-sweep.json'
    out.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f' [OK] saved {out}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
