<!-- Author: RKOJ-ELENO :: 2026-05-23 -->
# Deprecated audit scripts — replaced by `seraphim audit`

> **Deprecation date:** 2026-05-23 evening
> **Reason:** Each script duplicated ~200-300 LOC of circuit-build + submit-poll + record-usage logic that now lives in `tools/sinister-seraphim/cloud_submit.py`. The `seraphim audit --variant <name>` CLI subcommand replaces all of them with budget-gated, sim-baseline-aware single-command audits.
> **Authorship:** Operator-directed cleanup: *"deprecate the standalone audit scripts and update the readmes"*.

These files are preserved (not deleted) for historical reference to the empirical investigation that established the WK_C180 memory-kernel verdicts on 2026-05-23. The CLI replacement reproduces each test's logic exactly (sim baselines verified identical).

## CLI replacement mapping

| Deprecated script | CLI equivalent | Empirical anchor (MEMORY.md) |
|---|---|---|
| `run-qpu-10s-memory-test.py` | `seraphim audit --variant k4-angle` | 15:50Z — clean baseline, real-QPU off-diag 0.8398 vs sim 0.8975 |
| `run-qpu-k8-angle-audit.py` | `seraphim audit --variant k8-angle` | 16:08Z — noise wall at depth 16; real 0.6185 vs sim 0.8490 |
| `run-qpu-k4-angle-cnot-audit.py` | `seraphim audit --variant angle-cnot` | 16:18Z — cancellation theorem; sim ≡ plain ANGLE |
| `run-qpu-k4-zzfm-reps-audit.py` (REPS=1) | `seraphim audit --variant zzfm-r1` | sim-only check 16:25Z (marginal) |
| `run-qpu-k4-zzfm-reps-audit.py` (REPS=2) | `seraphim audit --variant zzfm-r2` | 16:35-43Z — noise saturation; real 0.2422 vs sim 0.6189 |
| `run-qpu-k4-zzfm-r2-finish.py` | _no direct CLI yet_ | 16:43Z — resume-from-partial pattern; queued as future `--resume-pair` flag |
| `sim-check-truncated-zz-fm.py` | `seraphim audit --variant zzfm-r1 --sim-only` (or `zzfm-r2`) | 16:25Z + 16:28Z — sim-only ZZ-FM sweep |

## Why these are kept (not deleted)

1. **Provenance trace.** The audit JSONs in `outputs/` reference each script's filename + run_id; preserving the scripts keeps the provenance chain unbroken.
2. **Self-contained reference implementations.** Each script has the FULL circuit-build + submit pattern in one file — useful as a reference for someone debugging a new encoding before the CLI catalog covers it.
3. **Resume-from-partial pattern.** `run-qpu-k4-zzfm-r2-finish.py` demonstrates how to combine a prior-pair result with a new submission — that pattern isn't yet in the CLI but should be added (`--resume-pair PAIR JSON_PATH`).

## What to use instead (new code)

```bash
# List available audit variants with depth + budget estimates
seraphim audit --list-variants

# Run sim-only check (zero cloud burn — predict before fire)
seraphim audit --variant k4-angle --sim-only

# Run full audit (sim baseline + real-QPU triad; budget pre-flight gate)
seraphim audit --variant k4-angle --shots 256 --cap 60 --stall 60

# Save full audit JSON to a specific path
seraphim audit --variant k8-angle --out outputs/k8-rerun-$(date +%Y%m%dT%H%M%SZ).json
```

```python
# Or from Python
from sinister_seraphim.memory_kernel import run_kernel_audit

result = run_kernel_audit(
    encoding='angle',  # or 'angle-cnot', 'zzfm'
    k=4,
    reps=1,
    shots=256,
    sim_only=False,  # set True to skip real-QPU
)
print(result['real_qpu_off_diag_mean'], result['sim_off_diag_mean'])
```

## Not deprecated (still at project root)

- `run-test.py` — original dual-emu Seraphim integration test (sim-local fingerprint generation; different use case)
- `run-all-memory-variants.py` — pre-inversion-overlap memory-kernel variants A/B/C (CPUQVM-local, historical comparison)
- `run-real-qpu-memory-kernel.py` — SWAP-test variant (proven decoherence-corrupted at K=4 depth ~9 in 14:10Z run; kept as historical reference for the failed-shape regression test)
- `run-real-qpu-inversion-overlap.py` — original inversion-overlap script (predates the per-variant audits; superseded conceptually by the CLI but retained for the SWAP-vs-inversion direct comparison from 14:20Z)
