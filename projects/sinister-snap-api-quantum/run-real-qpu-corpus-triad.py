"""Iter 101 - REAL Wukong-180 verification of corpus-triad QBC (10s/triad budget).

Author: RKOJ-ELENO :: 2026-05-24

Operator (verbatim 2026-05-24): 'run the quantum memory tool like you did for snap api
for snapi api emu project again and then the lernel apk snapchat creation. 10 seconds
of quantum on each'.

Generalizes run-real-qpu-memory-kernel.py to accept three arbitrary text-file paths
(NOT brain entries). SWAP-test on 9-qubit K=4 angle-encoded states, 1024 shots/pair.

Usage:
    python run-real-qpu-corpus-triad.py --label snap-emu \
        --doc D:/.../CURRENT-STATE.md \
        --doc D:/.../DECISIONS.md \
        --doc D:/.../NEXT-SESSION-RECIPE.md \
        --classical-off-diag 0.6869 --sim-off-diag 0.2802

Outputs: outputs/real-qpu-corpus-triad-<label>-<UTC>.json
"""
from __future__ import annotations

import argparse
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


def _load_key() -> str:
    return ''.join(l.strip() for l in KEY_PATH.read_text(encoding='utf-8').splitlines()
                   if l.strip() and not l.strip().startswith('##'))


def _angle_thetas(vec: np.ndarray, top_k: int = 4) -> np.ndarray:
    if vec.size <= top_k:
        feats = np.zeros(top_k)
        feats[: vec.size] = np.abs(vec)
    else:
        idx = np.argsort(np.abs(vec))[-top_k:]
        feats = np.abs(vec[idx])
    max_v = feats.max() if feats.max() > 0 else 1.0
    return np.pi * feats / max_v


def _build_swap_test_prog(thetas_a: np.ndarray, thetas_b: np.ndarray):
    from pyqpanda3.core import QCircuit, QProg, H, RY, SWAP, measure
    K = len(thetas_a)
    n_qubits = 2 * K + 1
    circ = QCircuit(n_qubits)
    for i in range(K):
        circ << RY(1 + i, float(thetas_a[i]))
        circ << RY(K + 1 + i, float(thetas_b[i]))
    circ << H(0)
    for i in range(K):
        swap_gate = SWAP(1 + i, K + 1 + i)
        try:
            csw = swap_gate.control([0])
            circ << csw
        except Exception:
            from pyqpanda3.core import CNOT, Toffoli
            circ << CNOT(K + 1 + i, 1 + i)
            circ << Toffoli(0, 1 + i, K + 1 + i)
            circ << CNOT(K + 1 + i, 1 + i)
    circ << H(0)
    prog = QProg()
    prog << circ << measure(0, 0)
    return prog, n_qubits


def _swap_overlap_from_counts(counts: dict, shots: int) -> float:
    c0 = int(counts.get('0', 0))
    p0 = c0 / max(1, shots)
    val = 2 * p0 - 1
    return max(0.0, min(1.0, val))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--label', required=True, help='Label for output file (e.g. snap-emu, kernel-apk-snap-creation)')
    ap.add_argument('--doc', action='append', required=True, help='Doc paths (must specify exactly 3)')
    ap.add_argument('--classical-off-diag', type=float, default=None, help='Reported classical off-diag mean from sim sweep')
    ap.add_argument('--sim-off-diag', type=float, default=None, help='Reported sim off-diag mean from sim sweep')
    ap.add_argument('--reported-advantage-pp', type=float, default=None, help='Reported QBC advantage from sim sweep')
    ap.add_argument('--budget-seconds', type=float, default=10.0, help='Cloud-Wukong budget for this triad')
    args = ap.parse_args()

    if len(args.doc) != 3:
        print(f'ERROR: need exactly 3 --doc paths, got {len(args.doc)}')
        return 2

    paths = [Path(d) for d in args.doc]
    for p in paths:
        if not p.exists():
            print(f'ERROR: missing doc: {p}')
            return 3

    print('=' * 76)
    print(f' Sinister Seraphim :: REAL Wukong-180 Corpus-Triad Verification ({args.label})')
    print('=' * 76)
    print(f' Run ID: {NOW}')
    print(f' Pre-budget: {remaining_seconds():.3f}s of 120s')
    print(f' Triad ({args.label}):')
    for i, p in enumerate(paths):
        print(f'   [{i}] {p.relative_to(SANCTUM_ROOT) if p.is_absolute() else p}')

    # Pre-flight: estimate budget
    check_budget(estimated_seconds=args.budget_seconds)

    # TF-IDF + classical + sim baselines
    print('\n [classical] computing TF-IDF baseline...')
    docs = [p.read_text(encoding='utf-8', errors='replace') for p in paths]
    tfidf = memory_kernel._tfidf_vectors(docs)
    classical_k = np.zeros((3, 3))
    for i in range(3):
        for j in range(3):
            classical_k[i, j] = memory_kernel._classical_cosine(tfidf[i], tfidf[j])
    cl_off = (classical_k.sum() - 3) / 6
    print(f'   classical kernel off-diag mean = {cl_off:.4f}')

    print('\n [cpuqvm-sim] computing angle-encoded sim baseline (K=4)...')
    angle_states = [memory_kernel._angle_encode_8q(v, top_k=4) for v in tfidf]
    sim_k = np.zeros((3, 3))
    for i in range(3):
        for j in range(3):
            sim_k[i, j] = memory_kernel._quantum_overlap_cpu(angle_states[i], angle_states[j])
    sm_off = (sim_k.sum() - 3) / 6
    print(f'   sim kernel off-diag mean = {sm_off:.4f}')

    # REAL QPU
    print('\n [WK_C180] connecting to Wukong-180...')
    from pyqpanda3.qcloud.qcloud import QCloudService, QCloudOptions
    svc = QCloudService(api_key=_load_key(), url='http://pyqanda-admin.qpanda.cn')
    backend = svc.backend('WK_C180')
    print(f'   backend acquired: {backend.name()}')

    thetas = [_angle_thetas(v, top_k=4) for v in tfidf]
    for i, th in enumerate(thetas):
        print(f'   thetas[{i}] = {[round(float(x), 3) for x in th]}')

    SHOTS = 1024
    real_k = np.eye(3)
    pair_results = []
    qpu_seconds_total = 0.0
    wall_total_t0 = time.monotonic()

    for (i, j) in [(0, 1), (0, 2), (1, 2)]:
        print(f'\n [WK_C180] pair ({i},{j}) — SWAP-test K=4, 9-qubit, {SHOTS} shots')
        prog, n_q = _build_swap_test_prog(thetas[i], thetas[j])
        opts = QCloudOptions()
        opts.set_mapping(True)
        opts.set_optimization(True)
        opts.set_is_prob_counts(True)

        check_budget(estimated_seconds=1.5)

        t_pair = time.monotonic()
        job = backend.run(prog, SHOTS, opts)
        job_id = job.job_id() if hasattr(job, 'job_id') else '?'
        for _ in range(120):
            try:
                raw_st = job.status()
            except Exception as e:
                # pyqpanda3 0.3.5 transient "value is not string" — retry next iteration
                time.sleep(1)
                continue
            try:
                st = str(raw_st).lower()
            except Exception:
                st = ''
            if 'finished' in st or 'failed' in st or 'error' in st:
                break
            time.sleep(1)
        # pyqpanda3 0.3.5 transient: job.result() also can raise "value is not string"
        res = None
        for _retry in range(10):
            try:
                res = job.result()
                break
            except Exception:
                time.sleep(2)
        if res is None:
            print(f'   [WARN] job.result() never returned cleanly for pair ({i},{j}); recording empty')
            counts = {}
            timing = {}
        else:
            counts = res.get_counts() if hasattr(res, 'get_counts') else {}
            timing = res.timing_info() if hasattr(res, 'timing_info') else {}
        elapsed = time.monotonic() - t_pair
        qpu_run_ms = float(timing.get('qpuRunTime', 0))
        overlap = _swap_overlap_from_counts(counts, SHOTS)
        real_k[i, j] = overlap
        real_k[j, i] = overlap
        record_usage(elapsed, purpose=f'corpus-triad-{args.label}-pair-{i}{j}',
                     extra={'job_id': job_id, 'qpu_run_ms': qpu_run_ms, 'shots': SHOTS, 'overlap': overlap})
        qpu_seconds_total += qpu_run_ms / 1000.0
        pair_results.append({
            'i': i, 'j': j, 'overlap': overlap, 'counts': counts,
            'wall_seconds': round(elapsed, 3), 'qpu_run_ms': qpu_run_ms,
            'job_id': job_id, 'timing_info': dict(timing) if timing else {},
        })
        print(f'   counts: {counts}')
        print(f'   overlap |<A|B>|² = {overlap:.4f}   wall {elapsed:.2f}s   qpu_run {qpu_run_ms}ms   job {job_id}')

    wall_total = time.monotonic() - wall_total_t0
    print(f'\n [WK_C180] all 3 pairs complete: wall {wall_total:.2f}s, qpu_run total {qpu_seconds_total:.4f}s')
    print(f'   budget after: {remaining_seconds():.3f}s of 120s')

    print()
    print(' ── 3-way comparison ──')
    print(f'   {"pair":>6}   {"classical":>10}   {"cpuqvm-sim":>12}   {"real-WK_C180":>14}')
    for (i, j) in [(0, 1), (0, 2), (1, 2)]:
        print(f'   ({i},{j})    {classical_k[i,j]: .4f}      {sim_k[i,j]: .4f}        {real_k[i,j]: .4f}')

    rl_off = (real_k.sum() - 3) / 6
    print(f'   off-diag mean:   {cl_off: .4f}      {sm_off: .4f}        {rl_off: .4f}')

    print('\n ── Honest verdict ──')
    sim_advantage_pp = (cl_off - sm_off) * 100
    real_advantage_pp = (cl_off - rl_off) * 100
    print(f'   sim QBC advantage (predicted) : {sim_advantage_pp:+.2f}pp')
    print(f'   real QBC advantage (measured) : {real_advantage_pp:+.2f}pp')
    print(f'   delta sim->real               : {real_advantage_pp - sim_advantage_pp:+.2f}pp')
    if abs(rl_off - sm_off) < 0.05:
        print('   Real QPU agrees with CPUQVM sim — sim recipe is faithful at K=4.')
    elif rl_off < sm_off:
        print('   Real QPU shows LOWER off-diag than sim — hardware noise disrupted encoding.')
    else:
        print('   Real QPU shows HIGHER off-diag than sim — surprising; investigate.')

    summary = {
        'schema': 'sinister-seraphim.real-qpu-corpus-triad.v1',
        'label': args.label,
        'run_id': NOW,
        'ts_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'backend': 'WK_C180',
        'shots_per_pair': SHOTS,
        'k_features': 4,
        'n_qubits_per_circuit': 9,
        'doc_paths': [str(p) for p in paths],
        'classical_kernel_matrix': classical_k.tolist(),
        'cpuqvm_sim_kernel_matrix': sim_k.tolist(),
        'real_qpu_kernel_matrix': real_k.tolist(),
        'classical_off_diag_mean': cl_off,
        'cpuqvm_sim_off_diag_mean': sm_off,
        'real_qpu_off_diag_mean': rl_off,
        'sim_advantage_pp': sim_advantage_pp,
        'real_advantage_pp': real_advantage_pp,
        'delta_sim_real_pp': real_advantage_pp - sim_advantage_pp,
        'reported_from_sim_sweep': {
            'classical': args.classical_off_diag,
            'sim': args.sim_off_diag,
            'advantage_pp': args.reported_advantage_pp,
        },
        'pair_results': pair_results,
        'wall_total_seconds': round(wall_total, 3),
        'qpu_run_seconds_total': round(qpu_seconds_total, 4),
        'budget_remaining_after': remaining_seconds(),
    }
    out_path = OUTPUTS / f'real-qpu-corpus-triad-{args.label}-{NOW}.json'
    out_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f'\n [saved] {out_path}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
