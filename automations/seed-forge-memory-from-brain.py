"""Seed forge-memory namespace 'brain' from _shared-memory/knowledge/*.md.

Author: RKOJ-ELENO :: 2026-05-25

Swimlane 1 of quantum-fleet-100x-master-plan-2026-05-25. Backfills the
forge-memory disk store with every brain markdown entry so any agent can
do `forge-memory recall '<topic>' --limit 5` and get semantically-best
top-5 brain entries instead of grepping 200 files.

Idempotent: upserts by content_hash; re-runs bump confidence + writes count.

Lane discipline:
  - Writes ONLY to namespace 'brain'. Existing namespaces (sinister-term,
    others) UNTOUCHED.
  - SKIP set excludes README / _INDEX / _TEMPLATE / _archive contents.
  - Dry-run mode prints would-write count without touching the store.

Usage:
    python automations/seed-forge-memory-from-brain.py --dry-run     # preview
    python automations/seed-forge-memory-from-brain.py              # backfill
    python automations/seed-forge-memory-from-brain.py --recall-smoke  # post-backfill smoke
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8')  # type: ignore[attr-defined]
except Exception:
    pass

SANCTUM_ROOT = Path(r'D:\Sinister Sanctum')
BRAIN_DIR = SANCTUM_ROOT / '_shared-memory' / 'knowledge'
SKIP = {'README.md', '_INDEX.md', '_TEMPLATE.md'}
NAMESPACE = 'brain'


def _derive_tags(filename: str) -> list[str]:
    """Tags = filename segments split by '-', dropping date tokens and short
    tokens. Composes with existing forge-memory tag-based recall."""
    stem = filename[:-3] if filename.endswith('.md') else filename
    segments = [s for s in stem.split('-') if len(s) >= 3 and not s.isdigit()]
    # cap at 8 tags so storage doesn't bloat
    return segments[:8]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true', help='Preview without writing')
    ap.add_argument('--recall-smoke', action='store_true',
                    help='After backfill, run 3 sample recalls as verification')
    ap.add_argument('--limit', type=int, default=None,
                    help='Cap total entries written (debug only)')
    args = ap.parse_args()

    try:
        from forge_memory_bridge import write as fm_write, recall as fm_recall, ls as fm_list
    except ImportError as e:
        print(f'ERROR: forge_memory_bridge not importable: {e}')
        print('Hint: pip install -e D:/Sinister Sanctum/tools/forge-memory-bridge')
        return 2

    if not BRAIN_DIR.exists():
        print(f'ERROR: brain dir missing: {BRAIN_DIR}')
        return 2

    files = sorted(p for p in BRAIN_DIR.glob('*.md') if p.name not in SKIP)
    if args.limit:
        files = files[: args.limit]

    print(f'[seed-forge] brain dir: {BRAIN_DIR}')
    print(f'[seed-forge] candidate files: {len(files)} (skipping {", ".join(sorted(SKIP))})')

    pre_existing = []
    try:
        pre_existing = fm_list(namespace=NAMESPACE)
    except TypeError:
        # API variant
        pre_existing = [r for r in fm_list() if r.get('namespace') == NAMESPACE]
    pre_count = len(pre_existing) if pre_existing else 0
    print(f"[seed-forge] forge namespace '{NAMESPACE}' pre-count: {pre_count}")

    if args.dry_run:
        print(f'[seed-forge] DRY-RUN — would write {len(files)} entries to namespace "{NAMESPACE}"')
        print(f'[seed-forge] sample (first 5):')
        for p in files[:5]:
            tags = _derive_tags(p.name)
            size_kb = p.stat().st_size / 1024
            print(f'  key={p.stem!r:60s} tags={tags}  size={size_kb:.1f}KB')
        return 0

    t0 = time.time()
    wrote = 0
    upserts = 0
    failed = 0

    for p in files:
        try:
            content = p.read_text(encoding='utf-8')
        except Exception as e:
            print(f'[seed-forge] READ-FAIL {p.name}: {e}')
            failed += 1
            continue
        tags = _derive_tags(p.name)
        try:
            fm_write(
                namespace=NAMESPACE,
                key=p.stem,
                value=content,
                tags=tags,
            )
            wrote += 1
        except TypeError:
            # Older API form
            try:
                fm_write(NAMESPACE, p.stem, content, tags)
                wrote += 1
            except Exception as e:
                print(f'[seed-forge] WRITE-FAIL {p.name}: {e}')
                failed += 1
        except Exception as e:
            print(f'[seed-forge] WRITE-FAIL {p.name}: {e}')
            failed += 1

    wall = time.time() - t0
    print(f'[seed-forge] DONE  wrote={wrote}  failed={failed}  wall={wall:.2f}s')

    # Post-backfill count
    try:
        post = fm_list(namespace=NAMESPACE)
    except TypeError:
        post = [r for r in fm_list() if r.get('namespace') == NAMESPACE]
    post_count = len(post) if post else 0
    print(f"[seed-forge] forge namespace '{NAMESPACE}' post-count: {post_count}")
    print(f'[seed-forge] delta: +{post_count - pre_count} new entries (rest = upserts)')

    if args.recall_smoke:
        print()
        print('[seed-forge] recall smoke (3 queries):')
        for q in ['quantum doctrine', 'multi-agent git', 'leo setup']:
            try:
                hits = fm_recall(q, limit=5, namespace=NAMESPACE)
            except TypeError:
                hits = fm_recall(q, 5)
            print(f"  query={q!r:30s} -> {len(hits)} hits")
            for h in (hits or [])[:3]:
                k = h.get('key', '?') if isinstance(h, dict) else str(h)[:80]
                print(f'      {k}')

    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
