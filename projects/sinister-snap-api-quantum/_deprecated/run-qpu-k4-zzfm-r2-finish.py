"""K=4 truncated ZZ-FM reps=2 — FINISH the partial 16:35Z triad.

Author: RKOJ-ELENO :: 2026-05-23

The 16:35Z reps=2 audit landed only pair (0,1) before BudgetExhausted
(pair 1 took 67.45s wall — depth-68 circuits are slow). This script
runs ONLY pairs (0,2) and (1,2) at reps=2 to complete the triad, then
combines all 3 pair results for the full off-diag mean.

Pair (0,1) reps=2 real-QPU result from 16:35Z:
  job_id = '2D227F2F34B1131C903D50B0A1B6A506'
  overlap = 0.1289
  wall_seconds = 67.453

Inherits the build / config / cap logic from run-qpu-k4-zzfm-reps-audit.py.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import numpy as np

try:
    sys.stdout.reconfigure(encoding='utf-8')  # type: ignore[attr-defined]
except Exception:
    pass

SANCTUM_ROOT = Path(os.environ.get('SINISTER_SANCTUM_ROOT', r'D:\Sinister Sanctum'))
SERAPHIM_DIR = SANCTUM_ROOT / 'tools' / 'sinister-seraphim'
THIS_PROJECT = Path(__file__).resolve().parent
if str(SERAPHIM_DIR) not in sys.path:
    sys.path.insert(0, str(SERAPHIM_DIR))
if str(THIS_PROJECT) not in sys.path:
    sys.path.insert(0, str(THIS_PROJECT))

import memory_kernel  # type: ignore  # noqa: E402
from budget import check_budget, record_usage, remaining_seconds  # type: ignore  # noqa: E402

# Import build helpers from the main reps audit script
import importlib.util
_spec = importlib.util.spec_from_file_location('reps_audit', THIS_PROJECT / 'run-qpu-k4-zzfm-reps-audit.py')
_reps = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_reps)  # type: ignore

KEY_PATH = SANCTUM_ROOT / '_vault-personal' / 'licenses' / 'originqc-qcloud-apikey.txt'
OUTPUTS = THIS_PROJECT / 'outputs'
NOW = time.strftime('%Y-%m-%dT%H%M%SZ', time.gmtime())

K = 4
SHOTS = 256
REPS = 2
PAIR_LOOP_CAP_SECONDS = 150.0  # 2 pairs at ~30-67s each
PER_PAIR_STALL_SECONDS = 90.0

# Cached result from 16:35Z partial run
PAIR_01_PRIOR = {
    'i': 0, 'j': 1, 'label': '01',
    'overlap': 0.12890625,
    'wall_seconds': 67.453,
    'qpu_run_ms': 0.0,
    'job_id': '2D227F2F34B1131C903D50B0A1B6A506',
    'source_run': '2026-05-23T163516Z',
    'stalled': False,
}


def _load_key() -> str:
    return ''.join(l.strip() for l in KEY_PATH.read_text(encoding='utf-8').splitlines()
                   if l.strip() and not l.strip().startswith('##'))


def run_one_pair(backend, opts, prog, label: str) -> dict:
    t0 = time.monotonic()
    check_budget(estimated_seconds=4.0)
    job = backend.run(prog, SHOTS, opts)
    job_id = job.job_id() if hasattr(job, 'job_id') else '?'
    stalled = False
    for _ in range(int(PER_PAIR_STALL_SECONDS) + 5):
        st = str(job.status()).lower()
        if 'finished' in st or 'failed' in st or 'error' in st:
            break
        if (time.monotonic() - t0) >= PER_PAIR_STALL_SECONDS:
            stalled = True
            break
        time.sleep(1)
    if stalled:
        elapsed = time.monotonic() - t0
        record_usage(elapsed, purpose=f'k4-zzfm-r{REPS}-{label}-stalled', extra={
            'job_id': job_id, 'shots': SHOTS, 'k': K, 'reps': REPS, 'stalled_at_seconds': elapsed,
        })
        return {'label': label, 'overlap': None, 'counts': {}, 'wall_seconds': round(elapsed, 3),
                'qpu_run_ms': 0.0, 'job_id': job_id, 'stalled': True}
    res = job.result()
    counts = res.get_counts() if hasattr(res, 'get_counts') else {}
    timing = res.timing_info() if hasattr(res, 'timing_info') else {}
    elapsed = time.monotonic() - t0
    overlap = _reps._overlap_from_counts(counts, SHOTS)
    record_usage(elapsed, purpose=f'k4-zzfm-r{REPS}-{label}', extra={
        'job_id': job_id, 'shots': SHOTS, 'k': K, 'reps': REPS, 'overlap': overlap,
        'qpu_run_ms': float(timing.get('qpuRunTime', 0)) if timing else 0.0,
    })
    return {'label': label, 'overlap': overlap, 'counts': counts,
            'wall_seconds': round(elapsed, 3),
            'qpu_run_ms': float(timing.get('qpuRunTime', 0)) if timing else 0.0,
            'job_id': job_id, 'stalled': False}


def main() -> int:
    print('=' * 76)
    print(f' Sinister Seraphim :: K=4 ZZ-FM r={REPS} FINISH :: pairs (0,2) + (1,2)')
    print('=' * 76)
    print(f' Run ID: {NOW}    K={K}    SHOTS={SHOTS}    REPS={REPS}')
    print(f' Cap: {PAIR_LOOP_CAP_SECONDS}s pair-loop, {PER_PAIR_STALL_SECONDS}s per-pair stall')
    print(f' Pre-budget: {remaining_seconds():.3f}s')
    print(f' Prior pair (0,1) from 16:35Z: overlap={PAIR_01_PRIOR["overlap"]:.4f}  (job={PAIR_01_PRIOR["job_id"]})')

    triad = memory_kernel.TRIAD_DEFAULT[:]
    docs = [memory_kernel._load_brain_entry(f) for f in triad]
    tfidf = memory_kernel._tfidf_vectors(docs)
    thetas = [_reps._thetas(v, K) for v in tfidf]

    classical_k = np.eye(3)
    for i in range(3):
        for j in range(3):
            if i != j:
                classical_k[i, j] = memory_kernel._classical_cosine(tfidf[i], tfidf[j])
    cl_mean = (classical_k.sum() - 3) / 6
    print(f'\n [classical] off-diag mean = {cl_mean:.4f}')

    print(' [WK_C180] connecting...')
    t_connect_start = time.monotonic()
    from pyqpanda3.qcloud.qcloud import QCloudService, QCloudOptions
    svc = QCloudService(api_key=_load_key(), url='http://pyqanda-admin.qpanda.cn')
    backend = svc.backend('WK_C180')
    opts = QCloudOptions()
    opts.set_mapping(True); opts.set_optimization(True); opts.set_is_prob_counts(True)
    connect_wall = time.monotonic() - t_connect_start
    print(f'   backend ready (connect+setup: {connect_wall:.2f}s)')

    t_pair_loop_start = time.monotonic()

    print(f'\n [K={K} ZZ-FM r={REPS}] running pairs (0,2) + (1,2) ──')
    real_zz = np.eye(3)
    real_zz[0, 1] = PAIR_01_PRIOR['overlap']
    real_zz[1, 0] = PAIR_01_PRIOR['overlap']
    pair_results = [PAIR_01_PRIOR.copy()]
    completed_new = 0
    aborted = False
    abort_reason = ''
    for (i, j) in [(0, 2), (1, 2)]:
        elapsed_loop = time.monotonic() - t_pair_loop_start
        if elapsed_loop >= PAIR_LOOP_CAP_SECONDS:
            aborted = True
            abort_reason = f'pair_loop_cap_reached:elapsed={elapsed_loop:.2f}s>={PAIR_LOOP_CAP_SECONDS}s'
            print(f'   [ABORT] {abort_reason}')
            break
        prog = _reps._build_zzfm_inversion(thetas[i], thetas[j], reps=REPS)
        r = run_one_pair(backend, opts, prog, f'{i}{j}')
        if r.get('stalled'):
            aborted = True
            abort_reason = f'per_pair_stall:pair=({i},{j}):wall={r["wall_seconds"]}s'
            print(f'   [STALL] {abort_reason}')
            pair_results.append({'i': i, 'j': j, **r})
            break
        real_zz[i, j] = r['overlap']
        real_zz[j, i] = r['overlap']
        pair_results.append({'i': i, 'j': j, **r})
        completed_new += 1
        all_zero = r['counts'].get('0' * K, 0)
        nonzero = sum(1 for v in r['counts'].values() if v > 0)
        print(f'   ({i},{j}) all-zero={all_zero}/{SHOTS}  nonzero={nonzero}  overlap={r["overlap"]:.4f}  wall={r["wall_seconds"]}s  job={r["job_id"]}')

    pair_loop_wall = time.monotonic() - t_pair_loop_start
    pairs_total = 1 + completed_new  # (0,1) carried over + new
    real_mean = ((real_zz.sum() - 3) / 6) if pairs_total == 3 else None

    sim_reps_2 = 0.6189
    sim_pairs = {(0, 1): 0.3411, (0, 2): 0.8072, (1, 2): 0.7083}

    print('\n ── full reps=2 triad audit ──')
    print(f'   {"pair":>8}  {"classical":>10}  {"sim-r2":>8}  {"real-r2":>8}  {"Δ":>10}')
    for (i, j) in [(0, 1), (0, 2), (1, 2)]:
        s = sim_pairs.get((i, j), 0.0)
        r = real_zz[i, j]
        delta = r - s
        print(f'   ({i},{j})       {classical_k[i,j]:.4f}    {s:.4f}    {r:.4f}    {delta:+.4f}')

    print('\n ── verdict ──')
    print(f'   pairs completed (new + carry):  {pairs_total}/3')
    print(f'   pair-loop wall (this run):       {pair_loop_wall:.2f}s')
    print(f'   aborted:                         {aborted}{(" :: " + abort_reason) if aborted else ""}')
    if real_mean is not None:
        delta_vs_sim = real_mean - sim_reps_2
        delta_vs_classical = real_mean - cl_mean
        noise_floor = 1 / (2 ** K)
        delta_vs_noise = real_mean - noise_floor
        print(f'   off-diag real-r2:        {real_mean:.4f}')
        print(f'   off-diag sim-r2:         {sim_reps_2:.4f}    (Δ vs real = {delta_vs_sim:+.4f})')
        print(f'   off-diag classical:      {cl_mean:.4f}    (Δ real-classical = {delta_vs_classical:+.4f})')
        print(f'   uniform-noise floor:     {noise_floor:.4f}    (Δ real-noise = {delta_vs_noise:+.4f})')
        if real_mean < noise_floor + 0.03:
            print('   VERDICT: ❌ real-QPU at/below noise floor — saturated. reps=2 does NOT help in real.')
        elif real_mean < cl_mean + 0.05:
            print('   VERDICT: ⚠️  real-QPU near classical baseline — could be noise OR matching classical.')
            print('             To distinguish would need lower-depth variant or error mitigation.')
        elif real_mean < 0.5 and delta_vs_sim < 0.25:
            print('   VERDICT: 🎯 partial discrimination survives — reps=2 helps in real-QPU (modestly).')
        else:
            print('   VERDICT: 🎯🎯 strong discrimination — reps=2 breaks plateau on real hardware.')

    summary = {
        'schema': 'sinister-seraphim.k4-zzfm-r2-finish.v1',
        'run_id': NOW,
        'k': K, 'shots': SHOTS, 'reps': REPS,
        'pair_loop_cap_seconds': PAIR_LOOP_CAP_SECONDS,
        'per_pair_stall_seconds': PER_PAIR_STALL_SECONDS,
        'triad': triad,
        'classical_kernel': classical_k.tolist(),
        'classical_off_diag_mean': cl_mean,
        'sim_reps_off_diag_mean': sim_reps_2,
        'sim_reps_per_pair': {str(k): v for k, v in sim_pairs.items()},
        'real_qpu_zzfm_reps_kernel': real_zz.tolist(),
        'real_qpu_zzfm_reps_off_diag_mean': real_mean,
        'pairs_completed_this_run': completed_new,
        'pairs_completed_total': pairs_total,
        'pair_results': pair_results,
        'pair_01_carried_from': PAIR_01_PRIOR['source_run'],
        'aborted': aborted,
        'abort_reason': abort_reason,
        'pair_loop_wall_seconds': round(pair_loop_wall, 3),
        'connect_setup_wall_seconds': round(connect_wall, 3),
        'budget_remaining_after': remaining_seconds(),
        'noise_floor_uniform': 1 / (2 ** K),
    }
    out = OUTPUTS / f'k4-zzfm-r{REPS}-finish-{NOW}.json'
    out.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f'\n [OK] saved {out}    budget remaining: {remaining_seconds():.3f}s')
    print('=' * 76)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
