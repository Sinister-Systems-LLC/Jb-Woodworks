"""REAL Wukong-180 inversion-overlap memory-kernel — shallower than SWAP-test.

Author: RKOJ-ELENO :: 2026-05-23

Per prior empirical finding (2026-05-23T14:10Z): 9-qubit SWAP-test on
Wukong-180 with K=4 RY encoding was too deep — pairs (0,1) and (1,2)
returned P(0)<0.5 (physically impossible for true overlaps), proving
decoherence corrupted the measurement.

Inversion-overlap fix:
  P(all-zero | U_B† · U_A · |0...0⟩) = |⟨B|A⟩|² = |⟨ψ_A|ψ_B⟩|²

  Circuit shape: K qubits only (no ancilla, no CSWAP).
  Depth: 2× encoding depth (forward + inverse).

We run two encodings side-by-side:
  - Simple angle encoding (RY top-K) — should ≈ CPUQVM sim, proves the
    hardware path works at shallow depth.
  - ZZ-feature-map (Havlicek) — has discrimination headroom in sim;
    if real QPU agrees, that's the EVE memory upgrade signal.

Budget gate via budget.check_budget; conservative wall-time recording.
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
SHOTS = 1024


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
    """U = (⊗ RY(-θ_B_i)) · (⊗ RY(θ_A_i)) ; measure all."""
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


def _build_zz_inversion(thetas_a: np.ndarray, thetas_b: np.ndarray, reps: int = 1):
    """ZZ-feature-map U_A then U_B† ; measure all.

    U_FM(θ) = ∏_reps [ H_all · ∏_i RZ(θ_i) on q_i · ∏_{i<j} ZZ(θ_i*θ_j/π) on (q_i,q_j) ]
    U_B† reverses gate order and negates angles.

    ZZ(α) = CNOT(i,j) · RZ(α) on j · CNOT(i,j).
    """
    from pyqpanda3.core import QCircuit, QProg, H, RZ, CNOT, measure
    circ = QCircuit(K)

    def fm_forward(thetas):
        for _ in range(reps):
            for q in range(K):
                circ << H(q)
            for q in range(K):
                circ << RZ(q, float(thetas[q]))
            for i in range(K):
                for j in range(i + 1, K):
                    a = float(thetas[i] * thetas[j] / np.pi)
                    circ << CNOT(i, j)
                    circ << RZ(j, a)
                    circ << CNOT(i, j)

    def fm_inverse(thetas):
        for _ in range(reps):
            # Reverse order, negate angles
            for i in reversed(range(K)):
                for j in reversed(range(i + 1, K)):
                    a = float(thetas[i] * thetas[j] / np.pi)
                    circ << CNOT(i, j)
                    circ << RZ(j, -a)
                    circ << CNOT(i, j)
            for q in range(K):
                circ << RZ(q, float(-thetas[q]))
            for q in range(K):
                circ << H(q)

    fm_forward(thetas_a)
    fm_inverse(thetas_b)

    prog = QProg()
    prog << circ
    for i in range(K):
        prog << measure(i, i)
    return prog


def _overlap_from_counts(counts: dict, shots: int) -> float:
    """P(all-zero outcome) = |⟨B|A⟩|² for inversion-overlap circuit."""
    # All-zero bitstring is '0' * K
    target = '0' * K
    # OriginIR convention puts c[0] first OR last — try both
    if target in counts:
        c = counts[target]
    else:
        # Fallback: substring or single '0'
        c = counts.get('0', 0)
    return c / max(1, shots)


def run_one_pair(backend, opts, prog, label: str) -> dict:
    t0 = time.monotonic()
    check_budget(estimated_seconds=1.5)
    job = backend.run(prog, SHOTS, opts)
    job_id = job.job_id() if hasattr(job, 'job_id') else '?'
    for _ in range(180):
        st = str(job.status()).lower()
        if 'finished' in st or 'failed' in st or 'error' in st:
            break
        time.sleep(1)
    res = job.result()
    counts = res.get_counts() if hasattr(res, 'get_counts') else {}
    timing = res.timing_info() if hasattr(res, 'timing_info') else {}
    elapsed = time.monotonic() - t0
    overlap = _overlap_from_counts(counts, SHOTS)
    record_usage(elapsed, purpose=f'inversion-overlap-{label}', extra={
        'job_id': job_id,
        'shots': SHOTS,
        'overlap': overlap,
        'qpu_run_ms': float(timing.get('qpuRunTime', 0)) if timing else 0.0,
    })
    return {
        'label': label, 'overlap': overlap, 'counts': counts,
        'wall_seconds': round(elapsed, 3),
        'qpu_run_ms': float(timing.get('qpuRunTime', 0)) if timing else 0.0,
        'job_id': job_id,
    }


def main() -> int:
    print('=' * 76)
    print(' Sinister Seraphim :: REAL Wukong-180 INVERSION-OVERLAP (shallower than SWAP)')
    print('=' * 76)
    print(f' Run ID: {NOW}    K={K}    SHOTS={SHOTS}')
    print(f' Pre-budget: {remaining_seconds():.3f}s of 120s')

    triad = memory_kernel.TRIAD_DEFAULT[:]
    docs = [memory_kernel._load_brain_entry(f) for f in triad]
    tfidf = memory_kernel._tfidf_vectors(docs)
    thetas = [_thetas(v, K) for v in tfidf]

    # Classical baseline (free)
    classical_k = np.eye(3)
    for i in range(3):
        for j in range(3):
            if i != j:
                classical_k[i, j] = memory_kernel._classical_cosine(tfidf[i], tfidf[j])
    cl_mean = (classical_k.sum() - 3) / 6
    print(f'\n [classical] off-diag mean = {cl_mean:.4f}')

    # CPUQVM-sim reference for both encodings
    print(' [cpuqvm-sim] computing reference overlaps...')
    sim_angle = np.eye(3)
    sim_zz = np.eye(3)
    angle_states = [memory_kernel._angle_encode_8q(v, top_k=K) for v in tfidf]
    zz_states = [memory_kernel._zz_feature_map_encode_4q(v, top_k=K, reps=1) for v in tfidf]
    for i in range(3):
        for j in range(3):
            if i != j:
                sim_angle[i, j] = memory_kernel._quantum_overlap_cpu(angle_states[i], angle_states[j])
                sim_zz[i, j] = memory_kernel._quantum_overlap_cpu(zz_states[i], zz_states[j])

    # Connect to QPU
    print(' [WK_C180] connecting...')
    from pyqpanda3.qcloud.qcloud import QCloudService, QCloudOptions
    svc = QCloudService(api_key=_load_key(), url='http://pyqanda-admin.qpanda.cn')
    backend = svc.backend('WK_C180')
    opts = QCloudOptions()
    opts.set_mapping(True); opts.set_optimization(True); opts.set_is_prob_counts(True)

    # ---- Experiment 1: ANGLE inversion (depth ~2K) ----
    print(f'\n [exp-1 ANGLE] inversion overlap, K={K} qubits, depth ~{2*K} ──')
    angle_real = np.eye(3)
    angle_results = []
    for (i, j) in [(0, 1), (0, 2), (1, 2)]:
        prog = _build_angle_inversion(thetas[i], thetas[j])
        r = run_one_pair(backend, opts, prog, f'angle-{i}{j}')
        angle_real[i, j] = r['overlap']
        angle_real[j, i] = r['overlap']
        angle_results.append({'i': i, 'j': j, **r})
        print(f'   ({i},{j}) counts={r["counts"]}  overlap={r["overlap"]:.4f}  wall={r["wall_seconds"]}s  qpu_run={r["qpu_run_ms"]}ms')

    # ---- Experiment 2: ZZ-feature-map inversion (deeper, real discrimination test) ----
    print(f'\n [exp-2 ZZ-FM] inversion overlap, K={K} qubits, depth ~{4*K + 2*K*(K-1)*3} ──')
    zz_real = np.eye(3)
    zz_results = []
    for (i, j) in [(0, 1), (0, 2), (1, 2)]:
        prog = _build_zz_inversion(thetas[i], thetas[j], reps=1)
        r = run_one_pair(backend, opts, prog, f'zz-{i}{j}')
        zz_real[i, j] = r['overlap']
        zz_real[j, i] = r['overlap']
        zz_results.append({'i': i, 'j': j, **r})
        print(f'   ({i},{j}) counts={r["counts"]}  overlap={r["overlap"]:.4f}  wall={r["wall_seconds"]}s  qpu_run={r["qpu_run_ms"]}ms')

    # Summary
    a_mean = (angle_real.sum() - 3) / 6
    z_mean = (zz_real.sum() - 3) / 6
    sa_mean = (sim_angle.sum() - 3) / 6
    sz_mean = (sim_zz.sum() - 3) / 6

    print('\n ── 5-way kernel comparison ──')
    print(f'   {"pair":>6}   {"classical":>10}   {"sim-angle":>10}   {"real-angle":>11}   {"sim-zz":>8}   {"real-zz":>8}')
    for (i, j) in [(0, 1), (0, 2), (1, 2)]:
        print(f'   ({i},{j})    {classical_k[i,j]: .4f}      {sim_angle[i,j]: .4f}      {angle_real[i,j]: .4f}      {sim_zz[i,j]: .4f}    {zz_real[i,j]: .4f}')
    print(f'   off-diag mean: {cl_mean: .4f}      {sa_mean: .4f}      {a_mean: .4f}      {sz_mean: .4f}    {z_mean: .4f}')

    print('\n ── Honest verdict ──')
    if a_mean > 0.4:
        print(' [angle real-QPU] off-diag > 0.4 — encoding worked through real hardware,')
        print('                   collapsed-but-not-decohered. Hardware path validated.')
    elif a_mean > 0.05:
        print(' [angle real-QPU] off-diag in (0.05, 0.4) — some hardware noise but recognizable.')
    else:
        print(' [angle real-QPU] off-diag < 0.05 — decoherence dominated even shallow circuit.')

    if abs(z_mean - sz_mean) < 0.1:
        print(' [ZZ-FM real-QPU] tracks sim within 10pp — real discrimination signal preserved.')
    elif z_mean < sz_mean - 0.2:
        print(' [ZZ-FM real-QPU] much lower than sim — depth too high; noise wins.')
    elif z_mean < cl_mean + 0.1:
        print(' [ZZ-FM real-QPU] approaches classical baseline — real discrimination signal!')
    else:
        print(' [ZZ-FM real-QPU] still collapsed; need shallower encoding or fewer reps.')

    summary = {
        'schema': 'sinister-seraphim.inversion-overlap-real-qpu.v1',
        'run_id': NOW, 'k': K, 'shots': SHOTS,
        'triad': triad,
        'classical': classical_k.tolist(), 'classical_off_diag_mean': cl_mean,
        'sim_angle': sim_angle.tolist(), 'sim_angle_off_diag_mean': sa_mean,
        'sim_zz': sim_zz.tolist(), 'sim_zz_off_diag_mean': sz_mean,
        'real_qpu_angle': angle_real.tolist(), 'real_qpu_angle_off_diag_mean': a_mean,
        'real_qpu_zz': zz_real.tolist(), 'real_qpu_zz_off_diag_mean': z_mean,
        'angle_results': angle_results,
        'zz_results': zz_results,
        'budget_remaining_after': remaining_seconds(),
    }
    out = OUTPUTS / f'real-qpu-inversion-overlap-{NOW}.json'
    out.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f'\n [OK] saved {out}    budget remaining (tracker): {remaining_seconds():.3f}s')
    print('=' * 76)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
