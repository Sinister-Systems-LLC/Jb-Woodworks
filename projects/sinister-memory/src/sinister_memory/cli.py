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


def _default_root() -> Path:
    env = os.environ.get("SINISTER_SANCTUM_ROOT")
    if env:
        return Path(env)
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
    p_cd.add_argument("--dry-run", action="store_true")

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

    # version
    sub.add_parser("version", help="print version + exit")

    return parser


def _resolve_root_and_db(args: argparse.Namespace) -> tuple[Path, Path]:
    root = args.root or _default_root()
    # Local import keeps `--help` cheap when sqlite is locked
    from . import indexer

    db = args.db or indexer.default_db_path(root)
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

    chunk = inject_for_spawn(args.agent_slug, root, limit=args.limit)
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


DISPATCH = {
    "recall": cmd_recall,
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
