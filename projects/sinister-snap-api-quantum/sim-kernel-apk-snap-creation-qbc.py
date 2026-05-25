"""Iter 101 - Quantum-expand new target: Kernel-APK Snapchat-creation corpus QBC sweep.

Author: RKOJ-ELENO :: 2026-05-24

Operator (verbatim 2026-05-24): 'run the quantum memory tool like you did for snap api
for snapi api emu project again and then the lernel apk snapchat creation. 10 seconds
of quantum on each'.

Corpus selection for Kernel-APK "Snapchat creation" doctrine:
  - source/source/.claude/memory/*.md (non-archive, non-sessions) = ~15 docs
  - source/source/living-mds/*.md = 5 docs (ACCOUNTS-CREATED, ATTEMPT-LOG, CURRENT-STATE, DECISIONS, GOTCHAS)
  - source/source/{CLAUDE.md, README.md, FULL-AUTONOMY-PLAN.md, RESUME-HERE.md, CHEATSHEET.md, NAVIGATION.md, SESSION-START.md} = 7 docs
Total: ~27 docs. C(27,3) = 2925 triads (sim sweep ~30s).

Question: 3 doctrine docs forming a conflict triangle in the snap-creation pipeline?
The kernel-apk lane has been at v1+ on PER-ACCOUNT-RITUAL — quantum-discriminable
triads would surface drift between rules + concrete operational docs.

Zero cloud burn for THIS script (sim only). Real-QPU follows via dispatcher.
"""
from __future__ import annotations

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

KAPK_ROOT = SANCTUM_ROOT / 'projects' / 'sinister-kernel-apk' / 'source' / 'source'
MEMORY_DIR = KAPK_ROOT / '.claude' / 'memory'
LIVING_DIR = KAPK_ROOT / 'living-mds'
TOPLEVEL_DOCS = [
    'CLAUDE.md', 'README.md', 'FULL-AUTONOMY-PLAN.md', 'RESUME-HERE.md',
    'CHEATSHEET.md', 'NAVIGATION.md', 'SESSION-START.md',
]

t0 = time.time()
docs_paths = []

# .claude/memory non-archive, non-sessions
if MEMORY_DIR.exists():
    for p in sorted(MEMORY_DIR.glob('*.md')):
        docs_paths.append(p)

# living-mds
if LIVING_DIR.exists():
    for p in sorted(LIVING_DIR.glob('*.md')):
        docs_paths.append(p)

# Top-level operational docs
for name in TOPLEVEL_DOCS:
    p = KAPK_ROOT / name
    if p.exists():
        docs_paths.append(p)

print(f'Kernel-APK Snap-creation corpus: {len(docs_paths)} docs')
print(f'  .claude/memory/ : {sum(1 for p in docs_paths if p.parent.name == "memory")}')
print(f'  living-mds/     : {sum(1 for p in docs_paths if p.parent.name == "living-mds")}')
print(f'  top-level       : {sum(1 for p in docs_paths if p.parent.name == "source")}')

if len(docs_paths) < 3:
    print('Not enough docs. Exiting.')
    sys.exit(0)

doc_names = [str(p.relative_to(SANCTUM_ROOT)).replace('\\', '/') for p in docs_paths]
texts = [p.read_text(encoding='utf-8', errors='replace') for p in docs_paths]

print(f'Loaded {len(texts)} docs in {time.time()-t0:.1f}s')

t1 = time.time()
tfidf = _tfidf_vectors(texts)
print(f'TF-IDF built in {time.time()-t1:.1f}s')

N = len(docs_paths)

t2 = time.time()
pair_cl = [[0.0] * N for _ in range(N)]
pair_sim = [[0.0] * N for _ in range(N)]
thetas = [_thetas_for_inversion(v, 4) for v in tfidf]
print(f'Thetas built in {time.time()-t2:.1f}s. Pair-kernel sweep starting (C({N},2)={N*(N-1)//2} pairs)...')

t3 = time.time()
for i in range(N):
    for j in range(i + 1, N):
        pair_cl[i][j] = pair_cl[j][i] = _classical_cosine(tfidf[i], tfidf[j])
        pair_sim[i][j] = pair_sim[j][i] = _sim_inversion_overlap(thetas[i], thetas[j], 'zzfm', 4, 1)

print(f'Pair sweep done in {time.time()-t3:.1f}s')

t4 = time.time()
scores = []
for i, j, k in combinations(range(N), 3):
    cl_off = (pair_cl[i][j] + pair_cl[i][k] + pair_cl[j][k]) / 3
    sim_off = (pair_sim[i][j] + pair_sim[i][k] + pair_sim[j][k]) / 3
    adv = cl_off - sim_off
    scores.append((adv, cl_off, sim_off, (i, j, k)))
scores.sort(reverse=True)
print(f'Triad enumeration done in {time.time()-t4:.1f}s. Total triads: {len(scores)}')

total_triads = len(scores)
qbc = sum(1 for s in scores if s[0] > 0)
print()
print(f'Total triads in Kernel-APK Snap-creation corpus: {total_triads}  (C({N},3))')
print(f'QBC count (sim < classical): {qbc} ({100*qbc/total_triads:.2f}%)')
print(f'Max advantage: {scores[0][0]*100:+.2f}pp')
print(f'Median advantage: {scores[len(scores)//2][0]*100:+.2f}pp')
print()

print('Top-10 QBC triads:')
for rank, (adv, cl, sim, idx) in enumerate(scores[:10], 1):
    if adv <= 0:
        break
    print(f'  #{rank}  adv=+{adv*100:.2f}pp  cl={cl:.4f}  sim={sim:.4f}')
    for i in idx:
        print(f'         {doc_names[i]}')

anti_scores = sorted(scores)
print()
print('Top-5 anti-QBC triads (aligned by feature space):')
for rank, (adv, cl, sim, idx) in enumerate(anti_scores[:5], 1):
    print(f'  #{rank}  adv={adv*100:+.2f}pp  cl={cl:.4f}  sim={sim:.4f}')
    for i in idx:
        print(f'         {doc_names[i]}')

by_cl = sorted(scores, key=lambda x: x[1], reverse=True)
print()
print('Top-5 highest-classical triads:')
for rank, (adv, cl, sim, idx) in enumerate(by_cl[:5], 1):
    print(f'  #{rank}  cl={cl:.4f}  sim={sim:.4f}  adv={adv*100:+.2f}pp')
    for i in idx:
        print(f'         {doc_names[i]}')

OUT_DIR = PROJ_ROOT / 'outputs'
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT = OUT_DIR / 'kernel-apk-snap-creation-qbc-iter101.json'

OUT.write_text(json.dumps({
    'schema': 'sinister-snap-api-quantum.kernel-apk-snap-creation-qbc.v1',
    'corpus_name': 'kernel-apk Snapchat-creation doctrine (.claude/memory + living-mds + top-level)',
    'n_docs': N,
    'doc_names': doc_names,
    'sim_variant': 'zzfm-r1-K4',
    'total_triads': total_triads,
    'qbc_count': qbc,
    'qbc_pct': qbc / total_triads * 100 if total_triads else 0,
    'max_advantage_pp': scores[0][0] * 100,
    'median_advantage_pp': scores[len(scores)//2][0] * 100,
    'top10_qbc': [
        {'rank': r + 1, 'advantage_pp': s[0] * 100, 'classical': s[1], 'sim': s[2],
         'doc_indices': list(s[3]),
         'docs': [doc_names[i] for i in s[3]]}
        for r, s in enumerate(scores[:10]) if s[0] > 0
    ],
    'top5_anti_qbc': [
        {'advantage_pp': s[0] * 100, 'classical': s[1], 'sim': s[2],
         'doc_indices': list(s[3]),
         'docs': [doc_names[i] for i in s[3]]}
        for s in anti_scores[:5]
    ],
    'top5_highest_classical': [
        {'classical': s[1], 'sim': s[2], 'advantage_pp': s[0] * 100,
         'doc_indices': list(s[3]),
         'docs': [doc_names[i] for i in s[3]]}
        for s in by_cl[:5]
    ],
    'wall_seconds': time.time() - t0,
}, indent=2), encoding='utf-8')

print()
print(f'[saved] {OUT}')
print(f'[total wall] {time.time()-t0:.1f}s')
