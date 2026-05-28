# Author: RKOJ-ELENO :: 2026-05-25
"""Sinister Memory :: CLI.

Four subcommands:
  recall <topic>                          -- BM25 search
  save   <key> <summary> --agent <slug>   -- iter-close memory
  index  --layer all                      -- rebuild / refresh index
  inject-spawn-phrase <agent-slug>        -- emit markdown chunk for PS1

Usage (development, no install):
  python -m sinister_memory.cli recall "loop relentless" --limit 5
  python projects/sinister-memory/src/sinister_memory/cli.py recall test --limit 1

After `pip install -e .`:
  sinister-memory recall "loop relentless"

Environment:
  SINISTER_SANCTUM_ROOT  -- defaults to D:\\Sinister Sanctum on Windows; CWD on
                            other platforms. Override for tests / alternate
                            workstations.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Optional

# Support direct file invocation (`python path/to/cli.py ...`) by ensuring
# the parent dir is on sys.path AND we run as a package, not a top-level
# module. This rewrites `__package__` so the relative imports below resolve.
if __package__ in (None, ""):  # direct invocation
    _here = Path(__file__).resolve().parent
    _parent = _here.parent  # .../src
    if str(_parent) not in sys.path:
        sys.path.insert(0, str(_parent))
    __package__ = "sinister_memory"  # noqa: A001


def _normalize_path(raw) -> Path:
    """Normalize bash-style drive paths (`/d/Sinister Sanctum`) to Windows
    (`D:\\Sinister Sanctum`).

    Why: passing `--root /d/Sinister Sanctum` from git-bash made argparse store
    Path('/d/Sinister Sanctum') which is a RELATIVE path on Windows. The
    indexer then wrote to `<cwd>\\d\\Sinister Sanctum\\_shared-memory\\...`
    -- a phantom path. Recall from a normal Windows shell found nothing.
    This caused fleet-wide silent memory loss for agents that called the CLI
    via git-bash piping.

    Operator 2026-05-25T~13:18Z (image): *"my agents have memory issues from
    something done like few hours ago ... we need perfect memory and need to
    expand it as much as we can"*.
    """
    if raw is None:
        return None  # type: ignore[return-value]
    s = str(raw).replace("\\", "/")
    if os.name == "nt" and len(s) >= 3 and s[0] == "/" and s[2] == "/" and s[1].isalpha():
        s = f"{s[1].upper()}:/{s[3:]}"
    return Path(s)


def _default_root() -> Path:
    env = os.environ.get("SINISTER_SANCTUM_ROOT")
    if env:
        return _normalize_path(env)
    win_default = Path(r"D:\Sinister Sanctum")
    if win_default.exists():
        return win_default
    return Path.cwd()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sinister-memory",
        description="Sinister Memory :: per-agent + per-project memory engine.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Sanctum root (default: SINISTER_SANCTUM_ROOT env or D:\\Sinister Sanctum)",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=None,
        help="Index DB path (default: <root>/_shared-memory/sinister-memory/index.db)",
    )

    sub = parser.add_subparsers(dest="command", required=False)

    # recall
    p_recall = sub.add_parser("recall", help="BM25 search across indexed memories")
    p_recall.add_argument("topic", help="search query")
    p_recall.add_argument("--limit", type=int, default=5)
    p_recall.add_argument(
        "--layer",
        action="append",
        choices=("brain", "progress", "heartbeat", "per-agent"),
        help="restrict to one or more layers (repeatable)",
    )
    p_recall.add_argument("--agent", help="restrict slug-scoped layers to this agent")
    p_recall.add_argument("--lane", help="R3 (iter-6) :: restrict to a project lane (slug match OR per-agent/<lane>/ path OR brain)")
    p_recall.add_argument("--no-rrf", action="store_true", help="R2 (iter-6) :: disable BM25+cosine RRF merge (BM25-only)")

    # save
    p_save = sub.add_parser("save", help="persist an iter-close memory")
    p_save.add_argument("key", help="iter label (e.g. iter-23 or any token; iter int parsed)")
    p_save.add_argument("summary", help="memory body (one positional arg; quote it)")
    p_save.add_argument("--agent", required=True, help="agent slug owning this memory")
    p_save.add_argument(
        "--reindex",
        action="store_true",
        help="run incremental indexer.build after save",
    )
    p_save.add_argument(
        "--category",
        choices=("correction", "preference", "procedure", "fact", "entity", "inferred"),
        help="v2 frontmatter category (drives per-category decay half-life; iter-3 P4)",
    )
    p_save.add_argument(
        "--confidence",
        type=float,
        help="v2 frontmatter confidence 0.0-1.0 (used by prune_low_confidence)",
    )
    p_save.add_argument(
        "--trust",
        choices=("low", "medium", "high"),
        help="v2 frontmatter trust label",
    )

    # index
    p_index = sub.add_parser("index", help="rebuild / refresh the FTS5 index")
    p_index.add_argument(
        "--layer",
        default="all",
        choices=("all", "brain", "progress", "heartbeat", "per-agent"),
        help="layer scope (currently 'all' is the only useful value; reserved)",
    )

    # inject-spawn-phrase
    p_inj = sub.add_parser(
        "inject-spawn-phrase",
        help="emit markdown chunk of last-N memories for a slug",
    )
    p_inj.add_argument("agent_slug")
    p_inj.add_argument("--limit", type=int, default=5)
    p_inj.add_argument(
        "--include-health",
        action="store_true",
        help="iter-16 :: prepend SINISTER_MEMORY_HEALTH one-liner so spawned agent sees fleet memory status",
    )

    # supersede
    p_sup = sub.add_parser("supersede", help="mark memory NEW as superseding OLD")
    p_sup.add_argument("new_id", help="path / stable id of the replacement memory")
    p_sup.add_argument("old_id", help="path / stable id of the superseded memory")
    p_sup.add_argument("--reason", default="", help="short why")

    # supersede-chain
    p_chain = sub.add_parser("supersede-chain", help="show the supersedes chain touching MEMORY_ID")
    p_chain.add_argument("memory_id")

    # mark-edge (typed graph edge per jcode EdgeKind taxonomy)
    p_edge = sub.add_parser(
        "mark-edge",
        help="generic typed edge: Supersedes/Contradicts/RelatesTo/HasTag/InCluster",
    )
    p_edge.add_argument("src_id")
    p_edge.add_argument("dst_id")
    p_edge.add_argument(
        "--kind",
        required=True,
        choices=("Supersedes", "Contradicts", "RelatesTo", "HasTag", "InCluster"),
    )
    p_edge.add_argument("--weight", type=float, default=None)
    p_edge.add_argument("--reason", default="")

    # cascade-retrieve
    p_casc = sub.add_parser(
        "cascade-retrieve",
        help="BFS through edges graph from MEMORY_ID up to N hops",
    )
    p_casc.add_argument("memory_id")
    p_casc.add_argument("--depth", type=int, default=2)
    p_casc.add_argument(
        "--kind",
        action="append",
        choices=("Supersedes", "Contradicts", "RelatesTo", "HasTag", "InCluster"),
    )

    # decay-recall
    p_dr = sub.add_parser(
        "decay-recall",
        help="BM25 recall re-ranked by time-decay (recent memories boosted)",
    )
    p_dr.add_argument("topic")
    p_dr.add_argument("--limit", type=int, default=5)
    p_dr.add_argument("--half-life-days", type=float, default=None)
    p_dr.add_argument(
        "--category",
        choices=("fact", "preference", "correction", "entity", "procedure", "inferred"),
        help="use per-category half-life (overridden by --half-life-days if both set)",
    )
    p_dr.add_argument("--alpha", type=float, default=0.5)
    p_dr.add_argument(
        "--layer",
        action="append",
        choices=("brain", "progress", "heartbeat", "per-agent"),
    )
    p_dr.add_argument("--agent")
    p_dr.add_argument("--gap-filter", action="store_true", help="enable jcode-style gap filter")

    # cluster-dedupe
    p_cd = sub.add_parser(
        "cluster-dedupe",
        help="run Jaccard dedupe pass over the index; marks dupes as superseded",
    )
    p_cd.add_argument("--threshold", type=float, default=0.85)
    p_cd.add_argument("--limit", type=int, default=5000)
    p_cd.add_argument(
        "--layer",
        action="append",
        choices=("brain", "progress", "heartbeat", "per-agent"),
        help="restrict dedupe to one or more layers (default: progress + per-agent)",
    )
    p_cd.add_argument("--dry-run", action="store_true",
                      help="don't write supersede edges; just report what WOULD be marked")
    # Iter-33 fix: add --apply as no-op alias for UX consistency with prune/consolidate
    # which use --apply (default dry-run). cluster-dedupe defaults to APPLY (a legacy
    # P5 oversight); --apply is accepted as a no-op so callers can chain consistently
    # without needing to remember which subcommand uses which flag.
    p_cd.add_argument("--apply", action="store_true",
                      help="no-op alias for UX consistency with prune/consolidate (cluster-dedupe defaults to apply; use --dry-run to NOT write edges)")

    # verify
    p_v = sub.add_parser("verify", help="grade a memory file against its source via Haiku/heuristic")
    p_v.add_argument("memory_path", help="path to the memory file to grade")
    p_v.add_argument("--source", help="path to the source-of-truth file (optional)")
    p_v.add_argument(
        "--prefer",
        choices=("auto", "online", "heuristic"),
        default="auto",
    )
    p_v.add_argument("--model", default="claude-haiku-4-5-20251001")

    # embed-index (kernel-vector pass over the FTS5 corpus)
    p_ei = sub.add_parser(
        "embed-index",
        help="compute + store embeddings for every indexed memory (kernel-vector pass)",
    )
    p_ei.add_argument("--limit", type=int, default=None, help="cap rows for incremental runs")
    p_ei.add_argument(
        "--backend",
        default="auto",
        choices=("auto", "ruflo", "tfidf", "null"),
    )

    # vector-recall (cosine over embeddings.db)
    p_vr = sub.add_parser(
        "vector-recall",
        help="cosine-similarity recall over the embeddings index",
    )
    p_vr.add_argument("query")
    p_vr.add_argument("--limit", type=int, default=5)
    p_vr.add_argument("--threshold", type=float, default=0.3)
    p_vr.add_argument(
        "--backend",
        default="auto",
        choices=("auto", "ruflo", "tfidf", "null"),
    )

    # prune (low confidence + age)
    p_pr = sub.add_parser(
        "prune",
        help="hard-delete memories with confidence < threshold AND age >= hours",
    )
    p_pr.add_argument("--confidence", type=float, default=0.15)
    p_pr.add_argument("--age-hours", type=float, default=24.0)
    p_pr.add_argument("--apply", action="store_true", help="default is dry-run")

    # consolidate (ambient mode)
    p_co = sub.add_parser(
        "consolidate",
        help="orchestrated ambient consolidation pass (index + dedupe + prune + optional embed/verify)",
    )
    p_co.add_argument("--apply", action="store_true", help="default is dry-run")
    p_co.add_argument("--with-embeddings", action="store_true")
    p_co.add_argument("--with-verify", action="store_true")

    # export-graph (for Sinister Mind D3 viz)
    p_eg = sub.add_parser(
        "export-graph",
        help="export the memory node + edge graph as JSON (Sinister Mind compatible)",
    )
    p_eg.add_argument("--out", required=True, help="output JSON path")
    p_eg.add_argument(
        "--layer",
        action="append",
        choices=("brain", "progress", "heartbeat", "per-agent"),
    )

    # health (iter-13) :: composite 0-100 memory health score
    p_he = sub.add_parser(
        "health",
        help="composite memory health score (0-100 + 7 sub-scores + letter grade)",
    )
    p_he.add_argument("--json", action="store_true")

    # doctor (iter-15) :: pick ONE concrete remediation + emit the fix command
    p_dr = sub.add_parser(
        "doctor",
        help="diagnose worst sub-score + emit the exact shell command to fix it",
    )
    p_dr.add_argument("--json", action="store_true")

    # verify-brain-refs (iter-64) :: scan files/dirs for `_shared-memory/knowledge/<name>.md`
    # references and report which resolve to real files. Generalizes the
    # iter-63 doctor.py lint pattern. Lane-internal but adoptable fleet-wide.
    p_vb = sub.add_parser(
        "verify-brain-refs",
        help="scan targets for `_shared-memory/knowledge/*.md` references; report broken/present",
    )
    p_vb.add_argument(
        "paths",
        nargs="+",
        help="files or directories to scan (recursive on dirs)",
    )
    p_vb.add_argument("--json", action="store_true")
    p_vb.add_argument(
        "--knowledge-dir",
        type=Path,
        default=None,
        help="override knowledge dir (default: <root>/_shared-memory/knowledge)",
    )

    # commit-isolated (iter-35) :: race-safe plumbing-based commit for shared monorepo
    p_ci = sub.add_parser(
        "commit-isolated",
        help="race-safe git commit via isolated GIT_INDEX_FILE plumbing (codifies cross-agent-monorepo-branch-collision-recovery doctrine)",
    )
    p_ci.add_argument("--parent", required=True, help="parent commit SHA")
    p_ci.add_argument("--branch", required=True, help="target branch name (e.g. agent/<lane>/<topic>-<utc>)")
    p_ci.add_argument("--message-file", required=True, help="path to commit message file")
    p_ci.add_argument("--files", nargs="+", required=True, help="repo-relative paths to stage")
    p_ci.add_argument("--repo-root", default=None, help="repo root (default: --root)")
    p_ci.add_argument("--push", action="store_true", help="push to remote after commit")
    p_ci.add_argument("--remote", default="origin")
    p_ci.add_argument("--json", action="store_true")

    # wait-for-heartbeat (iter-28) :: poll target slug's heartbeat appearance + freshness
    p_wh = sub.add_parser(
        "wait-for-heartbeat",
        help="poll for an agent's heartbeat appearance (chain after spawn to verify init)",
    )
    p_wh.add_argument("slug", help="target agent slug")
    p_wh.add_argument("--timeout", type=float, default=30.0, help="max wait seconds (default 30)")
    p_wh.add_argument("--poll", type=float, default=2.0, help="poll interval seconds (default 2)")
    p_wh.add_argument("--freshness", type=float, default=120.0, help="max acceptable mtime age in seconds (default 120)")
    p_wh.add_argument("--from-heartbeat", action="store_true",
                      help="iter-40: read expected_interval_s from heartbeat JSON and use grace_multiplier*interval as freshness window (overrides --freshness if both set)")
    p_wh.add_argument("--grace-multiplier", type=float, default=3.0,
                      help="iter-42: multiplier applied to expected_interval_s when --from-heartbeat (default 3.0 = allow up to 3 missed heartbeats)")
    p_wh.add_argument("--json", action="store_true")

    # sweep-adoption (iter-47) :: write newest PROGRESS heading per lane to
    # _shared-memory/sinister-memory/per-agent/<key>/ to close health.adoption gap
    p_sa = sub.add_parser(
        "sweep-adoption",
        help="walk every lane's PROGRESS file; save newest heading to per-agent dir with v2 frontmatter (closes adoption gap)",
    )
    p_sa.add_argument("--dry-run", action="store_true", help="scan + plan but write nothing")
    p_sa.add_argument("--max-per-lane", type=int, default=1, help="how many headings per lane (default 1 = newest only)")
    p_sa.add_argument("--json", action="store_true", help="emit JSON stats instead of human summary")

    # sweep-heartbeats (iter-56) :: heartbeat-fallback for lanes lacking PROGRESS
    p_sh = sub.add_parser(
        "sweep-heartbeats",
        help="for lanes with no PROGRESS file, derive a per-agent row from heartbeats/<slug>.json (composes after sweep-adoption)",
    )
    p_sh.add_argument("--dry-run", action="store_true", help="scan + plan but write nothing")
    p_sh.add_argument("--json", action="store_true", help="emit JSON stats instead of human summary")

    # version
    sub.add_parser("version", help="print version + exit")

    return parser


def _resolve_root_and_db(args: argparse.Namespace) -> tuple[Path, Path]:
    root = _normalize_path(args.root) if args.root else _default_root()
    # Local import keeps `--help` cheap when sqlite is locked
    from . import indexer

    db = _normalize_path(args.db) if args.db else indexer.default_db_path(root)
    return root, db


def cmd_recall(args: argparse.Namespace) -> int:
    root, db = _resolve_root_and_db(args)
    from .recall import format_hits_markdown, recall

    hits = recall(
        query=args.topic,
        db_path=db,
        limit=args.limit,
        layers=args.layer,
        agent=args.agent,
        lane=getattr(args, "lane", None),
        rrf=not getattr(args, "no_rrf", False),
    )
    print(format_hits_markdown(hits))
    return 0


def cmd_save(args: argparse.Namespace) -> int:
    root, _db = _resolve_root_and_db(args)
    from .auto_save import save_iter_close

    # Parse iter number from key (accepts "iter-23", "23", or any token w/ trailing int)
    iter_num = 0
    digits = "".join(c if c.isdigit() else " " for c in args.key).split()
    if digits:
        iter_num = int(digits[-1])

    out = save_iter_close(
        slug=args.agent,
        iter_num=iter_num,
        summary=args.summary,
        root=root,
        do_reindex=args.reindex,
        category=getattr(args, "category", None),
        confidence=getattr(args, "confidence", None),
        trust=getattr(args, "trust", None),
    )
    print(f"saved: {out}")
    return 0


def cmd_index(args: argparse.Namespace) -> int:
    root, db = _resolve_root_and_db(args)
    from . import indexer

    stats = indexer.build(root, db)
    print(f"indexed={stats['indexed']} skipped={stats['skipped']} removed={stats['removed']}")
    print(f"db: {db}")
    return 0


def cmd_inject_spawn(args: argparse.Namespace) -> int:
    root, _db = _resolve_root_and_db(args)
    from .spawn_inject import inject_for_spawn

    chunk = inject_for_spawn(
        args.agent_slug, root,
        limit=args.limit,
        include_health=getattr(args, "include_health", False),
    )
    print(chunk)
    return 0


def cmd_version(_args: argparse.Namespace) -> int:
    from . import __author__, __version__

    print(f"sinister-memory {__version__} (author: {__author__})")
    return 0


def cmd_supersede(args: argparse.Namespace) -> int:
    _root, db = _resolve_root_and_db(args)
    from . import supersede

    supersede.mark_supersedes(args.new_id, args.old_id, args.reason, db)
    print(f"marked: {args.new_id} supersedes {args.old_id}")
    return 0


def cmd_supersede_chain(args: argparse.Namespace) -> int:
    _root, db = _resolve_root_and_db(args)
    from . import supersede

    chain = supersede.chain_for(args.memory_id, db)
    if not chain:
        print("(no supersedes edges touching this id)")
        return 0
    for row in chain:
        print(f"{row['ts_utc']} -- {row['new_id']} supersedes {row['old_id']} ({row['reason']})")
    return 0


def cmd_mark_edge(args: argparse.Namespace) -> int:
    _root, db = _resolve_root_and_db(args)
    from . import supersede

    supersede.mark_edge(
        src_id=args.src_id,
        dst_id=args.dst_id,
        kind=args.kind,
        db_path=db,
        weight=args.weight,
        reason=args.reason,
    )
    print(f"edge: {args.src_id} --{args.kind}--> {args.dst_id}")
    return 0


def cmd_cascade_retrieve(args: argparse.Namespace) -> int:
    _root, db = _resolve_root_and_db(args)
    from . import supersede

    related = supersede.cascade_retrieve(args.memory_id, db, depth=args.depth, kinds=args.kind)
    if not related:
        print("(no related memories within depth)")
        return 0
    for r in related:
        print(r)
    return 0


def cmd_decay_recall(args: argparse.Namespace) -> int:
    _root, db = _resolve_root_and_db(args)
    from .decay import recall_with_decay
    from .recall import format_hits_markdown

    hits = recall_with_decay(
        query=args.topic,
        db_path=db,
        limit=args.limit,
        layers=args.layer,
        agent=args.agent,
        alpha=args.alpha,
        half_life_days=args.half_life_days,
        category=args.category,
        gap_filter=args.gap_filter,
    )
    print(format_hits_markdown(hits))
    return 0


def cmd_cluster_dedupe(args: argparse.Namespace) -> int:
    _root, db = _resolve_root_and_db(args)
    from . import cluster

    stats = cluster.dedupe(
        db_path=db,
        threshold=args.threshold,
        layers=args.layer or ("progress", "per-agent"),
        limit=args.limit,
        dry_run=args.dry_run,
    )
    print(
        f"scanned={stats['scanned']} clusters={stats['clusters']} "
        f"edges_added={stats['edges_added']} dry_run={stats['dry_run']}"
    )
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    from . import verify

    mem_path = Path(args.memory_path)
    try:
        memory_text = mem_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        print(f"sinister-memory: cannot read memory: {exc}", file=sys.stderr)
        return 2

    source_path = Path(args.source) if args.source else None
    v = verify.verify_memory(
        memory_text=memory_text,
        source_path=source_path,
        model=args.model,
        prefer=args.prefer,
    )
    print(f"verdict={v.verdict} model={v.model} cost_usd={v.cost_estimate_usd:.6f}")
    print(f"reason: {v.reason}")
    return 0


def cmd_embed_index(args: argparse.Namespace) -> int:
    root, _ = _resolve_root_and_db(args)
    from . import embed

    db = embed.default_embedding_db(root)
    stats = embed.build_embedding_index(root=root, db_path=db, backend=args.backend, limit=args.limit)
    print(
        f"scanned={stats['scanned']} written={stats['written']} "
        f"skipped={stats['skipped']} errors={stats['errors']} backend={stats['backend']}"
    )
    print(f"db: {db}")
    return 0


def cmd_vector_recall(args: argparse.Namespace) -> int:
    root, _ = _resolve_root_and_db(args)
    from . import embed

    db = embed.default_embedding_db(root)
    hits = embed.recall_by_vector(
        query_text=args.query,
        db_path=db,
        limit=args.limit,
        threshold=args.threshold,
        backend=args.backend,
    )
    if not hits:
        print("_(no vector hits >= threshold)_")
        return 0
    for h in hits:
        print(f"- score={h.score:.3f}  [{h.layer}] {h.path}:{h.line}  -- {h.snippet[:120]}")
    return 0


def cmd_prune(args: argparse.Namespace) -> int:
    root, db = _resolve_root_and_db(args)
    from . import prune

    stats = prune.prune_low_confidence(
        root=root,
        db_path=db,
        confidence_threshold=args.confidence,
        age_hours=args.age_hours,
        dry_run=not args.apply,
    )
    print(
        f"scanned={stats['scanned']} candidates={stats['candidates']} "
        f"pruned_fts={stats['pruned_fts']} pruned_embeddings={stats['pruned_embeddings']} "
        f"pruned_edges={stats['pruned_edges']} dry_run={stats['dry_run']}"
    )
    return 0


def cmd_consolidate(args: argparse.Namespace) -> int:
    root, db = _resolve_root_and_db(args)
    from . import consolidate as _co

    stats = _co.consolidate(
        root=root,
        db_path=db,
        dry_run=not args.apply,
        with_embeddings=args.with_embeddings,
        with_verify=args.with_verify,
    )
    import json as _json
    print(_json.dumps(stats, indent=2, default=str))
    return 0


def cmd_export_graph(args: argparse.Namespace) -> int:
    root, db = _resolve_root_and_db(args)
    from . import export_graph as _eg

    stats = _eg.export_graph(root=root, db_path=db, out_path=Path(args.out), layers=args.layer)
    print(f"nodes={stats['nodes']} edges={stats['edges']} written_to={stats['written_to']}")
    return 0


def cmd_health(args: argparse.Namespace) -> int:
    root, _db = _resolve_root_and_db(args)
    from . import health as _h
    rep = _h.health(root)
    if args.json:
        import json as _json
        print(_json.dumps(rep, indent=2))
        return 0
    grade = _h.health_grade(rep["score"])
    print(f"# Sinister Memory health :: {rep['score']}/100 (grade {grade})  @ {rep['ts_utc']}")
    print(f"  weight  score   sub-score")
    print(f"  ------  ------  --------------------")
    for name, sub in rep["sub_scores"].items():
        print(f"  {sub['weight']:>4}    {sub['score']:>5.1f}  {name}")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    root, _db = _resolve_root_and_db(args)
    from . import doctor as _doc
    rep = _doc.doctor(root)
    if args.json:
        import json as _json
        print(_json.dumps(rep, indent=2))
        return 0
    print(f"# Sinister Memory doctor :: score={rep['score']}/100 (grade {rep['grade']})")
    if rep.get("worst_sub") is None:
        print(f"  {rep['diagnosis']}")
        return 0
    print(f"  worst sub-score: {rep['worst_sub']} ({rep['worst_sub_score']}/100, weight {rep['worst_sub_weight']}, lost {rep['lost_points']} pts)")
    print(f"  diagnosis: {rep['diagnosis']}")
    print(f"  recipe:")
    for line in rep["recipe"].splitlines():
        print(f"    {line}")
    return 0


def cmd_verify_brain_refs(args: argparse.Namespace) -> int:
    root, _db = _resolve_root_and_db(args)
    from . import verify_brain_refs as _vb
    targets = [Path(p) for p in args.paths]
    report = _vb.scan_paths(
        root=root,
        targets=targets,
        knowledge_dir=args.knowledge_dir,
    )
    if args.json:
        import json as _json
        print(_json.dumps(report, indent=2))
    else:
        print(
            f"# verify-brain-refs :: scanned={report['scanned_files']} "
            f"files-with-refs={report['files_with_refs']} "
            f"refs={report['total_refs']} "
            f"present={report['present_count']} "
            f"missing={report['missing_count']}"
        )
        if report["missing"]:
            print("  MISSING (broken brain-refs):")
            for row in report["missing"]:
                print(f"    {row['file']}:{row['line']}  -> {row['ref']}")
        else:
            print("  All brain-refs resolve to verified-present files.")
    return 1 if report["missing_count"] else 0


def cmd_commit_isolated(args: argparse.Namespace) -> int:
    from . import commit_isolated as _ci
    repo_root = Path(args.repo_root) if args.repo_root else _resolve_root_and_db(args)[0]
    msg_path = Path(args.message_file)
    if not msg_path.exists():
        print(f"[FAIL] message file not found: {msg_path}", file=sys.stderr)
        return 2
    message = msg_path.read_text(encoding="utf-8")
    result = _ci.commit_isolated(
        repo_root=repo_root,
        parent_sha=args.parent,
        branch_name=args.branch,
        files=args.files,
        message=message,
        push=args.push,
        remote=args.remote,
    )
    if args.json:
        import json as _json
        print(_json.dumps(result, indent=2))
    else:
        if result["ok"]:
            print(f"[OK] commit-isolated: {result['commit_sha'][:10]} on {result['branch']} ({result['files_count']} files)")
            if "push_result" in result and result["push_result"].get("ok"):
                print(f"     pushed to {result['push_result']['remote']}")
        else:
            print(f"[FAIL] commit-isolated: {result.get('error', '?')}", file=sys.stderr)
    return 0 if result["ok"] else 1


def cmd_wait_for_heartbeat(args: argparse.Namespace) -> int:
    root, _db = _resolve_root_and_db(args)
    from . import heartbeat_wait
    result = heartbeat_wait.wait_for_heartbeat(
        slug=args.slug,
        root=root,
        timeout_s=args.timeout,
        poll_interval_s=args.poll,
        freshness_window_s=args.freshness,
        from_heartbeat=getattr(args, "from_heartbeat", False),
        grace_multiplier=getattr(args, "grace_multiplier", 3.0),
    )
    if args.json:
        import json as _json
        print(_json.dumps(result, indent=2))
    else:
        status = result["status"]
        flag = "OK" if result["ok"] else "FAIL"
        print(f"[{flag}] wait-for-heartbeat {args.slug}: {status} (elapsed {result['elapsed_s']}s)")
        if "age_s" in result:
            print(f"       hb_mtime={result.get('hb_mtime_iso')} age={result['age_s']}s")
    return 0 if result["ok"] else 1


def cmd_sweep_adoption(args: argparse.Namespace) -> int:
    root, _db = _resolve_root_and_db(args)
    from . import adoption_sweep

    stats = adoption_sweep.sweep_progress_to_per_agent(
        root,
        dry_run=getattr(args, "dry_run", False),
        max_per_lane=getattr(args, "max_per_lane", 1),
    )
    if getattr(args, "json", False):
        import json as _json
        print(_json.dumps(stats, indent=2))
        return 0
    mode = "DRY-RUN" if stats["dry_run"] else "APPLIED"
    written = stats.get("written", 0)
    updated = stats.get("updated", 0)
    unchanged = stats.get("unchanged", 0)
    print(
        f"[{mode}] sweep-adoption: processed={stats['processed']} "
        f"written={written} updated={updated} unchanged={unchanged} "
        f"skipped_no_progress={stats['skipped_no_progress']} "
        f"errors={len(stats.get('errors', []))}"
    )
    return 0


def cmd_sweep_heartbeats(args: argparse.Namespace) -> int:
    root, _db = _resolve_root_and_db(args)
    from . import heartbeat_fallback

    stats = heartbeat_fallback.heartbeat_fallback_sweep(
        root,
        dry_run=getattr(args, "dry_run", False),
    )
    if getattr(args, "json", False):
        import json as _json
        print(_json.dumps(stats, indent=2))
        return 0
    mode = "DRY-RUN" if stats["dry_run"] else "APPLIED"
    print(
        f"[{mode}] sweep-heartbeats: processed={stats['processed']} "
        f"written={stats.get('written', 0)} updated={stats.get('updated', 0)} "
        f"unchanged={stats.get('unchanged', 0)} "
        f"skipped_has_progress={stats['skipped_has_progress']} "
        f"skipped_no_heartbeat={stats['skipped_no_heartbeat']} "
        f"errors={len(stats.get('errors', []))}"
    )
    return 0


DISPATCH = {
    "recall": cmd_recall,
    "health": cmd_health,
    "doctor": cmd_doctor,
    "verify-brain-refs": cmd_verify_brain_refs,
    "commit-isolated": cmd_commit_isolated,
    "wait-for-heartbeat": cmd_wait_for_heartbeat,
    "sweep-adoption": cmd_sweep_adoption,
    "sweep-heartbeats": cmd_sweep_heartbeats,
    "save": cmd_save,
    "index": cmd_index,
    "inject-spawn-phrase": cmd_inject_spawn,
    "supersede": cmd_supersede,
    "supersede-chain": cmd_supersede_chain,
    "mark-edge": cmd_mark_edge,
    "cascade-retrieve": cmd_cascade_retrieve,
    "decay-recall": cmd_decay_recall,
    "cluster-dedupe": cmd_cluster_dedupe,
    "verify": cmd_verify,
    "embed-index": cmd_embed_index,
    "vector-recall": cmd_vector_recall,
    "prune": cmd_prune,
    "consolidate": cmd_consolidate,
    "export-graph": cmd_export_graph,
    "version": cmd_version,
}


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 0
    handler = DISPATCH.get(args.command)
    if handler is None:
        parser.print_help()
        return 2
    try:
        return handler(args)
    except KeyboardInterrupt:
        return 130
    except Exception as exc:  # noqa: BLE001 -- CLI top-level guard
        print(f"sinister-memory: error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
