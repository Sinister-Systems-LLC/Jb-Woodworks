"""Cloud-time budget tracker for sinister-seraphim.

Author: RKOJ-ELENO :: 2026-05-23

Operator hard-canonical 2026-05-23: "we only have 120 seconds on the
license key". This module enforces a fleet-wide budget cap on cloud
Wukong-180 calls so no agent (including peer agents, future code,
accidental scripts) can burn the operator's quantum-cloud seconds.

Budget state lives at _shared-memory/seraphim-cloud-budget.json — a
single source of truth for the whole fleet. Every cloud call MUST:

  1. Call `check_budget(estimated_seconds)` BEFORE submission.
     -> raises BudgetExhausted if not enough budget remains.
  2. Call `record_usage(actual_seconds, purpose)` AFTER completion.
     -> appends to the ledger + decrements remaining.

Default cap = 120 seconds (operator's licensed total). Hard-coded
reserve = 10 seconds (refuse calls when remaining < 10s so a small
emergency call can still go through later).

The sim-local + sim-pilotos backends DO NOT touch this — they run
entirely local and never debit the cloud budget. Only
backend='cloud-wukong-180' calls go through here.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

SANCTUM_ROOT = Path(os.environ.get('SINISTER_SANCTUM_ROOT', r'D:\Sinister Sanctum'))
BUDGET_FILE = SANCTUM_ROOT / '_shared-memory' / 'seraphim-cloud-budget.json'
LEDGER_FILE = SANCTUM_ROOT / '_shared-memory' / 'seraphim-cloud-ledger.jsonl'

# Operator-canonical hard caps (2026-05-23): 120 seconds total on the
# paid license. Reserve 10 seconds for emergency calls so we never hit
# zero unexpectedly.
DEFAULT_TOTAL_SECONDS = 120.0
EMERGENCY_RESERVE_SECONDS = 10.0


class BudgetExhausted(RuntimeError):
    """Raised when a cloud call would exceed the remaining budget."""


def _load_budget() -> dict[str, Any]:
    if not BUDGET_FILE.exists():
        return {
            'schema': 'sinister-seraphim.cloud-budget.v1',
            'total_seconds': DEFAULT_TOTAL_SECONDS,
            'used_seconds': 0.0,
            'reserve_seconds': EMERGENCY_RESERVE_SECONDS,
            'last_update_utc': None,
            'note': (
                'Operator hard-canonical 2026-05-23: "we only have 120 seconds '
                'on the license key". Reset only via reset_budget(...) with '
                'explicit operator confirmation.'
            ),
        }
    try:
        return json.loads(BUDGET_FILE.read_text(encoding='utf-8'))
    except Exception:
        # Corrupt budget file = treat as exhausted (fail-safe).
        return {
            'schema': 'sinister-seraphim.cloud-budget.v1',
            'total_seconds': DEFAULT_TOTAL_SECONDS,
            'used_seconds': DEFAULT_TOTAL_SECONDS,  # exhausted
            'reserve_seconds': EMERGENCY_RESERVE_SECONDS,
            'last_update_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'note': 'BUDGET FILE CORRUPT — assumed exhausted. Reset via reset_budget() only with operator confirmation.',
        }


def _save_budget(rec: dict[str, Any]) -> None:
    BUDGET_FILE.parent.mkdir(parents=True, exist_ok=True)
    rec['last_update_utc'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    BUDGET_FILE.write_text(
        json.dumps(rec, indent=2, ensure_ascii=False),
        encoding='utf-8',
    )


def remaining_seconds() -> float:
    """Return current remaining cloud-seconds in the operator's budget."""
    b = _load_budget()
    return max(0.0, float(b['total_seconds']) - float(b['used_seconds']))


def usable_seconds() -> float:
    """Return seconds available for normal (non-emergency) calls."""
    b = _load_budget()
    return max(0.0, float(b['total_seconds']) - float(b['used_seconds']) - float(b['reserve_seconds']))


def check_budget(estimated_seconds: float, *, allow_reserve: bool = False) -> None:
    """Raise BudgetExhausted if `estimated_seconds` would exceed the budget.

    Parameters
    ----------
    estimated_seconds : float
        How many cloud-seconds the upcoming call is expected to consume.
        Be conservative; this is a pre-flight check, not a refund.
    allow_reserve : bool
        If True, allow consuming into the emergency reserve. Default False.
        Pass True ONLY when the operator has explicitly authorized this
        single call.
    """
    if estimated_seconds < 0:
        raise ValueError(f'estimated_seconds must be >= 0, got {estimated_seconds!r}')
    available = remaining_seconds() if allow_reserve else usable_seconds()
    if estimated_seconds > available:
        b = _load_budget()
        raise BudgetExhausted(
            f'cloud-Wukong-180 call ({estimated_seconds:.2f}s estimated) exceeds '
            f"remaining budget ({available:.2f}s available, "
            f"{b['used_seconds']:.2f}s/{b['total_seconds']:.2f}s used). "
            f"Reserve = {b['reserve_seconds']:.2f}s (pass allow_reserve=True to dip in). "
            f"Operator hard-canonical: 120s total. Use sim-local or sim-pilotos backend instead."
        )


def record_usage(actual_seconds: float, *, purpose: str, extra: dict | None = None) -> dict[str, Any]:
    """Record cloud-seconds consumed by a completed call.

    Appends to the ledger (JSONL) + decrements the budget. Returns the
    updated budget record.
    """
    if actual_seconds < 0:
        raise ValueError(f'actual_seconds must be >= 0, got {actual_seconds!r}')
    if not purpose or not purpose.strip():
        raise ValueError('record_usage: purpose is required')

    b = _load_budget()
    b['used_seconds'] = float(b['used_seconds']) + float(actual_seconds)
    _save_budget(b)

    LEDGER_FILE.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        'ts_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'purpose': purpose.strip(),
        'actual_seconds': float(actual_seconds),
        'remaining_after_seconds': remaining_seconds(),
    }
    if extra:
        entry['extra'] = extra
    with LEDGER_FILE.open('a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')

    return b


def reset_budget(*, total_seconds: float = DEFAULT_TOTAL_SECONDS, operator_confirmed: bool = False) -> dict[str, Any]:
    """Reset the budget to a fresh state. REQUIRES operator_confirmed=True.

    Use case: operator buys a new license tranche / refills the cloud
    seconds. NEVER call this from an agent without explicit operator
    instruction.
    """
    if not operator_confirmed:
        raise RuntimeError(
            'reset_budget: operator_confirmed=True is required. '
            'This wipes the used-seconds counter and starts a fresh budget. '
            'Only the operator can authorize this.'
        )
    rec = {
        'schema': 'sinister-seraphim.cloud-budget.v1',
        'total_seconds': float(total_seconds),
        'used_seconds': 0.0,
        'reserve_seconds': EMERGENCY_RESERVE_SECONDS,
        'last_update_utc': None,
        'note': 'Reset by operator confirmation.',
    }
    _save_budget(rec)
    return rec


def status() -> dict[str, Any]:
    """Return the full budget snapshot for human display."""
    b = _load_budget()
    return {
        'total_seconds': b.get('total_seconds'),
        'used_seconds': b.get('used_seconds'),
        'remaining_seconds': remaining_seconds(),
        'usable_seconds': usable_seconds(),
        'reserve_seconds': b.get('reserve_seconds'),
        'last_update_utc': b.get('last_update_utc'),
    }


if __name__ == '__main__':
    import sys
    s = status()
    print('[seraphim.budget] status:')
    for k, v in s.items():
        print(f'  {k:>22} = {v}')
    if remaining_seconds() <= 0:
        print('  [WARN] budget exhausted — cloud calls will refuse.')
        sys.exit(1)
