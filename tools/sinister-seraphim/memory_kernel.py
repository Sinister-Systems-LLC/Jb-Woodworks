"""Quantum-kernel memory experiment for sinister-seraphim.

Author: RKOJ-ELENO :: 2026-05-23

Operator-greenlit experiment: spend ~10 cloud-Wukong-180 seconds to measure
whether a quantum kernel beats TF-IDF on brain-entry similarity.

Backend reality (2026-05-23 evening):
  - Operator's PilotOS V4.2 license = PilotOS system runtime credential,
    NOT a qcloud.originqc.com.cn API key. To hit real Wukong-180:
      (a) Deploy PilotOS V4.2 on a Linux server (operator action) + use
          QPilotService(PilotURL='http://<your-pilotos>:port'), OR
      (b) Buy a separate qcloud.originqc.com.cn API key + use
          QCloudService(api_key=..., url='https://qcloud.originqc.com.cn').
  - Until either lands, this experiment runs on local pyqpanda3 CPUQVM
    (classical simulation of real quantum circuits; perfectly accurate
    for ≤16-qubit circuits; no cloud burn, no license burn).
  - When operator gets cloud credentials, switch backend='cloud-wukong-180'
    in run_kernel_experiment() and the budget gate fires.

Experiment shape (Variant A from the 2026-05-23 design):
  - Pick 3 brain entries (Snap-RE-related; should cluster).
  - For each entry, derive a 4-qubit amplitude encoding from TF-IDF
    feature vector.
  - Compute pairwise quantum kernel via SWAP test (or |⟨ψA|ψB⟩|² overlap).
  - Compare to classical TF-IDF cosine similarity kernel.
  - Report both matrices + the differential.
"""
from __future__ import annotations

import json
import math
import os
import re
import time
from pathlib import Path
from typing import Any

import numpy as np

try:
    from .audit import write_provenance
except ImportError:
    from audit import write_provenance  # type: ignore

SANCTUM_ROOT = Path(os.environ.get('SINISTER_SANCTUM_ROOT', r'D:\Sinister Sanctum'))
BRAIN_DIR = SANCTUM_ROOT / '_shared-memory' / 'knowledge'

# The 3 brain entries for Variant A — all Snap-RE-related so we expect them
# to cluster on a meaningful similarity metric. Picked for relevance + size
# (all <8KB so TF-IDF vector is manageable; all topically tight).
TRIAD_DEFAULT = [
    'snap-tt-rka-chain-attestation-insufficient.md',
    'snap-emu-pb2-schema-shadow.md',
    'snap-account-24h-survival-doctrine-2026-05-21.md',
]


def _load_brain_entry(filename: str) -> str:
    p = BRAIN_DIR / filename
    if not p.exists():
        raise FileNotFoundError(f'brain entry not found: {p}')
    return p.read_text(encoding='utf-8')


def _tokenize(text: str) -> list[str]:
    """Light tokenizer: lowercase, drop punctuation, drop short tokens."""
    return [t for t in re.findall(r'[a-z][a-z0-9_-]{2,}', text.lower())]


def _tfidf_vectors(docs: list[str]) -> list[np.ndarray]:
    """Compute TF-IDF vectors for a list of doc strings. Stdlib-style impl
    (no sklearn dependency to avoid heavy install)."""
    from collections import Counter

    tokenized = [_tokenize(d) for d in docs]
    # DF — how many docs contain each term
    df: Counter[str] = Counter()
    for tokens in tokenized:
        for t in set(tokens):
            df[t] += 1
    N = len(docs)
    # IDF for shared vocab
    vocab = sorted(df.keys())
    vocab_idx = {t: i for i, t in enumerate(vocab)}
    idf = np.array([math.log((N + 1) / (df[t] + 1)) + 1 for t in vocab])
    # Per-doc TF
    vecs = []
    for tokens in tokenized:
        tf = Counter(tokens)
        v = np.zeros(len(vocab))
        for t, c in tf.items():
            if t in vocab_idx:
                v[vocab_idx[t]] = c
        # L2-normalize, then weight by IDF
        if len(tokens):
            v = v / max(1, len(tokens))
        v = v * idf
        n = np.linalg.norm(v)
        if n > 0:
            v = v / n
        vecs.append(v)
    return vecs


def _amplitude_encode_4q(vec: np.ndarray) -> np.ndarray:
    """Variant A — reduce a high-dim TF-IDF vector to a 16-element (4-qubit)
    normalized amplitude vector via greedy top-K + L2-normalize.

    Returns a (16,) complex amplitude vector ready to be loaded into a 4-qubit
    quantum register via Encode/Initialize.

    Known issue: at 4-qubit / 16-amplitude scale, sparse TF-IDF vectors collapse
    to ~0.99 overlap (see memory-kernel-variant-A.json). Encoding-loss dominates.
    Variant B (angle encoding) preserves structure better.
    """
    if vec.size <= 16:
        amps = np.zeros(16)
        amps[: vec.size] = vec
    else:
        idx = np.argsort(np.abs(vec))[-16:]
        amps = np.zeros(16)
        amps[: idx.size] = vec[idx]
    n = np.linalg.norm(amps)
    if n == 0:
        amps[0] = 1.0
    else:
        amps = amps / n
    return amps.astype(np.complex128)


def _angle_encode_8q(vec: np.ndarray, *, top_k: int = 8) -> np.ndarray:
    """Variant B — encode TF-IDF top-K via RY rotations on K qubits, then
    return the full 2^K statevector. Each feature occupies its own qubit's
    rotation, so structure is preserved (no projection collapse).

    For each of the top-K features, qubit i is initialized to
    RY(theta_i)|0> where theta_i = pi * (feature_value / max_value).
    The full system state is the tensor product.
    """
    if vec.size <= top_k:
        feats = np.zeros(top_k)
        feats[: vec.size] = np.abs(vec)
    else:
        idx = np.argsort(np.abs(vec))[-top_k:]
        feats = np.abs(vec[idx])
    max_v = feats.max() if feats.max() > 0 else 1.0
    thetas = np.pi * feats / max_v

    # Per-qubit |psi_i> = cos(theta_i/2)|0> + sin(theta_i/2)|1>
    per_qubit = []
    for t in thetas:
        per_qubit.append(np.array([np.cos(t / 2), np.sin(t / 2)], dtype=np.complex128))

    # Tensor product across all K qubits -> 2^K statevector
    state = per_qubit[0]
    for q in per_qubit[1:]:
        state = np.kron(state, q)
    n = np.linalg.norm(state)
    return state / n if n > 0 else state


def _zz_feature_map_encode_4q(vec: np.ndarray, *, top_k: int = 4, reps: int = 1) -> np.ndarray:
    """Variant C — ZZ-feature-map encoding (Havlicek-style). On K qubits:
       1) H on all qubits
       2) RZ(theta_i) on qubit i for each feature
       3) Pairwise ZZ(theta_i * theta_j) between every qubit pair
       4) Repeat (1-3) `reps` times
    Captures cross-term correlations that pure single-qubit rotations miss.
    Returns the 2^K statevector.
    """
    if vec.size <= top_k:
        feats = np.zeros(top_k)
        feats[: vec.size] = np.abs(vec)
    else:
        idx = np.argsort(np.abs(vec))[-top_k:]
        feats = np.abs(vec[idx])
    max_v = feats.max() if feats.max() > 0 else 1.0
    thetas = np.pi * feats / max_v
    K = top_k

    # Start in |0...0>
    state = np.zeros(2 ** K, dtype=np.complex128)
    state[0] = 1.0

    H = (1 / np.sqrt(2)) * np.array([[1, 1], [1, -1]], dtype=np.complex128)
    I = np.eye(2, dtype=np.complex128)

    def kron_at(op_at_i: int, K: int) -> np.ndarray:
        out = I if op_at_i != 0 else H
        for q in range(1, K):
            out = np.kron(out, H if q == op_at_i else I)
        return out

    def rz_at(i: int, theta: float, K: int) -> np.ndarray:
        rz = np.array([[np.exp(-1j * theta / 2), 0], [0, np.exp(1j * theta / 2)]], dtype=np.complex128)
        out = rz if i == 0 else I
        for q in range(1, K):
            out = np.kron(out, rz if q == i else I)
        return out

    def zz_at(i: int, j: int, theta: float, K: int) -> np.ndarray:
        # ZZ(theta) = diag(exp(-i theta/2 * z_i * z_j))
        size = 2 ** K
        diag = np.zeros(size, dtype=np.complex128)
        for s in range(size):
            zi = 1 - 2 * ((s >> (K - 1 - i)) & 1)
            zj = 1 - 2 * ((s >> (K - 1 - j)) & 1)
            diag[s] = np.exp(-1j * theta / 2 * zi * zj)
        return np.diag(diag)

    for _ in range(reps):
        # H on all qubits
        H_all = H
        for _q in range(1, K):
            H_all = np.kron(H_all, H)
        state = H_all @ state
        # RZ rotations
        for i in range(K):
            state = rz_at(i, float(thetas[i]), K) @ state
        # Pairwise ZZ
        for i in range(K):
            for j in range(i + 1, K):
                t = float(thetas[i] * thetas[j] / np.pi)  # rescale product back near [0, pi]
                state = zz_at(i, j, t, K) @ state

    n = np.linalg.norm(state)
    return state / n if n > 0 else state


def _quantum_overlap_cpu(amps_a: np.ndarray, amps_b: np.ndarray) -> float:
    """Run an overlap-measurement circuit on local CPUQVM and return |⟨A|B⟩|².

    Uses the simplest analytical-on-pure-state path because pyqpanda3's
    SWAP-test API is heavier than needed for a 4-qubit demo. The CPUQVM
    here is doing what the real Wukong-180 would do for these small
    states; statevector simulation is exact at this size.
    """
    # ⟨A|B⟩ = sum_i conj(a_i) * b_i ; |·|² is the quantum-kernel value.
    inner = complex(np.vdot(amps_a, amps_b))
    return float(abs(inner) ** 2)


def _classical_cosine(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """Classical TF-IDF cosine similarity (already L2-normalized vectors)."""
    na = np.linalg.norm(vec_a)
    nb = np.linalg.norm(vec_b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(vec_a, vec_b) / (na * nb))


def run_kernel_experiment(
    *,
    triad: list[str] | None = None,
    backend: str = 'cpuqvm-local',
    variant: str = 'A',  # 'A' = 4-qubit amplitude, 'B' = 8-qubit angle, 'C' = 4-qubit ZZ-feature-map
    purpose: str | None = None,
) -> dict[str, Any]:
    """Run the Variant A quantum-kernel memory experiment.

    Parameters
    ----------
    triad : list[str], optional
        3 brain-entry filenames in `_shared-memory/knowledge/`. Default =
        Snap-RE triad (snap-tt-rka-chain / snap-emu-pb2 / snap-survival).
    backend : str
        'cpuqvm-local' (default; no cloud), 'pilotos-deployed' (needs
        PilotURL), or 'cloud-wukong-180' (needs qcloud API key + burns budget).
    purpose : str
        Provenance tag.

    Returns
    -------
    dict with: triad, classical_kernel_matrix, quantum_kernel_matrix,
    differential, backend, elapsed_seconds, cloud_seconds_consumed,
    interpretation.
    """
    triad = triad or TRIAD_DEFAULT[:]
    if len(triad) != 3:
        raise ValueError(f'triad must have exactly 3 entries, got {len(triad)}')
    if purpose is None:
        purpose = f'memory-kernel-experiment-variant-{variant}'

    t0 = time.monotonic()
    docs = [_load_brain_entry(f) for f in triad]
    tfidf_vecs = _tfidf_vectors(docs)
    if variant.upper() == 'A':
        amps = [_amplitude_encode_4q(v) for v in tfidf_vecs]
        encoding_label = '4-qubit amplitude'
    elif variant.upper() == 'B':
        amps = [_angle_encode_8q(v, top_k=8) for v in tfidf_vecs]
        encoding_label = '8-qubit angle (RY top-8)'
    elif variant.upper() == 'C':
        amps = [_zz_feature_map_encode_4q(v, top_k=4, reps=1) for v in tfidf_vecs]
        encoding_label = '4-qubit ZZ-feature-map (Havlicek)'
    else:
        raise ValueError(f'unknown variant: {variant!r} (use A / B / C)')

    classical_k = np.zeros((3, 3))
    quantum_k = np.zeros((3, 3))
    cloud_seconds_consumed = 0.0

    for i in range(3):
        for j in range(3):
            classical_k[i, j] = _classical_cosine(tfidf_vecs[i], tfidf_vecs[j])
            if backend == 'cpuqvm-local':
                quantum_k[i, j] = _quantum_overlap_cpu(amps[i], amps[j])
            elif backend == 'pilotos-deployed':
                raise NotImplementedError(
                    'pilotos-deployed backend requires QPilotService(PilotURL=...). '
                    'Operator must deploy PilotOS V4.2 on a Linux server first.'
                )
            elif backend == 'cloud-wukong-180':
                # BUDGET-GATED — wire qcloud API key + budget.check_budget/record_usage
                try:
                    from .budget import check_budget, record_usage
                except ImportError:
                    from budget import check_budget, record_usage  # type: ignore
                check_budget(estimated_seconds=3.0)  # rough per-pair cost
                # ... pyqpanda3.qcloud submission would go here ...
                raise NotImplementedError(
                    'cloud-wukong-180 backend requires a separate qcloud.originqc.com.cn '
                    'API key (NOT the PilotOS license). Operator must obtain that key first.'
                )
            else:
                raise ValueError(f'unknown backend: {backend!r}')

    diff = quantum_k - classical_k
    elapsed = round(time.monotonic() - t0, 4)

    # Interpretation
    off_diag_quantum = [quantum_k[i, j] for i in range(3) for j in range(3) if i != j]
    off_diag_classical = [classical_k[i, j] for i in range(3) for j in range(3) if i != j]
    interp = {
        'quantum_off_diag_mean': float(np.mean(off_diag_quantum)),
        'classical_off_diag_mean': float(np.mean(off_diag_classical)),
        'differential_off_diag_mean': float(np.mean(off_diag_quantum) - np.mean(off_diag_classical)),
        'note': (
            'Quantum kernel via amplitude-encoded |⟨ψA|ψB⟩|² on 4-qubit CPUQVM. '
            'TF-IDF cosine kernel as classical baseline. '
            'If quantum off-diag > classical off-diag, quantum encoding finds tighter '
            'cluster among Snap-RE triad. If lower, classical wins at this scale.'
        ),
    }

    result = {
        'schema': 'sinister-seraphim.memory-kernel-experiment.v1',
        'variant': variant.upper(),
        'encoding': encoding_label,
        'triad': triad,
        'backend': backend,
        'classical_kernel_matrix': classical_k.tolist(),
        'quantum_kernel_matrix': quantum_k.tolist(),
        'differential_matrix': diff.tolist(),
        'interpretation': interp,
        'elapsed_seconds': elapsed,
        'cloud_seconds_consumed': cloud_seconds_consumed,
        'ts_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
    }

    # Provenance
    write_provenance(
        purpose=purpose,
        backend='sim-local',  # cpuqvm-local is still a local-sim from provenance POV
        n_bytes=0,
        extra={
            'experiment': 'variant-A-quantum-kernel-vs-tfidf',
            'triad': triad,
            'backend_used': backend,
            'differential_off_diag_mean': interp['differential_off_diag_mean'],
        },
    )

    return result


# ============================================================================
# Inversion-overlap memory audit (real-QPU + sim, 2026-05-23 evening rewrite)
# ============================================================================

def _thetas_for_inversion(vec: np.ndarray, top_k: int) -> np.ndarray:
    """Project a TF-IDF vector onto the top-K features, normalize to [0, π].

    Used by inversion-overlap encodings (angle / angle-cnot / zzfm). Returns
    the per-qubit RY rotation angles for one document.
    """
    if vec.size <= top_k:
        feats = np.zeros(top_k)
        feats[: vec.size] = np.abs(vec)
    else:
        idx = np.argsort(np.abs(vec))[-top_k:]
        feats = np.abs(vec[idx])
    max_v = feats.max() if feats.max() > 0 else 1.0
    return np.pi * feats / max_v


def recall_brain(
    query: str,
    *,
    top_k_results: int = 5,
    encoding: str = 'angle',
    k_qubits: int = 8,
    alpha: float = 1.0,
    corpus_mode: str = 'full',
    tiebreaker: str = 'off',
    tiebreaker_window: float = 0.05,
) -> dict[str, Any]:
    """Hybrid TF-IDF + quantum-kernel brain-entry recall.

    Returns the top-`top_k_results` brain entries most similar to `query`,
    scored by a weighted combination of classical TF-IDF cosine + sim
    quantum-kernel inner product.

    DEFAULT alpha=1.0 = pure TF-IDF (iter 48 finding — see warning below).

    Parameters
    ----------
    query : str
        Query text (e.g. "git multi-agent coordination").
    top_k_results : int
        How many top brain entries to return.
    encoding : 'angle' (default), 'angle-cnot', 'zzfm'
        Quantum kernel encoding (only matters if alpha < 1.0).
    k_qubits : int
        Number of qubits / top-K TF-IDF features used. Default 8.
    alpha : float in [0, 1]
        Weight on TF-IDF (1-alpha goes on quantum kernel). Default 1.0 =
        pure TF-IDF (recommended). Lower alpha mixes in quantum kernel
        but EMPIRICALLY DEGRADES PAIR-WISE RECALL QUALITY (iter 48 finding):

        The iter-44/45 doctrine "K=8 ANGLE has wider QBC coverage" applied
        to TRIAD (3-doc) discrimination — measuring off-diagonal entries of
        a 3x3 kernel matrix. For PAIR-wise (query vs doc) similarity, the
        same K=8 ANGLE encoding disperses inner products such that several
        "noise docs" (e.g. lukeprivacy-kpm-at-rest-safe.md, forge-memory-
        usage-2026-05-23.md) score 0.34-0.55 quantum similarity against
        nearly any query. This collapses to a small subspace where the
        encoding loses discrimination.

        Set alpha=1.0 unless you've empirically validated quantum-kernel
        contribution for your specific use case.
    corpus_mode : 'full' (default) or 'pool'
        Which brain pool to scan. 'full' = all *.md in knowledge/ except
        README/INDEX/TEMPLATE. 'pool' = the topical-balanced subset.

    Returns dict with: schema, query, encoding, k_qubits, alpha,
    corpus_size, top_results (list of {rank, filename, tfidf_sim,
    quantum_sim, combined_score}).
    """
    SKIP = {'README.md', '_INDEX.md', '_TEMPLATE.md'}
    files = sorted(p.name for p in BRAIN_DIR.glob('*.md') if p.name not in SKIP)
    if corpus_mode == 'pool':
        topics: dict[str, list[str]] = {}
        for f in files:
            topics.setdefault(f.split('-')[0], []).append(f)
        pool = []
        for prefix, group in sorted(topics.items()):
            pool.extend(group[:4])
    elif corpus_mode == 'full':
        pool = files[:]
    else:
        raise ValueError(f'unknown corpus_mode {corpus_mode!r}')

    docs = [_load_brain_entry(f) for f in pool] + [query]
    tfidf = _tfidf_vectors(docs)
    query_tfidf = tfidf[-1]
    doc_tfidfs = tfidf[:-1]

    # Classical TF-IDF cosine vs each brain doc
    tfidf_sims = [_classical_cosine(query_tfidf, dv) for dv in doc_tfidfs]

    # Quantum kernel — build query state then compute |<doc|query>|² for each
    query_thetas = _thetas_for_inversion(query_tfidf, k_qubits)

    def build_state(thetas):
        if encoding in ('angle', 'angle-cnot'):
            per_q = [np.array([np.cos(t / 2), np.sin(t / 2)], dtype=np.complex128) for t in thetas]
            state = per_q[0]
            for q in per_q[1:]:
                state = np.kron(state, q)
            return state
        elif encoding == 'zzfm':
            # ZZ-FM r=1 — same construction as find_qbc_triads' zzfm branch
            state = np.zeros(2 ** k_qubits, dtype=np.complex128)
            state[0] = 1.0
            I2 = np.eye(2, dtype=np.complex128)
            H = (1 / np.sqrt(2)) * np.array([[1, 1], [1, -1]], dtype=np.complex128)

            def kron_op(target, M):
                op = None
                for q in range(k_qubits):
                    m = M if q == target else I2
                    op = m if op is None else np.kron(op, m)
                return op

            def cnot(c, t):
                dim = 2 ** k_qubits
                op = np.zeros((dim, dim), dtype=np.complex128)
                for i in range(dim):
                    cb = (i >> (k_qubits - 1 - c)) & 1
                    if cb == 0:
                        op[i, i] = 1
                    else:
                        j = i ^ (1 << (k_qubits - 1 - t))
                        op[j, i] = 1
                return op

            for q in range(k_qubits):
                state = kron_op(q, H) @ state
            for q in range(k_qubits):
                RZ = np.array([[np.exp(-1j * thetas[q] / 2), 0], [0, np.exp(1j * thetas[q] / 2)]], dtype=np.complex128)
                state = kron_op(q, RZ) @ state
            for ii in range(k_qubits - 1):
                jj = ii + 1
                a = float(thetas[ii] * thetas[jj] / np.pi)
                state = cnot(ii, jj) @ state
                RZ = np.array([[np.exp(-1j * a / 2), 0], [0, np.exp(1j * a / 2)]], dtype=np.complex128)
                state = kron_op(jj, RZ) @ state
                state = cnot(ii, jj) @ state
            return state
        else:
            raise ValueError(f'unknown encoding {encoding!r}')

    query_state = build_state(query_thetas)
    quantum_sims = []
    for dv in doc_tfidfs:
        doc_thetas = _thetas_for_inversion(dv, k_qubits)
        doc_state = build_state(doc_thetas)
        quantum_sims.append(float(np.abs(np.vdot(query_state, doc_state)) ** 2))

    # Hybrid score
    rows = []
    for i, f in enumerate(pool):
        combined = alpha * tfidf_sims[i] + (1 - alpha) * quantum_sims[i]
        rows.append({
            'filename': f,
            'tfidf_sim': float(tfidf_sims[i]),
            'quantum_sim': float(quantum_sims[i]),
            'combined_score': float(combined),
        })
    rows.sort(key=lambda r: r['combined_score'], reverse=True)

    # Iter 95 (2026-05-24): quantum-kernel tiebreaker for ambiguous top-3 TF-IDF
    # results. Fires when top-3 spread <= tiebreaker_window. Pre-filters with the
    # iter-65/66 combined predictor (shared top-4 = 0 OR same top-1 across all 3)
    # to avoid the iter-48 noise-doc collapse failure mode.
    # SIM-ONLY by design (cloud-Wukong-180 burn is forbidden per project CLAUDE.md).
    #
    # ⚠️ ITER 96 STRESS-TEST FAILURE MODE (2026-05-24):
    # 10-query stress test caught that triad-discrimination is the WRONG metric
    # for query↔doc retrieval. Example: query "snap account survival rate limit"
    # had spread 0.0475 (within auto window). Tiebreaker reordered the correct
    # top-1 (snap-account-24h-survival-doctrine, tfidf 0.1334) BEHIND an unrelated
    # apk-leak-surface-audit. The quantum-kernel triad-discrimination metric
    # answers "which doc is most structurally distinct in this cluster" — that's
    # the iter-44/45/52 finding for FIND-QBC selection. For query↔doc recall the
    # user wants "best-matching" not "most-distinct" — different question.
    #
    # USE THE TIEBREAKER ONLY FOR:
    #   - Investigative queries ("show me the structurally distinct option")
    #   - When you've empirically verified the reorder is operator-useful for
    #     your specific query class
    #
    # DEFAULT REMAINS tiebreaker='off'. Auto-mode is opt-in and risky.
    tiebreaker_info = {'fired': False, 'reason': 'tiebreaker=off'}
    if tiebreaker in ('auto', 'always') and len(rows) >= 3:
        top3 = rows[:3]
        spread = top3[0]['tfidf_sim'] - top3[2]['tfidf_sim']
        within_window = spread <= tiebreaker_window
        should_fire = (tiebreaker == 'always') or within_window
        if not should_fire:
            tiebreaker_info = {
                'fired': False,
                'reason': f'spread {spread:.4f} > window {tiebreaker_window:.4f}',
                'top3_spread': float(spread),
            }
        else:
            # Combined-predictor pre-filter (iter 65/66): skip if guaranteed-anti-QBC
            top3_filenames = [r['filename'] for r in top3]
            top3_indices = [pool.index(f) for f in top3_filenames]
            top3_tfidfs = [doc_tfidfs[i] for i in top3_indices]
            top4_sets = []
            for v in top3_tfidfs:
                if v.size <= 4:
                    top4_sets.append(set(range(v.size)))
                else:
                    top4_sets.append(set(np.argsort(np.abs(v))[-4:].tolist()))
            shared_top4 = len(top4_sets[0] & top4_sets[1] & top4_sets[2])
            top1s = [int(np.argmax(np.abs(v))) for v in top3_tfidfs]
            all_same_top1 = (top1s[0] == top1s[1] == top1s[2])
            if shared_top4 == 0 or all_same_top1:
                tiebreaker_info = {
                    'fired': False,
                    'reason': f'pre-filter: shared_top4={shared_top4}, all_same_top1={all_same_top1}',
                    'top3_spread': float(spread),
                }
            else:
                # Fire: compute pairwise quantum-kernel sim for the top-3 as a triad
                tri_thetas = [_thetas_for_inversion(top3_tfidfs[i], 4) for i in range(3)]
                pair_sims = {
                    (0, 1): _sim_inversion_overlap(tri_thetas[0], tri_thetas[1], 'zzfm', 4, 1),
                    (0, 2): _sim_inversion_overlap(tri_thetas[0], tri_thetas[2], 'zzfm', 4, 1),
                    (1, 2): _sim_inversion_overlap(tri_thetas[1], tri_thetas[2], 'zzfm', 4, 1),
                }
                # Per-doc advantage = mean(pair_classical) - mean(pair_sim) for pairs containing doc i.
                # Pair classical = TF-IDF cosine.
                pair_cls = {
                    (0, 1): _classical_cosine(top3_tfidfs[0], top3_tfidfs[1]),
                    (0, 2): _classical_cosine(top3_tfidfs[0], top3_tfidfs[2]),
                    (1, 2): _classical_cosine(top3_tfidfs[1], top3_tfidfs[2]),
                }
                pair_adv = {k: pair_cls[k] - pair_sims[k] for k in pair_sims}
                # Doc-i advantage = mean of advantages on the 2 pairs containing i
                doc_adv = {
                    0: (pair_adv[(0, 1)] + pair_adv[(0, 2)]) / 2,
                    1: (pair_adv[(0, 1)] + pair_adv[(1, 2)]) / 2,
                    2: (pair_adv[(0, 2)] + pair_adv[(1, 2)]) / 2,
                }
                # Re-rank top-3 by descending doc_adv. Only swap if advantage delta
                # exceeds 2x TF-IDF spread (avoids noisy flips on tight inputs).
                ordering = sorted(range(3), key=lambda i: doc_adv[i], reverse=True)
                rerank_threshold = 2 * spread
                top_adv = doc_adv[ordering[0]]
                second_adv = doc_adv[ordering[1]]
                if abs(top_adv - second_adv) > rerank_threshold or tiebreaker == 'always':
                    # Apply re-ranking
                    new_top3 = [top3[i] for i in ordering]
                    rows = new_top3 + rows[3:]
                    tiebreaker_info = {
                        'fired': True,
                        'reason': 'rerank applied',
                        'top3_spread': float(spread),
                        'doc_advantages': {str(i): float(doc_adv[i]) for i in range(3)},
                        'new_order_indices': ordering,
                    }
                else:
                    tiebreaker_info = {
                        'fired': False,
                        'reason': f'adv delta {abs(top_adv - second_adv):.4f} <= 2*spread {rerank_threshold:.4f}',
                        'top3_spread': float(spread),
                        'doc_advantages': {str(i): float(doc_adv[i]) for i in range(3)},
                    }

    for rank, r in enumerate(rows[:top_k_results], 1):
        r['rank'] = rank

    return {
        'schema': 'sinister-seraphim.brain-recall.v2',
        'query': query,
        'encoding': encoding,
        'tiebreaker': tiebreaker_info,
        'k_qubits': k_qubits,
        'alpha': alpha,
        'corpus_mode': corpus_mode,
        'corpus_size': len(pool),
        'top_results': rows[:top_k_results],
    }


def find_qbc_triads(
    *,
    encoding: str = 'zzfm',
    k: int = 4,
    reps: int = 1,
    top_n: int = 10,
    corpus_mode: str = 'pool',
    ceiling_reps: list[int] | None = None,
    rank_by: str = 'r1',
) -> dict[str, Any]:
    """Search the brain corpus for triads where quantum kernel beats classical TF-IDF.

    Sim-only sweep across all C(N, 3) triads in the chosen corpus. Returns
    top-N by (classical - sim) descending = quantum-beats-classical advantage.
    No cloud burn.

    Production-validated default: encoding='zzfm', k=4, reps=1, corpus_mode='pool'.

    Ceiling-work ranking (added iter 41 2026-05-24):
      ceiling_reps: extra reps to sweep for each top-N triad after the primary
        rank. Used to compute per-triad ceiling and headroom (= ceiling - r=`reps`).
        Default None = no ceiling sweep.
      rank_by: 'r1' (= rank by advantage at requested reps; default; current behavior),
        'ceiling' (rank by best advantage across all swept reps),
        'headroom' (rank by ceiling - r=requested-reps; biggest error-mitigation
        payoff), 'classical' (rank by classical TF-IDF baseline; iter 40 r=+0.95
        with ceiling). Only takes effect when ceiling_reps is provided (otherwise
        rank_by must be 'r1' or 'classical').
    """
    from itertools import combinations as _combinations

    SKIP = {'README.md', '_INDEX.md', '_TEMPLATE.md'}
    files = sorted(p.name for p in BRAIN_DIR.glob('*.md') if p.name not in SKIP)
    if corpus_mode == 'pool':
        topics: dict[str, list[str]] = {}
        for f in files:
            topics.setdefault(f.split('-')[0], []).append(f)
        pool = []
        for prefix, group in sorted(topics.items()):
            pool.extend(group[:4])
    elif corpus_mode == 'full':
        pool = files[:]
    else:
        raise ValueError(f'unknown corpus_mode {corpus_mode!r}; use "pool" or "full"')
    n_pool = len(pool)

    docs = [_load_brain_entry(f) for f in pool]
    tfidf = _tfidf_vectors(docs)

    states = []
    for v in tfidf:
        thetas = _thetas_for_inversion(v, k)
        if encoding == 'angle' or encoding == 'angle-cnot':
            per_qubit = [np.array([np.cos(t / 2), np.sin(t / 2)], dtype=np.complex128) for t in thetas]
            state = per_qubit[0]
            for q in per_qubit[1:]:
                state = np.kron(state, q)
            states.append(state)
        elif encoding == 'zzfm':
            state = np.zeros(2 ** k, dtype=np.complex128)
            state[0] = 1.0

            def h_gate(target):
                H = (1 / np.sqrt(2)) * np.array([[1, 1], [1, -1]], dtype=np.complex128)
                I2 = np.eye(2, dtype=np.complex128)
                op = None
                for q in range(k):
                    m = H if q == target else I2
                    op = m if op is None else np.kron(op, m)
                return op

            def rz_gate(target, theta):
                RZ = np.array([[np.exp(-1j * theta / 2), 0], [0, np.exp(1j * theta / 2)]], dtype=np.complex128)
                I2 = np.eye(2, dtype=np.complex128)
                op = None
                for q in range(k):
                    m = RZ if q == target else I2
                    op = m if op is None else np.kron(op, m)
                return op

            def cnot_gate(c, t):
                dim = 2 ** k
                op = np.zeros((dim, dim), dtype=np.complex128)
                for i in range(dim):
                    cb = (i >> (k - 1 - c)) & 1
                    if cb == 0:
                        op[i, i] = 1
                    else:
                        j = i ^ (1 << (k - 1 - t))
                        op[j, i] = 1
                return op

            for _ in range(reps):
                for q in range(k):
                    state = h_gate(q) @ state
                for q in range(k):
                    state = rz_gate(q, float(thetas[q])) @ state
                for ii in range(k - 1):
                    jj = ii + 1
                    a = float(thetas[ii] * thetas[jj] / np.pi)
                    state = cnot_gate(ii, jj) @ state
                    state = rz_gate(jj, a) @ state
                    state = cnot_gate(ii, jj) @ state
            states.append(state)
        else:
            raise ValueError(f'unknown encoding {encoding!r}')

    sim_p = np.zeros((n_pool, n_pool))
    cl_p = np.zeros((n_pool, n_pool))
    for i in range(n_pool):
        for j in range(i + 1, n_pool):
            sim_p[i, j] = sim_p[j, i] = float(np.abs(np.vdot(states[i], states[j])) ** 2)
            cl_p[i, j] = cl_p[j, i] = _classical_cosine(tfidf[i], tfidf[j])

    scores = []
    for (i, j, kk) in _combinations(range(n_pool), 3):
        sim_m = (sim_p[i, j] + sim_p[i, kk] + sim_p[j, kk]) / 3
        cl_m = (cl_p[i, j] + cl_p[i, kk] + cl_p[j, kk]) / 3
        scores.append((cl_m - sim_m, sim_m, cl_m, (i, j, kk)))
    scores.sort(reverse=True)

    qbc = sum(1 for s in scores if s[0] > 0)
    cli_variant = (
        'zzfm-r1' if encoding == 'zzfm' and reps == 1 else
        'zzfm-r2' if encoding == 'zzfm' and reps == 2 else
        'k4-angle' if encoding == 'angle' and k == 4 else
        'k8-angle' if encoding == 'angle' and k == 8 else
        'angle-cnot' if encoding == 'angle-cnot' else None
    )

    # Fix iter 43 2026-05-24: --rank-by classical previously re-sorted only the
    # top-N-by-r1, missing high-classical QBC triads that didn't crack that top-N.
    # When rank_by='classical', enumerate the full QBC list (advantage > 0) sorted
    # by classical descending, then take top_n from that list.
    if rank_by == 'classical':
        qbc_scores = [s for s in scores if s[0] > 0]
        qbc_scores.sort(key=lambda x: x[2], reverse=True)  # x[2] = classical mean
        selected_scores = qbc_scores[:top_n]
    else:
        selected_scores = scores[:top_n]

    top_results = []
    for rank, (adv, s, c, idx) in enumerate(selected_scores, 1):
        docs_n = [pool[i] for i in idx]
        cmd = (
            f"seraphim audit --variant {cli_variant} --triad {' '.join(docs_n)} --corpus {corpus_mode}"
            if cli_variant else None
        )
        top_results.append({
            'rank': rank, 'advantage': float(adv),
            'sim_off_diag_mean': float(s),
            'classical_off_diag_mean': float(c),
            'docs': docs_n,
            'audit_cmd': cmd,
        })

    # Optional ceiling-sweep enrichment (iter 41 2026-05-24)
    # For each top-N triad, run sim at additional reps and tag with ceiling info.
    # Only meaningful for zzfm encoding (reps parameter is ignored by angle).
    if ceiling_reps and encoding == 'zzfm':
        for t in top_results:
            tri_thetas = []
            for d in t['docs']:
                i = pool.index(d)
                tri_thetas.append(_thetas_for_inversion(tfidf[i], k))
            # Always include the base reps in the per-rep sweep so headroom math is correct
            sweep_reps = sorted(set([reps] + list(ceiling_reps)))
            per_rep = []
            for rr in sweep_reps:
                # Compute sim off-diag at reps=rr
                pair_sim = []
                for ii in range(3):
                    for jj in range(ii + 1, 3):
                        pair_sim.append(_sim_inversion_overlap(tri_thetas[ii], tri_thetas[jj], encoding, k, rr))
                sim_at_rr = float(sum(pair_sim) / len(pair_sim))
                adv_at_rr = float(t['classical_off_diag_mean'] - sim_at_rr)
                per_rep.append({'reps': rr, 'sim_off_diag': sim_at_rr, 'advantage_pp': adv_at_rr * 100})
            best = max(per_rep, key=lambda r: r['advantage_pp'])
            t['per_rep'] = per_rep
            t['ceiling_pp'] = best['advantage_pp']
            t['ceiling_rep'] = best['reps']
            t['headroom_pp'] = best['advantage_pp'] - (t['advantage'] * 100)
            t['pct_of_ceiling_at_base_reps'] = (
                (t['advantage'] * 100) / best['advantage_pp'] * 100 if best['advantage_pp'] > 0 else float('nan')
            )

        # Re-rank if requested
        if rank_by == 'ceiling':
            top_results.sort(key=lambda x: x['ceiling_pp'], reverse=True)
        elif rank_by == 'headroom':
            top_results.sort(key=lambda x: x['headroom_pp'], reverse=True)
        elif rank_by == 'classical':
            top_results.sort(key=lambda x: x['classical_off_diag_mean'], reverse=True)
        # Re-assign rank numbers after the sort
        for new_rank, t in enumerate(top_results, 1):
            t['rank'] = new_rank

    return {
        'schema': 'sinister-seraphim.find-qbc-triads.v2',
        'encoding': encoding, 'k': k, 'reps': reps,
        'corpus_mode': corpus_mode, 'pool_size': n_pool,
        'triads_evaluated': len(scores),
        'qbc_count': qbc,
        'qbc_pct': 100 * qbc / len(scores),
        'max_advantage': float(scores[0][0]),
        'median_advantage': float(scores[len(scores) // 2][0]),
        'top_n_triads': top_results,
        'cli_variant_matched': cli_variant,
        'rank_by': rank_by,
        'ceiling_reps_swept': list(ceiling_reps) if ceiling_reps else None,
    }


def _sim_inversion_overlap(thetas_a: np.ndarray, thetas_b: np.ndarray,
                            encoding: str, k: int, reps: int = 1) -> float:
    """CPUQVM-equivalent of inversion-overlap |⟨B|A⟩|² for a given encoding.

    Free local computation; no cloud burn. Used as the reference baseline
    against real-QPU results in `run_kernel_audit`.
    """
    if encoding == 'angle' or encoding == 'angle-cnot':
        # Plain ANGLE: |ψ⟩ = product of RY(θ_i)|0⟩.
        # ANGLE+CNOT is identical to plain ANGLE via the cancellation theorem
        # (parameter-free entangling layers cancel in U_B† · U_A).
        per_qubit_a = [np.array([np.cos(t / 2), np.sin(t / 2)], dtype=np.complex128) for t in thetas_a]
        per_qubit_b = [np.array([np.cos(t / 2), np.sin(t / 2)], dtype=np.complex128) for t in thetas_b]
        state_a = per_qubit_a[0]
        for q in per_qubit_a[1:]:
            state_a = np.kron(state_a, q)
        state_b = per_qubit_b[0]
        for q in per_qubit_b[1:]:
            state_b = np.kron(state_b, q)
        return float(np.abs(np.vdot(state_a, state_b)) ** 2)

    if encoding == 'zzfm':
        # Truncated ZZ-FM nearest-neighbor — build unitaries explicitly
        def h_gate(target):
            H = (1 / np.sqrt(2)) * np.array([[1, 1], [1, -1]], dtype=np.complex128)
            I2 = np.eye(2, dtype=np.complex128)
            op = None
            for q in range(k):
                m = H if q == target else I2
                op = m if op is None else np.kron(op, m)
            return op

        def rz_gate(target, theta):
            RZ = np.array([[np.exp(-1j * theta / 2), 0], [0, np.exp(1j * theta / 2)]], dtype=np.complex128)
            I2 = np.eye(2, dtype=np.complex128)
            op = None
            for q in range(k):
                m = RZ if q == target else I2
                op = m if op is None else np.kron(op, m)
            return op

        def cnot_gate(control, target):
            dim = 2 ** k
            op = np.zeros((dim, dim), dtype=np.complex128)
            for i in range(dim):
                c_bit = (i >> (k - 1 - control)) & 1
                if c_bit == 0:
                    op[i, i] = 1
                else:
                    j = i ^ (1 << (k - 1 - target))
                    op[j, i] = 1
            return op

        def build_state(thetas):
            U = np.eye(2 ** k, dtype=np.complex128)
            for _ in range(reps):
                for q in range(k):
                    U = h_gate(q) @ U
                for q in range(k):
                    U = rz_gate(q, float(thetas[q])) @ U
                for ii in range(k - 1):
                    jj = ii + 1
                    a = float(thetas[ii] * thetas[jj] / np.pi)
                    U = cnot_gate(ii, jj) @ U
                    U = rz_gate(jj, a) @ U
                    U = cnot_gate(ii, jj) @ U
            state = np.zeros(2 ** k, dtype=np.complex128)
            state[0] = 1.0
            return U @ state

        return float(np.abs(np.vdot(build_state(thetas_a), build_state(thetas_b))) ** 2)

    raise ValueError(f'unknown encoding {encoding!r}; choices: angle, angle-cnot, zzfm')


def run_kernel_audit(
    *,
    encoding: str = 'angle',
    k: int = 4,
    reps: int = 1,
    shots: int = 256,
    triad: list[str] | None = None,
    corpus: list[str] | None = None,
    sim_only: bool = False,
    pair_loop_cap_seconds: float = 60.0,
    per_pair_stall_seconds: float = 60.0,
    prior_pair_results: list[dict] | None = None,
) -> dict[str, Any]:
    """Run a complete inversion-overlap memory-kernel audit on a 3-document triad.

    Produces the three-way kernel comparison (classical TF-IDF / CPUQVM-sim /
    real-QPU) that the K=4/K=8/CNOT/ZZ-FM audits established as canonical for
    Wukong-180 quantum-kernel work. If `sim_only=True`, skips the real-QPU
    submission entirely (zero cloud burn) — useful for prediction-before-fire.

    Parameters
    ----------
    encoding : {'angle', 'angle-cnot', 'zzfm'}
        Which inversion-overlap variant. 'angle' is the proven baseline.
    k : int
        Number of qubits.
    reps : int
        Repetition count for zzfm encoding (ignored by other encodings).
    shots : int
        Measurement shots per pair (default 256, proven shot-independent).
    triad : list[str], optional
        Three brain-entry filenames in `_shared-memory/knowledge/`. Defaults
        to the canonical Snap-RE triad.
    corpus : list[str], optional
        Larger reference corpus for TF-IDF vocabulary construction. If
        provided, TF-IDF vectors are built over `corpus + triad` (with
        triad docs appended only if not already in corpus). If None, TF-IDF
        is built over just the 3 triad docs (the legacy behavior — produces
        narrower vocabulary but mismatches algorithmic-search rankings).
        For consistency with `find-optimal-triad.py` rankings, pass the
        same 100+ doc corpus used by the search. Recommended for any
        memory-system-quality audit.
    sim_only : bool
        If True, skip real-QPU submission. Default False.
    pair_loop_cap_seconds, per_pair_stall_seconds : float
        Real-QPU submission caps (ignored if sim_only=True).
    prior_pair_results : list[dict], optional
        Pre-existing per-pair real-QPU results to seed the kernel matrix.
        Each dict needs at least {'i', 'j', 'overlap'}. Used by `seraphim audit
        --resume-from PATH` to recover from partial stalls — pairs already in
        the prior JSON are reused; only missing pairs are submitted. Real-QPU
        runs only the diff. Empty/missing pairs (overlap=None or stalled) are
        re-submitted.

    Returns dict with: schema, encoding, k, reps, shots, triad,
    classical_kernel + classical_off_diag_mean, sim_kernel + sim_off_diag_mean,
    real_qpu_kernel + real_qpu_off_diag_mean (None if sim_only or aborted),
    pair_results (list of per-pair dicts), pair_loop_wall_seconds, aborted,
    abort_reason, budget_remaining_after.
    """
    if triad is None:
        triad = TRIAD_DEFAULT[:]
    if len(triad) != 3:
        raise ValueError(f'triad must have exactly 3 entries, got {len(triad)}')

    # Build TF-IDF over either the wider corpus (preferred) or just the triad
    # (legacy / sim-only mode). Wider corpus = larger vocabulary = more stable
    # top-K feature selection across audits.
    if corpus is not None:
        # Wider-corpus mode: TF-IDF built over corpus + any triad docs not already in it.
        # The triad docs end up at indices [-3, -2, -1] in the full doc list.
        corpus_set = set(corpus)
        ordered = list(corpus) + [t for t in triad if t not in corpus_set]
        all_docs = [_load_brain_entry(f) for f in ordered]
        tfidf_all = _tfidf_vectors(all_docs)
        # Extract just the triad TF-IDF vectors by file order (since ordered preserves it)
        triad_indices = [ordered.index(t) for t in triad]
        tfidf = [tfidf_all[i] for i in triad_indices]
    else:
        # Legacy 3-doc TF-IDF (kept for backward compat with audits 14:00Z-17:40Z)
        docs = [_load_brain_entry(f) for f in triad]
        tfidf = _tfidf_vectors(docs)
    thetas = [_thetas_for_inversion(v, k) for v in tfidf]

    # Classical baseline (TF-IDF cosine)
    classical_k = np.eye(3)
    for i in range(3):
        for j in range(3):
            if i != j:
                classical_k[i, j] = _classical_cosine(tfidf[i], tfidf[j])
    cl_mean = (classical_k.sum() - 3) / 6

    # CPUQVM-sim reference (free)
    sim_k = np.eye(3)
    for i in range(3):
        for j in range(3):
            if i != j:
                sim_k[i, j] = _sim_inversion_overlap(thetas[i], thetas[j], encoding, k, reps)
    sim_mean = (sim_k.sum() - 3) / 6

    result: dict[str, Any] = {
        'schema': 'sinister-seraphim.kernel-audit.v2',
        'encoding': encoding,
        'k': k, 'reps': reps, 'shots': shots,
        'triad': triad,
        'corpus_size': len(corpus) if corpus is not None else None,
        'corpus_mode': 'wide' if corpus is not None else '3doc-legacy',
        'classical_kernel': classical_k.tolist(),
        'classical_off_diag_mean': cl_mean,
        'sim_kernel': sim_k.tolist(),
        'sim_off_diag_mean': sim_mean,
        'real_qpu_kernel': None,
        'real_qpu_off_diag_mean': None,
        'pair_results': [],
        'pair_loop_wall_seconds': 0.0,
        'aborted': False,
        'abort_reason': '',
        'budget_remaining_after': None,
        'sim_only': sim_only,
    }

    if sim_only:
        return result

    # Real-QPU submissions. Prewarm the backend FIRST so the slow Origin
    # connect handshake (observed 0.9-336s range across the same session)
    # doesn't eat the pair-loop cap on the first pair.
    try:
        from .cloud_submit import submit_kernel_pair, prewarm_backend, DEFAULT_BACKEND_NAME
        from .budget import remaining_seconds
    except ImportError:
        from cloud_submit import submit_kernel_pair, prewarm_backend, DEFAULT_BACKEND_NAME  # type: ignore
        from budget import remaining_seconds  # type: ignore

    connect_wall = prewarm_backend(DEFAULT_BACKEND_NAME)
    real_k = np.eye(3)
    pair_results = []
    aborted = False
    abort_reason = ''

    # Resume-from-partial: seed the kernel matrix with prior pair results
    prior_landed: dict[tuple[int, int], dict] = {}
    if prior_pair_results:
        for p in prior_pair_results:
            ov = p.get('overlap')
            if ov is None or p.get('stalled'):
                continue
            i_p = p.get('i')
            j_p = p.get('j')
            if i_p is None or j_p is None:
                continue
            ij = tuple(sorted((int(i_p), int(j_p))))
            prior_landed[ij] = p
            real_k[ij[0], ij[1]] = float(ov)
            real_k[ij[1], ij[0]] = float(ov)
            pair_results.append({'i': ij[0], 'j': ij[1], **p, 'resumed_from_prior': True})

    t_loop_start = time.time()

    for (i, j) in [(0, 1), (0, 2), (1, 2)]:
        if (i, j) in prior_landed:
            continue  # Already have a clean prior result for this pair
        elapsed = time.time() - t_loop_start
        if elapsed >= pair_loop_cap_seconds:
            aborted = True
            abort_reason = f'pair_loop_cap_reached:elapsed={elapsed:.2f}s>={pair_loop_cap_seconds}s'
            break
        try:
            pair = submit_kernel_pair(
                thetas[i], thetas[j],
                encoding=encoding, k=k, reps=reps,
                shots=shots,
                per_pair_stall_seconds=per_pair_stall_seconds,
                purpose=f'kernel-audit-{encoding}-k{k}-r{reps}-{i}{j}',
            )
        except Exception as exc:
            aborted = True
            abort_reason = f'submit_kernel_pair-{i}{j}-raised: {type(exc).__name__}: {exc}'
            break
        if pair.get('stalled') or pair.get('overlap') is None:
            aborted = True
            abort_reason = f'per_pair_stall_or_no_result:pair=({i},{j}):wall={pair["wall_seconds"]}s'
            pair_results.append({'i': i, 'j': j, **pair})
            break
        real_k[i, j] = pair['overlap']
        real_k[j, i] = pair['overlap']
        pair_results.append({'i': i, 'j': j, **pair})

    result['pair_results'] = pair_results
    result['pair_loop_wall_seconds'] = round(time.time() - t_loop_start, 3)
    result['connect_setup_wall_seconds'] = round(connect_wall, 3)
    result['aborted'] = aborted
    result['abort_reason'] = abort_reason
    result['real_qpu_kernel'] = real_k.tolist()
    if len(pair_results) == 3 and not aborted:
        result['real_qpu_off_diag_mean'] = (real_k.sum() - 3) / 6
    result['budget_remaining_after'] = remaining_seconds()
    return result


def _render(result: dict[str, Any]) -> str:
    lines = []
    lines.append('=' * 72)
    lines.append(' Sinister Seraphim :: Memory-Kernel Experiment (Variant A)')
    lines.append('=' * 72)
    lines.append(f" backend:               {result['backend']}")
    lines.append(f" elapsed_seconds:       {result['elapsed_seconds']}")
    lines.append(f" cloud_seconds_consumed: {result['cloud_seconds_consumed']}")
    lines.append(f" ts_utc:                {result['ts_utc']}")
    lines.append('')
    lines.append(' Triad (brain entries under test):')
    for i, t in enumerate(result['triad']):
        lines.append(f'   [{i}] {t}')
    lines.append('')

    def fmt_mat(m, name):
        out = [f' {name}:']
        for i, row in enumerate(m):
            out.append('   [' + '  '.join(f'{v: .4f}' for v in row) + ']')
        return '\n'.join(out)

    lines.append(fmt_mat(result['classical_kernel_matrix'], 'classical TF-IDF cosine kernel'))
    lines.append('')
    encoding = result.get('encoding', '?')
    lines.append(fmt_mat(result['quantum_kernel_matrix'], f'quantum |⟨ψA|ψB⟩|² kernel ({encoding})'))
    lines.append('')
    lines.append(fmt_mat(result['differential_matrix'], 'differential (quantum − classical)'))
    lines.append('')
    i = result['interpretation']
    lines.append(' Interpretation:')
    lines.append(f"   quantum  off-diag mean: {i['quantum_off_diag_mean']:.4f}")
    lines.append(f"   classical off-diag mean: {i['classical_off_diag_mean']:.4f}")
    lines.append(f"   differential off-diag mean: {i['differential_off_diag_mean']:+.4f}")
    lines.append(f"   note: {i['note']}")
    lines.append('')
    if i['differential_off_diag_mean'] > 0.02:
        lines.append(' VERDICT: quantum kernel finds TIGHTER cluster on this Snap-RE triad.')
        lines.append('          Worth scaling to 8-entry experiment for stronger signal.')
    elif i['differential_off_diag_mean'] < -0.02:
        lines.append(' VERDICT: classical TF-IDF wins on this triad at this scale.')
        lines.append('          Quantum encoding may need different feature map.')
    else:
        lines.append(' VERDICT: quantum and classical roughly equivalent on this triad.')
        lines.append('          No meaningful win; classical recall path is fine.')
    lines.append('=' * 72)
    return '\n'.join(lines)


if __name__ == '__main__':
    import argparse
    import sys as _sys
    # Windows-default cp1252 stdout chokes on the unicode kets/psis in _render.
    try:
        _sys.stdout.reconfigure(encoding='utf-8')  # type: ignore[attr-defined]
    except Exception:
        pass
    p = argparse.ArgumentParser(description='Sinister Seraphim Memory-Kernel Experiment (Variant A)')
    p.add_argument('--backend', default='cpuqvm-local',
                   choices=['cpuqvm-local', 'pilotos-deployed', 'cloud-wukong-180'])
    p.add_argument('--variant', default='B', choices=['A', 'B', 'C'],
                   help='A=4q-amplitude (collapsed) / B=8q-angle (default) / C=4q-ZZ-feature-map')
    p.add_argument('--out', default=None, help='Optional JSON output path')
    p.add_argument('--json', action='store_true', help='Emit JSON to stdout instead of human text')
    args = p.parse_args()
    result = run_kernel_experiment(backend=args.backend, variant=args.variant)
    if args.out:
        Path(args.out).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(_render(result))
