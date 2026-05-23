"""SIM-ONLY check: does truncated ZZ-FM (nearest-neighbor RZZ only) break
the encoding-collapse plateau? If yes → worth burning cloud budget to
test on real-QPU. If no → save the budget for something else.

Author: RKOJ-ELENO :: 2026-05-23

Zero cloud burn; runs entirely in numpy on local CPU. Per the
cancellation-theorem anchor (MEMORY.md 16:18Z), only data-parameterized
entangling gates can possibly break the structural plateau, because
parameter-free layers cancel in the inversion-overlap protocol. ZZ-FM
RZZ(theta_i * theta_j / pi) gates ARE data-parameterized, so they don't
cancel — but whether they discriminate the triad meaningfully is an
empirical question this script answers for free.

Variant compared:
  - sim K=4 plain ANGLE inversion overlap (baseline; off-diag 0.8975 expected)
  - sim K=4 truncated ZZ-FM nearest-neighbor only, reps=1 (the new test)

ZZ-FM forward at K=4 with nearest-neighbor entanglement:
  for q in 0..K-1:  H q
  for q in 0..K-1:  RZ(q, theta_q)
  for (i,j) in [(0,1), (1,2), (2,3)]:  CNOT(i,j) ; RZ(j, theta_i*theta_j/pi) ; CNOT(i,j)

Depth at K=4 reps=1: 4 H + 4 RZ + 3*(2 CNOT + 1 RZ) = 17 forward + 17 inverse = ~34 total.
"""
from __future__ import annotations

import os
import sys
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

K = 4


def _thetas(vec: np.ndarray, top_k: int = K) -> np.ndarray:
    if vec.size <= top_k:
        feats = np.zeros(top_k)
        feats[: vec.size] = np.abs(vec)
    else:
        idx = np.argsort(np.abs(vec))[-top_k:]
        feats = np.abs(vec[idx])
    max_v = feats.max() if feats.max() > 0 else 1.0
    return np.pi * feats / max_v


def _kron_gate(gate_1q: np.ndarray, target_qubit: int, n: int) -> np.ndarray:
    """Lift a 1-qubit gate to the full n-qubit Hilbert space."""
    I2 = np.eye(2, dtype=np.complex128)
    op = None
    for q in range(n):
        m = gate_1q if q == target_qubit else I2
        op = m if op is None else np.kron(op, m)
    return op


def _h_gate(n: int, target: int) -> np.ndarray:
    H = (1 / np.sqrt(2)) * np.array([[1, 1], [1, -1]], dtype=np.complex128)
    return _kron_gate(H, target, n)


def _rz_gate(n: int, target: int, theta: float) -> np.ndarray:
    e_plus = np.exp(-1j * theta / 2)
    e_minus = np.exp(1j * theta / 2)
    RZ = np.array([[e_plus, 0], [0, e_minus]], dtype=np.complex128)
    return _kron_gate(RZ, target, n)


def _cnot_gate(n: int, control: int, target: int) -> np.ndarray:
    dim = 2 ** n
    op = np.zeros((dim, dim), dtype=np.complex128)
    for i in range(dim):
        c_bit = (i >> (n - 1 - control)) & 1
        if c_bit == 0:
            op[i, i] = 1
        else:
            j = i ^ (1 << (n - 1 - target))
            op[j, i] = 1
    return op


def _zz_fm_unitary(thetas: np.ndarray) -> np.ndarray:
    """Build the full unitary for K=4 truncated ZZ-FM (nearest-neighbor, reps=1)."""
    n = K
    U = np.eye(2 ** n, dtype=np.complex128)
    # H layer
    for q in range(n):
        U = _h_gate(n, q) @ U
    # RZ(theta) per qubit
    for q in range(n):
        U = _rz_gate(n, q, float(thetas[q])) @ U
    # Nearest-neighbor RZZ via CNOT-RZ-CNOT
    for i in range(n - 1):
        j = i + 1
        angle = float(thetas[i] * thetas[j] / np.pi)
        U = _cnot_gate(n, i, j) @ U
        U = _rz_gate(n, j, angle) @ U
        U = _cnot_gate(n, i, j) @ U
    return U


def _zz_fm_state(thetas: np.ndarray) -> np.ndarray:
    """|psi> = U_ZZFM |0...0> for K=4 truncated ZZ-FM."""
    n = K
    state = np.zeros(2 ** n, dtype=np.complex128)
    state[0] = 1.0
    U = _zz_fm_unitary(thetas)
    return U @ state


def _angle_state(thetas: np.ndarray) -> np.ndarray:
    """|psi> = product of RY(theta_i)|0> for K=4 plain ANGLE (baseline)."""
    per_qubit = [np.array([np.cos(t / 2), np.sin(t / 2)], dtype=np.complex128) for t in thetas]
    state = per_qubit[0]
    for q in per_qubit[1:]:
        state = np.kron(state, q)
    return state


def _overlap(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.abs(np.vdot(a, b)) ** 2)


def main() -> int:
    print('=' * 76)
    print(' Sinister Seraphim :: SIM-ONLY check :: truncated ZZ-FM vs plain ANGLE')
    print('=' * 76)
    print(f' K={K}   variant: nearest-neighbor RZZ, reps=1, depth ~34')
    print(' Cloud burn: ZERO (numpy only)')
    print()

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

    # Plain ANGLE baseline
    angle_states = [_angle_state(t) for t in thetas]
    angle_k = np.eye(3)
    for i in range(3):
        for j in range(3):
            if i != j:
                angle_k[i, j] = _overlap(angle_states[i], angle_states[j])
    angle_mean = (angle_k.sum() - 3) / 6

    # Truncated ZZ-FM
    zz_states = [_zz_fm_state(t) for t in thetas]
    zz_k = np.eye(3)
    for i in range(3):
        for j in range(3):
            if i != j:
                zz_k[i, j] = _overlap(zz_states[i], zz_states[j])
    zz_mean = (zz_k.sum() - 3) / 6

    print(f' Triad:')
    for i, t in enumerate(triad):
        print(f'   [{i}] {t}')
    print()
    print(f'   {"pair":>8}  {"classical":>10}  {"plain-ANGLE":>11}  {"truncated-ZZ-FM":>15}')
    for (i, j) in [(0, 1), (0, 2), (1, 2)]:
        print(f'   ({i},{j})       {classical_k[i,j]:.4f}        {angle_k[i,j]:.4f}           {zz_k[i,j]:.4f}')
    print(f'   off-diag    {cl_mean:.4f}        {angle_mean:.4f}           {zz_mean:.4f}')
    print()

    delta_vs_plain = zz_mean - angle_mean
    delta_vs_classical = zz_mean - cl_mean

    print(' ── verdict (sim-only) ──')
    print(f'   plain-ANGLE off-diag:       {angle_mean:.4f}')
    print(f'   truncated-ZZ-FM off-diag:   {zz_mean:.4f}')
    print(f'   Δ vs plain-ANGLE:           {delta_vs_plain:+.4f}')
    print(f'   Δ vs classical baseline:    {delta_vs_classical:+.4f}')
    print()
    if delta_vs_plain < -0.15 and zz_mean < 0.5:
        print('   ✅✅ truncated ZZ-FM BREAKS the plateau in sim — worth real-QPU test.')
        print(f'   Predicted real-QPU off-diag at depth ~34: ~{zz_mean + 0.30:.2f}-{zz_mean + 0.50:.2f}')
        print(f'   (noise drop ~30-50pp per the depth-vs-noise model from 16:18Z)')
    elif delta_vs_plain < -0.15:
        print('   ✅ truncated ZZ-FM improves discrimination in sim but still > 0.5.')
        print('   Real-QPU at depth ~34 likely too noisy to add value — skip.')
    elif delta_vs_plain < -0.05:
        print('   ⚠️  marginal improvement in sim. Real-QPU not worth the depth cost.')
    else:
        print('   ❌ truncated ZZ-FM does NOT improve discrimination in sim.')
        print('   Plateau persists; do not run real-QPU. Try a different feature map.')
    print('=' * 76)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
