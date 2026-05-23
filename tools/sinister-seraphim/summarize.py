"""Aggregate summarizer for sinister-seraphim provenance + ledger.

Author: RKOJ-ELENO :: 2026-05-23

Analog to snap-emu's `summarize_recent_fires.py` — reads the
fleet-wide Seraphim ledger + provenance dir and emits aggregate stats:

  - Provenance: total records, by backend, by purpose-prefix, by lane,
    bytes-emitted total, age distribution
  - Snap-RE ledger: total fires, by fire_kind, verdicts, recent activity
  - Cloud budget: remaining + recent burns

CLI:
    seraphim summarize             # human-readable
    seraphim summarize --json      # JSON for downstream consumers
    seraphim summarize --since 24h # filter to last N hours/days

No cloud cost. Pure read-only over local state.
"""
from __future__ import annotations

import json
import os
import time
from collections import Counter
from pathlib import Path
from typing import Any

SANCTUM_ROOT = Path(os.environ.get('SINISTER_SANCTUM_ROOT', r'D:\Sinister Sanctum'))
PROVENANCE_DIR = SANCTUM_ROOT / '_shared-memory' / 'qrng-provenance'
SNAP_RE_LEDGER = SANCTUM_ROOT / '_shared-memory' / 'seraphim-snap-re-ledger.jsonl'
CLOUD_LEDGER = SANCTUM_ROOT / '_shared-memory' / 'seraphim-cloud-ledger.jsonl'
BUDGET_FILE = SANCTUM_ROOT / '_shared-memory' / 'seraphim-cloud-budget.json'


def _parse_since(s: str | None) -> float | None:
    """Parse '24h' / '3d' / '90m' into a unix-time cutoff (seconds).

    Returns None if `s` is None or unparseable; means no filter.
    """
    if not s:
        return None
    s = s.strip().lower()
    if not s:
        return None
    units = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
    if s[-1] in units and s[:-1].isdigit():
        return time.time() - int(s[:-1]) * units[s[-1]]
    if s.isdigit():
        return time.time() - int(s)
    return None


def _purpose_prefix(purpose: str) -> str:
    """Group purposes by their first dash-separated segment ('fingerprint-snap-emu' -> 'fingerprint')."""
    return purpose.split('-', 1)[0] if '-' in purpose else purpose


def _safe_load_json(p: Path) -> dict | None:
    try:
        return json.loads(p.read_text(encoding='utf-8'))
    except Exception:
        return None


def _safe_load_jsonl(p: Path) -> list[dict]:
    if not p.exists():
        return []
    out = []
    for line in p.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out


def summarize_provenance(since_cutoff: float | None = None) -> dict[str, Any]:
    """Aggregate stats over qrng-provenance/*.json files."""
    if not PROVENANCE_DIR.exists():
        return {
            'total_records': 0,
            'note': f'PROVENANCE_DIR not found at {PROVENANCE_DIR}',
        }

    by_backend: Counter[str] = Counter()
    by_purpose_prefix: Counter[str] = Counter()
    by_lane: Counter[str] = Counter()
    total_bytes = 0
    total_records = 0
    oldest_ts: str | None = None
    newest_ts: str | None = None
    oldest_mtime: float | None = None
    newest_mtime: float | None = None

    for p in PROVENANCE_DIR.glob('*.json'):
        try:
            mt = p.stat().st_mtime
        except Exception:
            continue
        if since_cutoff is not None and mt < since_cutoff:
            continue
        rec = _safe_load_json(p)
        if not rec:
            continue
        total_records += 1
        by_backend[str(rec.get('backend', 'unknown'))] += 1
        by_purpose_prefix[_purpose_prefix(str(rec.get('purpose', 'unknown')))] += 1
        nb = rec.get('n_bytes')
        if isinstance(nb, int):
            total_bytes += nb
        ts = rec.get('ts_utc')
        if isinstance(ts, str):
            if oldest_ts is None or ts < oldest_ts:
                oldest_ts = ts
                oldest_mtime = mt
            if newest_ts is None or ts > newest_ts:
                newest_ts = ts
                newest_mtime = mt
        # Lane detection from `extra.lane` (fingerprints) or purpose-suffix
        extra = rec.get('extra')
        if isinstance(extra, dict):
            lane = extra.get('lane')
            if isinstance(lane, str):
                by_lane[lane] += 1
        purpose = str(rec.get('purpose', ''))
        for lane_name in ('snap-emu', 'tiktok-emu', 'bumble-emu', 'kernel-apk', 'sinister-emulator'):
            if lane_name in purpose:
                by_lane[lane_name] += 1
                break

    return {
        'total_records': total_records,
        'total_bytes_aggregated': total_bytes,
        'by_backend': dict(by_backend.most_common()),
        'by_purpose_prefix': dict(by_purpose_prefix.most_common(15)),
        'by_lane': dict(by_lane.most_common()),
        'oldest_ts_utc': oldest_ts,
        'newest_ts_utc': newest_ts,
        'span_seconds': (newest_mtime - oldest_mtime) if (oldest_mtime and newest_mtime) else None,
    }


def summarize_snap_re(since_cutoff: float | None = None) -> dict[str, Any]:
    """Aggregate stats over seraphim-snap-re-ledger.jsonl."""
    rows = _safe_load_jsonl(SNAP_RE_LEDGER)
    if since_cutoff is not None:
        rows = [r for r in rows if isinstance(r.get('ts_utc'), str) and _ts_to_unix(r['ts_utc']) >= since_cutoff]
    by_kind: Counter[str] = Counter()
    by_verdict: Counter[str] = Counter()
    for r in rows:
        by_kind[str(r.get('fire_kind', 'unknown'))] += 1
        by_verdict[str(r.get('verdict', 'none'))] += 1
    return {
        'total_fires': len(rows),
        'by_fire_kind': dict(by_kind.most_common(20)),
        'by_verdict': dict(by_verdict.most_common(20)),
        'recent_5': rows[-5:][::-1],
    }


def summarize_cloud(since_cutoff: float | None = None) -> dict[str, Any]:
    """Cloud-Wukong-180 budget + ledger summary."""
    budget = _safe_load_json(BUDGET_FILE) or {
        'total_seconds': 120.0,
        'used_seconds': 0.0,
        'reserve_seconds': 10.0,
    }
    rows = _safe_load_jsonl(CLOUD_LEDGER)
    if since_cutoff is not None:
        rows = [r for r in rows if isinstance(r.get('ts_utc'), str) and _ts_to_unix(r['ts_utc']) >= since_cutoff]
    total_burn = sum(float(r.get('actual_seconds', 0.0)) for r in rows)
    return {
        'budget_total_seconds': float(budget.get('total_seconds', 120.0)),
        'budget_used_seconds': float(budget.get('used_seconds', 0.0)),
        'budget_remaining_seconds': max(0.0, float(budget.get('total_seconds', 120.0)) - float(budget.get('used_seconds', 0.0))),
        'cloud_calls_in_window': len(rows),
        'cloud_seconds_in_window': round(total_burn, 3),
        'recent_3_calls': rows[-3:][::-1],
    }


def _ts_to_unix(ts: str) -> float:
    """Parse ISO-UTC string to unix time; returns 0 on parse fail."""
    try:
        if ts.endswith('Z'):
            ts = ts[:-1] + '+00:00'
        from datetime import datetime
        return datetime.fromisoformat(ts).timestamp()
    except Exception:
        return 0.0


def summarize_all(since: str | None = None) -> dict[str, Any]:
    cutoff = _parse_since(since)
    return {
        'schema': 'sinister-seraphim.summarize.v1',
        'generated_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'since_filter': since,
        'since_cutoff_unix': cutoff,
        'provenance': summarize_provenance(cutoff),
        'snap_re': summarize_snap_re(cutoff),
        'cloud': summarize_cloud(cutoff),
    }


def render_human(s: dict[str, Any]) -> str:
    """Human-readable text output."""
    out = []
    out.append('=' * 64)
    out.append(' Sinister Seraphim :: aggregate summary')
    out.append('=' * 64)
    out.append(f" generated: {s['generated_utc']}")
    if s['since_filter']:
        out.append(f" filter:    since {s['since_filter']}")
    out.append('')
    p = s['provenance']
    out.append(f" [provenance] {p['total_records']:>5} records, {p['total_bytes_aggregated']:,} bytes aggregated")
    if p.get('oldest_ts_utc'):
        out.append(f"              span: {p['oldest_ts_utc']} -> {p['newest_ts_utc']}")
    if p.get('by_backend'):
        out.append('              by backend:')
        for k, v in p['by_backend'].items():
            out.append(f'                {v:>5}  {k}')
    if p.get('by_lane'):
        out.append('              by lane:')
        for k, v in p['by_lane'].items():
            out.append(f'                {v:>5}  {k}')
    if p.get('by_purpose_prefix'):
        out.append('              top purpose prefixes:')
        for k, v in list(p['by_purpose_prefix'].items())[:8]:
            out.append(f'                {v:>5}  {k}')
    out.append('')
    sr = s['snap_re']
    out.append(f" [snap-re]    {sr['total_fires']:>5} fire-audit entries")
    if sr.get('by_fire_kind'):
        out.append('              by fire_kind:')
        for k, v in sr['by_fire_kind'].items():
            out.append(f'                {v:>5}  {k}')
    if sr.get('by_verdict'):
        out.append('              by verdict:')
        for k, v in sr['by_verdict'].items():
            out.append(f'                {v:>5}  {k}')
    out.append('')
    c = s['cloud']
    out.append(f" [cloud]      Wukong-180 budget: {c['budget_remaining_seconds']:.1f}s / {c['budget_total_seconds']:.1f}s remaining")
    out.append(f"              cloud calls in window: {c['cloud_calls_in_window']}, seconds burned: {c['cloud_seconds_in_window']:.3f}")
    out.append('')
    out.append('=' * 64)
    return '\n'.join(out)


def cli(args) -> int:
    s = summarize_all(since=getattr(args, 'since', None))
    if getattr(args, 'json', False):
        print(json.dumps(s, indent=2, ensure_ascii=False, default=str))
    else:
        print(render_human(s))
    return 0


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description='Sinister Seraphim aggregate summarizer')
    p.add_argument('--json', action='store_true')
    p.add_argument('--since', default=None, help="Filter to last N (e.g. '24h', '3d', '90m')")
    raise SystemExit(cli(p.parse_args()))
