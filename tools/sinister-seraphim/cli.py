"""CLI entry-point for sinister-seraphim.

Author: RKOJ-ELENO :: 2026-05-23

`seraphim <command>` — installed via pyproject.toml scripts. Subcommands:

  seraphim qrng [-n N] [--purpose P]            # generate N bytes of QRNG entropy
  seraphim fingerprint [--lane L]                # generate one emulator fingerprint
  seraphim fingerprint-batch [-n N]              # generate N fingerprints (Lane 2 sim)
  seraphim license-check                         # verify license + print sha256[0:12]
  seraphim budget                                # show cloud-Wukong-180 budget
  seraphim dashboard [--out PATH]                # regenerate the dashboard HTML
  seraphim summarize [--since W]                 # provenance + ledger aggregation
  seraphim audit --variant V [--sim-only]        # run an inversion-overlap memory audit
  seraphim version                               # print package version

Use --json for machine-readable output (default = human-readable).
"""
from __future__ import annotations

import argparse
import json
import sys

# Windows-default cp1252 stdout chokes on unicode that the audit subcommand
# prints (Δ symbol, kets in variant notes). Reconfigure to utf-8 if available.
try:
    sys.stdout.reconfigure(encoding='utf-8')  # type: ignore[attr-defined]
except Exception:
    pass


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


# Audit variant catalog (operator-canonical mapping from CLI flag to encoding params).
# Mirrors the variants empirically validated by audits on 2026-05-23.
_AUDIT_VARIANTS = {
    'k4-angle':   {'encoding': 'angle',      'k': 4, 'reps': 1, 'depth_est': 8,  'budget_est_s': 30,
                   'notes': 'Plain ANGLE inversion overlap, K=4. The canonical regression test.'},
    'k8-angle':   {'encoding': 'angle',      'k': 8, 'reps': 1, 'depth_est': 16, 'budget_est_s': 35,
                   'notes': 'Plain ANGLE K=8. Tests whether bigger Hilbert space breaks the plateau (it does NOT; noise wall starts here).'},
    'angle-cnot': {'encoding': 'angle-cnot', 'k': 4, 'reps': 1, 'depth_est': 12, 'budget_est_s': 20,
                   'notes': 'ANGLE + linear-CNOT chain. Parameter-free entanglement self-cancels (cancellation theorem); sim == plain ANGLE.'},
    'zzfm-r1':    {'encoding': 'zzfm',       'k': 4, 'reps': 1, 'depth_est': 34, 'budget_est_s': 45,
                   'notes': 'PRODUCTION RECIPE: Truncated ZZ-FM r=1. QUADRUPLE-verified 25-34pp quantum advantage over classical on real WK_C180 (4 QBC triads, mean 30pp). Find candidate triads via find-zzfm-qbc-triads.py. Noise pushes overlap DOWN below sim at depth 34 (helps, not hurts).'},
    'zzfm-r2':    {'encoding': 'zzfm',       'k': 4, 'reps': 2, 'depth_est': 68, 'budget_est_s': 80,
                   'notes': 'Sim breaks plateau dramatically (3.076% QBC rate vs r=1 0.142%); but real-QPU at depth 68 noise-saturates near classical baseline. Use r=1 for real-QPU; r=2 sim-only.'},
}


def _audit_cmd(args) -> int:
    try:
        from .memory_kernel import run_kernel_audit
        from .budget import remaining_seconds, BudgetExhausted
    except ImportError:
        from memory_kernel import run_kernel_audit  # type: ignore
        from budget import remaining_seconds, BudgetExhausted  # type: ignore

    if args.list_variants:
        if args.json:
            print(json.dumps(_AUDIT_VARIANTS, indent=2, ensure_ascii=False))
        else:
            print('[seraphim audit] available variants:\n')
            for name, v in _AUDIT_VARIANTS.items():
                print(f'  {name:<12} encoding={v["encoding"]:<10} k={v["k"]}  reps={v["reps"]}  depth~{v["depth_est"]}  est-burn~{v["budget_est_s"]}s')
                print(f'  {"":12} {v["notes"]}')
                print()
        return 0

    if args.variant not in _AUDIT_VARIANTS:
        print(f'[seraphim audit] unknown variant {args.variant!r}. Use --list-variants.', file=sys.stderr)
        return 2

    v = _AUDIT_VARIANTS[args.variant]
    shots = args.shots if args.shots is not None else 256

    if not args.sim_only:
        # Variant-level real-QPU guard: zzfm-r2 (depth 68) is past the noise wall
        # per the 16:43Z empirical anchor (sim 0.62 saturated to real 0.24 near classical).
        # Real-QPU at this depth wastes budget. Refuse unless --force-real-qpu.
        if args.variant == 'zzfm-r2' and not args.force_real_qpu:
            msg = (
                f"[seraphim audit] variant 'zzfm-r2' (depth ~68) is sim-only-recommended. "
                f"Empirical anchor 2026-05-23T16:43Z showed depth-68 ZZ-FM r=2 saturates "
                f"near classical baseline on real WK_C180 — wastes cloud budget. "
                f"Re-run with --sim-only, OR (if you really mean it) --force-real-qpu."
            )
            if args.json:
                print(json.dumps({'ok': False, 'reason': 'variant-sim-only-recommended', 'detail': msg}))
            else:
                print(msg, file=sys.stderr)
            return 6

        # Budget pre-flight (rough; submit_kernel_pair will gate per call too)
        rem = remaining_seconds()
        if rem < v['budget_est_s']:
            msg = (f'[seraphim audit] budget pre-flight: variant {args.variant!r} estimated burn '
                   f'{v["budget_est_s"]}s exceeds remaining {rem:.2f}s. Re-run with --sim-only, '
                   f'or reset budget (operator: `seraphim budget` to inspect).')
            if args.json:
                print(json.dumps({'ok': False, 'reason': 'budget-insufficient', 'detail': msg}))
            else:
                print(msg, file=sys.stderr)
            return 3

    # Resolve --corpus into a list of brain entry filenames (or None)
    corpus = None
    if args.corpus:
        import os
        from pathlib import Path as _P
        SR = _P(os.environ.get('SINISTER_SANCTUM_ROOT', r'D:\Sinister Sanctum'))
        BD = SR / '_shared-memory' / 'knowledge'
        if args.corpus == 'full':
            corpus = sorted(p.name for p in BD.glob('*.md') if p.name not in {'README.md', '_INDEX.md', '_TEMPLATE.md'})
        elif args.corpus == 'pool':
            # Re-derive the 124-doc balanced pool used by find-optimal-triad.py
            files = sorted(p.name for p in BD.glob('*.md') if p.name not in {'README.md', '_INDEX.md', '_TEMPLATE.md'})
            topics: dict[str, list[str]] = {}
            for f in files:
                topics.setdefault(f.split('-')[0], []).append(f)
            corpus = []
            for prefix, group in sorted(topics.items()):
                corpus.extend(group[:4])
        elif _P(args.corpus).exists():
            corpus = [ln.strip() for ln in _P(args.corpus).read_text(encoding='utf-8').splitlines() if ln.strip()]
        else:
            print(f'[seraphim audit] unknown --corpus value {args.corpus!r}. Try "full" / "pool" / path-to-file.', file=sys.stderr)
            return 5

    # Resume-from-partial: load prior_pair_results from the saved JSON
    prior_pair_results = None
    if args.resume_from:
        from pathlib import Path as _P
        try:
            prior = json.loads(_P(args.resume_from).read_text(encoding='utf-8'))
            prior_pair_results = prior.get('pair_results', [])
            landed = [p for p in prior_pair_results if p.get('overlap') is not None and not p.get('stalled')]
            print(f'[seraphim audit] resuming from {args.resume_from}: {len(landed)} prior pair(s) will be reused')
        except Exception as exc:
            print(f'[seraphim audit] --resume-from failed: {type(exc).__name__}: {exc}', file=sys.stderr)
            return 7

    try:
        result = run_kernel_audit(
            encoding=v['encoding'],
            k=v['k'],
            reps=v['reps'],
            shots=shots,
            triad=args.triad,
            corpus=corpus,
            sim_only=args.sim_only,
            pair_loop_cap_seconds=args.cap,
            per_pair_stall_seconds=args.stall,
            prior_pair_results=prior_pair_results,
        )
    except BudgetExhausted as exc:
        if args.json:
            print(json.dumps({'ok': False, 'reason': 'budget-exhausted', 'detail': str(exc)}))
        else:
            print(f'[seraphim audit] BUDGET EXHAUSTED: {exc}', file=sys.stderr)
        return 4

    result['variant'] = args.variant
    result['variant_notes'] = v['notes']

    # Optional output file
    if args.out:
        from pathlib import Path
        Path(args.out).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        cl = result['classical_off_diag_mean']
        sm = result['sim_off_diag_mean']
        rq = result['real_qpu_off_diag_mean']
        print(f'[seraphim audit] variant={args.variant}  ({v["notes"]})')
        print(f'  triad: {", ".join(result["triad"])}')
        print(f'  classical off-diag mean: {cl:.4f}')
        print(f'  sim off-diag mean:       {sm:.4f}    Δ vs classical = {sm - cl:+.4f}')
        if rq is not None:
            d_real_sim = rq - sm
            d_real_classical = rq - cl
            print(f'  real-QPU off-diag mean:  {rq:.4f}    Δ vs sim = {d_real_sim:+.4f}    Δ vs classical = {d_real_classical:+.4f}')
            pairs_landed = sum(1 for p in result['pair_results'] if p.get('overlap') is not None)
            print(f'  pairs landed: {pairs_landed}/3   pair-loop wall: {result["pair_loop_wall_seconds"]}s')
            if result['budget_remaining_after'] is not None:
                print(f'  budget remaining after: {result["budget_remaining_after"]:.3f}s')
        elif result.get('sim_only'):
            print(f'  real-QPU:                skipped (--sim-only)')
        elif result.get('aborted'):
            print(f'  real-QPU:                ABORTED ({result["abort_reason"]})')
        if args.out:
            print(f'  saved: {args.out}')
    return 0


def _audit_pipeline_cmd(args) -> int:
    """3-phase orchestration: find QBC triads → sim-gate → real-QPU verify the survivors.

    Walks the top-N QBC triads through the production workflow. For each:
      Phase A: sim audit (free; confirms sim < classical = positive advantage)
      Phase B: real-QPU audit IF sim passed AND budget remaining > variant estimate
    Skips real-QPU per-triad when sim_off_diag >= classical_off_diag (bidirectional rule).
    Stops short-circuit if budget runs low.
    """
    try:
        from .memory_kernel import find_qbc_triads, run_kernel_audit
        from .budget import remaining_seconds, BudgetExhausted
    except ImportError:
        from memory_kernel import find_qbc_triads, run_kernel_audit  # type: ignore
        from budget import remaining_seconds, BudgetExhausted  # type: ignore

    v_map = {
        'zzfm-r1': ('zzfm', 4, 1),
        'k4-angle': ('angle', 4, 1),
    }
    if args.variant not in v_map:
        print(f'[seraphim audit-pipeline] variant {args.variant!r} not supported (use zzfm-r1 — the production winner)', file=sys.stderr)
        return 2
    encoding, k, reps = v_map[args.variant]

    # Phase 1: discover
    print(f'[seraphim audit-pipeline] Phase 1: find top-{args.top_n} QBC triads (sim sweep, free)')
    print(f'  variant={args.variant}  corpus={args.corpus}')
    qbc = find_qbc_triads(encoding=encoding, k=k, reps=reps, top_n=args.top_n, corpus_mode=args.corpus)
    print(f'  pool={qbc["pool_size"]}  triads_evaluated={qbc["triads_evaluated"]:,}  qbc_count={qbc["qbc_count"]:,} ({qbc["qbc_pct"]:.3f}%)')
    print()

    # Phase 2 + 3: per-triad sim-gate + real-QPU
    results = []
    for t in qbc['top_n_triads']:
        rank = t['rank']
        docs = t['docs']
        sim_adv = t['advantage']
        print(f'  --- Triad #{rank} (sim advantage +{sim_adv:.4f}) ---')
        for d in docs:
            print(f'    {d}')

        if sim_adv <= 0:
            print(f'    PHASE 2 (sim-gate): sim advantage {sim_adv:+.4f} not positive — SKIP real-QPU (bidirectional rule)')
            results.append({'rank': rank, 'docs': docs, 'sim_advantage': sim_adv, 'real_qpu_off_diag_mean': None, 'phase': 'skipped-sim-gate'})
            continue

        if args.skip_real_qpu:
            print(f'    PHASE 2 (sim-gate): sim advantage {sim_adv:+.4f} OK; PHASE 3 (real-QPU) SKIPPED (--skip-real-qpu)')
            results.append({'rank': rank, 'docs': docs, 'sim_advantage': sim_adv, 'real_qpu_off_diag_mean': None, 'phase': 'sim-gated-skip-real'})
            continue

        rem = remaining_seconds()
        per_triad_est = 45 if args.variant == 'zzfm-r1' else 30
        if rem < per_triad_est:
            print(f'    BUDGET: remaining {rem:.2f}s < estimate {per_triad_est}s — STOPPING short-circuit (operator: reset budget to continue)')
            results.append({'rank': rank, 'docs': docs, 'sim_advantage': sim_adv, 'real_qpu_off_diag_mean': None, 'phase': 'budget-exhausted'})
            break

        print(f'    PHASE 3 (real-QPU audit)... budget pre-audit {rem:.2f}s')
        try:
            r = run_kernel_audit(
                encoding=encoding, k=k, reps=reps, shots=args.shots,
                triad=docs,
                corpus=None if args.corpus is None else _resolve_corpus(args.corpus),
                sim_only=False,
                pair_loop_cap_seconds=args.cap,
                per_pair_stall_seconds=args.stall,
            )
        except BudgetExhausted as exc:
            print(f'    BudgetExhausted mid-audit: {exc}')
            results.append({'rank': rank, 'docs': docs, 'sim_advantage': sim_adv, 'real_qpu_off_diag_mean': None, 'phase': 'budget-exhausted-midcall'})
            break

        cl = r['classical_off_diag_mean']
        sm = r['sim_off_diag_mean']
        rq = r['real_qpu_off_diag_mean']
        if rq is not None:
            adv_real = cl - rq
            print(f'    RESULT: classical={cl:.4f}  sim={sm:.4f}  real-QPU={rq:.4f}  advantage={adv_real:+.4f}')
        else:
            print(f'    RESULT: aborted ({r["abort_reason"]})')

        results.append({
            'rank': rank, 'docs': docs,
            'sim_advantage': sim_adv,
            'classical_off_diag_mean': cl, 'sim_off_diag_mean': sm,
            'real_qpu_off_diag_mean': rq,
            'pair_results': r.get('pair_results', []),
            'aborted': r.get('aborted'), 'abort_reason': r.get('abort_reason', ''),
            'pair_loop_wall_seconds': r.get('pair_loop_wall_seconds'),
            'phase': 'verified' if rq is not None else 'aborted',
        })
        print()

    # Summary
    print('[seraphim audit-pipeline] === SUMMARY ===')
    print(f'  {"#":>3} {"phase":>22} {"sim adv":>10} {"real adv":>10}')
    for r_row in results:
        phase = r_row['phase']
        sim_a = r_row['sim_advantage']
        rq = r_row.get('real_qpu_off_diag_mean')
        if rq is not None:
            cl = r_row['classical_off_diag_mean']
            real_a = cl - rq
            print(f'  {r_row["rank"]:>3} {phase:>22} {sim_a:>+10.4f} {real_a:>+10.4f}')
        else:
            print(f'  {r_row["rank"]:>3} {phase:>22} {sim_a:>+10.4f} {"-":>10}')

    if args.out:
        from pathlib import Path
        summary = {
            'schema': 'sinister-seraphim.audit-pipeline.v1',
            'variant': args.variant, 'corpus': args.corpus,
            'top_n': args.top_n, 'shots': args.shots,
            'cap': args.cap, 'stall': args.stall,
            'qbc_sweep_stats': {
                'pool_size': qbc['pool_size'],
                'triads_evaluated': qbc['triads_evaluated'],
                'qbc_count': qbc['qbc_count'],
                'qbc_pct': qbc['qbc_pct'],
            },
            'results': results,
            'budget_remaining_after': remaining_seconds(),
        }
        Path(args.out).write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')
        print(f'  saved: {args.out}')
    return 0


def _resolve_corpus(corpus_arg):
    """Shared corpus resolver used by _audit_pipeline_cmd and _audit_cmd."""
    import os
    from pathlib import Path as _P
    SR = _P(os.environ.get('SINISTER_SANCTUM_ROOT', r'D:\Sinister Sanctum'))
    BD = SR / '_shared-memory' / 'knowledge'
    if corpus_arg == 'full':
        return sorted(p.name for p in BD.glob('*.md') if p.name not in {'README.md', '_INDEX.md', '_TEMPLATE.md'})
    if corpus_arg == 'pool':
        files = sorted(p.name for p in BD.glob('*.md') if p.name not in {'README.md', '_INDEX.md', '_TEMPLATE.md'})
        topics: dict[str, list[str]] = {}
        for f in files:
            topics.setdefault(f.split('-')[0], []).append(f)
        pool = []
        for prefix, group in sorted(topics.items()):
            pool.extend(group[:4])
        return pool
    if _P(corpus_arg).exists():
        return [ln.strip() for ln in _P(corpus_arg).read_text(encoding='utf-8').splitlines() if ln.strip()]
    return None


def _find_qbc_cmd(args) -> int:
    try:
        from .memory_kernel import find_qbc_triads
    except ImportError:
        from memory_kernel import find_qbc_triads  # type: ignore

    encoding = args.encoding
    k = args.k
    reps = args.reps
    if args.variant:
        # Map variant flag to (encoding, k, reps) for convenience
        v_map = {
            'zzfm-r1': ('zzfm', 4, 1),
            'zzfm-r2': ('zzfm', 4, 2),
            'k4-angle': ('angle', 4, 1),
            'k8-angle': ('angle', 8, 1),
            'angle-cnot': ('angle-cnot', 4, 1),
        }
        if args.variant not in v_map:
            print(f'[seraphim find-qbc] unknown --variant {args.variant!r}; use one of {sorted(v_map)}', file=sys.stderr)
            return 2
        encoding, k, reps = v_map[args.variant]

    # Parse --ceiling-reps (space- or comma-separated) and auto-enable for
    # ceiling/headroom ranking when not explicitly provided.
    ceiling_reps_list: list[int] | None = None
    if args.ceiling_reps:
        raw = args.ceiling_reps.replace(',', ' ').split()
        try:
            ceiling_reps_list = [int(x) for x in raw if x]
        except ValueError:
            print(f'[seraphim find-qbc] invalid --ceiling-reps {args.ceiling_reps!r}; '
                  f'use space- or comma-separated integers (e.g. "2 3 4 5 6")', file=sys.stderr)
            return 2
    if args.rank_by in ('ceiling', 'headroom') and ceiling_reps_list is None:
        ceiling_reps_list = [2, 3, 4, 5, 6]
    if args.rank_by in ('ceiling', 'headroom') and encoding != 'zzfm':
        print(f"[seraphim find-qbc] --rank-by {args.rank_by} requires zzfm encoding "
              f"(reps parameter is ignored by {encoding!r}); use --variant zzfm-r1 or --encoding zzfm",
              file=sys.stderr)
        return 2

    result = find_qbc_triads(
        encoding=encoding, k=k, reps=reps,
        top_n=args.top_n, corpus_mode=args.corpus,
        ceiling_reps=ceiling_reps_list, rank_by=args.rank_by,
    )

    if args.out:
        from pathlib import Path
        Path(args.out).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0

    # Human-readable summary
    print(f'[seraphim find-qbc] encoding={encoding}  k={k}  reps={reps}  corpus={result["corpus_mode"]}  pool={result["pool_size"]}')
    print(f'  triads evaluated: {result["triads_evaluated"]:,}')
    print(f'  quantum-beats-classical: {result["qbc_count"]:,} ({result["qbc_pct"]:.3f}%)')
    print(f'  max advantage: +{result["max_advantage"]:.4f}')
    print(f'  median advantage: {result["median_advantage"]:+.4f}')
    if ceiling_reps_list:
        print(f'  ceiling sweep: reps {ceiling_reps_list}  ranking: {args.rank_by}')
    print()

    rank_desc = {
        'r1': 'classical - sim at r=1',
        'ceiling': 'best advantage across ceiling sweep (= max headroom + r=1)',
        'headroom': 'ceiling - r=1 (biggest error-mitigation payoff)',
        'classical': 'classical TF-IDF baseline (iter 40: predicts ceiling with r=+0.95)',
    }[args.rank_by]
    print(f'  Top {args.top_n} QBC triads (ranked by {rank_desc}):')
    for t in result['top_n_triads']:
        print(f'    #{t["rank"]:>2}  adv=+{t["advantage"]:.4f}  sim={t["sim_off_diag_mean"]:.4f}  classical={t["classical_off_diag_mean"]:.4f}')
        if 'ceiling_pp' in t:
            print(f'         ceiling=+{t["ceiling_pp"]:.2f}pp@r{t["ceiling_rep"]}  '
                  f'headroom=+{t["headroom_pp"]:.2f}pp  ({t["pct_of_ceiling_at_base_reps"]:.1f}% at r={reps})')
        for d in t['docs']:
            print(f'         {d}')
        if t['audit_cmd']:
            print(f'         RUN: {t["audit_cmd"]}')
        print()
    if args.out:
        print(f'  [saved] {args.out}')
    return 0


def _brain_recall_cmd(args) -> int:
    try:
        from .memory_kernel import recall_brain
    except ImportError:
        from memory_kernel import recall_brain  # type: ignore

    result = recall_brain(
        args.query,
        top_k_results=args.top_k,
        encoding=args.encoding,
        k_qubits=args.k,
        alpha=args.alpha,
        corpus_mode=args.corpus,
    )

    if args.out:
        from pathlib import Path
        Path(args.out).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0

    print(f'[seraphim brain-recall] query: {result["query"]!r}')
    print(f'  encoding={result["encoding"]}  k_qubits={result["k_qubits"]}  alpha={result["alpha"]}  '
          f'corpus={result["corpus_mode"]} ({result["corpus_size"]} docs)')
    print()
    print(f'  Top {args.top_k} results (ranked by alpha*tfidf + (1-alpha)*quantum):')
    for r in result['top_results']:
        print(f'    #{r["rank"]:>2}  combined={r["combined_score"]:.4f}  '
              f'tfidf={r["tfidf_sim"]:.4f}  quantum={r["quantum_sim"]:.4f}')
        print(f'         {r["filename"]}')
    if args.out:
        print(f'  [saved] {args.out}')
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

    p_au = sub.add_parser('audit', help='Run an inversion-overlap memory-kernel audit on a triad')
    p_au.add_argument('--variant', default='k4-angle', help='Audit variant (use --list-variants to see all)')
    p_au.add_argument('--list-variants', action='store_true', help='List available audit variants + their depth/burn estimates')
    p_au.add_argument('--sim-only', action='store_true', help='Skip real-QPU submission; sim baseline only (zero cloud burn)')
    p_au.add_argument('--shots', type=int, default=None, help='Shots per pair (default 256)')
    p_au.add_argument('--cap', type=float, default=60.0, help='Pair-loop wall cap in seconds (default 60)')
    p_au.add_argument('--stall', type=float, default=60.0, help='Per-pair stall guard in seconds (default 60)')
    p_au.add_argument('--triad', nargs=3, default=None, metavar=('DOC1', 'DOC2', 'DOC3'),
                      help='Override the default triad with 3 brain-entry filenames')
    p_au.add_argument('--corpus', default=None, metavar='MODE',
                      help='TF-IDF vocabulary corpus: "full" (all 145 knowledge entries), "pool" (124-doc balanced pool from find-optimal-triad), or path to a file listing entries one-per-line. If omitted, uses 3-doc-legacy mode.')
    p_au.add_argument('--out', default=None, help='Optional output JSON path')
    p_au.add_argument('--force-real-qpu', action='store_true',
                      help='Override sim-only-recommended guards (currently: zzfm-r2 at depth 68 noise-saturates near classical per 16:43Z anchor). Use only if you really mean it.')
    p_au.add_argument('--resume-from', default=None, metavar='JSON_PATH',
                      help='Resume from a prior partial audit JSON. Pairs already in prior_pair_results with valid overlap are reused; only missing/stalled pairs get fresh real-QPU submissions.')
    p_au.set_defaults(fn=_audit_cmd)

    p_pl = sub.add_parser('audit-pipeline', help='3-phase orchestration: find QBC triads → sim-gate → real-QPU verify (the production workflow in one command)')
    p_pl.add_argument('--variant', default='zzfm-r1', help='Audit variant (default zzfm-r1, the production winner)')
    p_pl.add_argument('--top-n', dest='top_n', type=int, default=3, help='How many top-N QBC triads to walk (default 3)')
    p_pl.add_argument('--corpus', default='pool', help='Corpus mode (default pool)')
    p_pl.add_argument('--shots', type=int, default=256, help='Shots per pair (default 256)')
    p_pl.add_argument('--cap', type=float, default=180.0, help='Pair-loop wall cap per audit (default 180s)')
    p_pl.add_argument('--stall', type=float, default=120.0, help='Per-pair stall guard (default 120s)')
    p_pl.add_argument('--skip-real-qpu', action='store_true', help='Only run sim phase (no real-QPU)')
    p_pl.add_argument('--out', default=None, help='Optional summary JSON path')
    p_pl.set_defaults(fn=_audit_pipeline_cmd)

    p_fq = sub.add_parser('find-qbc', help='Find quantum-beats-classical triads via sim sweep (zero cloud burn)')
    p_fq.add_argument('--variant', default='zzfm-r1', help='Audit variant shortcut (default zzfm-r1, the production winner)')
    p_fq.add_argument('--encoding', default='zzfm', help='Override encoding directly (zzfm / angle / angle-cnot)')
    p_fq.add_argument('--k', type=int, default=4, help='Number of qubits (default 4)')
    p_fq.add_argument('--reps', type=int, default=1, help='Repetition count for zzfm (default 1)')
    p_fq.add_argument('--top-n', dest='top_n', type=int, default=10, help='How many top-N QBC triads to return (default 10)')
    p_fq.add_argument('--corpus', default='pool', help='Corpus mode (pool=124-doc balanced / full=145+ entries)')
    p_fq.add_argument('--out', default=None, help='Optional output JSON path')
    p_fq.add_argument('--rank-by', dest='rank_by', default='r1', choices=['r1', 'ceiling', 'headroom', 'classical'],
                      help='How to rank top-N triads (default r1 = current behavior). ceiling/headroom require a ceiling sweep; '
                           'auto-enables --ceiling-reps "2 3 4 5 6" if not set.')
    p_fq.add_argument('--ceiling-reps', dest='ceiling_reps', default=None,
                      help='Space- or comma-separated extra reps to sweep for ceiling/headroom computation (e.g. "2 3 4 5 6"). '
                           'Only applies to zzfm encoding. Adds ~0.5s per triad at top-N=10.')
    p_fq.set_defaults(fn=_find_qbc_cmd)

    p_br = sub.add_parser('brain-recall', help='TF-IDF + quantum-kernel hybrid brain-entry recall (iter 47)')
    p_br.add_argument('query', help='Query text (e.g. "git multi-agent coordination")')
    p_br.add_argument('--top-k', dest='top_k', type=int, default=5, help='How many top brain entries to return (default 5)')
    p_br.add_argument('--encoding', default='angle', choices=['angle', 'angle-cnot', 'zzfm'],
                      help='Quantum kernel encoding (default angle = K=8 ANGLE per iter-44 doctrine)')
    p_br.add_argument('-k', type=int, default=8, help='Qubits / top-K TF-IDF features (default 8 per iter-44)')
    p_br.add_argument('--alpha', type=float, default=1.0,
                      help='TF-IDF weight (default 1.0=pure TF-IDF). Iter 48 stress-test showed alpha<1.0 degrades '
                           'pair-wise recall — the quantum kernel collapses to a few noise docs across diverse queries. '
                           'Override only after empirical validation for your use case.')
    p_br.add_argument('--corpus', default='full', choices=['full', 'pool'], help='Brain corpus mode (default full)')
    p_br.add_argument('--out', default=None, help='Optional output JSON path')
    p_br.set_defaults(fn=_brain_recall_cmd)

    p_ver = sub.add_parser('version', help='Print package version')
    p_ver.set_defaults(fn=_version_cmd)

    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == '__main__':
    raise SystemExit(main())
