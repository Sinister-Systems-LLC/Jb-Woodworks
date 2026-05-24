"""Iter 99 — Quantum-Expand Option 3: PROGRESS-cross-lane pattern-finder.

Author: RKOJ-ELENO :: 2026-05-24

Per iter-97 quantum-expand recommendation: detect duplicated work + missed
cross-lane reuse by find-qbc-style triad discovery across ALL fleet lanes'
PROGRESS files.

Strategy:
  1. Load 29 PROGRESS files from `_shared-memory/PROGRESS/`
  2. Chunk each by `## ` headers (most PROGRESS entries start with `## YYYY-MM-DD`)
  3. Keep chunks from the last 3 days + tag with source lane
  4. Filter chunks > 200 chars (signal-grade content)
  5. Run TF-IDF + ZZ-FM r=1 sim sweep
  6. Find triads where 3 chunks from 3 DIFFERENT lanes are quantum-discriminable
     → these are candidate "different lanes describing the same milestone in
        different vocabularies" cases
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timedelta
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

PROGRESS_DIR = SANCTUM_ROOT / '_shared-memory' / 'PROGRESS'
SKIP = {'README.md', '_TEMPLATE.md'}

# Filter to recent entries — last 3 days
NOW = datetime(2026, 5, 25)  # current session date
CUTOFF = NOW - timedelta(days=3)

# Match `## 2026-05-XX...` or `## 2026-05-XXTHHMMSSZ ...` headers
ENTRY_HEADER = re.compile(r'^## (\d{4}-\d{2}-\d{2})[T\s]', re.MULTILINE)

chunks = []  # list of {lane, date, text}
for pfile in sorted(PROGRESS_DIR.glob('*.md')):
    if pfile.name in SKIP:
        continue
    lane = pfile.stem  # e.g., 'Sinister Forge', 'rkoj', 'jb-woodworks'
    text = pfile.read_text(encoding='utf-8', errors='replace')
    # Find all header positions
    headers = [(m.start(), m.group(1)) for m in ENTRY_HEADER.finditer(text)]
    for i, (pos, date_str) in enumerate(headers):
        try:
            ts = datetime.fromisoformat(date_str)
        except ValueError:
            continue
        if ts < CUTOFF:
            continue
        # Extract chunk from this header to the next header (or EOF)
        end = headers[i + 1][0] if i + 1 < len(headers) else len(text)
        chunk_text = text[pos:end].strip()
        if len(chunk_text) < 200:  # filter low-signal stubs
            continue
        chunks.append({'lane': lane, 'date': date_str, 'text': chunk_text})

print(f'Loaded {len(chunks)} chunks from {len(set(c["lane"] for c in chunks))} lanes (cutoff: {CUTOFF.date()})')
if len(chunks) < 6:
    print('Not enough chunks for cross-lane triad analysis.')
    sys.exit(0)

# Cap at 80 to keep enumeration tractable (C(80,3) = 82,160)
# Take the most recent chunks per lane up to 80 total
chunks.sort(key=lambda c: c['date'], reverse=True)
if len(chunks) > 80:
    chunks = chunks[:80]
    print(f'Capped to 80 most-recent chunks')

# Build TF-IDF
docs = [c['text'] for c in chunks]
tfidf = _tfidf_vectors(docs)
N = len(docs)

# Pair classical + pair sim
pair_cl = [[0.0] * N for _ in range(N)]
pair_sim = [[0.0] * N for _ in range(N)]
thetas = [_thetas_for_inversion(v, 4) for v in tfidf]
for i in range(N):
    for j in range(i + 1, N):
        pair_cl[i][j] = pair_cl[j][i] = _classical_cosine(tfidf[i], tfidf[j])
        pair_sim[i][j] = pair_sim[j][i] = _sim_inversion_overlap(thetas[i], thetas[j], 'zzfm', 4, 1)

# Enumerate triads — keep only those where all 3 lanes are different
scores_cross_lane = []
scores_same_lane = []
for i, j, k in combinations(range(N), 3):
    lanes_in_triad = {chunks[i]['lane'], chunks[j]['lane'], chunks[k]['lane']}
    cl_off = (pair_cl[i][j] + pair_cl[i][k] + pair_cl[j][k]) / 3
    sim_off = (pair_sim[i][j] + pair_sim[i][k] + pair_sim[j][k]) / 3
    adv = cl_off - sim_off
    entry = (adv, cl_off, sim_off, (i, j, k), lanes_in_triad)
    if len(lanes_in_triad) == 3:
        scores_cross_lane.append(entry)
    else:
        scores_same_lane.append(entry)

scores_cross_lane.sort(reverse=True)

total_cross = len(scores_cross_lane)
qbc_cross = sum(1 for s in scores_cross_lane if s[0] > 0)
high_classical_cross = [s for s in scores_cross_lane if s[1] > 0.30]
print(f'Cross-lane triads (3 distinct lanes): {total_cross}')
print(f'  QBC (sim<classical): {qbc_cross} ({100*qbc_cross/max(1,total_cross):.2f}%)')
print(f'  High-classical (>0.30): {len(high_classical_cross)}')
print()

# Report top-5 cross-lane QBC triads — these are the candidate "same milestone, different vocabularies"
print('Top-5 cross-lane QBC triads (3 distinct lanes; quantum discriminable):')
for rank, (adv, cl, sim, idx, lanes) in enumerate(scores_cross_lane[:5], 1):
    if adv <= 0:
        break
    print(f'  #{rank}  adv=+{adv*100:.2f}pp  cl={cl:.4f}  sim={sim:.4f}  lanes={sorted(lanes)}')
    for ix in idx:
        c = chunks[ix]
        title_line = c['text'].split('\n')[0][:80]
        print(f'         [{c["lane"]}] {c["date"]}: {title_line}')
    print()

# Top-3 highest-classical cross-lane triads (most lexical overlap across lanes — duplicate-work candidates)
print('Top-3 highest-classical cross-lane triads (most lexical overlap — candidate duplicate work):')
by_cl = sorted(scores_cross_lane, key=lambda x: x[1], reverse=True)
for rank, (adv, cl, sim, idx, lanes) in enumerate(by_cl[:3], 1):
    print(f'  #{rank}  cl={cl:.4f}  sim={sim:.4f}  adv={adv*100:+.2f}pp  lanes={sorted(lanes)}')
    for ix in idx:
        c = chunks[ix]
        title_line = c['text'].split('\n')[0][:80]
        print(f'         [{c["lane"]}] {c["date"]}: {title_line}')
    print()

OUT_DIR = PROJ_ROOT / 'outputs'
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT = OUT_DIR / 'progress-cross-lane-iter99.json'
OUT.write_text(json.dumps({
    'schema': 'sinister-snap-api-quantum.progress-cross-lane.v1',
    'cutoff_date': CUTOFF.date().isoformat(),
    'n_chunks': N,
    'lanes': sorted(set(c['lane'] for c in chunks)),
    'cross_lane_triads_total': total_cross,
    'cross_lane_qbc_count': qbc_cross,
    'cross_lane_qbc_pct': qbc_cross / max(1, total_cross) * 100,
    'top5_qbc_cross_lane': [
        {'rank': r + 1, 'advantage_pp': s[0] * 100, 'classical': s[1], 'sim': s[2],
         'lanes': sorted(s[4]),
         'chunks': [{'lane': chunks[i]['lane'], 'date': chunks[i]['date'],
                     'title': chunks[i]['text'].split(chr(10))[0]} for i in s[3]]}
        for r, s in enumerate(scores_cross_lane[:5]) if s[0] > 0
    ],
    'top3_highest_classical_cross_lane': [
        {'classical': s[1], 'sim': s[2], 'advantage_pp': s[0] * 100,
         'lanes': sorted(s[4]),
         'chunks': [{'lane': chunks[i]['lane'], 'date': chunks[i]['date'],
                     'title': chunks[i]['text'].split(chr(10))[0]} for i in s[3]]}
        for s in by_cl[:3]
    ],
}, indent=2, ensure_ascii=False), encoding='utf-8')
print(f'[saved] {OUT}')
