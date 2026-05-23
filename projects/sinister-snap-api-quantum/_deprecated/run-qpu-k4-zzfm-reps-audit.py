"""K=4 truncated ZZ-feature-map (nearest-neighbor, reps configurable) audit on WK_C180.

Author: RKOJ-ELENO :: 2026-05-23

Operator (2026-05-23 RESUME, turn 5): "continue with the next test if reps=2 helps."

Sim sweep (16:25Z + 16:28Z) showed reps=2 drops sim off-diag to 0.6189 (vs
plain-ANGLE 0.8975 — a 28pp improvement). reps=3 drops to 0.4504 — within
0.25 of classical baseline 0.20. Hardware-noise model predicts depth-68
real-QPU to be saturated near 0 (sim 0.62 minus ~50pp noise = ~0.10).

This script verifies the noise-wall prediction empirically. Either:
  (a) Real-QPU lands near 0 → noise wall confirmed; encoding-limited
      discrimination unreachable on WK_C180 today.
  (b) Real-QPU shows residual discrimination → noise model over-predicts;
      worth iterating further.

Configurable via REPS constant at top. Default: REPS=2 (the reps the
operator approved testing).

Circuit per direction:
  for q in 0..K-1:  H(q)
  for q in 0..K-1:  RZ(q, theta_q)
  for (i,j) in [(0,1), (1,2), (2,3)]:  CNOT(i,j); RZ(j, theta_i*theta_j/pi); CNOT(i,j)
Repeated REPS times.

Depth at K=4 reps=2: 2 × (4 H + 4 RZ + 3 × 3) = 34 forward + 34 inverse = 68 gates.
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
if str(SERAPHIM_DIR) not in sys.path:
    sys.path.insert(0, str(SERAPHIM_DIR))

import memory_kernel  # type: ignore  # noqa: E402
from budget import check_budget, record_usage, remaining_seconds  # type: ignore  # noqa: E402

KEY_PATH = SANCTUM_ROOT / '_vault-personal' / 'licenses' / 'originqc-qcloud-apikey.txt'
THIS_PROJECT = Path(__file__).resolve().parent
OUTPUTS = THIS_PROJECT / 'outputs'
OUTPUTS.mkdir(parents=True, exist_ok=True)
NOW = time.strftime('%Y-%m-%dT%H%M%SZ', time.gmtime())

K = 4
SHOTS = 256
REPS = 2
PAIR_LOOP_CAP_SECONDS = 80.0
PER_PAIR_STALL_SECONDS = 90.0


def _load_key() -> str:
    return ''.join(l.strip() for l in KEY_PATH.read_text(encoding='utf-8').splitlines()
                   if l.strip() and not l.strip().startswith('##'))


def _thetas(vec: np.ndarray, top_k: int = K) -> np.ndarray:
    if vec.size <= top_k:
        feats = np.zeros(top_k)
        feats[: vec.size] = np.abs(vec)
    else:
        idx = np.argsort(np.abs(vec))[-top_k:]
        feats = np.abs(vec[idx])
    max_v = feats.max() if feats.max() > 0 else 1.0
    return np.pi * feats / max_v


def _build_zzfm_inversion(thetas_a: np.ndarray, thetas_b: np.ndarray, reps: int = REPS):
    """U_B† · U_A with U = (truncated ZZ-FM, nearest-neighbor, reps layers).

    Per direction, per rep:
      H_all -> RZ(theta_q) per q -> for i in 0..K-2: CNOT(i,i+1) -> RZ(i+1, theta_i*theta_{i+1}/pi) -> CNOT(i,i+1)

    Inverse reverses gate order + negates RZ angles.
    """
    from pyqpanda3.core import QCircuit, QProg, H, RZ, CNOT, measure
    circ = QCircuit(K)

    def forward(thetas):
        for _ in range(reps):
            for q in range(K):
                circ << H(q)
            for q in range(K):
                circ << RZ(q, float(thetas[q]))
            for i in range(K - 1):
                j = i + 1
                a = float(thetas[i] * thetas[j] / np.pi)
                circ << CNOT(i, j)
                circ << RZ(j, a)
                circ << CNOT(i, j)

    def inverse(thetas):
        for _ in range(reps):
            for i in reversed(range(K - 1)):
                j = i + 1
                a = float(thetas[i] * thetas[j] / np.pi)
                circ << CNOT(i, j)
                circ << RZ(j, -a)
                circ << CNOT(i, j)
            for q in range(K):
                circ << RZ(q, float(-thetas[q]))
            for q in range(K):
                circ << H(q)

    forward(thetas_a)
    inverse(thetas_b)

    prog = QProg()
    prog << circ
    for i in range(K):
        prog << measure(i, i)
    return prog


def _overlap_from_counts(counts: dict, shots: int) -> float:
    target = '0' * K
    if target in counts:
        c = counts[target]
    else:
        c = counts.get('0', 0)
    return c / max(1, shots)


def run_one_pair(backend, opts, prog, label: str) -> dict:
    t0 = time.monotonic()
    check_budget(estimated_seconds=4.0)  # bumped for depth-68 circuits
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
        return {
            'label': label, 'overlap': None, 'counts': {},
            'wall_seconds': round(elapsed, 3),
            'qpu_run_ms': 0.0,
            'job_id': job_id,
            'stalled': True,
        }
    res = job.result()
    counts = res.get_counts() if hasattr(res, 'get_counts') else {}
    timing = res.timing_info() if hasattr(res, 'timing_info') else {}
    elapsed = time.monotonic() - t0
    overlap = _overlap_from_counts(counts, SHOTS)
    record_usage(elapsed, purpose=f'k4-zzfm-r{REPS}-{label}', extra={
        'job_id': job_id, 'shots': SHOTS, 'k': K, 'reps': REPS, 'overlap': overlap,
        'qpu_run_ms': float(timing.get('qpuRunTime', 0)) if timing else 0.0,
    })
    return {
        'label': label, 'overlap': overlap, 'counts': counts,
        'wall_seconds': round(elapsed, 3),
        'qpu_run_ms': float(timing.get('qpuRunTime', 0)) if timing else 0.0,
        'job_id': job_id,
        'stalled': False,
    }


def main() -> int:
    expected_depth = 2 * REPS * (K + K + 3 * 3)  # forward + inverse, each rep has K H + K RZ + 3 CNOT-RZ-CNOT
    print('=' * 76)
    print(f' Sinister Seraphim :: K={K} truncated ZZ-FM r={REPS} audit :: data-parameterized entanglement')
    print('=' * 76)
    print(f' Run ID: {NOW}    K={K}    SHOTS={SHOTS}    REPS={REPS}    expected depth ~{expected_depth}')
    print(f' Pair-loop cap: {PAIR_LOOP_CAP_SECONDS}s (excludes connect)    Per-pair stall: {PER_PAIR_STALL_SECONDS}s')
    print(f' Pre-budget: {remaining_seconds():.3f}s')
    print(f' Sim prediction (sim-check 16:28Z): reps={REPS} sim off-diag = 0.6189')
    print(f' Real-QPU prediction (noise model ~0.012pp/gate × {expected_depth} = ~{expected_depth*0.012:.2f} drop): real ~{0.6189 - expected_depth*0.012:.2f}')

    triad = memory_kernel.TRIAD_DEFAULT[:]
    docs = [memory_kernel._load_brain_entry(f) for f in triad]
    tfidf = memory_kernel._tfidf_vectors(docs)
    thetas = [_thetas(v, K) for v in tfidf]

    classical_k = np.eye(3)
    for i in range(3):
        for j in range(3):
            if i != j:
                classical_k[i, j] = memory_kernel._classical_cosine(tfidf[i], tfidf[j])
    cl_mean = (classical_k.sum() - 3) / 6
    print(f'\n [classical] off-diag mean = {cl_mean:.4f}')

    print(' [WK_C180] connecting (wall time NOT counted against pair-loop cap)...')
    t_connect_start = time.monotonic()
    from pyqpanda3.qcloud.qcloud import QCloudService, QCloudOptions
    svc = QCloudService(api_key=_load_key(), url='http://pyqanda-admin.qpanda.cn')
    backend = svc.backend('WK_C180')
    opts = QCloudOptions()
    opts.set_mapping(True); opts.set_optimization(True); opts.set_is_prob_counts(True)
    connect_wall = time.monotonic() - t_connect_start
    print(f'   backend ready (connect+setup wall: {connect_wall:.2f}s)')

    t_pair_loop_start = time.monotonic()

    print(f'\n [K={K} ZZ-FM r={REPS}] inversion overlap, depth ~{expected_depth}, SHOTS={SHOTS} ──')
    real_zz = np.eye(3)
    pair_results = []
    completed = 0
    aborted = False
    abort_reason = ''
    for (i, j) in [(0, 1), (0, 2), (1, 2)]:
        elapsed_loop = time.monotonic() - t_pair_loop_start
        if elapsed_loop >= PAIR_LOOP_CAP_SECONDS:
            aborted = True
            abort_reason = f'pair_loop_cap_reached:elapsed={elapsed_loop:.2f}s>={PAIR_LOOP_CAP_SECONDS}s'
            print(f'   [ABORT] {abort_reason} — skipping remaining pairs.')
            break
        prog = _build_zzfm_inversion(thetas[i], thetas[j], reps=REPS)
        r = run_one_pair(backend, opts, prog, f'{i}{j}')
        if r.get('stalled'):
            aborted = True
            abort_reason = f'per_pair_stall:pair=({i},{j}):wall={r["wall_seconds"]}s>={PER_PAIR_STALL_SECONDS}s'
            print(f'   [STALL] {abort_reason} — aborting loop.')
            pair_results.append({'i': i, 'j': j, **r})
            break
        real_zz[i, j] = r['overlap']
        real_zz[j, i] = r['overlap']
        pair_results.append({'i': i, 'j': j, **r})
        completed += 1
        all_zero_count = r['counts'].get('0' * K, 0)
        nonzero = sum(1 for v in r['counts'].values() if v > 0)
        print(f'   ({i},{j}) all-zero={all_zero_count}/{SHOTS}  nonzero={nonzero}  overlap={r["overlap"]:.4f}  wall={r["wall_seconds"]}s  job={r["job_id"]}')

    pair_loop_wall = time.monotonic() - t_pair_loop_start
    real_mean = ((real_zz.sum() - 3) / 6) if completed == 3 else None

    sim_reps_2 = 0.6189
    sim_pairs = {(0, 1): 0.3411, (0, 2): 0.8072, (1, 2): 0.7083}

    print('\n ── audit comparison ──')
    print(f'   {"pair":>8}  {"classical":>10}  {"sim-r{REPS}":>10}  {"real-r{REPS}":>10}')
    for (i, j) in [(0, 1), (0, 2), (1, 2)]:
        s = sim_pairs.get((i, j), 0.0)
        r_str = f'{real_zz[i,j]:.4f}' if completed >= 1 else '   ----'
        print(f'   ({i},{j})       {classical_k[i,j]:.4f}      {s:.4f}      {r_str}')

    print('\n ── verdict ──')
    print(f'   completed pairs:   {completed}/3')
    print(f'   pair-loop wall:    {pair_loop_wall:.2f}s (cap {PAIR_LOOP_CAP_SECONDS}s)')
    print(f'   connect+setup:     {connect_wall:.2f}s (excluded from cap)')
    print(f'   aborted:           {aborted}{(" :: " + abort_reason) if aborted else ""}')
    if completed == 3 and real_mean is not None:
        delta_vs_sim = real_mean - sim_reps_2
        delta_vs_predicted = real_mean - (sim_reps_2 - expected_depth * 0.012)
        print(f'   off-diag real-r{REPS}:    {real_mean:.4f}')
        print(f'   off-diag sim-r{REPS}:     {sim_reps_2:.4f}    (Δ vs real = {delta_vs_sim:+.4f})')
        print(f'   off-diag classical:    {cl_mean:.4f}    (Δ real-classical = {real_mean - cl_mean:+.4f})')
        print(f'   noise model predicted: ~{sim_reps_2 - expected_depth*0.012:.4f}    (Δ vs real = {delta_vs_predicted:+.4f})')
        if real_mean < 0.05:
            print('   VERDICT: ❌ real-QPU saturated near 0 — noise wall confirmed at this depth.')
        elif real_mean < 0.25:
            print('   VERDICT: ⚠️  real-QPU at/below classical baseline — noise-dominated.')
        elif abs(delta_vs_sim) < 0.20:
            print('   VERDICT: 🎯 real-QPU tracks sim within 20pp — discrimination signal SURVIVES depth-68!')
        else:
            print('   VERDICT: ⚠️  real-QPU between noise and signal — partial discrimination + noise mix.')

    summary = {
        'schema': 'sinister-seraphim.k4-zzfm-reps-audit.v1',
        'run_id': NOW,
        'k': K, 'shots': SHOTS, 'reps': REPS,
        'expected_depth': expected_depth,
        'pair_loop_cap_seconds': PAIR_LOOP_CAP_SECONDS,
        'per_pair_stall_seconds': PER_PAIR_STALL_SECONDS,
        'triad': triad,
        'classical_kernel': classical_k.tolist(),
        'classical_off_diag_mean': cl_mean,
        'sim_reps_off_diag_mean': sim_reps_2,
        'sim_reps_per_pair': {str(k): v for k, v in sim_pairs.items()},
        'real_qpu_zzfm_reps_kernel': real_zz.tolist(),
        'real_qpu_zzfm_reps_off_diag_mean': real_mean,
        'pairs_completed': completed,
        'pairs_planned': 3,
        'aborted': aborted,
        'abort_reason': abort_reason,
        'pair_loop_wall_seconds': round(pair_loop_wall, 3),
        'connect_setup_wall_seconds': round(connect_wall, 3),
        'pair_results': pair_results,
        'budget_remaining_after': remaining_seconds(),
        'noise_model_predicted_real': sim_reps_2 - expected_depth * 0.012,
    }
    out = OUTPUTS / f'k4-zzfm-r{REPS}-audit-{NOW}.json'
    out.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f'\n [OK] saved {out}    budget remaining: {remaining_seconds():.3f}s')
    print('=' * 76)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
