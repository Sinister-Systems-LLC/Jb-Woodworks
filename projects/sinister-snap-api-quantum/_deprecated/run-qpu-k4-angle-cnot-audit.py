"""K=4 ANGLE + linear-CNOT-chain inversion-overlap audit on WK_C180.

Author: RKOJ-ELENO :: 2026-05-23

Operator (2026-05-23 RESUME, turn 4 continuation): "continue wokring."

Hypothesis: the encoding-collapse plateau in K=4 ANGLE (sim 0.8975) and
K=8 ANGLE (sim 0.8490) is STRUCTURAL to product-state encoding — bigger
Hilbert space barely moves it (Δ=-0.049). The plateau exists because
each document's state is a tensor product of per-qubit RY rotations,
with NO entanglement to capture cross-feature correlations.

Test: add a single linear-CNOT chain entangling layer BETWEEN the forward
and inverse encodings:

  U_A = (⊗ RY(θ_A_i)) · (CNOT 0→1 · CNOT 1→2 · CNOT 2→3)
  U_B† = (CNOT 2→3 · CNOT 1→2 · CNOT 0→1) · (⊗ RY(-θ_B_i))

Circuit: U_B† · U_A on K qubits, measure all. P(all-zero) = |⟨B|A⟩|².
Depth at K=4: ~12 gates (4 RY + 3 CNOT + 3 CNOT + 4 RY). Well under
the noise wall observed at K=8 depth ~16 (real-vs-sim Δ widened to 23pp).

If sim with CNOT chain shows off-diag drop > 0.1 vs sim K=4 plain ANGLE,
that's the structural plateau being broken — entanglement is doing
discrimination work. If real-QPU also tracks sim within ~10pp, hardware
holds at this depth.

Cap design inherited from K=8 audit (60s pair-loop, 60s per-pair stall).
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


def _angle_cnot_state(thetas: np.ndarray) -> np.ndarray:
    """CPUQVM-equivalent of: (⊗ RY(θ_i)) followed by linear CNOT chain 0→1→2→3.

    Returns the full 2^K statevector. Used for the sim reference baseline.
    """
    # Start with |0...0>
    state = np.zeros(2 ** K, dtype=np.complex128)
    state[0] = 1.0

    # Apply per-qubit RY(θ_i): |psi_i> = cos(θ_i/2)|0> + sin(θ_i/2)|1>
    # Build tensor product from per-qubit states (encoding-only)
    per_qubit = [np.array([np.cos(t / 2), np.sin(t / 2)], dtype=np.complex128) for t in thetas]
    state = per_qubit[0]
    for q in per_qubit[1:]:
        state = np.kron(state, q)

    # Apply linear CNOT chain: CNOT(0→1), CNOT(1→2), CNOT(2→3)
    # For each CNOT(c, t): if c bit is 1, flip t bit
    def cnot(state: np.ndarray, control: int, target: int, n: int) -> np.ndarray:
        out = np.zeros_like(state)
        for i in range(2 ** n):
            # Bit indexing: qubit q is bit (n-1-q) under big-endian kron
            c_bit = (i >> (n - 1 - control)) & 1
            t_bit = (i >> (n - 1 - target)) & 1
            if c_bit == 1:
                j = i ^ (1 << (n - 1 - target))
                out[j] = state[i]
            else:
                out[i] = state[i]
        return out

    for c in range(K - 1):
        state = cnot(state, c, c + 1, K)
    return state


def _build_angle_cnot_inversion(thetas_a: np.ndarray, thetas_b: np.ndarray):
    """U_B† · U_A on K qubits; measure all.

    U_A = (⊗ RY(θ_A_i)) · (linear CNOT chain 0→1→2→...→K-1)
    U_B† = (reverse CNOT chain K-1→K-2→...→1→0) · (⊗ RY(-θ_B_i))

    (CNOT is self-inverse, so U_B† just reverses the gate order.)
    """
    from pyqpanda3.core import QCircuit, QProg, RY, CNOT, measure
    circ = QCircuit(K)
    # U_A: encode A then entangle
    for i in range(K):
        circ << RY(i, float(thetas_a[i]))
    for c in range(K - 1):
        circ << CNOT(c, c + 1)
    # U_B†: reverse entangle then decode -B
    for c in reversed(range(K - 1)):
        circ << CNOT(c, c + 1)
    for i in range(K):
        circ << RY(i, float(-thetas_b[i]))
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


def _quantum_overlap(state_a: np.ndarray, state_b: np.ndarray) -> float:
    """|⟨A|B⟩|² for two 2^K statevectors."""
    inner = np.vdot(state_a, state_b)
    return float(np.abs(inner) ** 2)


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
        record_usage(elapsed, purpose=f'k4-cnot-angle-{label}-stalled', extra={
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
    record_usage(elapsed, purpose=f'k4-cnot-angle-{label}', extra={
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
    print(' Sinister Seraphim :: K=4 ANGLE+CNOT-chain audit :: entanglement minimum-depth')
    print('=' * 76)
    print(f' Run ID: {NOW}    K={K}    SHOTS={SHOTS}    depth ~3K={3*K}')
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

    # CPUQVM-sim K=4 ANGLE+CNOT-chain reference (free, local)
    print(' [cpuqvm-sim K=4 ANGLE+CNOT] computing reference overlaps...')
    sim_states = [_angle_cnot_state(t) for t in thetas]
    sim_cnot = np.eye(3)
    for i in range(3):
        for j in range(3):
            if i != j:
                sim_cnot[i, j] = _quantum_overlap(sim_states[i], sim_states[j])
    sim_cnot_mean = (sim_cnot.sum() - 3) / 6
    print(f'   sim K=4 ANGLE+CNOT off-diag mean = {sim_cnot_mean:.4f}    (plain ANGLE K=4 was 0.8975 — does entanglement drop it?)')

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

    print(f'\n [K=4 angle+CNOT] inversion overlap, depth ~{3*K}, SHOTS={SHOTS} ──')
    real_cnot = np.eye(3)
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
        prog = _build_angle_cnot_inversion(thetas[i], thetas[j])
        r = run_one_pair(backend, opts, prog, f'{i}{j}')
        if r.get('stalled'):
            aborted = True
            abort_reason = f'per_pair_stall:pair=({i},{j}):wall={r["wall_seconds"]}s>={PER_PAIR_STALL_SECONDS}s'
            print(f'   [STALL] {abort_reason} — aborting loop.')
            pair_results.append({'i': i, 'j': j, **r})
            break
        real_cnot[i, j] = r['overlap']
        real_cnot[j, i] = r['overlap']
        pair_results.append({'i': i, 'j': j, **r})
        completed += 1
        all_zero_count = r['counts'].get('0' * K, 0)
        nonzero = sum(1 for v in r['counts'].values() if v > 0)
        print(f'   ({i},{j}) all-zero={all_zero_count}/{SHOTS}  nonzero={nonzero}  overlap={r["overlap"]:.4f}  wall={r["wall_seconds"]}s  job={r["job_id"]}')

    pair_loop_wall = time.monotonic() - t_pair_loop_start
    real_mean = ((real_cnot.sum() - 3) / 6) if completed == 3 else None

    pair_table = []
    for (i, j) in [(0, 1), (0, 2), (1, 2)]:
        row = {
            'pair': f'({i},{j})',
            'classical': round(float(classical_k[i, j]), 4),
            'sim_angle_cnot': round(float(sim_cnot[i, j]), 4),
            'real_qpu_angle_cnot': round(float(real_cnot[i, j]), 4) if completed >= 1 else None,
        }
        pair_table.append(row)

    print('\n ── audit comparison ──')
    print(f'   {"pair":>8}  {"classical":>10}  {"sim-A+CNOT":>11}  {"real-A+CNOT":>12}')
    for row in pair_table:
        real_str = f'{row["real_qpu_angle_cnot"]:.4f}' if row['real_qpu_angle_cnot'] is not None else '   ----  '
        print(f'   {row["pair"]:>8}    {row["classical"]:.4f}       {row["sim_angle_cnot"]:.4f}        {real_str}')

    print('\n ── ANGLE + CNOT-chain entanglement test verdict ──')
    print(f'   completed pairs:   {completed}/3')
    print(f'   pair-loop wall:    {pair_loop_wall:.2f}s (cap {PAIR_LOOP_CAP_SECONDS}s)')
    print(f'   connect+setup:     {connect_wall:.2f}s (excluded from cap)')
    print(f'   aborted:           {aborted}{(" :: " + abort_reason) if aborted else ""}')
    if completed == 3 and real_mean is not None:
        delta_vs_sim = abs(real_mean - sim_cnot_mean)
        delta_real_vs_classical = real_mean - cl_mean
        sim_vs_k4_plain = sim_cnot_mean - 0.8975  # K=4 plain ANGLE sim baseline
        real_vs_k4_plain = real_mean - 0.8398     # K=4 plain ANGLE real baseline
        print(f'   off-diag real:      {real_mean:.4f}')
        print(f'   off-diag sim:       {sim_cnot_mean:.4f}    (Δ vs real = {delta_vs_sim:+.4f})')
        print(f'   off-diag classical: {cl_mean:.4f}    (Δ real-classical = {delta_real_vs_classical:+.4f})')
        print(f'   sim vs K=4 plain:   {sim_vs_k4_plain:+.4f}  ({"PLATEAU BREAKS" if sim_vs_k4_plain < -0.15 else "plateau holds"})')
        print(f'   real vs K=4 plain:  {real_vs_k4_plain:+.4f}')
        if sim_vs_k4_plain < -0.15 and delta_vs_sim < 0.15:
            print('   VERDICT: ✅✅ entanglement BREAKS the structural plateau AND hardware holds.')
        elif sim_vs_k4_plain < -0.15:
            print('   VERDICT: ✅ sim shows entanglement breaks plateau; real has more noise.')
        elif delta_vs_sim < 0.15:
            print('   VERDICT: ⚠️  hardware tracks sim but plateau unchanged (entanglement insufficient).')
        else:
            print('   VERDICT: ❌ both plateau persistent AND hardware drift.')

    summary = {
        'schema': 'sinister-seraphim.k4-angle-cnot-audit.v1',
        'run_id': NOW,
        'k': K, 'shots': SHOTS,
        'pair_loop_cap_seconds': PAIR_LOOP_CAP_SECONDS,
        'per_pair_stall_seconds': PER_PAIR_STALL_SECONDS,
        'triad': triad,
        'classical_kernel': classical_k.tolist(),
        'classical_off_diag_mean': cl_mean,
        'sim_angle_cnot_kernel': sim_cnot.tolist(),
        'sim_angle_cnot_off_diag_mean': sim_cnot_mean,
        'real_qpu_angle_cnot_kernel': real_cnot.tolist(),
        'real_qpu_angle_cnot_off_diag_mean': real_mean,
        'pair_table': pair_table,
        'pairs_completed': completed,
        'pairs_planned': 3,
        'aborted': aborted,
        'abort_reason': abort_reason,
        'pair_loop_wall_seconds': round(pair_loop_wall, 3),
        'connect_setup_wall_seconds': round(connect_wall, 3),
        'pair_results': pair_results,
        'budget_remaining_after': remaining_seconds(),
        'comparisons': {
            'k4_plain_sim_off_diag_mean': 0.8975,
            'k4_plain_real_off_diag_mean': 0.8398,
            'k8_plain_sim_off_diag_mean': 0.8490,
            'k8_plain_real_off_diag_mean': 0.6185,
            'sim_delta_cnot_vs_plain_k4': (sim_cnot_mean - 0.8975) if sim_cnot_mean is not None else None,
            'real_delta_cnot_vs_plain_k4': (real_mean - 0.8398) if real_mean is not None else None,
        },
    }
    out = OUTPUTS / f'k4-angle-cnot-audit-{NOW}.json'
    out.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f'\n [OK] saved {out}    budget remaining: {remaining_seconds():.3f}s')
    print('=' * 76)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
