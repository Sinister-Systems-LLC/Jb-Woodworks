"""REAL Wukong-180 quantum-kernel memory experiment — 10-second budget.

Author: RKOJ-ELENO :: 2026-05-23

Per operator: 'run the 10 second test to upgrade eve memory'.

Approach: SWAP-test overlap between angle-encoded brain entries on real
WK_C180 hardware. 3 brain entries (Snap-RE triad) → 3 unique pair-kernels
→ 3 QPU submissions @ 1024 shots each. Estimated total cost ~6-10s of
the 120s free-tier budget based on the H+measure rate (0.23s for a
100-shot single-qubit submit) scaled up.

Compares 3 kernels side-by-side:
  - Classical TF-IDF cosine (CPU, free)
  - CPUQVM simulated quantum kernel (Variant B angle-encoding, free)
  - REAL Wukong-180 quantum kernel (the one we paid for in cloud-seconds)

Output:
  outputs/real-qpu-memory-kernel-<UTC>.json
  outputs/real-qpu-memory-kernel-<UTC>.log
"""
from __future__ import annotations

import json
import math
import os
import sys
import time
from pathlib import Path

import numpy as np

# UTF-8 stdout
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
    """Top-K |TF-IDF| features → RY rotation angles, normalized to [0, pi]."""
    if vec.size <= top_k:
        feats = np.zeros(top_k)
        feats[: vec.size] = np.abs(vec)
    else:
        idx = np.argsort(np.abs(vec))[-top_k:]
        feats = np.abs(vec[idx])
    max_v = feats.max() if feats.max() > 0 else 1.0
    return np.pi * feats / max_v


def _build_swap_test_prog(thetas_a: np.ndarray, thetas_b: np.ndarray):
    """SWAP-test circuit on K+K+1 = 2K+1 qubits.

    Register layout:
      ancilla = q[0]
      register A = q[1..K]
      register B = q[K+1..2K]

    For each i, prepare q[1+i] in RY(theta_A_i)|0> and q[K+1+i] in RY(theta_B_i)|0>.
    Then SWAP test: H(0); for each i CSWAP(0, A_i, B_i); H(0); measure(0).
    P(measure=0) = (1 + |<A|B>|²) / 2.
    """
    from pyqpanda3.core import QCircuit, QProg, H, RY, SWAP, measure
    K = len(thetas_a)
    n_qubits = 2 * K + 1
    circ = QCircuit(n_qubits)

    # Encode register A on q[1..K], register B on q[K+1..2K]
    for i in range(K):
        circ << RY(1 + i, float(thetas_a[i]))
        circ << RY(K + 1 + i, float(thetas_b[i]))

    # SWAP test: H on ancilla
    circ << H(0)
    # Controlled-SWAP between A_i and B_i, controlled by ancilla q[0]
    # pyqpanda3 SWAP() returns a Gate; .control([qubit_idx]) wraps as controlled.
    for i in range(K):
        swap_gate = SWAP(1 + i, K + 1 + i)
        # Try to make controlled — pyqpanda3 0.3.5 supports gate.control([q])
        try:
            csw = swap_gate.control([0])
            circ << csw
        except Exception:
            # Fallback decomposition: CSWAP = CNOT(b,a) + Toffoli(ctrl,a,b) + CNOT(b,a)
            from pyqpanda3.core import CNOT, Toffoli
            circ << CNOT(K + 1 + i, 1 + i)
            circ << Toffoli(0, 1 + i, K + 1 + i)
            circ << CNOT(K + 1 + i, 1 + i)
    # H on ancilla
    circ << H(0)

    prog = QProg()
    prog << circ << measure(0, 0)
    return prog, n_qubits


def _swap_overlap_from_counts(counts: dict, shots: int) -> float:
    """|<A|B>|² = 2*P(measure ancilla = 0) - 1, clamped to [0, 1]."""
    c0 = int(counts.get('0', 0))
    p0 = c0 / max(1, shots)
    val = 2 * p0 - 1
    return max(0.0, min(1.0, val))


def main() -> int:
    print('=' * 76)
    print(' Sinister Seraphim :: REAL Wukong-180 Memory-Kernel Experiment (10s budget)')
    print('=' * 76)
    print(f' Run ID: {NOW}')
    print(f' Pre-budget: {remaining_seconds():.3f}s of 120s')

    # Pre-flight: estimate ~10s for the whole run
    check_budget(estimated_seconds=10.0)

    # Brain triad — same as Variant A/B/C local-sim runs for direct comparison
    triad = memory_kernel.TRIAD_DEFAULT[:]
    print(' Triad:')
    for i, t in enumerate(triad):
        print(f'   [{i}] {t}')

    # TF-IDF + classical baseline + local-sim quantum reference
    print('\n [classical] computing TF-IDF baseline...')
    docs = [memory_kernel._load_brain_entry(f) for f in triad]
    tfidf = memory_kernel._tfidf_vectors(docs)
    classical_k = np.zeros((3, 3))
    for i in range(3):
        for j in range(3):
            classical_k[i, j] = memory_kernel._classical_cosine(tfidf[i], tfidf[j])
    print(f'   classical kernel off-diag mean = {(classical_k.sum() - 3) / 6:.4f}')

    # Local CPUQVM sim baseline (angle encoding, same K=4 as real QPU)
    print('\n [cpuqvm-sim] computing angle-encoded sim baseline (K=4)...')
    angle_states = [memory_kernel._angle_encode_8q(v, top_k=4) for v in tfidf]
    sim_k = np.zeros((3, 3))
    for i in range(3):
        for j in range(3):
            sim_k[i, j] = memory_kernel._quantum_overlap_cpu(angle_states[i], angle_states[j])
    print(f'   sim kernel off-diag mean = {(sim_k.sum() - 3) / 6:.4f}')

    # REAL QPU
    print('\n [WK_C180] connecting to Wukong-180...')
    from pyqpanda3.qcloud.qcloud import QCloudService, QCloudOptions
    svc = QCloudService(api_key=_load_key(), url='http://pyqanda-admin.qpanda.cn')
    backend = svc.backend('WK_C180')
    print(f'   backend acquired: {backend.name()}')

    # Per-entry RY angle vectors
    thetas = [_angle_thetas(v, top_k=4) for v in tfidf]
    for i, th in enumerate(thetas):
        print(f'   thetas[{i}] = {[round(float(x), 3) for x in th]}')

    SHOTS = 1024
    real_k = np.eye(3)
    pair_results = []
    qpu_seconds_total = 0.0
    wall_total_t0 = time.monotonic()

    for (i, j) in [(0, 1), (0, 2), (1, 2)]:
        print(f'\n [WK_C180] pair ({i},{j}) — SWAP-test, K=4, 9-qubit circuit, {SHOTS} shots')
        prog, n_q = _build_swap_test_prog(thetas[i], thetas[j])
        opts = QCloudOptions()
        opts.set_mapping(True)
        opts.set_optimization(True)
        opts.set_is_prob_counts(True)

        # Budget gate — conservative 1s per pair
        check_budget(estimated_seconds=1.5)

        t_pair = time.monotonic()
        job = backend.run(prog, SHOTS, opts)
        job_id = job.job_id() if hasattr(job, 'job_id') else '?'
        # Poll
        for _ in range(120):  # up to 2 min wait
            st = str(job.status()).lower()
            if 'finished' in st or 'failed' in st or 'error' in st:
                break
            time.sleep(1)
        res = job.result()
        counts = res.get_counts() if hasattr(res, 'get_counts') else {}
        timing = res.timing_info() if hasattr(res, 'timing_info') else {}
        elapsed = time.monotonic() - t_pair
        qpu_run_ms = float(timing.get('qpuRunTime', 0))
        overlap = _swap_overlap_from_counts(counts, SHOTS)
        real_k[i, j] = overlap
        real_k[j, i] = overlap
        # Conservative budget burn — record the wall as an upper bound
        record_usage(elapsed, purpose=f'memory-kernel-real-qpu-pair-{i}{j}',
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

    # Side-by-side comparison
    print()
    print(' ── 3-way comparison ──')
    print(f'   {"pair":>6}   {"classical":>10}   {"cpuqvm-sim":>12}   {"real-WK_C180":>14}')
    for (i, j) in [(0, 1), (0, 2), (1, 2)]:
        print(f'   ({i},{j})    {classical_k[i,j]: .4f}      {sim_k[i,j]: .4f}        {real_k[i,j]: .4f}')

    cl_mean = (classical_k.sum() - 3) / 6
    sm_mean = (sim_k.sum() - 3) / 6
    rl_mean = (real_k.sum() - 3) / 6
    print(f'   off-diag mean:   {cl_mean: .4f}      {sm_mean: .4f}        {rl_mean: .4f}')

    # Honest verdict
    print('\n ── Honest verdict ──')
    if abs(rl_mean - sm_mean) < 0.05:
        print('   Real QPU agrees with CPUQVM sim — quantum hardware noise is small at K=4.')
    elif rl_mean < sm_mean:
        print('   Real QPU shows LOWER off-diag than sim — hardware noise disrupted')
        print('   the encoding, separating states by decoherence (not necessarily useful).')
    else:
        print('   Real QPU shows HIGHER off-diag than sim — surprising; investigate.')

    if rl_mean > cl_mean + 0.2:
        print('   Real QPU still collapses vs classical TF-IDF — K=4 too small.')
        print('   Real upgrade path: scale to K=8 (17-qubit SWAP test, still well within WK_C180).')
    elif rl_mean < cl_mean:
        print('   Real QPU disagrees with classical in the OPPOSITE direction — strong')
        print('   evidence the encoding is capturing different structure.')
    else:
        print('   Real QPU and classical are roughly aligned at this scale.')

    summary = {
        'schema': 'sinister-seraphim.real-qpu-memory-kernel.v1',
        'run_id': NOW,
        'ts_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'backend': 'WK_C180',
        'shots_per_pair': SHOTS,
        'k_features': 4,
        'n_qubits_per_circuit': 9,
        'triad': triad,
        'classical_kernel_matrix': classical_k.tolist(),
        'cpuqvm_sim_kernel_matrix': sim_k.tolist(),
        'real_qpu_kernel_matrix': real_k.tolist(),
        'classical_off_diag_mean': cl_mean,
        'cpuqvm_sim_off_diag_mean': sm_mean,
        'real_qpu_off_diag_mean': rl_mean,
        'pair_results': pair_results,
        'wall_total_seconds': round(wall_total, 3),
        'qpu_run_seconds_total': round(qpu_seconds_total, 4),
        'budget_remaining_after': remaining_seconds(),
    }
    out_path = OUTPUTS / f'real-qpu-memory-kernel-{NOW}.json'
    out_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f'\n [OK] saved {out_path}')
    print('=' * 76)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
