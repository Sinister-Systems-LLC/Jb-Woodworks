"""Iter 102 - Backlog Option 5: Plans-vs-shipped reconciler (cross-corpus).

Author: RKOJ-ELENO :: 2026-05-24

Operator: /loop "complete everything i said to do and keep expanding".

Cross-corpus QBC: 52 plan-docs (_shared-memory/plans/) x 153 brain-entries
(_shared-memory/knowledge/). Question: which plan-docs have quantum-near-equivalent
SHIPPED brain doctrine? Surface them so operator can mark plans complete + avoid
re-implementation.

Approach:
- For every (plan, brain_entry) pair: compute classical TF-IDF cosine + ZZ-FM r=1 K=4
  sim overlap.
- Surface pairs where BOTH are high (>0.30 cl + >0.50 sim) → likely re-implementation
  risk: the plan was a description of what was eventually shipped.
- Also surface pairs where classical is low but sim is high (sim >> cl by 0.2+) →
  the brain entry quantum-aligns with the plan despite different vocabulary
  (operator-actionable: the plan may already be shipped under a different name).

Zero cloud burn. Sim only. Output: outputs/plans-vs-shipped-reconciler-iter102.json
"""
from __future__ import annotations

import json
import sys
import time
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

PLANS_DIR = SANCTUM_ROOT / '_shared-memory' / 'plans'
BRAIN_DIR = SANCTUM_ROOT / '_shared-memory' / 'knowledge'
SKIP_BRAIN = {'README.md', '_INDEX.md', '_TEMPLATE.md'}

t0 = time.time()

plan_paths = sorted(p for p in PLANS_DIR.rglob('*.md'))
brain_paths = sorted(p for p in BRAIN_DIR.glob('*.md') if p.name not in SKIP_BRAIN)

plan_names = [str(p.relative_to(SANCTUM_ROOT)).replace('\\', '/') for p in plan_paths]
brain_names = [str(p.relative_to(SANCTUM_ROOT)).replace('\\', '/') for p in brain_paths]

print(f'Plans:  {len(plan_paths)}')
print(f'Brain:  {len(brain_paths)}')
print(f'Pairs:  {len(plan_paths) * len(brain_paths)}')

# Load all texts
plan_texts = [p.read_text(encoding='utf-8', errors='replace') for p in plan_paths]
brain_texts = [p.read_text(encoding='utf-8', errors='replace') for p in brain_paths]
all_texts = plan_texts + brain_texts
N_PLANS = len(plan_paths)
N_BRAIN = len(brain_paths)

# Single TF-IDF over the combined corpus (so vocab is shared)
print(f'Loaded {N_PLANS + N_BRAIN} docs in {time.time()-t0:.1f}s')
tfidf = _tfidf_vectors(all_texts)
thetas = [_thetas_for_inversion(v, 4) for v in tfidf]
print(f'TF-IDF + thetas built in {time.time()-t0:.1f}s')

# Cross-corpus pair sweep
t1 = time.time()
pairs = []
for pi in range(N_PLANS):
    for bi in range(N_BRAIN):
        global_bi = N_PLANS + bi
        cl = _classical_cosine(tfidf[pi], tfidf[global_bi])
        sim = _sim_inversion_overlap(thetas[pi], thetas[global_bi], 'zzfm', 4, 1)
        pairs.append((pi, bi, cl, sim))
    if (pi + 1) % 10 == 0:
        elapsed = time.time() - t1
        print(f'  plan-row {pi+1}/{N_PLANS} ({elapsed:.0f}s elapsed)')

print(f'Cross-corpus sweep done in {time.time()-t1:.1f}s')

# Sort by classical (paraphrase signal — high cl = plan was rewritten as brain)
by_classical = sorted(pairs, key=lambda x: x[2], reverse=True)

# Sort by sim (quantum-equivalence signal — high sim = plan matches brain structurally)
by_sim = sorted(pairs, key=lambda x: x[3], reverse=True)

# Reconciliation candidates: both high (>0.30 cl + >0.50 sim)
recon = [p for p in pairs if p[2] > 0.30 and p[3] > 0.50]
recon.sort(key=lambda x: -(x[2] + x[3]))

# Sim-only matches (quantum sees alignment classical misses)
sim_only = [p for p in pairs if p[2] < 0.20 and p[3] > 0.65]
sim_only.sort(key=lambda x: -x[3])

print()
print(f'Reconciliation candidates (cl>0.30 AND sim>0.50): {len(recon)}')
print(f'Sim-only matches (cl<0.20 AND sim>0.65 — quantum sees alignment classical misses): {len(sim_only)}')
print()

print('Top-20 reconciliation candidates (plan -> brain, both high):')
for rank, (pi, bi, cl, sim) in enumerate(recon[:20], 1):
    print(f'  #{rank}  cl={cl:.4f}  sim={sim:.4f}  combined={(cl+sim):.4f}')
    print(f'         plan : {plan_names[pi]}')
    print(f'         brain: {brain_names[bi]}')

print()
print('Top-10 sim-only matches (quantum-aligned, classical-divergent):')
for rank, (pi, bi, cl, sim) in enumerate(sim_only[:10], 1):
    print(f'  #{rank}  cl={cl:.4f}  sim={sim:.4f}')
    print(f'         plan : {plan_names[pi]}')
    print(f'         brain: {brain_names[bi]}')

print()
print('Top-10 highest-classical pairs:')
for rank, (pi, bi, cl, sim) in enumerate(by_classical[:10], 1):
    print(f'  #{rank}  cl={cl:.4f}  sim={sim:.4f}')
    print(f'         plan : {plan_names[pi]}')
    print(f'         brain: {brain_names[bi]}')

OUT_DIR = PROJ_ROOT / 'outputs'
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT = OUT_DIR / 'plans-vs-shipped-reconciler-iter102.json'

OUT.write_text(json.dumps({
    'schema': 'sinister-snap-api-quantum.plans-vs-shipped-reconciler.v1',
    'corpus_plans_count': N_PLANS,
    'corpus_brain_count': N_BRAIN,
    'total_pairs': N_PLANS * N_BRAIN,
    'sim_variant': 'zzfm-r1-K4',
    'reconciliation_candidates_count': len(recon),
    'sim_only_matches_count': len(sim_only),
    'top_reconciliation_candidates': [
        {'rank': r + 1, 'classical': cl, 'sim': sim, 'combined': cl + sim,
         'plan': plan_names[pi], 'brain': brain_names[bi]}
        for r, (pi, bi, cl, sim) in enumerate(recon[:30])
    ],
    'top_sim_only_matches': [
        {'rank': r + 1, 'classical': cl, 'sim': sim,
         'plan': plan_names[pi], 'brain': brain_names[bi]}
        for r, (pi, bi, cl, sim) in enumerate(sim_only[:20])
    ],
    'top_highest_classical': [
        {'rank': r + 1, 'classical': cl, 'sim': sim,
         'plan': plan_names[pi], 'brain': brain_names[bi]}
        for r, (pi, bi, cl, sim) in enumerate(by_classical[:20])
    ],
    'wall_seconds': time.time() - t0,
}, indent=2), encoding='utf-8')

print()
print(f'[saved] {OUT}')
print(f'[total wall] {time.time()-t0:.1f}s')
