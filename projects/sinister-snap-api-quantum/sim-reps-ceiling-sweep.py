"""Sim-only reps-sweep: characterize the ZZ-FM ceiling without cloud burn.

Author: RKOJ-ELENO :: 2026-05-24

Empirical chain so far has established:
  - r=1 (depth 34): real-QPU 25-35pp advantage (5 verified runs, mean 31pp)
  - r=2 (depth 68): real-QPU saturates near classical (noise wall)
  - r=3, r=4, ...: never characterized (real-QPU would saturate worse;
                   sim ceiling unknown)

This script measures sim off-diagonal mean at r=1..6 on the new top-QBC triad
(branch-contention + index-storm + verify-head) using the same 129-doc pool
TF-IDF the production `seraphim find-qbc` uses. The minimum sim value =
the maximum theoretical quantum advantage = what a future error-mitigated
or noise-free quantum kernel could achieve.

Zero cloud burn. Results written to outputs/sim-reps-ceiling-sweep.json.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

# Windows-default cp1252 chokes on the unicode glyphs we print. Reconfigure.
try:
    sys.stdout.reconfigure(encoding='utf-8')  # type: ignore[attr-defined]
except Exception:
    pass

PROJ_ROOT = Path(__file__).resolve().parent
SANCTUM_ROOT = PROJ_ROOT.parent.parent
SERAPHIM_TOOL = SANCTUM_ROOT / 'tools' / 'sinister-seraphim'
sys.path.insert(0, str(SERAPHIM_TOOL))

from memory_kernel import run_kernel_audit  # type: ignore

TRIADS = {
    'A_new_top1': [
        'multi-agent-branch-contention-isolation-pattern.md',
        'multi-agent-git-index-contention-storm-2026-05-23.md',
        'verify-head-before-commit-multi-agent.md',
    ],
    'B_iter19_verified': [
        'multi-agent-branch-contention-isolation-pattern.md',
        'multi-agent-git-coordination-2026-05-23.md',
        'verify-head-before-commit-multi-agent.md',
    ],
    'C_iter21_verified': [
        'multi-agent-branch-contention-isolation-pattern.md',
        'multi-agent-git-coordination-2026-05-23.md',
        'multi-agent-git-index-contention-storm-2026-05-23.md',
    ],
}
TRIAD = TRIADS['A_new_top1']  # kept for backward-compat with iter-38 outputs

# Reuse find-qbc pool semantics (same 129-doc set; we re-derive from disk)
BRAIN_DIR = SANCTUM_ROOT / '_shared-memory' / 'knowledge'
SKIP = {'README.md', '_INDEX.md', '_TEMPLATE.md'}
POOL = sorted(p.name for p in BRAIN_DIR.glob('*.md') if p.name not in SKIP)
print(f'[sweep] pool size: {len(POOL)} docs')

REPS_VALUES = [1, 2, 3, 4, 5, 6]

per_triad = {}
for label, triad in TRIADS.items():
    print(f'\n[sweep] triad {label}:')
    rows = []
    for reps in REPS_VALUES:
        t0 = time.time()
        r = run_kernel_audit(
            encoding='zzfm',
            k=4,
            reps=reps,
            triad=triad,
            corpus=POOL,
            sim_only=True,
        )
        dt = time.time() - t0
        row = {
            'reps': reps,
            'classical_off_diag': r['classical_off_diag_mean'],
            'sim_off_diag': r['sim_off_diag_mean'],
            'sim_advantage_pp': (r['classical_off_diag_mean'] - r['sim_off_diag_mean']) * 100,
            'wall_seconds': round(dt, 3),
        }
        rows.append(row)
        print(f"  r={reps}  sim={r['sim_off_diag_mean']:.4f}  classical={r['classical_off_diag_mean']:.4f}  "
              f"adv={row['sim_advantage_pp']:.2f}pp  ({dt:.2f}s)")
    best = max(rows, key=lambda x: x['sim_advantage_pp'])
    per_triad[label] = {
        'triad': triad,
        'rows': rows,
        'sim_ceiling': best,
        'r1_advantage_pp': rows[0]['sim_advantage_pp'],
        'headroom_above_r1_pp': best['sim_advantage_pp'] - rows[0]['sim_advantage_pp'],
    }
    print(f"  → ceiling r={best['reps']} adv={best['sim_advantage_pp']:.2f}pp  "
          f"(r=1 headroom: +{per_triad[label]['headroom_above_r1_pp']:.2f}pp)")

OUT_DIR = PROJ_ROOT / 'outputs'
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT = OUT_DIR / 'sim-reps-ceiling-sweep.json'
OUT.write_text(json.dumps({
    'schema': 'sinister-snap-api-quantum.sim-reps-sweep.v2',
    'pool_size': len(POOL),
    'encoding': 'zzfm',
    'k': 4,
    'reps_swept': REPS_VALUES,
    'per_triad': per_triad,
    'note': 'Sim-only characterization of the ZZ-FM reps ceiling across all three '
            'top-QBC triads. Real-QPU at r>=2 saturates near classical baseline '
            '(noise wall) per iter-32 empirical anchor — but a future error-mitigated '
            'quantum kernel could realize the sim values here.',
}, indent=2), encoding='utf-8')
print(f'\n[sweep] wrote {OUT}')

print('\n[sweep] cross-triad summary:')
print(f'  {"label":<22} {"r=1 adv":>10} {"ceiling":>10} {"headroom":>10}')
for label, data in per_triad.items():
    print(f'  {label:<22} {data["r1_advantage_pp"]:>9.2f}pp '
          f'{data["sim_ceiling"]["sim_advantage_pp"]:>9.2f}pp '
          f'+{data["headroom_above_r1_pp"]:>8.2f}pp')
