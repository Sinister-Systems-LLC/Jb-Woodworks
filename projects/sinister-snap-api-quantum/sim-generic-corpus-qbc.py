"""Iter 103 - Generic per-lane corpus QBC sweep (parameterized).

Author: RKOJ-ELENO :: 2026-05-24

Operator: /loop "keep going". Promote per-lane sweep to generic parameterized form
so the fleet can self-serve without writing a new script per lane.

Usage:
    python sim-generic-corpus-qbc.py --label <lane-name> --root <path>
                                     [--max-depth N] [--cap M]
                                     [--exclude <dirname>]...

Reads all .md under <root> (filtered by depth + exclude list), runs ZZ-FM r=1 K=4
sim sweep, outputs to outputs/<label>-corpus-qbc-iter103.json + console.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from itertools import combinations
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8')  # type: ignore[attr-defined]
except Exception:
    pass

PROJ_ROOT = Path(__file__).resolve().parent
SANCTUM_ROOT = PROJ_ROOT.parent.parent
SERAPHIM_TOOL = SANCTUM_ROOT / 'tools' / 'sinister-seraphim'
sys.path.insert(0, str(SERAPHIM_TOOL))

from memory_kernel import (  # type: ignore
    _tfidf_vectors, _classical_cosine,
    _thetas_for_inversion, _sim_inversion_overlap,
)

DEFAULT_EXCLUDE = {'node_modules', 'dist', '.git', '.next', 'build', 'outputs', 'target', '_archive', '__pycache__'}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--label', required=True, help='Lane label (used in filename)')
    ap.add_argument('--root', required=True, help='Corpus root directory')
    ap.add_argument('--max-depth', type=int, default=5, help='Max .md path depth from root')
    ap.add_argument('--cap', type=int, default=120, help='Max docs to keep (most-recent-modified first)')
    ap.add_argument('--exclude', action='append', default=[], help='Additional exclude dirnames')
    args = ap.parse_args()

    excludes = DEFAULT_EXCLUDE | set(args.exclude)
    root = Path(args.root)
    if not root.exists():
        print(f'ERROR: corpus root not found: {root}')
        return 2

    t0 = time.time()
    docs_paths = []
    for p in root.rglob('*.md'):
        if any(part in excludes for part in p.parts):
            continue
        try:
            rel = p.relative_to(root)
        except ValueError:
            continue
        if len(rel.parts) > args.max_depth:
            continue
        docs_paths.append(p)

    pre_cap = len(docs_paths)
    if len(docs_paths) > args.cap:
        docs_paths = sorted(docs_paths, key=lambda p: p.stat().st_mtime, reverse=True)[: args.cap]

    print(f'Lane: {args.label}')
    print(f'Root: {root}')
    print(f'Docs found: {pre_cap}  (capped to {len(docs_paths)})')

    if len(docs_paths) < 3:
        print('Not enough docs (<3). Exiting.')
        return 3

    doc_names = [str(p.relative_to(SANCTUM_ROOT)).replace('\\', '/') for p in docs_paths]
    texts = [p.read_text(encoding='utf-8', errors='replace') for p in docs_paths]
    print(f'Loaded {len(texts)} docs in {time.time()-t0:.1f}s')

    t1 = time.time()
    tfidf = _tfidf_vectors(texts)
    print(f'TF-IDF built in {time.time()-t1:.1f}s')

    N = len(docs_paths)
    pair_cl = [[0.0] * N for _ in range(N)]
    pair_sim = [[0.0] * N for _ in range(N)]
    thetas = [_thetas_for_inversion(v, 4) for v in tfidf]

    t2 = time.time()
    for i in range(N):
        for j in range(i + 1, N):
            pair_cl[i][j] = pair_cl[j][i] = _classical_cosine(tfidf[i], tfidf[j])
            pair_sim[i][j] = pair_sim[j][i] = _sim_inversion_overlap(thetas[i], thetas[j], 'zzfm', 4, 1)
    print(f'Pair sweep done in {time.time()-t2:.1f}s (C({N},2)={N*(N-1)//2})')

    t3 = time.time()
    scores = []
    for i, j, k in combinations(range(N), 3):
        cl_off = (pair_cl[i][j] + pair_cl[i][k] + pair_cl[j][k]) / 3
        sim_off = (pair_sim[i][j] + pair_sim[i][k] + pair_sim[j][k]) / 3
        adv = cl_off - sim_off
        scores.append((adv, cl_off, sim_off, (i, j, k)))
    scores.sort(reverse=True)
    print(f'Triad enumeration done in {time.time()-t3:.1f}s. Total triads: {len(scores)}')

    qbc = sum(1 for s in scores if s[0] > 0)
    print()
    print(f'Total triads: {len(scores)}')
    print(f'QBC count: {qbc} ({100*qbc/len(scores):.2f}%)')
    print(f'Max advantage: {scores[0][0]*100:+.2f}pp')
    print(f'Median advantage: {scores[len(scores)//2][0]*100:+.2f}pp')

    print('\nTop-10 QBC triads:')
    for rank, (adv, cl, sim, idx) in enumerate(scores[:10], 1):
        if adv <= 0:
            break
        print(f'  #{rank}  adv=+{adv*100:.2f}pp  cl={cl:.4f}  sim={sim:.4f}')
        for i in idx:
            print(f'         {doc_names[i]}')

    by_cl = sorted(scores, key=lambda x: x[1], reverse=True)
    print('\nTop-5 highest-classical triads:')
    for rank, (adv, cl, sim, idx) in enumerate(by_cl[:5], 1):
        print(f'  #{rank}  cl={cl:.4f}  sim={sim:.4f}  adv={adv*100:+.2f}pp')
        for i in idx:
            print(f'         {doc_names[i]}')

    OUT_DIR = PROJ_ROOT / 'outputs'
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT = OUT_DIR / f'{args.label}-corpus-qbc-iter103.json'

    OUT.write_text(json.dumps({
        'schema': 'sinister-snap-api-quantum.generic-corpus-qbc.v1',
        'label': args.label,
        'root': str(root),
        'n_docs_found': pre_cap,
        'n_docs_used': N,
        'cap': args.cap,
        'doc_names': doc_names,
        'sim_variant': 'zzfm-r1-K4',
        'total_triads': len(scores),
        'qbc_count': qbc,
        'qbc_pct': qbc / len(scores) * 100 if scores else 0,
        'max_advantage_pp': scores[0][0] * 100,
        'median_advantage_pp': scores[len(scores)//2][0] * 100,
        'top10_qbc': [
            {'rank': r + 1, 'advantage_pp': s[0] * 100, 'classical': s[1], 'sim': s[2],
             'docs': [doc_names[i] for i in s[3]]}
            for r, s in enumerate(scores[:10]) if s[0] > 0
        ],
        'top5_highest_classical': [
            {'classical': s[1], 'sim': s[2], 'advantage_pp': s[0] * 100,
             'docs': [doc_names[i] for i in s[3]]}
            for s in by_cl[:5]
        ],
        'wall_seconds': time.time() - t0,
    }, indent=2), encoding='utf-8')
    print(f'\n[saved] {OUT}')
    print(f'[total wall] {time.time()-t0:.1f}s')
    return 0


if __name__ == '__main__':
    sys.exit(main())
