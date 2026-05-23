"""Real cloud-Wukong-180 submission path for sinister-seraphim.

Author: RKOJ-ELENO :: 2026-05-23

Empirically-validated wrapper around pyqpanda3.qcloud.QCloudService. Reads
the qcloud API key from `_vault-personal/licenses/originqc-qcloud-apikey.txt`
(separate from the PilotOS license — the qcloud key auths against the
public OriginQ cloud product, not the self-hosted PilotOS system).

Budget-gated: every cloud call goes through `budget.check_budget(est_seconds)`
BEFORE submission and `budget.record_usage(actual_seconds)` AFTER. The
operator-hard-canonical 120-second cap applies to cloud QPU submissions.

## Architecture (post-2026-05-23 evening rewrite)

Three layers:

1. **Auth + service** (`confirm_auth`, `_service`, `_load_qcloud_key`) —
   loads the vault key, constructs `QCloudService`, lists backends.

2. **Circuit builders** (`build_angle_inversion`, `build_angle_cnot_inversion`,
   `build_zzfm_inversion`) — return pyqpanda3 `QProg` instances ready to
   submit. Each builds an inversion-overlap circuit `U_B† · U_A` whose
   `P(|0...0⟩)` measures `|⟨B|A⟩|²`. Empirically validated by 4 real-QPU
   audits on 2026-05-23 (K=4 ANGLE, K=8 ANGLE, K=4 ANGLE+CNOT, K=4 ZZ-FM r=2).

3. **Submission** (`submit_circuit`, `submit_kernel_pair`) — generic and
   high-level. Generic `submit_circuit(prog, ...)` does budget-check, fire,
   poll, result, record-usage. High-level `submit_kernel_pair(thetas_a,
   thetas_b, encoding=..., ...)` picks the right builder and returns the
   overlap.

## Usage

```python
from sinister_seraphim.cloud_submit import (
    confirm_auth,         # ~0.1s; lists backends; cheap probe
    submit_kernel_pair,   # one |⟨ψA|ψB⟩|² overlap on WK_C180
)

# Cheap probe first
r = confirm_auth()
assert r['ok'], r.get('detail')

# Submit one inversion-overlap pair (K=4 plain ANGLE)
import numpy as np
thetas_a = np.array([0.5, 1.0, 1.5, 2.0])
thetas_b = np.array([0.4, 1.1, 1.6, 1.9])
result = submit_kernel_pair(thetas_a, thetas_b, encoding='angle', k=4, shots=256)
print(result['overlap'], result['wall_seconds'], result['job_id'])
```

## Verified constants (2026-05-23 empirical anchor)

- `DEFAULT_QCLOUD_URL = 'http://pyqanda-admin.qpanda.cn'` — the BACKEND admin
  domain (HTTP, default in pyqpanda3 0.3.5). NOT the `https://qcloud.originqc.com.cn`
  website URL — that's the frontend; the lib's parser rejects HTML responses.
- `DEFAULT_BACKEND_NAME = 'WK_C180'` — Wukong-180 chip name confirmed via
  `svc.backends()`. Other available backends: `PQPUMESH8` (8-qubit test chip),
  `full_amplitude` / `partial_amplitude` / `single_amplitude` (sim).
"""
from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

try:
    from .budget import BudgetExhausted, check_budget, record_usage, remaining_seconds
except ImportError:
    from budget import BudgetExhausted, check_budget, record_usage, remaining_seconds  # type: ignore

SANCTUM_ROOT = Path(os.environ.get('SINISTER_SANCTUM_ROOT', r'D:\Sinister Sanctum'))
QCLOUD_KEY_PATH = SANCTUM_ROOT / '_vault-personal' / 'licenses' / 'originqc-qcloud-apikey.txt'

# Verified empirical anchors 2026-05-23:
# - 'http://pyqanda-admin.qpanda.cn' is the working backend URL (lib default).
#   The website URL 'https://qcloud.originqc.com.cn' returns HTML that the
#   lib's parser rejects with 'Invalid value.'.
# - 'WK_C180' is the real Wukong-180 chip name. Use confirm_auth() to list
#   all available backends in the current account.
DEFAULT_QCLOUD_URL = 'http://pyqanda-admin.qpanda.cn'
DEFAULT_BACKEND_NAME = 'WK_C180'

# Conservative per-pair stall guard. Origin's queue + compile + run cycle is
# non-stationary across runs (observed range: 4-112s per 1024-shot small-qubit
# pair). Default per-pair stall is 60s; bump higher for known-deep circuits
# (ZZ-FM reps=2 at depth 68 was observed at 67s wall for one pair).
DEFAULT_PER_PAIR_STALL_SECONDS = 60.0


class QCloudAuthMissing(RuntimeError):
    """Raised when the operator hasn't dropped a qcloud API key in the vault."""


def _load_qcloud_key() -> str:
    if not QCLOUD_KEY_PATH.exists():
        raise QCloudAuthMissing(
            f'qcloud API key not found at {QCLOUD_KEY_PATH}.\n\n'
            f'  Unblock: register at https://qcloud.originqc.com.cn/,\n'
            f'  copy the API key from your account dashboard, paste it\n'
            f'  into the file at the path above (one line, no quotes).\n'
            f'  The file is gitignored; never reaches GitHub.'
        )
    raw = QCLOUD_KEY_PATH.read_text(encoding='utf-8')
    lines = [ln.strip() for ln in raw.splitlines() if ln.strip() and not ln.strip().startswith('##')]
    if not lines:
        raise QCloudAuthMissing(
            f'qcloud API key file {QCLOUD_KEY_PATH} has no non-comment lines.'
        )
    return ''.join(lines)


# Cached service + backend handles. Origin connect/auth is non-stationary
# (observed 0.9s to 336s in a single session). Constructing QCloudService +
# backend lookup on EVERY submit_circuit call is a perf bug: the slow-connect
# hits each pair, exhausting the pair-loop cap before the second pair starts.
# Cache once per process; reset via `_clear_service_cache()` if the operator
# rotates the API key.
_cached_service = None
_cached_backend_handles: dict[str, Any] = {}


def _clear_service_cache() -> None:
    """Drop the cached QCloudService + backend handles. Use if the API key
    is rotated or after a process-level network failure."""
    global _cached_service
    _cached_service = None
    _cached_backend_handles.clear()


def _service():
    """Construct OR return the cached QCloudService.

    Cache is process-global. First call pays the auth handshake; subsequent
    calls reuse. If you need to reconnect (key rotation, network blip), call
    `_clear_service_cache()` first.
    """
    global _cached_service
    if _cached_service is None:
        from pyqpanda3.qcloud.qcloud import QCloudService
        _cached_service = QCloudService(api_key=_load_qcloud_key(), url=DEFAULT_QCLOUD_URL)
    return _cached_service


def _backend(name: str):
    """Construct OR return the cached backend handle for `name`. Reuses
    the cached QCloudService."""
    if name not in _cached_backend_handles:
        svc = _service()
        _cached_backend_handles[name] = svc.backend(name)
    return _cached_backend_handles[name]


def prewarm_backend(backend_name: str = DEFAULT_BACKEND_NAME) -> float:
    """Ensure the cached QCloudService + backend handle for `backend_name`
    are ready. Returns the wall-seconds spent on the connect/setup (0 if
    already cached). Use this BEFORE starting a pair-loop cap-bounded
    submission sequence so the slow-connect doesn't eat the cap.
    """
    import time as _time
    if _cached_service is not None and backend_name in _cached_backend_handles:
        return 0.0
    t0 = _time.monotonic()
    _backend(backend_name)
    return _time.monotonic() - t0


def _default_options():
    """Build the QCloudOptions block used by the audited inversion-overlap protocol."""
    from pyqpanda3.qcloud.qcloud import QCloudOptions
    opts = QCloudOptions()
    opts.set_mapping(True)
    opts.set_optimization(True)
    opts.set_is_prob_counts(True)
    return opts


def confirm_auth() -> dict[str, Any]:
    """Cheap auth probe — lists available backends without submitting a circuit.

    Costs near zero qcloud-seconds (auth + list only).
    Returns {'ok': True, 'backends': {...}} on success, or
    {'ok': False, 'reason': '...'} on auth failure.
    """
    try:
        svc = _service()
        backends = svc.backends()
        return {
            'ok': True,
            'backends': dict(backends),
            'budget_remaining': remaining_seconds(),
        }
    except QCloudAuthMissing as exc:
        return {'ok': False, 'reason': 'auth-missing', 'detail': str(exc)}
    except Exception as exc:
        return {
            'ok': False,
            'reason': 'auth-rejected-or-unreachable',
            'detail': f'{type(exc).__name__}: {exc}',
            'budget_remaining': remaining_seconds(),
        }


# ============================================================================
# Circuit builders for inversion-overlap memory kernels
# ============================================================================

def build_angle_inversion(thetas_a, thetas_b, k: int):
    """K-qubit ANGLE inversion overlap: U = (⊗ RY(-θ_B_i)) · (⊗ RY(θ_A_i)).

    Depth: 2K gates (no entanglement). P(|0...0⟩) = |⟨B|A⟩|².
    Verified clean on WK_C180 at K=4 depth 8 (15:50Z 2026-05-23 audit).
    """
    from pyqpanda3.core import QCircuit, QProg, RY, measure
    circ = QCircuit(k)
    for i in range(k):
        circ << RY(i, float(thetas_a[i]))
    for i in range(k):
        circ << RY(i, float(-thetas_b[i]))
    prog = QProg()
    prog << circ
    for i in range(k):
        prog << measure(i, i)
    return prog


def build_angle_cnot_inversion(thetas_a, thetas_b, k: int):
    """K-qubit ANGLE + linear-CNOT-chain inversion overlap.

    Depth: ~3K gates (K RY + (K-1) CNOT + (K-1) CNOT + K RY).
    PARAMETER-FREE entanglement self-cancels in inversion-overlap protocol
    (cancellation theorem 2026-05-23T16:18Z): sim result is IDENTICAL to plain
    ANGLE despite added gates. Provided here for the cancellation-theorem
    regression test, NOT for actual discrimination.
    """
    from pyqpanda3.core import QCircuit, QProg, RY, CNOT, measure
    circ = QCircuit(k)
    # U_A: encode A then entangle
    for i in range(k):
        circ << RY(i, float(thetas_a[i]))
    for c in range(k - 1):
        circ << CNOT(c, c + 1)
    # U_B†: reverse entangle then decode -B
    for c in reversed(range(k - 1)):
        circ << CNOT(c, c + 1)
    for i in range(k):
        circ << RY(i, float(-thetas_b[i]))
    prog = QProg()
    prog << circ
    for i in range(k):
        prog << measure(i, i)
    return prog


def build_zzfm_inversion(thetas_a, thetas_b, k: int, reps: int = 1):
    """K-qubit truncated ZZ-feature-map inversion overlap, nearest-neighbor only.

    Per direction per rep:
        H_all -> RZ(θ_q) per q -> for i in 0..k-2: CNOT(i,i+1); RZ(j, θ_i·θ_j/π); CNOT(i,i+1)
    Inverse reverses gate order + negates RZ angles.

    Depth: 2 * reps * (2K + 3(K-1)) gates. At K=4 reps=1: depth ~34. At K=4 reps=2: depth ~68.
    DATA-PARAMETERIZED entanglement (RZZ angle depends on θ_i·θ_j) so the
    cancellation theorem doesn't apply. Sim breaks the plateau (reps=2 sim
    off-diag 0.6189 vs plain ANGLE 0.8975); real-QPU at depth ≥68 noise-saturates.
    """
    import numpy as np
    from pyqpanda3.core import QCircuit, QProg, H, RZ, CNOT, measure
    circ = QCircuit(k)

    def forward(thetas):
        for _ in range(reps):
            for q in range(k):
                circ << H(q)
            for q in range(k):
                circ << RZ(q, float(thetas[q]))
            for i in range(k - 1):
                j = i + 1
                a = float(thetas[i] * thetas[j] / np.pi)
                circ << CNOT(i, j)
                circ << RZ(j, a)
                circ << CNOT(i, j)

    def inverse(thetas):
        for _ in range(reps):
            for i in reversed(range(k - 1)):
                j = i + 1
                a = float(thetas[i] * thetas[j] / np.pi)
                circ << CNOT(i, j)
                circ << RZ(j, -a)
                circ << CNOT(i, j)
            for q in range(k):
                circ << RZ(q, float(-thetas[q]))
            for q in range(k):
                circ << H(q)

    forward(thetas_a)
    inverse(thetas_b)
    prog = QProg()
    prog << circ
    for i in range(k):
        prog << measure(i, i)
    return prog


# ============================================================================
# Submission layer (generic + high-level)
# ============================================================================

def submit_circuit(
    prog,
    *,
    n_qubits: int,
    backend_name: str = DEFAULT_BACKEND_NAME,
    shots: int = 256,
    estimated_seconds: float = 3.0,
    per_pair_stall_seconds: float = DEFAULT_PER_PAIR_STALL_SECONDS,
    purpose: str = 'cloud-submit',
    extra_ledger: dict | None = None,
) -> dict[str, Any]:
    """Generic cloud-QPU submission with budget gate + poll + stall guard.

    Budget-gated: pre-flight `check_budget(estimated_seconds)` raises
    BudgetExhausted if over budget. Post-result `record_usage(wall_seconds)`
    debits actual wall time. Per-pair stall guard aborts polling if Origin's
    queue exceeds `per_pair_stall_seconds` (default 60s).

    Returns a dict with: counts (dict[str, int]), wall_seconds, qpu_run_ms,
    job_id, stalled (bool).
    """
    check_budget(estimated_seconds)
    backend = _backend(backend_name)
    opts = _default_options()

    t0 = time.monotonic()
    job = backend.run(prog, shots, opts)
    job_id = job.job_id() if hasattr(job, 'job_id') else '?'

    stalled = False
    for _ in range(int(per_pair_stall_seconds) + 5):
        st = str(job.status()).lower()
        if 'finished' in st or 'failed' in st or 'error' in st:
            break
        if (time.monotonic() - t0) >= per_pair_stall_seconds:
            stalled = True
            break
        time.sleep(1)

    # Note: as of 2026-05-23 evening, submit_circuit DOES NOT call record_usage.
    # The caller (submit_kernel_pair) records usage AFTER computing the overlap
    # so the ledger row includes the overlap field (a regression discovered when
    # the medium-doctrine v2 audit's print step crashed before saving JSON —
    # ledger was the only fallback and had no overlap field). Keep this contract.
    if stalled:
        elapsed = time.monotonic() - t0
        return {
            'counts': {}, 'wall_seconds': round(elapsed, 3),
            'qpu_run_ms': 0.0, 'job_id': job_id, 'stalled': True,
        }

    res = job.result()
    counts = res.get_counts() if hasattr(res, 'get_counts') else {}
    timing = res.timing_info() if hasattr(res, 'timing_info') else {}
    elapsed = time.monotonic() - t0
    qpu_ms = float(timing.get('qpuRunTime', 0)) if timing else 0.0

    return {
        'counts': counts, 'wall_seconds': round(elapsed, 3),
        'qpu_run_ms': qpu_ms, 'job_id': job_id, 'stalled': False,
    }


def _overlap_from_counts(counts: dict, k: int, shots: int) -> float:
    """P(|0...0⟩) from a measurement-counts dict, for inversion-overlap circuits."""
    target = '0' * k
    c = counts.get(target, counts.get('0', 0))
    return c / max(1, shots)


_ENCODING_BUILDERS = {
    'angle': lambda ta, tb, k, reps: build_angle_inversion(ta, tb, k),
    'angle-cnot': lambda ta, tb, k, reps: build_angle_cnot_inversion(ta, tb, k),
    'zzfm': lambda ta, tb, k, reps: build_zzfm_inversion(ta, tb, k, reps),
}


def submit_kernel_pair(
    thetas_a,
    thetas_b,
    *,
    encoding: str = 'angle',
    k: int | None = None,
    reps: int = 1,
    backend_name: str = DEFAULT_BACKEND_NAME,
    shots: int = 256,
    estimated_seconds: float | None = None,
    per_pair_stall_seconds: float = DEFAULT_PER_PAIR_STALL_SECONDS,
    purpose: str | None = None,
) -> dict[str, Any]:
    """High-level: submit one |⟨B|A⟩|² inversion-overlap pair to real QPU.

    Parameters
    ----------
    thetas_a, thetas_b : array-like of length K
        Per-qubit rotation angles for encoding A and B (typically derived
        from TF-IDF top-K features via `memory_kernel._thetas` or similar).
    encoding : {'angle', 'angle-cnot', 'zzfm'}
        Which inversion-overlap variant to use. 'angle' is the proven-clean
        baseline; 'zzfm' is the data-parameterized variant that breaks the
        encoding-collapse plateau in sim (noise-limited on real WK_C180).
    k : int, optional
        Number of qubits. Defaults to `len(thetas_a)`.
    reps : int
        Repetition count for zzfm encoding (ignored by other encodings).
    backend_name : str
        QPU backend name. Default 'WK_C180' (Wukong-180).
    shots : int
        Measurement shots per pair. Default 256 (proven sufficient).
    estimated_seconds : float, optional
        Budget pre-flight estimate. Defaults based on encoding/depth.
    per_pair_stall_seconds : float
        Abort polling after this many wall-seconds. Default 60s.
    purpose : str, optional
        Ledger purpose tag. Defaults to f'kernel-pair-{encoding}-r{reps}'.

    Returns dict with: overlap (float), counts, wall_seconds, qpu_run_ms,
    job_id, stalled (bool), encoding, k, reps.
    """
    if encoding not in _ENCODING_BUILDERS:
        raise ValueError(f'unknown encoding {encoding!r}; choices: {sorted(_ENCODING_BUILDERS)}')
    if k is None:
        k = len(thetas_a)
    if k != len(thetas_a) or k != len(thetas_b):
        raise ValueError(f'thetas length mismatch: k={k}, len(thetas_a)={len(thetas_a)}, len(thetas_b)={len(thetas_b)}')

    # Default budget estimate scales roughly with circuit depth
    if estimated_seconds is None:
        depth_estimate = {'angle': 2 * k, 'angle-cnot': 3 * k, 'zzfm': 2 * reps * (2 * k + 3 * (k - 1))}[encoding]
        estimated_seconds = max(2.0, depth_estimate * 0.1)

    if purpose is None:
        purpose = f'kernel-pair-{encoding}-k{k}'
        if encoding == 'zzfm':
            purpose += f'-r{reps}'

    prog = _ENCODING_BUILDERS[encoding](thetas_a, thetas_b, k, reps)

    result = submit_circuit(
        prog,
        n_qubits=k,
        backend_name=backend_name,
        shots=shots,
        estimated_seconds=estimated_seconds,
        per_pair_stall_seconds=per_pair_stall_seconds,
        purpose=purpose,
        extra_ledger={'encoding': encoding, 'k': k, 'reps': reps},
    )

    overlap = _overlap_from_counts(result['counts'], k, shots) if not result['stalled'] else None
    result['overlap'] = overlap
    result['encoding'] = encoding
    result['k'] = k
    result['reps'] = reps

    # Record usage AFTER computing overlap so the ledger row carries the
    # full provenance (was a regression — overlap missing from ledger as of
    # the 16:43Z ZZ-FM r=2 audit; fixed 2026-05-23 evening).
    ledger_extra = {
        'job_id': result['job_id'], 'shots': shots,
        'qpu_run_ms': result['qpu_run_ms'],
        'encoding': encoding, 'k': k, 'reps': reps,
        'overlap': overlap,
        'stalled': result['stalled'],
    }
    ledger_purpose = purpose if not result['stalled'] else f'{purpose}-stalled'
    record_usage(result['wall_seconds'], purpose=ledger_purpose, extra=ledger_extra)

    return result


if __name__ == '__main__':
    import json
    import sys
    try:
        sys.stdout.reconfigure(encoding='utf-8')  # type: ignore[attr-defined]
    except Exception:
        pass
    print('[seraphim.cloud_submit] confirm_auth() probe (no QPU burn)')
    r = confirm_auth()
    print(json.dumps(r, indent=2, ensure_ascii=False))
    if r.get('ok'):
        print('\n  [OK] qcloud auth works. Ready to fire submit_kernel_pair().')
    else:
        print(f'\n  [BLOCKED] {r.get("reason")}: {r.get("detail")}')
