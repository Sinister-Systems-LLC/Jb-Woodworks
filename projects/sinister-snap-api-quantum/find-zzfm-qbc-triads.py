"""Algorithmic search for triads where K=4 ZZ-FM r=1 beats classical TF-IDF.

Author: RKOJ-ELENO :: 2026-05-23

⚠️ SUPERSEDED iter 41 (2026-05-24): the canonical entry point is now
   `seraphim find-qbc --variant zzfm-r1 --top-n N --corpus pool`
   (with --rank-by ceiling|headroom|classical for error-mitigation
   target selection). This standalone script remains runnable for
   historical reproducibility but the CLI version has more features
   (rank-by modes, ceiling-sweep enrichment, JSON output, --out flag).

Operator (2026-05-23 evening loop iteration 6): "keep working and dont stop
until the memory system is fuckign great and told to the agents what to
add and fixc".

Iteration 4 finding: K=4 ANGLE quantum-beats-classical for only 0.005% of triads
(16/317,750). The ANGLE encoding is product-state — has structural plateau.

ZZ-FM has DATA-PARAMETERIZED entanglement (the cancellation theorem doesn't
apply — RZZ angles depend on theta_i * theta_j). The plateau is partially broken
in sim at reps=1 (sim 0.77 vs ANGLE 0.90 on the canonical Snap-RE triad).

Hypothesis: ZZ-FM r=1 should find MORE triads with quantum advantage than K=4
ANGLE because the parameterized entanglement captures cross-feature correlations
TF-IDF misses.

Cost: zero cloud burn. Slower than K=4 ANGLE search due to 2^K x 2^K matrix
operations (estimated ~60s for state building + ~5s for pair overlaps + ~1s
for triad enumeration).
"""
from __future__ import annotations

import os
import sys
import time
from itertools import combinations
from pathlib import Path

import numpy as np

try:
    sys.stdout.reconfigure(encoding='utf-8')  # type: ignore[attr-defined]
except Exception:
    pass

SANCTUM_ROOT = Path(os.environ.get('SINISTER_SANCTUM_ROOT', r'D:\Sinister Sanctum'))
SERAPHIM_DIR = SANCTUM_ROOT / 'tools' / 'sinister-seraphim'
BRAIN_DIR = SANCTUM_ROOT / '_shared-memory' / 'knowledge'
if str(SERAPHIM_DIR) not in sys.path:
    sys.path.insert(0, str(SERAPHIM_DIR))

import memory_kernel  # type: ignore  # noqa: E402

K = 4
REPS = 1
SKIP = {'README.md', '_INDEX.md', '_TEMPLATE.md'}


def _list_pool() -> list[str]:
    """Same 124-doc balanced pool as find-optimal-triad.py."""
    files = sorted(p.name for p in BRAIN_DIR.glob('*.md') if p.name not in SKIP)
    topics: dict[str, list[str]] = {}
    for f in files:
        topics.setdefault(f.split('-')[0], []).append(f)
    pool = []
    for prefix, group in sorted(topics.items()):
        pool.extend(group[:4])
    return pool


def _zzfm_state(thetas: np.ndarray) -> np.ndarray:
    """Build the ZZ-FM r=1 state |psi> = U_zzfm |0...0> at K=4."""
    n = K
    state = np.zeros(2 ** n, dtype=np.complex128)
    state[0] = 1.0

    # Helper gates
    def h_gate(target):
        H = (1 / np.sqrt(2)) * np.array([[1, 1], [1, -1]], dtype=np.complex128)
        I2 = np.eye(2, dtype=np.complex128)
        op = None
        for q in range(n):
            m = H if q == target else I2
            op = m if op is None else np.kron(op, m)
        return op

    def rz_gate(target, theta):
        RZ = np.array([[np.exp(-1j * theta / 2), 0], [0, np.exp(1j * theta / 2)]], dtype=np.complex128)
        I2 = np.eye(2, dtype=np.complex128)
        op = None
        for q in range(n):
            m = RZ if q == target else I2
            op = m if op is None else np.kron(op, m)
        return op

    def cnot_gate(control, target):
        dim = 2 ** n
        op = np.zeros((dim, dim), dtype=np.complex128)
        for i in range(dim):
            c_bit = (i >> (n - 1 - control)) & 1
            if c_bit == 0:
                op[i, i] = 1
            else:
                j = i ^ (1 << (n - 1 - target))
                op[j, i] = 1
        return op

    for _ in range(REPS):
        # H layer
        for q in range(n):
            state = h_gate(q) @ state
        # RZ(theta_q) per qubit
        for q in range(n):
            state = rz_gate(q, float(thetas[q])) @ state
        # Nearest-neighbor ZZ via CNOT-RZ-CNOT
        for ii in range(n - 1):
            jj = ii + 1
            a = float(thetas[ii] * thetas[jj] / np.pi)
            state = cnot_gate(ii, jj) @ state
            state = rz_gate(jj, a) @ state
            state = cnot_gate(ii, jj) @ state

    return state


def main() -> int:
    print('=' * 76)
    print(f' Sinister Seraphim :: ZZ-FM r={REPS} K={K} quantum-beats-classical search')
    print('=' * 76)
    pool = _list_pool()
    n_pool = len(pool)
    n_triads = n_pool * (n_pool - 1) * (n_pool - 2) // 6
    print(f' Brain entry pool: {n_pool} files')
    print(f' Triads to evaluate: C({n_pool},3) = {n_triads:,}')
    print(f' Cloud burn: ZERO')
    print()

    t0 = time.monotonic()
    docs = [memory_kernel._load_brain_entry(f) for f in pool]
    tfidf = memory_kernel._tfidf_vectors(docs)
    print(f' TF-IDF (124-doc corpus) computed in {time.monotonic() - t0:.1f}s')

    t0 = time.monotonic()
    zzfm_states = []
    for v in tfidf:
        thetas = memory_kernel._thetas_for_inversion(v, K)
        zzfm_states.append(_zzfm_state(thetas))
    print(f' ZZ-FM states ({n_pool} of them) computed in {time.monotonic() - t0:.1f}s')

    t0 = time.monotonic()
    sim_p = np.zeros((n_pool, n_pool))
    cl_p = np.zeros((n_pool, n_pool))
    for i in range(n_pool):
        for j in range(i + 1, n_pool):
            s = float(np.abs(np.vdot(zzfm_states[i], zzfm_states[j])) ** 2)
            c = memory_kernel._classical_cosine(tfidf[i], tfidf[j])
            sim_p[i, j] = sim_p[j, i] = s
            cl_p[i, j] = cl_p[j, i] = c
    print(f' Pair overlaps ({n_pool*(n_pool-1)//2:,} pairs) in {time.monotonic() - t0:.1f}s')

    # Triad search: by (classical - sim) descending = quantum-beats-classical advantage
    t0 = time.monotonic()
    scores = []
    for (i, j, k) in combinations(range(n_pool), 3):
        sim_m = (sim_p[i, j] + sim_p[i, k] + sim_p[j, k]) / 3
        cl_m = (cl_p[i, j] + cl_p[i, k] + cl_p[j, k]) / 3
        advantage = cl_m - sim_m
        scores.append((advantage, sim_m, cl_m, (i, j, k)))
    scores.sort(reverse=True)
    print(f' Triad search ({len(scores):,} triads) in {time.monotonic() - t0:.1f}s')
    print()

    # Stats: QBC rate
    qbc = sum(1 for s in scores if s[0] > 0)
    print(f' ── ZZ-FM r={REPS} quantum-beats-classical results ──')
    print(f'   Triads where quantum (ZZ-FM) beats classical: {qbc:,} / {len(scores):,}  ({100*qbc/len(scores):.3f}%)')
    print(f'   Max advantage: +{scores[0][0]:.4f}')
    print(f'   Median advantage: {scores[len(scores)//2][0]:+.4f}')
    print(f'   Compare to K=4 ANGLE (iteration 4): 0.005% QBC rate, max +0.1854')
    print()

    print(' Top 10 ZZ-FM-r1 QBC triads:')
    print(f'   {"rank":>4} {"adv":>8} {"sim":>8} {"classical":>10}  docs')
    for rank, (a, s, c, idx) in enumerate(scores[:10], 1):
        docs = ', '.join(pool[i].replace('.md','')[:25] for i in idx)[:80]
        print(f'   {rank:>4} +{a:>7.4f} {s:>8.4f} {c:>10.4f}  {docs}')
    print()

    print(' Top 3 with full doc names:')
    for rank, (a, s, c, idx) in enumerate(scores[:3], 1):
        print(f'  rank {rank}: advantage=+{a:.4f}, sim={s:.4f}, classical={c:.4f}')
        for i in idx:
            print(f'    {pool[i]}')
        print()

    # Save
    import json
    out = SANCTUM_ROOT / 'projects' / 'sinister-snap-api-quantum' / 'outputs' / 'zzfm-r1-qbc-search.json'
    summary = {
        'schema': 'sinister-seraphim.zzfm-r1-qbc-search.v1',
        'k': K, 'reps': REPS, 'pool_size': n_pool, 'triads_evaluated': len(scores),
        'qbc_count': qbc,
        'qbc_pct': 100 * qbc / len(scores),
        'max_advantage': float(scores[0][0]),
        'median_advantage': float(scores[len(scores)//2][0]),
        'pool': pool,
        'top_25_by_advantage': [
            {'rank': r, 'advantage': float(a), 'sim_off_diag_mean': float(s),
             'classical_off_diag_mean': float(c), 'docs': [pool[i] for i in idx]}
            for r, (a, s, c, idx) in enumerate(scores[:25], 1)
        ],
        'comparison_to_k4_angle': {
            'k4_angle_qbc_count': 16, 'k4_angle_qbc_pct': 0.005,
            'k4_angle_max_advantage': 0.1854,
            'zzfm_r1_qbc_count': qbc, 'zzfm_r1_qbc_pct': 100 * qbc / len(scores),
            'zzfm_r1_max_advantage': float(scores[0][0]),
            'zzfm_advantage_over_angle': qbc / max(1, 16),
        },
    }
    out.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f' [OK] saved {out}')
    print('=' * 76)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
