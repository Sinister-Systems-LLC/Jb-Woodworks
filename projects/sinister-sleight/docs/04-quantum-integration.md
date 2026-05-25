<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
# 04 — Quantum integration

> Operator brief: *"use our quantum toools to expand"*.

## Stance (per fleet doctrine)

Sleight follows the bidirectional-scope rule from `_shared-memory/knowledge/sinister-os-quantum-applicability-2026-05-24.md`:

- **DO use** quantum primitives where classical loses measurably
- **DO NOT** ship quantum-for-quantum-sake when classical wins; document the negative result

Default backend for all quantum calls: `sim-local`. Cloud Wukong-180 budget gated behind `[ASK]` to `sinister-snap-api-quantum` lane owner.

Sibling lane: `D:\Sinister Sanctum\projects\sinister-snap-api-quantum\` owns the `seraphim` CLI + the production recipe (K=4 ZZ-FM r=1 + algorithmically-selected QBC triads). Sleight CONSUMES, does not duplicate.

## Three candidate quantum hooks in Sleight

### Hook 1 — Quantum-kernel SVM for market regime classification

**Classical baseline:** TF-IDF on regime "descriptor" docs (e.g., "high vol + falling breadth + flat term structure" sentence per day) + SVM classifier.

**Quantum candidate:** Quantum-kernel SVM using ZZ-FeatureMap (per `seraphim` production recipe). Pre-screen: run `seraphim find-qbc` on a regime-doc corpus; only proceed if classical TF-IDF off-diag > 0.4 (bidirectional scope rule).

**Acceptance criterion:** Quantum classifier beats classical on out-of-sample regime label accuracy on a 1-year labeled S&P regime dataset. If not, document and use classical.

**Cost:** Sim-local (free) for development; one Wukong-180 verification fire (gated, ~10-30s budget).

### Hook 2 — QAOA for portfolio optimization

**Classical baseline:** Mean-variance optimization (Markowitz) with quadratic programming solver (cvxpy).

**Quantum candidate:** QAOA (Quantum Approximate Optimization Algorithm) for the constrained portfolio problem — particularly useful when:
- Universe > 50 assets
- Hard constraints present (sector caps, ESG screens, position-size caps)
- The classical problem is QUBO-formulatable

**Acceptance criterion:** QAOA-optimized portfolio achieves Sharpe >= classical mean-variance over 90-day OOS window AT EQUAL CONSTRAINT SATISFACTION. If not, document and use classical.

**Implementation reference:** Qiskit Finance has working examples (`qiskit_finance.applications.optimization.PortfolioOptimization`).

**Cost:** Sim-local default; cloud Wukong-180 only after sim shows promise.

### Hook 3 — Amplitude estimation for option pricing

**Classical baseline:** Black-Scholes (analytic) or Monte Carlo (numerical).

**Quantum candidate:** Quantum Amplitude Estimation (QAE) for European / American option pricing. The Qiskit Finance `EuropeanCallPricing` is a worked example with measurable RMSE wins over MC at ~1000+ simulated paths.

**Acceptance criterion:** QAE matches Black-Scholes analytical within 1% relative error on European calls AND beats Monte Carlo on RMSE for >= 1000 simulated paths.

**Cost:** Sim-local sufficient for sub-10-qubit circuits; cloud only if scaling beyond.

**P5+ feature** — applies only when options trading is added.

## What we are NOT doing (anti-quantum-buzzword)

- **Quantum ML for direction prediction** — classical XGBoost on 50 features will demolish quantum for this. Documented negative result via iter-23 anchor in fleet brain.
- **Quantum sentiment analysis** — classical Claude embeddings + cosine similarity are state-of-the-art; quantum offers no advantage.
- **"Quantum supremacy" claims** — we don't ship marketing; we ship measured advantages OR document negative results.
- **Vendor-locked quantum cloud spend** — all primitives go through `seraphim` (operator-controlled wrapper); no raw IBM Q / Rigetti / IonQ API calls.

## How Sleight calls Seraphim

```python
# Hook 1 example (quantum-kernel SVM regime classifier)
from sinister_seraphim import audit

result = audit(
    triad=[regime_doc_a, regime_doc_b, regime_doc_c],
    corpus="regime-pool",
    variant="zzfm-r1",
    backend="sim-local",   # never cloud without [ASK]
)
# If sim shows quantum advantage > classical, proceed to gated real-QPU verification
```

```python
# Hook 2 example (QAOA portfolio optimization)
# (Pseudocode; actual impl uses qiskit_finance API)
from sleight.quantum.portfolio import qaoa_optimize

weights = qaoa_optimize(
    expected_returns=mu,
    covariance=sigma,
    constraints=hard_constraints,
    backend="sim-local",
)
```

## Operator decisions for quantum spend

- Sim-local: no operator approval needed (free, local CPU).
- Cloud Wukong-180 sim shadow: no approval needed (still free).
- Real-QPU Wukong-180 < 30s: notify operator queue; auto-proceed after 10min if no veto.
- Real-QPU Wukong-180 > 30s: blocking [ASK] to operator via OPERATOR-ACTION-QUEUE.md row.

## Composes with

- `_shared-memory/knowledge/sinister-os-quantum-applicability-2026-05-24.md` (bidirectional scope rule, Lane-1 entropy yes / doc-classification no)
- `_shared-memory/knowledge/quantum-memory-kernel-fleet-action-items-2026-05-23.md` (current production recipe, theorem, conjecture, pre-screen)
- `_shared-memory/knowledge/seraphim-cloud-qpu-real-first-fire-2026-05-23.md` (empirical anchors, cancellation theorem, noise model)
- `_shared-memory/knowledge/fleet-quantum-qbc-patterns-2026-05-24.md` (fleet patterns, session-handoff hotspot, K=8 noise-floor cap)
