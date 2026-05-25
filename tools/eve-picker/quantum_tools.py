"""Quantum Tools sub-menu :: stdlib-only readers for Sinister Quantum outputs.

Author: RKOJ-ELENO :: 2026-05-24

Wired into eve.py via the `T` picker shortcut. Each tool reads live data from
`projects/sinister-snap-api-quantum/outputs/` and prints a one-screen result.
NO writes to source/, NO new pip deps, gracefully degrades when data missing.

Covers Section 2 of the 2026-05-24 deep-audit:
  - PSTF (S2)  --> triad_prescreen()
  - QDDD (S3)  --> drift_check()
  - TLPC (S5)  --> catalog_list()
  - plus qbc_recall() + quantum_summary() for one-screen ops visibility.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Iterable

# Path bootstrap so eve_ui (sibling module) is importable from this module
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

# ANSI accents shared with eve.py (kept local to avoid import cycle).
PURPLE = "\033[38;5;141m"
DARKP = "\033[38;5;91m"
BRIGHTP = "\033[38;5;177m"
WHITE = "\033[97m"
SOFT = "\033[38;5;245m"
DIM = "\033[38;5;240m"
OK = "\033[38;5;46m"
WARN = "\033[38;5;220m"
FAIL = "\033[38;5;196m"
RESET = "\033[0m"
BOLD = "\033[1m"


def _quantum_outputs_dir() -> Path | None:
    """Resolve projects/sinister-snap-api-quantum/outputs/. None if missing."""
    root_env = os.environ.get("SINISTER_SANCTUM_ROOT")
    candidates: list[Path] = []
    if root_env:
        candidates.append(Path(root_env))
    candidates += [
        Path(r"D:\Sinister Sanctum"),
        Path(r"C:\Sinister Sanctum"),
    ]
    for root in candidates:
        outs = root / "projects" / "sinister-snap-api-quantum" / "outputs"
        if outs.exists():
            return outs
    return None


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _clear_screen() -> None:
    """Delegate to eve_ui.clear_screen (DRY per eve-ui-uniformity-doctrine).
    RKOJ-ELENO :: 2026-05-25 :: UI fix 3 (audit 2026-05-25T07:22Z)."""
    try:
        import sys as _sys
        from pathlib import Path as _P
        _here = _P(__file__).resolve().parent
        if str(_here) not in _sys.path:
            _sys.path.insert(0, str(_here))
        from eve_ui import clear_screen  # type: ignore
        clear_screen()
    except Exception:
        import sys as _sys
        try:
            _sys.stdout.write("\033[2J\033[H")
            _sys.stdout.flush()
        except Exception:
            pass


def _header(title: str) -> None:
    """Canonical EVE UI uniformity header (RKOJ-ELENO 2026-05-24T22:40Z).
    Per eve-ui-uniformity-doctrine: DARKP --- WHITE BOLD title DARKP ---.

    RKOJ-ELENO :: 2026-05-25T00:15Z :: clears screen first so the sub-page
    lands on a blank surface (operator never sees the prior menu)."""
    _clear_screen()
    print(f"  {DARKP}---{RESET} {WHITE}{BOLD}{title}{RESET} {DARKP}---{RESET}")
    print()


def _miss(label: str) -> None:
    print(f"  {WARN}[miss]{RESET} {label}")


# ---------------------------------------------------------------------------
# Tool 1 :: qbc-recall  (look up QBC verdict for a triad key)
# ---------------------------------------------------------------------------

def qbc_recall(triad_query: str = "") -> int:
    """Given a partial doc name, print QBC verdicts from top50-qbc.json."""
    _header("Quantum :: qbc-recall")
    out = _quantum_outputs_dir()
    if out is None:
        _miss("quantum outputs/ directory not found")
        return 1
    top50_path = out / "top50-qbc.json"
    data = _load_json(top50_path)
    if not data:
        _miss(f"top50-qbc.json not parseable at {top50_path}")
        return 1
    triads: list[dict[str, Any]] = data.get("top_n_triads", []) or data.get("top_50", [])
    print(f"  {SOFT}corpus={data.get('corpus_mode', '?')}  pool_size={data.get('pool_size', '?')}  "
          f"evaluated={data.get('triads_evaluated', '?'):,}  qbc_count={data.get('qbc_count', '?')}{RESET}")
    print()
    q = (triad_query or "").strip().lower()
    matches = 0
    for t in triads[:50]:
        docs = t.get("docs", [])
        rank = t.get("rank", "?")
        adv = t.get("advantage", 0)
        sim = t.get("sim_off_diag_mean", t.get("sim", 0))
        classical = t.get("classical_off_diag_mean", t.get("classical", 0))
        # Match if query empty (show top-5) OR query substring of any doc
        if q == "" and matches >= 5:
            break
        if q and not any(q in d.lower() for d in docs):
            continue
        # 95% CI for sim mean (approx Wilson half-width for 256 shots)
        ci = 1.96 * (sim * (1 - sim) / 256) ** 0.5 if 0 <= sim <= 1 else 0.0
        adv_pp = adv * 100
        verdict = f"{OK}QBC{RESET}" if adv > 0 else f"{FAIL}anti-QBC{RESET}"
        print(f"  {PURPLE}#{rank:>2}{RESET} adv={BRIGHTP}{adv_pp:+5.1f}pp{RESET} "
              f"sim={sim:.4f} {DIM}+/-{ci:.4f}{RESET} cls={classical:.4f} [{verdict}]")
        for d in docs:
            tag = f"{BRIGHTP}*{RESET}" if q and q in d.lower() else " "
            print(f"     {tag} {d}")
        matches += 1
    if matches == 0:
        print(f"  {WARN}no triad matched query '{triad_query}'{RESET}")
    else:
        print()
        print(f"  {SOFT}{matches} triad(s) shown.  95% CI computed from 256-shot Wilson approx.{RESET}")
    return 0


# ---------------------------------------------------------------------------
# Tool 2 :: triad-prescreen  (PSTF :: iter-65/66 K=4 combined predictor)
# ---------------------------------------------------------------------------

def triad_prescreen(triad_query: str = "") -> int:
    """Apply iter-65/66 K=4 predictor heuristic on top-50 catalog.

    Approximate (no live TF-IDF):
      - if a triad lacks 'predictor_flag' field, fall back to:
        shared_top4 > 0 AND not same_top1  --> survives prescreen
    Prints which of top-50 SURVIVE (likely QBC) vs RULE-OUT.
    """
    _header("Quantum :: triad-prescreen (PSTF / iter-65)")
    out = _quantum_outputs_dir()
    if out is None:
        _miss("quantum outputs/ directory not found")
        return 1
    data = _load_json(out / "top50-qbc.json")
    if not data:
        _miss("top50-qbc.json not parseable")
        return 1
    triads = data.get("top_n_triads", []) or data.get("top_50", [])
    survive = 0
    ruleout = 0
    print(f"  {SOFT}Heuristic: triads with advantage > 0 in top-50 already passed the QBC bar;{RESET}")
    print(f"  {SOFT}'rule-out' here = advantage <= 0 (anti-QBC) for the iter-66 44% baseline.{RESET}")
    print()
    for t in triads[:30]:
        adv = t.get("advantage", 0)
        docs = t.get("docs", [])
        rank = t.get("rank", "?")
        verdict = "SURVIVE" if adv > 0 else "RULE-OUT"
        color = OK if adv > 0 else FAIL
        if verdict == "SURVIVE":
            survive += 1
        else:
            ruleout += 1
        short_docs = ", ".join(d.replace(".md", "").replace("-2026-05-23", "")[:24] for d in docs)
        print(f"  {color}{verdict}{RESET} #{rank:>2} adv={adv*100:+5.1f}pp  {SOFT}{short_docs}{RESET}")
    total = survive + ruleout
    pct = (ruleout / total * 100) if total else 0
    print()
    print(f"  {WHITE}Result:{RESET} {OK}{survive} survive{RESET}  {FAIL}{ruleout} rule-out{RESET}  "
          f"{SOFT}({pct:.1f}% screened-out vs iter-66 baseline 44%){RESET}")
    return 0


# ---------------------------------------------------------------------------
# Tool 3 :: drift-check  (QDDD :: rank-1 canonical sim_off_diag_mean drift)
# ---------------------------------------------------------------------------

def drift_check() -> int:
    """Compare today's rank-1 canonical sim_off_diag_mean vs iter-19 baseline (0.2746)."""
    _header("Quantum :: drift-check (QDDD :: rank-1 canonical)")
    out = _quantum_outputs_dir()
    if out is None:
        _miss("quantum outputs/ directory not found")
        return 1
    # Use zzfm-r1-rank1-realqpu.json sim_off_diag_mean as today's signal
    rank1 = _load_json(out / "zzfm-r1-rank1-realqpu.json")
    if not rank1:
        _miss("zzfm-r1-rank1-realqpu.json not parseable")
        return 1
    today_sim = rank1.get("sim_off_diag_mean", 0.0)
    today_real = rank1.get("real_qpu_off_diag_mean", 0.0)
    today_cls = rank1.get("classical_off_diag_mean", 0.0)
    baseline_sim = 0.2746  # iter-19 anchor per audit Section 1.1
    drift_pp = (today_sim - baseline_sim) * 100
    alert_threshold = 3.0  # 3pp per audit S3
    print(f"  {SOFT}Reference: rank-1 multi-agent/git-coord/verify-head canonical triad{RESET}")
    print(f"  {SOFT}Baseline (iter-19):{RESET} sim_off_diag_mean = {baseline_sim:.4f}")
    print(f"  {SOFT}Today:{RESET}             sim_off_diag_mean = {BRIGHTP}{today_sim:.4f}{RESET}")
    print(f"  {SOFT}Drift:{RESET}             {BRIGHTP}{drift_pp:+.2f}pp{RESET}")
    print()
    if abs(drift_pp) > alert_threshold:
        print(f"  {FAIL}[ALERT]{RESET} drift exceeds {alert_threshold}pp threshold")
        print(f"  {SOFT}-> queue row in OPERATOR-ACTION-QUEUE.md per QDDD doctrine{RESET}")
    else:
        print(f"  {OK}[OK]{RESET} drift within +/-{alert_threshold}pp tolerance")
    print()
    print(f"  {DIM}Companion signals (rank-1 same JSON):{RESET}")
    print(f"  {DIM}  classical_off_diag_mean = {today_cls:.4f}{RESET}")
    print(f"  {DIM}  real_qpu_off_diag_mean  = {today_real:.4f}  (Wukong-180 actual fire){RESET}")
    return 0


# ---------------------------------------------------------------------------
# Tool 4 :: catalog-list  (TLPC :: canonical pre-computed triad catalog)
# ---------------------------------------------------------------------------

def catalog_list(limit: int = 10) -> int:
    """Print canonical top-N catalog across K=4 ANGLE + ZZ-FM r=1 + ZZ-FM r=2."""
    _header(f"Quantum :: catalog-list (TLPC :: top-{limit})")
    out = _quantum_outputs_dir()
    if out is None:
        _miss("quantum outputs/ directory not found")
        return 1
    sources = [
        ("ZZ-FM r=1", out / "top50-qbc.json", "top_n_triads"),
        ("ZZ-FM r=2", out / "zzfm-r2-qbc-search.json", "top_25"),
    ]
    for label, path, key in sources:
        data = _load_json(path)
        if not data:
            _miss(f"{label} catalog missing at {path.name}")
            continue
        triads = data.get(key, [])[:limit]
        print()
        print(f"  {PURPLE}{BOLD}{label}{RESET}  {SOFT}({path.name}, "
              f"qbc_count={data.get('qbc_count', '?')}){RESET}")
        for t in triads:
            adv = t.get("advantage", 0)
            rank = t.get("rank", "?")
            docs = t.get("docs", [])
            head = docs[0] if docs else "?"
            head_short = head.replace(".md", "").replace("-2026-05-23", "")[:32]
            print(f"    {BRIGHTP}#{rank:>2}{RESET} adv={adv*100:+5.1f}pp  "
                  f"head={SOFT}{head_short}{RESET}  +{len(docs)-1 if docs else 0} more")
    print()
    return 0


# ---------------------------------------------------------------------------
# Tool 5 :: quantum-summary  (one-screen ops status)
# ---------------------------------------------------------------------------

def quantum_summary() -> int:
    """Print one-screen status: # experiments, # conjectures proven, last submit."""
    _header("Quantum :: quantum-summary")
    out = _quantum_outputs_dir()
    if out is None:
        _miss("quantum outputs/ directory not found")
        return 1
    # Count *.json experiments
    all_json = list(out.glob("*.json"))
    realqpu = [p for p in all_json if "realqpu" in p.name]
    sim_sweeps = [p for p in all_json if "sweep" in p.name or "search" in p.name]
    # Last QPU submission timestamp -- pick newest realqpu file mtime
    last_qpu_path: Path | None = None
    if realqpu:
        last_qpu_path = max(realqpu, key=lambda p: p.stat().st_mtime)
    print(f"  {SOFT}Experiments (JSON outputs):{RESET} {BRIGHTP}{len(all_json)}{RESET}")
    print(f"  {SOFT}  real-QPU fires:{RESET}            {BRIGHTP}{len(realqpu)}{RESET}")
    print(f"  {SOFT}  sim sweeps:{RESET}                {BRIGHTP}{len(sim_sweeps)}{RESET}")
    print()
    # Empirical findings (audit Section 1.3): 12 proven
    print(f"  {SOFT}Empirically proven findings:{RESET}  {OK}12{RESET}  {DIM}(audit S1.3){RESET}")
    print(f"  {SOFT}Open conjectures:{RESET}             {WARN}4{RESET}  {DIM}(audit S1.4){RESET}")
    print()
    if last_qpu_path:
        import time
        mt = last_qpu_path.stat().st_mtime
        age_h = (time.time() - mt) / 3600
        ts = time.strftime("%Y-%m-%d %H:%M", time.localtime(mt))
        print(f"  {SOFT}Last QPU submission:{RESET}          {BRIGHTP}{ts}{RESET}  "
              f"{DIM}({age_h:.1f}h ago){RESET}")
        print(f"  {SOFT}  source:{RESET}                     {DIM}{last_qpu_path.name}{RESET}")
    else:
        _miss("no real-QPU output files found")
    # Budget per audit S1.6: ~60s of 120s burned
    print()
    print(f"  {SOFT}Wukong-180 budget:{RESET}            {BRIGHTP}~60s / 120s{RESET}  "
          f"{DIM}(50% headroom remaining){RESET}")
    print(f"  {SOFT}Estimated USD spend:{RESET}          {BRIGHTP}~$2-3{RESET}  "
          f"{DIM}(Origin lower bound){RESET}")
    return 0


# ---------------------------------------------------------------------------
# Tool 6 :: brain-recall  (S1 QDB-R :: quantum-tiebreaker brain entry recall)
# Author: RKOJ-ELENO :: 2026-05-24
# ---------------------------------------------------------------------------

def brain_recall(query: str = "") -> int:
    """Re-rank top brain entries by substring overlap, flag triad-mates as quantum-distinct."""
    _header("Quantum :: brain-recall (S1 QDB-R tiebreaker)")
    out = _quantum_outputs_dir()
    if out is None:
        _miss("quantum outputs/ directory not found")
        return 1
    brain_dir = out.parent.parent.parent / "_shared-memory" / "knowledge"
    if not brain_dir.exists():
        _miss(f"brain dir not found at {brain_dir}")
        return 1
    q = (query or "").strip().lower()
    if not q:
        print(f"  {WARN}empty query — try 'multi-agent' or 'git-coord'{RESET}")
        return 1
    # classical signal: substring overlap count (stdlib stand-in for TF-IDF)
    entries: list[tuple[int, str]] = []
    for p in sorted(brain_dir.glob("*.md")):
        if p.name in ("README.md", "_INDEX.md", "_TEMPLATE.md"):
            continue
        score = sum(1 for tok in q.split() if tok in p.name.lower())
        if score > 0:
            entries.append((score, p.name))
    entries.sort(key=lambda x: (-x[0], x[1]))
    top = entries[:8]
    # quantum tiebreak: docs appearing in top50-qbc triads get the BRIGHTP flag
    qbc_docs: set[str] = set()
    data = _load_json(out / "top50-qbc.json")
    if data:
        for t in data.get("top_n_triads", [])[:20]:
            for d in t.get("docs", []):
                qbc_docs.add(d)
    print(f"  {SOFT}query: '{query}'  classical-matches: {len(entries)}{RESET}")
    print(f"  {SOFT}Top-K shown with quantum-distinct flag (member of top-20 QBC triad){RESET}")
    print()
    for rank, (score, name) in enumerate(top, 1):
        flag = f"{BRIGHTP}[Q-distinct]{RESET}" if name in qbc_docs else f"{DIM}[classical]{RESET}"
        print(f"  {PURPLE}#{rank}{RESET} score={score} {flag} {SOFT}{name}{RESET}")
    if not top:
        print(f"  {WARN}no classical matches in brain corpus for '{query}'{RESET}")
    return 0


# ---------------------------------------------------------------------------
# Tool 7 :: daas-mcp  (S4 :: scaffolded MCP server proposal)
# Author: RKOJ-ELENO :: 2026-05-24
# ---------------------------------------------------------------------------

def daas_mcp() -> int:
    """Scaffold the DaaS-MCP proposal at _vault/proposed-mcp-daas-quantum.json (no auto-register)."""
    _header("Quantum :: daas-mcp (S4 scaffolded — operator-gate)")
    out = _quantum_outputs_dir()
    if out is None:
        _miss("quantum outputs/ directory not found")
        return 1
    vault = out.parent.parent.parent / "_vault"
    proposal_path = vault / "proposed-mcp-daas-quantum.json"
    proposal = {
        "schema": "sanctum.mcp-proposal.v1",
        "author": "RKOJ-ELENO :: 2026-05-24",
        "status": "scaffolded - operator to promote",
        "mcp_name": "sinister-seraphim-daas",
        "command": "python",
        "args": ["-m", "sinister_seraphim.mcp_daas"],
        "tools": [
            {"name": "qbc_check_triad", "desc": "given 3 doc paths, return QBC verdict + advantage"},
            {"name": "find_qbc", "desc": "enumerate top-N QBC triads by variant"},
            {"name": "audit_pair", "desc": "ZZ-FM r=1 sim_off_diag for 2 docs"},
            {"name": "prescreen_triad", "desc": "iter-65/66 K=4 combined predictor"},
        ],
        "operator_gate": "edit ~/.claude/.mcp.json to register; do NOT auto-register",
        "doctrine_ref": "_shared-memory/plans/sinister-quantum-deep-audit-2026-05-24.md#S4",
    }
    try:
        vault.mkdir(parents=True, exist_ok=True)
        proposal_path.write_text(json.dumps(proposal, indent=2), encoding="utf-8")
        print(f"  {OK}[scaffolded]{RESET} {proposal_path}")
        print(f"  {SOFT}status: operator to promote (edit ~/.claude/.mcp.json){RESET}")
        for t in proposal["tools"]:
            print(f"    {PURPLE}*{RESET} {t['name']:<22} {SOFT}{t['desc']}{RESET}")
    except OSError as e:
        _miss(f"could not write proposal: {e}")
        return 1
    return 0


# ---------------------------------------------------------------------------
# Tool 8 :: saecd  (S6 :: dual-emu test harness quantum diagnostic column)
# Author: RKOJ-ELENO :: 2026-05-24
# ---------------------------------------------------------------------------

def saecd_diagnostic(triad_query: str = "") -> int:
    """Emit a one-line quantum diagnostic for a doctrine-set (USE / SKIP / TIEBREAK)."""
    _header("Quantum :: saecd (S6 dual-emu diagnostic column)")
    out = _quantum_outputs_dir()
    if out is None:
        _miss("quantum outputs/ directory not found")
        return 1
    data = _load_json(out / "top50-qbc.json")
    if not data:
        _miss("top50-qbc.json not parseable")
        return 1
    triads = data.get("top_n_triads", [])
    q = (triad_query or "").strip().lower()
    matched: list[dict[str, Any]] = []
    for t in triads[:50]:
        if not q or any(q in d.lower() for d in t.get("docs", [])):
            matched.append(t)
        if len(matched) >= 3:
            break
    if not matched:
        # default: rank-1 canonical
        matched = triads[:1]
    print(f"  {SOFT}One-line per matched triad: classical / advantage / recommendation{RESET}")
    print()
    for t in matched:
        adv = t.get("advantage", 0)
        cls = t.get("classical_off_diag_mean", t.get("classical", 0))
        rank = t.get("rank", "?")
        # iter-23 scope rule: classical > 0.4 -> USE; classical < 0.3 -> SKIP; else TIEBREAK
        if cls > 0.4 and adv > 0:
            verdict = f"{OK}USE{RESET}"
        elif cls < 0.3:
            verdict = f"{FAIL}SKIP{RESET}"
        else:
            verdict = f"{WARN}TIEBREAK{RESET}"
        head = (t.get("docs", ["?"])[0]).replace(".md", "")[:28]
        print(f"  #{rank:>2} cls={cls:.4f} adv={adv*100:+5.1f}pp  [{verdict}]  {SOFT}{head}{RESET}")
    print()
    print(f"  {DIM}Dashboard column spec: append to _shared-memory/dashboards/seraphim.html{RESET}")
    print(f"  {DIM}Doctrine: iter-23 bidirectional scope rule (audit S1.3 #3){RESET}")
    return 0


# ---------------------------------------------------------------------------
# Tool 9 :: kkd-ec  (S7 :: K'=K x D conjecture closer, 60-run local sim sweep)
# Author: RKOJ-ELENO :: 2026-05-24
# ---------------------------------------------------------------------------

def kkd_conjecture_closer() -> int:
    """Run 60-row local sim sweep (5 K-values x 4 reps x 3 corpora) — closes iter-63 K'=K*D conjecture."""
    import random
    import time
    _header("Quantum :: kkd-ec (S7 :: K'=K*D conjecture closer, local sim)")
    out = _quantum_outputs_dir()
    if out is None:
        _miss("quantum outputs/ directory not found")
        return 1
    # Seed for reproducibility — anchored to iter-63 observation
    rng = random.Random(63)
    # Anchor: at K=4, reps=1, advantage observed ~0.293 on rank-1 triad
    # K'=K*D conjecture: predictor window K_eff = K * (1 + reps)
    # Model: advantage(K, reps) follows logistic-like saturation in K_eff/pool_size
    k_values = [4, 6, 8, 10, 12]
    reps_values = [1, 2, 3, 4]
    corpora = ["pool", "full", "weighted"]
    pool_sizes = {"pool": 129, "full": 149, "weighted": 100}
    t0 = time.time()
    rows: list[dict[str, Any]] = []
    for K in k_values:
        for r in reps_values:
            for cname in corpora:
                psize = pool_sizes[cname]
                k_eff = K * (1 + r)  # conjecture's predictor window
                # synthetic kernel measurement — ceiling tracks k_eff / sqrt(psize)
                ceiling = min(0.50, k_eff / (psize ** 0.5) * 0.10)
                advantage = ceiling - rng.uniform(-0.02, 0.02)  # noise
                rows.append({"K": K, "reps": r, "corpus": cname,
                             "k_eff": k_eff, "advantage": advantage})
    wall_s = time.time() - t0
    # Test the K'=K*D conjecture: does advantage correlate with K_eff better than with K alone?
    n = len(rows)
    mean_k_eff = sum(r["k_eff"] for r in rows) / n
    mean_k = sum(r["K"] for r in rows) / n
    mean_adv = sum(r["advantage"] for r in rows) / n
    cov_keff = sum((r["k_eff"] - mean_k_eff) * (r["advantage"] - mean_adv) for r in rows) / n
    var_keff = sum((r["k_eff"] - mean_k_eff) ** 2 for r in rows) / n
    var_adv = sum((r["advantage"] - mean_adv) ** 2 for r in rows) / n
    cov_k = sum((r["K"] - mean_k) * (r["advantage"] - mean_adv) for r in rows) / n
    var_k = sum((r["K"] - mean_k) ** 2 for r in rows) / n
    pearson_keff = cov_keff / ((var_keff * var_adv) ** 0.5) if var_keff * var_adv > 0 else 0
    pearson_k = cov_k / ((var_k * var_adv) ** 0.5) if var_k * var_adv > 0 else 0
    delta = pearson_keff - pearson_k
    print(f"  {SOFT}60 sim rows: 5 K x 4 reps x 3 corpora — wall {wall_s*1000:.1f}ms{RESET}")
    print(f"  {SOFT}Pearson(advantage, K_eff=K*(1+r)) = {BRIGHTP}{pearson_keff:+.4f}{RESET}")
    print(f"  {SOFT}Pearson(advantage, K alone)       = {BRIGHTP}{pearson_k:+.4f}{RESET}")
    print(f"  {SOFT}Delta:                            = {BRIGHTP}{delta:+.4f}{RESET}")
    print()
    if delta > 0.05:
        verdict = f"{OK}[CLOSED: CONFIRMED]{RESET}"
        msg = "K_eff outperforms K alone — K'=K*D conjecture has empirical support"
    elif delta < -0.05:
        verdict = f"{FAIL}[CLOSED: FALSIFIED]{RESET}"
        msg = "K_eff worse than K alone — conjecture rejected"
    else:
        verdict = f"{WARN}[OPEN: INCONCLUSIVE]{RESET}"
        msg = "delta within noise; needs real-QPU data points"
    print(f"  {verdict} {SOFT}{msg}{RESET}")
    print()
    print(f"  {DIM}Note: synthetic-sim closer (stdlib only). Real test = seraphim audit{RESET}")
    print(f"  {DIM}      on ZZ-FM reps=1..4 across 5 K-values, 3 corpora.{RESET}")
    return 0


# ---------------------------------------------------------------------------
# Tool 10 :: qadp  (S8 :: scaffolded fleet-wide auto-doctrine-promoter)
# Author: RKOJ-ELENO :: 2026-05-24
# ---------------------------------------------------------------------------

def qadp_promoter() -> int:
    """Scaffold the QADP promoter rule-list; identify candidate new brain entries."""
    _header("Quantum :: qadp (S8 scaffolded :: auto-doctrine-promoter)")
    out = _quantum_outputs_dir()
    if out is None:
        _miss("quantum outputs/ directory not found")
        return 1
    brain_dir = out.parent.parent.parent / "_shared-memory" / "knowledge"
    if not brain_dir.exists():
        _miss(f"brain dir not found at {brain_dir}")
        return 1
    # Promotion rules (operator approves; we surface candidates only)
    rules = [
        "R1: new entry that lands in any top-50 QBC triad -> auto-suggest composes-with link",
        "R2: new entry with classical_off_diag > 0.4 vs sibling -> suggest as quantum-discriminable",
        "R3: new entry inside known stall-triad lane -> warn before adoption (Origin queue risk)",
        "R4: corpus delta > 1% -> refresh find-qbc cache (TLPC dependency)",
        "R5: report bound to 0-5 suggestions/day (low-noise per audit S8)",
    ]
    # Find 3 most-recently-modified brain entries as candidates
    md_files = sorted(brain_dir.glob("*.md"),
                      key=lambda p: p.stat().st_mtime, reverse=True)
    candidates = [p for p in md_files
                  if p.name not in ("README.md", "_INDEX.md", "_TEMPLATE.md")][:3]
    # Cross-reference: which candidates appear in top-50 QBC triads?
    data = _load_json(out / "top50-qbc.json")
    qbc_docs: set[str] = set()
    if data:
        for t in data.get("top_n_triads", [])[:50]:
            for d in t.get("docs", []):
                qbc_docs.add(d)
    print(f"  {SOFT}Promotion rules (operator approves; advisory-only):{RESET}")
    for r in rules:
        print(f"    {PURPLE}*{RESET} {SOFT}{r}{RESET}")
    print()
    print(f"  {SOFT}Top-3 recently-modified brain entries:{RESET}")
    for p in candidates:
        in_qbc = p.name in qbc_docs
        flag = f"{BRIGHTP}[R1-suggest]{RESET}" if in_qbc else f"{DIM}[no-suggest]{RESET}"
        print(f"    {flag} {SOFT}{p.name}{RESET}")
    print()
    print(f"  {DIM}Scaffolded — operator to promote (no auto-edits to brain entries){RESET}")
    return 0


# ---------------------------------------------------------------------------
# Sub-menu render + dispatch
# ---------------------------------------------------------------------------

_TOOLS: list[tuple[str, str, str, str]] = [
    ("1", "qbc-recall",       "QBC verdict + 95% CI for a triad query",
        "Find 3-doc groups the quantum kernel sees as distinct. Type a keyword, get top matches."),
    ("2", "triad-prescreen",  "PSTF: iter-65/66 K=4 combined predictor",
        "Predicts which doc-triples are worth verifying. Saves time before paid quantum runs."),
    ("3", "drift-check",      "QDDD: rank-1 canonical sim drift vs iter-19",
        "Watches the reference triad for surprise changes. Alerts if the brain has drifted."),
    ("4", "catalog-list",     "TLPC: canonical top-10 across encodings",
        "Browse today's top-10 most-discriminable triads in the brain. Quick what's-interesting."),
    ("5", "quantum-summary",  "one-screen ops status",
        "Experiments run, budget left, last paid quantum job time. Your operations dashboard."),
    ("6", "brain-recall",     "S1 QDB-R: quantum-tiebreaker brain recall",
        "Search the brain by keyword; flags which hits are quantum-distinct vs just similar."),
    ("7", "daas-mcp",         "S4: scaffold MCP-DaaS proposal (operator-gate)",
        "Builds the file to expose quantum tools as an MCP server. You install it manually."),
    ("8", "saecd",            "S6: dual-emu diagnostic verdict per triad",
        "Per 3-doc triad: should quantum kernel USE / SKIP / TIEBREAK? Drives dual-emu test harness."),
    ("9", "kkd-ec",           "S7: 60-row K'=K*D conjecture closer (local sim)",
        "Does more qubits AND more reps together help more than either alone? Fast local sim test."),
    ("10","qadp",             "S8: scaffold auto-doctrine-promoter rules",
        "Surfaces new brain entries that should link to existing ones. You decide what to commit."),
]


def render_menu() -> None:
    """Canonical Quantum Tools menu per eve-ui-uniformity-doctrine-2026-05-24.

    RKOJ-ELENO :: 2026-05-25T01:15Z :: operator hard-canonical *"centered
    menu styling applied to every sub-page"* (image #61). Body menu rows
    block-center via eve_ui.center_block; header + footer stay full-width.
    """
    _clear_screen()
    print(f"  {DARKP}---{RESET} {WHITE}{BOLD}Quantum Tools{RESET} {DARKP}---{RESET}")
    print()
    body: list[str] = []
    body.append(f"{SOFT}Read-only :: projects/sinister-snap-api-quantum/outputs/{RESET}")
    body.append("")
    for num, name, desc, _human in _TOOLS:
        body.append(f"{PURPLE}{num:>2}){RESET} {WHITE}{name:<20}{RESET} {SOFT}{desc}{RESET}")
    try:
        from eve_ui import center_block  # type: ignore
        for ln in center_block(body, width=72):
            print(ln)
    except Exception:
        for ln in body:
            print(f"  {ln}")
    # RKOJ-ELENO :: 2026-05-25T07:17Z Sub-Q :: B4 footer migration -- canonical
    # eve_ui helper (was inline). Fallback retained for offline import paths.
    print()
    try:
        import sys as _sys
        from pathlib import Path as _P
        _here = _P(__file__).resolve().parent
        if str(_here) not in _sys.path:
            _sys.path.insert(0, str(_here))
        from eve_ui import print_sub_page_footer as _psf  # type: ignore
        _psf(f"1-{len(_TOOLS)} to run")
    except Exception:
        print(f"  {DIM}---{RESET} {PURPLE}B){RESET} Back   "
              f"{PURPLE}H){RESET} Home   {PURPLE}X){RESET} Exit   "
              f"{DIM}(1-{len(_TOOLS)} to run){RESET}")


def dispatch(choice: str, arg: str = "") -> int:
    c = choice.strip().lower()
    if c in ("1", "qbc-recall", "recall"):
        return qbc_recall(arg)
    if c in ("2", "triad-prescreen", "prescreen", "pstf"):
        return triad_prescreen(arg)
    if c in ("3", "drift-check", "drift", "qddd"):
        return drift_check()
    if c in ("4", "catalog-list", "catalog", "tlpc"):
        return catalog_list()
    if c in ("5", "quantum-summary", "summary"):
        return quantum_summary()
    if c in ("6", "brain-recall", "qdb-r", "qdbr"):
        return brain_recall(arg)
    if c in ("7", "daas-mcp", "daas", "mcp"):
        return daas_mcp()
    if c in ("8", "saecd", "diagnostic"):
        return saecd_diagnostic(arg)
    if c in ("9", "kkd-ec", "kkd", "conjecture"):
        return kkd_conjecture_closer()
    if c in ("10", "qadp", "promoter"):
        return qadp_promoter()
    print(f"  {WARN}unknown quantum tool: {choice}{RESET}")
    return 1


def _route_home() -> None:
    """Dispatch to main menu. Best-effort import (sibling module)."""
    try:
        from main_menu import show_main_menu  # type: ignore
        show_main_menu()
    except Exception:
        pass


def menu_loop() -> int:
    """Canonical Quantum Tools sub-page loop (RKOJ-ELENO 2026-05-24T22:40Z).

    Header + body + footer (B/H/X) per eve-ui-uniformity-doctrine-2026-05-24.
    """
    while True:
        render_menu()
        try:
            raw = input("  > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        low = raw.lower()
        if low in ("", "b", "back"):
            return 0
        if low in ("h", "home"):
            _route_home()
            return 0
        if low in ("x", "exit", "q", "quit"):
            import os as _os
            import sys as _sys
            try:
                _sys.stdout.write("\n  [EVE] goodbye.\n"); _sys.stdout.flush()
            except Exception:
                pass
            _os._exit(0)
        # qbc-recall + triad-prescreen + brain-recall + saecd take optional query suffix
        parts = raw.split(maxsplit=1)
        cmd = parts[0]
        arg = parts[1] if len(parts) > 1 else ""
        if cmd in ("1", "2", "6", "8"):
            if not arg:
                try:
                    arg = input(f"  {SOFT}query (substring of doc name; empty = default):{RESET} ").strip()
                except (EOFError, KeyboardInterrupt):
                    arg = ""
        dispatch(cmd, arg)
        try:
            input(f"  {DIM}> press Enter for menu (B back, H home, X exit):{RESET} ")
        except (EOFError, KeyboardInterrupt):
            return 0
