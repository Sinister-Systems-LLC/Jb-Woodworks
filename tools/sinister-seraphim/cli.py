"""CLI entry-point for sinister-seraphim.

Author: RKOJ-ELENO :: 2026-05-23

`seraphim <command>` — installed via pyproject.toml scripts. Subcommands:

  seraphim qrng [-n N] [--purpose P]      # generate N bytes of QRNG entropy
  seraphim fingerprint [--lane L]          # generate one emulator fingerprint
  seraphim fingerprint-batch [-n N]        # generate N fingerprints (Lane 2 sim)
  seraphim license-check                   # verify license + print sha256[0:12]
  seraphim version                         # print package version

Use --json for machine-readable output (default = human-readable).
"""
from __future__ import annotations

import argparse
import json
import sys


def _qrng_cmd(args) -> int:
    try:
        from .qrng import quantum_random
    except ImportError:
        from qrng import quantum_random  # type: ignore
    data = quantum_random(args.n, purpose=args.purpose, backend=args.backend)
    if args.json:
        print(json.dumps({'n_bytes': args.n, 'hex': data.hex(), 'backend': args.backend, 'purpose': args.purpose}))
    else:
        print(f'[seraphim qrng] {args.n} bytes (backend={args.backend}): {data.hex()}')
    return 0


def _fingerprint_cmd(args) -> int:
    try:
        from .fingerprint import make_fingerprint
    except ImportError:
        from fingerprint import make_fingerprint  # type: ignore
    fp = make_fingerprint(lane=args.lane, build_fingerprint_stub=args.build_fp, backend=args.backend)
    print(json.dumps(fp, indent=None if args.json else 2))
    return 0


def _fingerprint_batch_cmd(args) -> int:
    try:
        from .fingerprint import make_fingerprint_batch
    except ImportError:
        from fingerprint import make_fingerprint_batch  # type: ignore
    batch = make_fingerprint_batch(args.n, lane=args.lane, build_fingerprint_stub=args.build_fp, backend=args.backend)
    if args.json:
        print(json.dumps(batch))
    else:
        for fp in batch:
            print(json.dumps(fp, indent=2))
            print()
    return 0


def _license_check_cmd(args) -> int:
    try:
        from .license import LicenseError, license_fingerprint
    except ImportError:
        from license import LicenseError, license_fingerprint  # type: ignore
    try:
        fp = license_fingerprint()
        if args.json:
            print(json.dumps({'ok': True, 'sha256_12': fp}))
        else:
            print(f'[seraphim license] loaded OK; sha256[0:12] = {fp}')
        return 0
    except LicenseError as exc:
        if args.json:
            print(json.dumps({'ok': False, 'error': str(exc)}))
        else:
            print(f'[seraphim license] FAIL: {exc}', file=sys.stderr)
        return 2


def _dashboard_cmd(args) -> int:
    try:
        from .dashboard import write_dashboard
    except ImportError:
        from dashboard import write_dashboard  # type: ignore
    from pathlib import Path
    out = Path(args.out) if args.out else None
    p = write_dashboard(out)
    if args.json:
        print(json.dumps({'path': str(p), 'url': f'file:///{str(p).replace(chr(92), "/")}'}))
    else:
        print(f'[seraphim dashboard] wrote {p}')
        print(f'[seraphim dashboard] open in browser: file:///{str(p).replace(chr(92), "/")}')
    return 0


def _summarize_cmd(args) -> int:
    try:
        from .summarize import render_human, summarize_all
    except ImportError:
        from summarize import render_human, summarize_all  # type: ignore
    s = summarize_all(since=args.since)
    if args.json:
        print(json.dumps(s, indent=2, ensure_ascii=False, default=str))
    else:
        print(render_human(s))
    return 0


def _budget_cmd(args) -> int:
    try:
        from .budget import status, remaining_seconds
    except ImportError:
        from budget import status, remaining_seconds  # type: ignore
    s = status()
    if args.json:
        print(json.dumps(s))
    else:
        print('[seraphim budget] cloud-Wukong-180 license budget (operator hard-canonical: 120s total):')
        for k, v in s.items():
            print(f'  {k:>22} = {v}')
        if remaining_seconds() <= 0:
            print('  [WARN] budget exhausted — cloud calls will refuse.')
            return 1
    return 0


def _version_cmd(args) -> int:
    try:
        from . import __version__
    except ImportError:
        __version__ = '0.1.0'  # fallback when imported flat
    if args.json:
        print(json.dumps({'version': __version__}))
    else:
        print(f'sinister-seraphim {__version__}')
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog='seraphim', description='Sinister Seraphim CLI (Origin PilotOS / quantum-compute wrapper)')
    p.add_argument('--json', action='store_true', help='Machine-readable JSON output')
    sub = p.add_subparsers(dest='cmd', required=True)

    p_qrng = sub.add_parser('qrng', help='Generate N bytes of QRNG entropy')
    p_qrng.add_argument('-n', type=int, default=16, help='Bytes to generate (1-4096)')
    p_qrng.add_argument('--purpose', default='cli-ad-hoc', help='Provenance purpose tag')
    p_qrng.add_argument('--backend', default='sim-local', choices=['sim-local', 'sim-pilotos', 'cloud-wukong-180'])
    p_qrng.set_defaults(fn=_qrng_cmd)

    p_fp = sub.add_parser('fingerprint', help='Generate one emulator device-fingerprint blob')
    p_fp.add_argument('--lane', default='generic', help='Lane name (snap-emu/tiktok-emu/bumble-emu/kernel-apk/generic)')
    p_fp.add_argument('--build-fp', dest='build_fp', default=None, help='Optional build_fingerprint stub')
    p_fp.add_argument('--backend', default='sim-local', choices=['sim-local', 'sim-pilotos', 'cloud-wukong-180'])
    p_fp.set_defaults(fn=_fingerprint_cmd)

    p_fb = sub.add_parser('fingerprint-batch', help='Generate N fingerprints (Lane 2 starter)')
    p_fb.add_argument('-n', type=int, default=5, help='Count (1-10000)')
    p_fb.add_argument('--lane', default='generic')
    p_fb.add_argument('--build-fp', dest='build_fp', default=None)
    p_fb.add_argument('--backend', default='sim-local', choices=['sim-local', 'sim-pilotos', 'cloud-wukong-180'])
    p_fb.set_defaults(fn=_fingerprint_batch_cmd)

    p_lc = sub.add_parser('license-check', help='Verify license loads + print sha256[0:12] fingerprint')
    p_lc.set_defaults(fn=_license_check_cmd)

    p_bg = sub.add_parser('budget', help='Show cloud-Wukong-180 license-budget status (120s operator cap)')
    p_bg.set_defaults(fn=_budget_cmd)

    p_db = sub.add_parser('dashboard', help='Regenerate the static HTML dashboard (_shared-memory/dashboards/seraphim.html)')
    p_db.add_argument('--out', default=None, help='Optional output path (defaults to _shared-memory/dashboards/seraphim.html)')
    p_db.set_defaults(fn=_dashboard_cmd)

    p_sum = sub.add_parser('summarize', help='Aggregate provenance + snap-re ledger + cloud-budget stats')
    p_sum.add_argument('--since', default=None, help="Filter window (e.g. '24h', '3d', '90m')")
    p_sum.set_defaults(fn=_summarize_cmd)

    p_ver = sub.add_parser('version', help='Print package version')
    p_ver.set_defaults(fn=_version_cmd)

    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == '__main__':
    raise SystemExit(main())
