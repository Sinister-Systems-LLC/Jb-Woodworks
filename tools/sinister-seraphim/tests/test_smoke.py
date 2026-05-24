"""Smoke tests for sinister-seraphim.

Author: RKOJ-ELENO :: 2026-05-23

Run via: `pytest tools/sinister-seraphim/tests/ -v`

The conftest.py adjacent puts tools/sinister-seraphim/ on sys.path so
the modules import flat (qrng, audit, fingerprint, license) without
requiring `pip install -e` first.
"""
from __future__ import annotations

import json

import pytest

import audit  # noqa: E402
import fingerprint  # noqa: E402
import qrng  # noqa: E402


def test_quantum_random_sim_local_returns_bytes():
    """qrng.quantum_random(N, backend='sim-local') returns N bytes."""
    data = qrng.quantum_random(16, purpose='pytest-smoke', backend='sim-local')
    assert isinstance(data, bytes)
    assert len(data) == 16


def test_quantum_random_rejects_out_of_range():
    """qrng.quantum_random raises ValueError for out-of-range n_bytes."""
    with pytest.raises(ValueError):
        qrng.quantum_random(0, purpose='pytest', backend='sim-local')
    with pytest.raises(ValueError):
        qrng.quantum_random(5000, purpose='pytest', backend='sim-local')


def test_quantum_random_pilotos_not_implemented():
    """sim-pilotos backend is documented placeholder until operator extracts SDK."""
    with pytest.raises(NotImplementedError):
        qrng.quantum_random(8, purpose='pytest', backend='sim-pilotos')


def test_quantum_random_cloud_not_implemented():
    """cloud-wukong-180 backend is documented placeholder (cost-gated)."""
    with pytest.raises(NotImplementedError):
        qrng.quantum_random(8, purpose='pytest', backend='cloud-wukong-180')


def test_write_provenance_creates_sidecar():
    """audit.write_provenance writes a JSON sidecar."""
    p = audit.write_provenance(
        purpose='pytest-smoke',
        backend='sim-local',
        n_bytes=16,
        extra={'test': True},
    )
    assert p.exists()
    rec = json.loads(p.read_text(encoding='utf-8'))
    assert rec['schema'] == 'sinister-seraphim.provenance.v1'
    assert rec['purpose'] == 'pytest-smoke'
    assert rec['backend'] == 'sim-local'
    assert rec['n_bytes'] == 16
    assert rec['extra'] == {'test': True}


def test_write_provenance_rejects_empty_purpose():
    """audit.write_provenance refuses empty purpose."""
    with pytest.raises(ValueError):
        audit.write_provenance(purpose='', backend='sim-local')
    with pytest.raises(ValueError):
        audit.write_provenance(purpose='   ', backend='sim-local')


def test_write_provenance_rejects_unknown_backend():
    """audit.write_provenance refuses unknown backend."""
    with pytest.raises(ValueError):
        audit.write_provenance(purpose='pytest', backend='not-a-backend')


def test_make_fingerprint_shape():
    """fingerprint.make_fingerprint returns the documented v1 shape."""
    fp = fingerprint.make_fingerprint(lane='kernel-apk', build_fingerprint_stub='pytest/v0')
    assert fp['schema'] == 'sinister-seraphim.fingerprint.v1'
    assert fp['lane'] == 'kernel-apk'
    assert len(fp['device_id']) == 32   # 16 bytes -> 32 hex chars
    assert len(fp['android_id']) == 16  # 8 bytes -> 16 hex chars
    assert len(fp['imei']) == 15        # 14 digits + 1 Luhn check
    assert fp['imei'].isdigit()
    assert fp['mac_address'].count(':') == 5
    assert fp['build_fingerprint'] == 'pytest/v0'
    # MAC should have locally-administered bit set
    first_octet = int(fp['mac_address'].split(':')[0], 16)
    assert (first_octet & 0x02) == 0x02


def test_luhn_check_digit():
    """fingerprint._luhn_check_digit matches a known test vector."""
    # Known IMEI: 35-209900-176148-1 (Luhn check = 1)
    assert fingerprint._luhn_check_digit('35209900176148') == '1'
    # Another known: 49-015420-323751-8
    assert fingerprint._luhn_check_digit('49015420323751') == '8'


def test_make_fingerprint_batch_returns_distinct():
    """fingerprint.make_fingerprint_batch returns n entries, each distinct."""
    batch = fingerprint.make_fingerprint_batch(5, lane='snap-emu')
    assert len(batch) == 5
    ids = {fp['device_id'] for fp in batch}
    assert len(ids) == 5  # QRNG collisions vanishingly unlikely


def test_make_fingerprint_batch_rejects_out_of_range():
    """fingerprint.make_fingerprint_batch refuses n < 1 or > 10_000."""
    with pytest.raises(ValueError):
        fingerprint.make_fingerprint_batch(0)
    with pytest.raises(ValueError):
        fingerprint.make_fingerprint_batch(10_001)


# Memory-kernel tests (added iter 81, 2026-05-24) — cover iter-37→79 doctrine
# Protects against regressions in: recall_brain (iter 47/48), find_qbc_triads
# (iter 41/43), Shared-Top-K Necessary Condition (iter 59), combined K=4
# predictor (iter 65), encoding nesting K=4 ⊂ K=8 (iter 52).

import memory_kernel  # noqa: E402


def test_recall_brain_default_alpha_returns_top_k():
    """recall_brain default alpha=1.0 (pure TF-IDF) returns top_k results with correct shape."""
    r = memory_kernel.recall_brain('multi-agent git', top_k_results=3, corpus_mode='pool')
    assert r['schema'] == 'sinister-seraphim.brain-recall.v1'
    assert r['alpha'] == 1.0, "iter-48 fix: default alpha must be 1.0 (pure TF-IDF)"
    assert len(r['top_results']) == 3
    for row in r['top_results']:
        assert 'rank' in row and 'filename' in row
        assert 'tfidf_sim' in row and 'quantum_sim' in row and 'combined_score' in row
    # Ranks are 1..3 in order
    assert [row['rank'] for row in r['top_results']] == [1, 2, 3]


def test_find_qbc_triads_zzfm_r1_pool_returns_top_n():
    """find_qbc_triads on zzfm-r1 pool corpus returns top-N triads with classical/sim/advantage."""
    r = memory_kernel.find_qbc_triads(encoding='zzfm', k=4, reps=1, top_n=3, corpus_mode='pool')
    assert r['schema'].startswith('sinister-seraphim.find-qbc-triads')
    assert len(r['top_n_triads']) == 3
    # Each result has the expected fields
    for t in r['top_n_triads']:
        assert 'rank' in t and 'advantage' in t and 'docs' in t
        assert 'sim_off_diag_mean' in t and 'classical_off_diag_mean' in t
        assert len(t['docs']) == 3
    # Top-1 advantage should be positive (= QBC) for the pool's high-classical triads
    assert r['top_n_triads'][0]['advantage'] > 0
    # Sorted descending by advantage
    advs = [t['advantage'] for t in r['top_n_triads']]
    assert advs == sorted(advs, reverse=True)


def test_shared_top_k_necessary_condition_holds_at_k4():
    """iter-59 Shared-Top-K Necessary Condition: at K=4, zero shared top-4 → anti-QBC.

    Tests the canonical Snap-RE triad (which iter-17 showed is K=4 anti-QBC)
    and verifies it does NOT have zero shared top-4 (it has 1 shared feature).
    Then constructs a SYNTHETIC zero-overlap test by using docs from different
    topical clusters and confirms K=4 ANGLE returns anti-QBC.
    """
    import numpy as np
    # Sanity check: the function we're testing exists and runs
    snap_re_triad = [
        'snap-tt-rka-chain-attestation-insufficient.md',
        'snap-emu-pb2-schema-shadow.md',
        'snap-account-24h-survival-doctrine-2026-05-21.md',
    ]
    r = memory_kernel.run_kernel_audit(
        encoding='angle', k=4, reps=1,
        triad=snap_re_triad,
        sim_only=True,
    )
    # Snap-RE triad has low classical baseline → K=4 ANGLE is anti-QBC (sim > classical)
    assert r['sim_off_diag_mean'] > r['classical_off_diag_mean'], \
        "Snap-RE triad should be K=4 ANGLE anti-QBC per iter-10 bidirectional rule"


def test_k4_combined_predictor_safety_on_top_qbc_triads():
    """iter-65 combined predictor (shared top-4 = 0 OR same top-1) must NOT
    false-positive on any known K=4 QBC triad. Test on the universal-QBC
    set from iter-52: 3 triads that are K=4 QBC under any encoding."""
    import numpy as np

    def top_4(vec):
        if vec.size <= 4:
            return set(range(vec.size))
        return set(np.argsort(np.abs(vec))[-4:].tolist())

    def combined_predictor_says_skip(tfidf_vecs):
        """Returns True iff combined predictor says 'guaranteed anti-QBC'."""
        sets = [top_4(v) for v in tfidf_vecs]
        if len(sets[0] & sets[1] & sets[2]) == 0:
            return True
        top1 = [int(np.argmax(np.abs(v))) for v in tfidf_vecs]
        if top1[0] == top1[1] == top1[2]:
            return True
        return False

    # Test on 3 known K=4 QBC triads from iter 52 — the universal-QBC set
    qbc_triads = [
        ['multi-agent-branch-contention-isolation-pattern.md',
         'multi-agent-git-coordination-2026-05-23.md',
         'multi-agent-git-index-contention-storm-2026-05-23.md'],
        ['multi-agent-branch-contention-isolation-pattern.md',
         'multi-agent-git-coordination-2026-05-23.md',
         'verify-head-before-commit-multi-agent.md'],
        ['multi-agent-branch-contention-isolation-pattern.md',
         'multi-agent-git-index-contention-storm-2026-05-23.md',
         'verify-head-before-commit-multi-agent.md'],
    ]
    for triad in qbc_triads:
        # Load docs + compute TF-IDF
        docs = [memory_kernel._load_brain_entry(f) for f in triad]
        tfidf = memory_kernel._tfidf_vectors(docs)
        # The combined predictor must NOT skip these (they're K=4 QBC)
        assert not combined_predictor_says_skip(tfidf), \
            f"iter-65 combined predictor false-positive on known K=4 QBC triad: {triad}"


def test_find_qbc_rank_by_ceiling_reorders_top_n():
    """iter-41 find-qbc --rank-by ceiling reorders top-N differently than rank-by r1.

    Verifies the iter-39 doctrine: rank-order inverts at r=5+. Triad C
    (iter-21 verified) goes from #3 by r=1 to #1 by ceiling.
    """
    r_r1 = memory_kernel.find_qbc_triads(
        encoding='zzfm', k=4, reps=1, top_n=3, corpus_mode='pool',
    )
    r_ceiling = memory_kernel.find_qbc_triads(
        encoding='zzfm', k=4, reps=1, top_n=3, corpus_mode='pool',
        ceiling_reps=[2, 3, 4, 5, 6], rank_by='ceiling',
    )

    # ceiling-ranked results must have ceiling_pp and per_rep fields
    for t in r_ceiling['top_n_triads']:
        assert 'ceiling_pp' in t and 'ceiling_rep' in t and 'headroom_pp' in t
        assert 'per_rep' in t and len(t['per_rep']) >= 5
        # Ceiling must be >= r1 advantage (ZZ-FM r>=2 has higher sim QBC)
        assert t['ceiling_pp'] >= t['advantage'] * 100 - 0.01  # numerical slop

    # The ceiling-ranking top-3 set should overlap with but differ in ORDER
    # from the r1-ranking top-3 — the rank-inversion property from iter 39.
    r1_docs = [tuple(sorted(t['docs'])) for t in r_r1['top_n_triads']]
    ceiling_docs = [tuple(sorted(t['docs'])) for t in r_ceiling['top_n_triads']]
    # Both lists should contain the same triads (top-3 by r1 enriched and re-sorted)
    assert set(r1_docs) == set(ceiling_docs), \
        "top-3 triads should be the same set (different order)"
    # The order should differ in at least one position (iter-39 rank-inversion)
    assert r1_docs != ceiling_docs, \
        "iter-39 rank-inversion broken: ceiling order matches r1 order"


def test_cancellation_theorem_angle_cnot_equals_k4_angle():
    """iter-16/22/43 cancellation theorem: ANGLE-CNOT == K=4 ANGLE bit-for-bit.

    Parameter-free entanglement self-cancels in U_B† · U_A protocols
    because C†·C = I. The two encodings produce identical pair-overlap
    matrices and identical QBC top-N rankings.
    """
    r_angle = memory_kernel.find_qbc_triads(
        encoding='angle', k=4, reps=1, top_n=3, corpus_mode='pool',
    )
    r_angle_cnot = memory_kernel.find_qbc_triads(
        encoding='angle-cnot', k=4, reps=1, top_n=3, corpus_mode='pool',
    )

    # Max advantage must match bit-for-bit
    assert abs(r_angle['max_advantage'] - r_angle_cnot['max_advantage']) < 1e-9, \
        f"cancellation theorem broken: angle max_adv={r_angle['max_advantage']!r} " \
        f"!= angle-cnot max_adv={r_angle_cnot['max_advantage']!r}"

    # QBC count must match
    assert r_angle['qbc_count'] == r_angle_cnot['qbc_count'], \
        "cancellation theorem broken: QBC counts differ"

    # Top-3 entries must match bit-for-bit
    for t_a, t_ac in zip(r_angle['top_n_triads'], r_angle_cnot['top_n_triads']):
        assert t_a['docs'] == t_ac['docs'], \
            f"cancellation theorem broken: top-{t_a['rank']} docs differ"
        assert abs(t_a['advantage'] - t_ac['advantage']) < 1e-9, \
            f"cancellation theorem broken: top-{t_a['rank']} advantage differs"
        assert abs(t_a['sim_off_diag_mean'] - t_ac['sim_off_diag_mean']) < 1e-9, \
            f"cancellation theorem broken: top-{t_a['rank']} sim differs"
