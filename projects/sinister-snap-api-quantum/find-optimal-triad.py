"""Algorithmic triad selection: find the most-discriminating triad across all
brain entries by maximizing TF-IDF top-K feature diversity.

Author: RKOJ-ELENO :: 2026-05-23

Operator (2026-05-23 evening, loop iteration 3): "keep working and testing all
of this to get the memory as good as we can get it"

Iteration 2 finding (17:40Z): the encoding-collapse plateau is TRIAD-LIMITED.
Medium-doctrine triad got real-QPU off-diag 0.5417 (vs sim 0.5520, Δ=-0.010).
That was a hand-picked triad from 3 doctrine entries. Could an algorithmic
search find an even better triad across all 145 brain entries?

Approach:
  1. Load all .md files in _shared-memory/knowledge/ (skip _INDEX, _TEMPLATE, etc.)
  2. For each, compute TF-IDF vector → top-K (K=4) features
  3. For all 3-document combinations (or a tractable sample):
     - Compute sim K=4 ANGLE off-diag mean
     - Compute classical TF-IDF off-diag mean
  4. Rank triads by sim off-diag mean (lowest = best discrimination in sim)
  5. Report top 5 candidates with their sim and classical baselines

Zero cloud burn — all CPUQVM-sim.

Combinatorial check: C(145, 3) = 488,180 combinations. Too many for exhaustive.
Strategy: filter to a candidate pool (say 30-40 brain entries spanning the
catalog), then enumerate C(30, 3) = 4060 — tractable in seconds.
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

# Skip files that aren't substantive doctrine/empirical entries
SKIP = {'README.md', '_INDEX.md', '_TEMPLATE.md'}


def _list_candidates() -> list[str]:
    files = sorted(p.name for p in BRAIN_DIR.glob('*.md') if p.name not in SKIP)
    # Filter to a tractable pool — pick ~40 by topic diversity (spread across categories).
    # Heuristic: include all distinct "topic prefixes" (first hyphen-separated chunk).
    topics: dict[str, list[str]] = {}
    for f in files:
        prefix = f.split('-')[0]
        topics.setdefault(prefix, []).append(f)
    # Sample up to 4 per topic prefix (gives us diversity AND tractability)
    pool = []
    for prefix, group in sorted(topics.items()):
        pool.extend(group[:4])
    return pool


def main() -> int:
    print('=' * 76)
    print(' Sinister Seraphim :: algorithmic optimal-triad search')
    print('=' * 76)
    pool = _list_candidates()
    n_pool = len(pool)
    n_triads = n_pool * (n_pool - 1) * (n_pool - 2) // 6
    print(f' Brain entry pool: {n_pool} files')
    print(f' Triads to evaluate: C({n_pool},3) = {n_triads:,}')
    print(f' K=4 ANGLE inversion overlap, CPUQVM (zero cloud burn)')
    print()

    # Pre-compute TF-IDF vectors + thetas for every pool entry
    t_load_start = time.monotonic()
    docs = []
    for f in pool:
        try:
            docs.append(memory_kernel._load_brain_entry(f))
        except Exception as exc:
            print(f'  [WARN] failed to load {f}: {exc}')
            docs.append('')
    tfidf = memory_kernel._tfidf_vectors(docs)
    # Replace empty docs with zero vectors (will give classical 0 overlaps with anything)
    print(f'  loaded {n_pool} entries + computed TF-IDF in {time.monotonic() - t_load_start:.2f}s')

    # Per-document angle-encoded statevector (for sim overlap computation)
    t_states_start = time.monotonic()
    states = []
    for v in tfidf:
        thetas = memory_kernel._thetas_for_inversion(v, K)
        per_qubit = [np.array([np.cos(t / 2), np.sin(t / 2)], dtype=np.complex128) for t in thetas]
        state = per_qubit[0]
        for q in per_qubit[1:]:
            state = np.kron(state, q)
        states.append(state)
    print(f'  computed {n_pool} K={K} ANGLE statevectors in {time.monotonic() - t_states_start:.2f}s')

    # Pairwise overlap matrix (sim K=4 ANGLE)
    t_pair_start = time.monotonic()
    pair_overlap = np.zeros((n_pool, n_pool))
    pair_classical = np.zeros((n_pool, n_pool))
    for i in range(n_pool):
        for j in range(i + 1, n_pool):
            sim_ov = float(np.abs(np.vdot(states[i], states[j])) ** 2)
            cl_ov = memory_kernel._classical_cosine(tfidf[i], tfidf[j])
            pair_overlap[i, j] = sim_ov
            pair_overlap[j, i] = sim_ov
            pair_classical[i, j] = cl_ov
            pair_classical[j, i] = cl_ov
    print(f'  computed all pair overlaps in {time.monotonic() - t_pair_start:.2f}s')
    print()

    # Enumerate all triads, score each by sim off-diag mean
    t_search_start = time.monotonic()
    triad_scores = []
    for (i, j, k) in combinations(range(n_pool), 3):
        # Off-diag mean = (overlap_ij + overlap_ik + overlap_jk) * 2 / 6 = sum/3
        sim_mean = (pair_overlap[i, j] + pair_overlap[i, k] + pair_overlap[j, k]) / 3
        cl_mean = (pair_classical[i, j] + pair_classical[i, k] + pair_classical[j, k]) / 3
        triad_scores.append((sim_mean, cl_mean, (i, j, k)))
    triad_scores.sort()  # ascending by sim_mean → lowest sim plateau first
    print(f'  evaluated {len(triad_scores):,} triads in {time.monotonic() - t_search_start:.2f}s')
    print()

    print(' Top 10 triads by lowest sim K=4 ANGLE off-diag mean:')
    print(f'   {"rank":>4}  {"sim":>8}  {"classical":>10}  {"docs":<60}')
    for rank, (sim_mean, cl_mean, idx) in enumerate(triad_scores[:10], 1):
        docs = ', '.join(pool[i].replace('.md', '') for i in idx)
        if len(docs) > 80:
            docs = docs[:77] + '...'
        print(f'   {rank:>4}  {sim_mean:.4f}    {cl_mean:.4f}      {docs}')
    print()

    print(' Comparison to known triads (rank position):')
    known_triads = {
        'default-snap-re': ['snap-tt-rka-chain-attestation-insufficient.md',
                            'snap-emu-pb2-schema-shadow.md',
                            'snap-account-24h-survival-doctrine-2026-05-21.md'],
        'wide-unrelated': ['seraphim-cloud-qpu-real-first-fire-2026-05-23.md',
                           'agent-identity-eve.md',
                           'apk-classifier-aup-doctrine.md'],
        'medium-doctrine': ['snap-emu-doctrine-drift-2026-05-23.md',
                            'sinister-freeze-project-doctrine.md',
                            'forever-expanding-modular-architecture-doctrine.md'],
    }
    for name, triad in known_triads.items():
        # Find this triad's index tuple in pool
        try:
            idx = tuple(sorted(pool.index(f) for f in triad))
        except ValueError as exc:
            print(f'   {name}: ⚠️  not in pool ({exc})')
            continue
        # Find its rank
        for rank, (sim_mean, cl_mean, score_idx) in enumerate(triad_scores, 1):
            if tuple(sorted(score_idx)) == idx:
                print(f'   {name}: rank #{rank}/{len(triad_scores):,}  (sim={sim_mean:.4f}, classical={cl_mean:.4f})')
                break

    # Save full results
    import json
    out = SANCTUM_ROOT / 'projects' / 'sinister-snap-api-quantum' / 'outputs' / 'optimal-triad-search.json'
    summary = {
        'schema': 'sinister-seraphim.optimal-triad-search.v1',
        'k': K,
        'pool_size': n_pool,
        'triads_evaluated': len(triad_scores),
        'pool': pool,
        'top_25_triads': [
            {
                'rank': rank,
                'sim_off_diag_mean': float(s_mean),
                'classical_off_diag_mean': float(c_mean),
                'docs': [pool[i] for i in idx],
            }
            for rank, (s_mean, c_mean, idx) in enumerate(triad_scores[:25], 1)
        ],
        'known_triad_ranks': {},
    }
    for name, triad in known_triads.items():
        try:
            idx = tuple(sorted(pool.index(f) for f in triad))
            for rank, (sim_mean, cl_mean, score_idx) in enumerate(triad_scores, 1):
                if tuple(sorted(score_idx)) == idx:
                    summary['known_triad_ranks'][name] = {
                        'rank': rank, 'sim_off_diag_mean': float(sim_mean),
                        'classical_off_diag_mean': float(cl_mean), 'docs': triad,
                    }
                    break
        except ValueError:
            summary['known_triad_ranks'][name] = {'rank': None, 'reason': 'not in pool'}

    out.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')
    print()
    print(f' [OK] saved {out}')
    print('=' * 76)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
