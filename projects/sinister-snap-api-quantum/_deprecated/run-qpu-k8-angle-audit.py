"""K=8 ANGLE inversion-overlap memory audit on WK_C180.

Author: RKOJ-ELENO :: 2026-05-23

Operator (2026-05-23 RESUME, turn 4): "run the K=8 ANGLE test next and
continue wokring."

Hypothesis: K=4 ANGLE inversion overlap (verified clean at 15:50Z, real
0.8398 vs sim 0.8975 within 6pp) showed the encoding-collapse plateau —
off-diag mean 0.84 vs classical TF-IDF 0.20. The encoding collapses
because the K=4 Hilbert space (16 states) is too small to discriminate
distinct documents. K=8 ANGLE has a 256-state Hilbert space (16× larger)
with depth only doubled (~16 gates), still well within hardware tolerance.

If real-QPU K=8 ANGLE still matches CPUQVM-sim within tolerance → hardware
path holds at this depth. If sim K=8 off-diag mean drops below the K=4
plateau → the encoding can discriminate at this scale. Both confirmations
together = real progress toward a usable quantum memory kernel.

Cap design (inherited + tightened from 15:50Z audit-v2):
  - PAIR_LOOP_CAP_SECONDS = 60.0 (60s pair-loop wall; excludes connect)
  - PER_PAIR_STALL_SECONDS = 60.0 (bumped from 45s — K=8 may compile slower
    on Origin side; allow more headroom before declaring a stall)
  - check_budget(estimated_seconds=2.0) per pair (bumped 1.5→2.0 for K=8)

Triad: same Snap-RE 3-document set as K=4 audit. Side-by-side CPUQVM-sim
inline for the audit.
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

K = 8
SHOTS = 256
PAIR_LOOP_CAP_SECONDS = 60.0
PER_PAIR_STALL_SECONDS = 60.0


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


def _build_angle_inversion(thetas_a: np.ndarray, thetas_b: np.ndarray):
    """U = (⊗ RY(-θ_B_i)) · (⊗ RY(θ_A_i)) on K qubits; measure all."""
    from pyqpanda3.core import QCircuit, QProg, RY, measure
    circ = QCircuit(K)
    for i in range(K):
        circ << RY(i, float(thetas_a[i]))
    for i in range(K):
        circ << RY(i, float(-thetas_b[i]))
    prog = QProg()
    prog << circ
    for i in range(K):
        prog << measure(i, i)
    return prog


def _overlap_from_counts(counts: dict, shots: int) -> float:
    """P(all-zero outcome) = |⟨B|A⟩|² for inversion-overlap circuit."""
    target = '0' * K
    if target in counts:
        c = counts[target]
    else:
        c = counts.get('0', 0)
    return c / max(1, shots)


def run_one_pair(backend, opts, prog, label: str) -> dict:
    t0 = time.monotonic()
    check_budget(estimated_seconds=2.0)
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
        record_usage(elapsed, purpose=f'k8-audit-angle-{label}-stalled', extra={
            'job_id': job_id, 'shots': SHOTS, 'k': K, 'stalled_at_seconds': elapsed,
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
    record_usage(elapsed, purpose=f'k8-audit-angle-{label}', extra={
        'job_id': job_id, 'shots': SHOTS, 'k': K, 'overlap': overlap,
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
    print('=' * 76)
    print(' Sinister Seraphim :: K=8 ANGLE memory audit :: 256-state Hilbert space')
    print('=' * 76)
    print(f' Run ID: {NOW}    K={K}    SHOTS={SHOTS}')
    print(f' Pair-loop cap: {PAIR_LOOP_CAP_SECONDS}s (excludes connect)    Per-pair stall: {PER_PAIR_STALL_SECONDS}s')
    print(f' Pre-budget: {remaining_seconds():.3f}s')

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

    # CPUQVM-sim K=8 ANGLE reference (free, local)
    print(' [cpuqvm-sim K=8 ANGLE] computing reference overlaps...')
    sim_angle = np.eye(3)
    angle_states = [memory_kernel._angle_encode_8q(v, top_k=K) for v in tfidf]
    for i in range(3):
        for j in range(3):
            if i != j:
                sim_angle[i, j] = memory_kernel._quantum_overlap_cpu(angle_states[i], angle_states[j])
    sim_a_mean = (sim_angle.sum() - 3) / 6
    print(f'   sim K=8 ANGLE off-diag mean = {sim_a_mean:.4f}    (K=4 sim was 0.8975 — does it drop?)')

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

    print(f'\n [K=8 angle] inversion overlap, {K} qubits, depth ~{2*K}, SHOTS={SHOTS} ──')
    angle_real = np.eye(3)
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
        prog = _build_angle_inversion(thetas[i], thetas[j])
        r = run_one_pair(backend, opts, prog, f'{i}{j}')
        if r.get('stalled'):
            aborted = True
            abort_reason = f'per_pair_stall:pair=({i},{j}):wall={r["wall_seconds"]}s>={PER_PAIR_STALL_SECONDS}s'
            print(f'   [STALL] {abort_reason} — job left running on Origin, aborting loop.')
            pair_results.append({'i': i, 'j': j, **r})
            break
        angle_real[i, j] = r['overlap']
        angle_real[j, i] = r['overlap']
        pair_results.append({'i': i, 'j': j, **r})
        completed += 1
        # Counts can be huge for K=8 (up to 256 bitstrings); print summary instead of full dict
        nonzero = sum(1 for v in r['counts'].values() if v > 0)
        all_zero_count = r['counts'].get('0' * K, 0)
        print(f'   ({i},{j}) all-zero={all_zero_count}/{SHOTS}  nonzero-bitstrings={nonzero}  overlap={r["overlap"]:.4f}  wall={r["wall_seconds"]}s  job={r["job_id"]}')

    pair_loop_wall = time.monotonic() - t_pair_loop_start
    a_mean = ((angle_real.sum() - 3) / 6) if completed == 3 else None

    pair_table = []
    for (i, j) in [(0, 1), (0, 2), (1, 2)]:
        row = {
            'pair': f'({i},{j})',
            'classical': round(float(classical_k[i, j]), 4),
            'sim_k8_angle': round(float(sim_angle[i, j]), 4),
            'real_qpu_k8_angle': round(float(angle_real[i, j]), 4) if completed >= 1 else None,
        }
        pair_table.append(row)

    print('\n ── K=8 audit comparison ──')
    print(f'   {"pair":>8}  {"classical":>10}  {"sim-K8":>10}  {"real-K8":>10}')
    for row in pair_table:
        real_str = f'{row["real_qpu_k8_angle"]:.4f}' if row['real_qpu_k8_angle'] is not None else '   ----'
        print(f'   {row["pair"]:>8}    {row["classical"]:.4f}      {row["sim_k8_angle"]:.4f}      {real_str}')

    print('\n ── K=8 audit verdict ──')
    print(f'   completed pairs:   {completed}/3')
    print(f'   pair-loop wall:    {pair_loop_wall:.2f}s (cap {PAIR_LOOP_CAP_SECONDS}s)')
    print(f'   connect+setup:     {connect_wall:.2f}s (excluded from cap)')
    print(f'   aborted:           {aborted}{(" :: " + abort_reason) if aborted else ""}')
    if completed == 3 and a_mean is not None:
        delta_vs_sim = abs(a_mean - sim_a_mean)
        delta_vs_classical = a_mean - cl_mean
        sim_vs_k4_sim = sim_a_mean - 0.8975  # K=4 sim baseline from 15:50Z audit
        real_vs_k4_real = a_mean - 0.8398    # K=4 real baseline from 15:50Z audit
        print(f'   off-diag real-K8:   {a_mean:.4f}')
        print(f'   off-diag sim-K8:    {sim_a_mean:.4f}    (Δ vs real = {delta_vs_sim:+.4f})')
        print(f'   off-diag classical: {cl_mean:.4f}    (Δ real-classical = {delta_vs_classical:+.4f})')
        print(f'   K=8 vs K=4 sim:     {sim_vs_k4_sim:+.4f}  ({"plateau breaking" if sim_vs_k4_sim < -0.05 else "plateau holds"})')
        print(f'   K=8 vs K=4 real:    {real_vs_k4_real:+.4f}  ({"discrimination improving" if real_vs_k4_real < -0.05 else "discrimination flat"})')
        if delta_vs_sim < 0.15 and sim_vs_k4_sim < -0.05:
            print('   VERDICT: ✅✅ hardware path holds AT K=8 AND larger Hilbert space breaks plateau.')
        elif delta_vs_sim < 0.15:
            print('   VERDICT: ✅ hardware path holds at K=8 but plateau still present at this scale.')
        elif a_mean > 0.4:
            print('   VERDICT: ⚠️  K=8 real-QPU deviates from sim but encoding survives.')
        else:
            print('   VERDICT: ❌ K=8 real-QPU off-diag collapsed below 0.4 — depth or noise issue.')

    summary = {
        'schema': 'sinister-seraphim.k8-angle-audit.v1',
        'run_id': NOW,
        'k': K, 'shots': SHOTS,
        'pair_loop_cap_seconds': PAIR_LOOP_CAP_SECONDS,
        'per_pair_stall_seconds': PER_PAIR_STALL_SECONDS,
        'triad': triad,
        'classical_kernel': classical_k.tolist(),
        'classical_off_diag_mean': cl_mean,
        'sim_k8_angle_kernel': sim_angle.tolist(),
        'sim_k8_angle_off_diag_mean': sim_a_mean,
        'real_qpu_k8_angle_kernel': angle_real.tolist(),
        'real_qpu_k8_angle_off_diag_mean': a_mean,
        'pair_table': pair_table,
        'pairs_completed': completed,
        'pairs_planned': 3,
        'aborted': aborted,
        'abort_reason': abort_reason,
        'pair_loop_wall_seconds': round(pair_loop_wall, 3),
        'connect_setup_wall_seconds': round(connect_wall, 3),
        'pair_results': pair_results,
        'budget_remaining_after': remaining_seconds(),
        'comparisons_to_k4_15_50Z': {
            'k4_sim_angle_off_diag_mean': 0.8975,
            'k4_real_qpu_angle_off_diag_mean': 0.8398,
            'sim_delta_k8_vs_k4': (sim_a_mean - 0.8975) if sim_a_mean is not None else None,
            'real_delta_k8_vs_k4': (a_mean - 0.8398) if a_mean is not None else None,
        },
    }
    out = OUTPUTS / f'k8-angle-audit-{NOW}.json'
    out.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f'\n [OK] saved {out}    budget remaining: {remaining_seconds():.3f}s')
    print('=' * 76)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
