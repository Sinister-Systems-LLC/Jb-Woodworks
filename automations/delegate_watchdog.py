#!/usr/bin/env python3
# Author: RKOJ-ELENO :: 2026-05-26
# AGPL-3.0-or-later
#
# delegate_watchdog.py - Watchdog for [DELEGATE] inbox messages.
#
# Walks _shared-memory/inbox/<slug>/*.json, finds messages with
#   kind == "delegate" and a delegate_id, and:
#     - marks completed (and optionally moves to _acked/) if a
#       _shared-memory/completions/<delegate_id>.json file exists,
#     - else if older than ack_timeout_ms and the target heartbeat is stale
#       (>30 min) or no completion exists, copies the delegate to the next
#       fallback slug's inbox (idempotency-key dedup),
#     - escalates to sinister-sanctum inbox after max_retries.
#
# Owned paths (Wave 1.C, iter-86):
#   automations/delegate_watchdog.py
#   _shared-memory/completions/.gitkeep
#   _shared-memory/delegate-watchdog-state.json
#   _shared-memory/delegate-watchdog.log.jsonl
#
# Stdlib only. ~500 LOC.

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------

# Default to the canonical Sanctum layout. Allow override via env for tests.
SANCTUM_ROOT = Path(
    os.environ.get("SINISTER_SANCTUM_ROOT", r"D:\Sinister Sanctum")
).resolve()
SHARED_MEM = SANCTUM_ROOT / "_shared-memory"
INBOX_ROOT = SHARED_MEM / "inbox"
COMPLETIONS_DIR = SHARED_MEM / "completions"
HEARTBEATS_DIR = SHARED_MEM / "heartbeats"
STATE_FILE = SHARED_MEM / "delegate-watchdog-state.json"
LOG_FILE = SHARED_MEM / "delegate-watchdog.log.jsonl"

MASTER_INBOX_SLUG = "sinister-sanctum"
HEARTBEAT_STALE_MS = 30 * 60 * 1000  # 30 min
ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")
SAFE_SLUG_RE = re.compile(r"^[A-Za-z0-9._-]+$")
MAX_SEEN_IDS = 50

# --------------------------------------------------------------------------
# Utilities
# --------------------------------------------------------------------------


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def now_iso() -> str:
    return now_utc().strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso(s: str) -> datetime | None:
    """Parse a flexible ISO-8601 UTC timestamp. Returns None on failure."""
    if not isinstance(s, str):
        return None
    s = s.strip()
    if not s:
        return None
    # normalize trailing Z -> +00:00 so fromisoformat accepts it
    try:
        if s.endswith("Z"):
            s2 = s[:-1] + "+00:00"
        else:
            s2 = s
        dt = datetime.fromisoformat(s2)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        pass
    # Some inboxes use e.g. 2026-05-22T2255Z (no colons/seconds). Best effort.
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})T(\d{2})(\d{2})Z?$", s)
    if m:
        try:
            return datetime(
                int(m[1]), int(m[2]), int(m[3]),
                int(m[4]), int(m[5]), 0,
                tzinfo=timezone.utc,
            )
        except Exception:
            return None
    return None


def is_safe_slug(slug: str) -> bool:
    return bool(slug) and bool(SAFE_SLUG_RE.match(slug)) and ".." not in slug


def atomic_write_json(path: Path, payload: Any) -> None:
    """Write JSON via .tmp + os.replace for atomicity (works on Windows)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    data = json.dumps(payload, indent=2, ensure_ascii=False)
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(data)
    os.replace(tmp, path)


def append_log(row: dict[str, Any]) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(row, ensure_ascii=False)
    try:
        with open(LOG_FILE, "a", encoding="utf-8", newline="\n") as f:
            f.write(line + "\n")
    except Exception as e:
        print(f"[delegate_watchdog] WARN: could not append log: {e}", file=sys.stderr)


def load_state() -> dict[str, Any]:
    if not STATE_FILE.exists():
        return {
            "schema": "sinister.delegate-watchdog.state.v1",
            "last_tick_utc": None,
            "total_acked": 0,
            "total_retried": 0,
            "total_escalated": 0,
            "last_seen_delegate_ids": [],
        }
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(
            f"[delegate_watchdog] WARN: state file unreadable ({e}); resetting",
            file=sys.stderr,
        )
        return {
            "schema": "sinister.delegate-watchdog.state.v1",
            "last_tick_utc": None,
            "total_acked": 0,
            "total_retried": 0,
            "total_escalated": 0,
            "last_seen_delegate_ids": [],
        }


def save_state(state: dict[str, Any]) -> None:
    atomic_write_json(STATE_FILE, state)


def remember_seen(state: dict[str, Any], delegate_id: str) -> None:
    lst = state.setdefault("last_seen_delegate_ids", [])
    if delegate_id in lst:
        # move to front
        lst.remove(delegate_id)
    lst.insert(0, delegate_id)
    del lst[MAX_SEEN_IDS:]


# --------------------------------------------------------------------------
# Heartbeat freshness
# --------------------------------------------------------------------------


def heartbeat_age_ms(slug: str) -> int | None:
    """Return age (ms) of slug's heartbeat file (json or .beat), else None."""
    if not is_safe_slug(slug):
        return None
    candidates = [
        HEARTBEATS_DIR / f"{slug}.json",
        HEARTBEATS_DIR / f"{slug}.beat",
    ]
    for p in candidates:
        try:
            if p.exists():
                mtime = p.stat().st_mtime
                age = int((time.time() - mtime) * 1000)
                return age
        except Exception:
            continue
    return None


def heartbeat_is_stale(slug: str) -> bool:
    """True if heartbeat is older than HEARTBEAT_STALE_MS OR missing."""
    age = heartbeat_age_ms(slug)
    if age is None:
        return True
    return age > HEARTBEAT_STALE_MS


# --------------------------------------------------------------------------
# Inbox walking
# --------------------------------------------------------------------------


def iter_inbox_slugs() -> list[Path]:
    if not INBOX_ROOT.exists():
        return []
    out = []
    try:
        for child in INBOX_ROOT.iterdir():
            if child.is_dir() and is_safe_slug(child.name):
                out.append(child)
    except Exception as e:
        print(f"[delegate_watchdog] WARN: cannot iter inbox root: {e}", file=sys.stderr)
    return out


def load_inbox_message(path: Path) -> dict[str, Any] | None:
    """Read JSON; return None on any failure (logged to stderr)."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            obj = json.load(f)
        if not isinstance(obj, dict):
            return None
        return obj
    except json.JSONDecodeError as e:
        print(
            f"[delegate_watchdog] skip corrupt JSON: {path} ({e})", file=sys.stderr
        )
        return None
    except Exception as e:
        print(
            f"[delegate_watchdog] skip unreadable inbox msg {path}: {e}",
            file=sys.stderr,
        )
        return None


def find_idempotent_dup(target_inbox: Path, idempotency_key: str) -> Path | None:
    """Return the first existing message in target_inbox with the same key."""
    if not idempotency_key or not target_inbox.exists():
        return None
    try:
        for entry in target_inbox.iterdir():
            if not entry.is_file() or entry.suffix.lower() != ".json":
                continue
            msg = load_inbox_message(entry)
            if not msg:
                continue
            if msg.get("idempotency_key") == idempotency_key:
                return entry
    except Exception:
        pass
    return None


# --------------------------------------------------------------------------
# Core algorithm
# --------------------------------------------------------------------------


class Tick:
    def __init__(self, dry_run: bool = False, verbose: bool = False) -> None:
        self.dry_run = dry_run
        self.verbose = verbose
        self.state = load_state()
        self.completed_count = 0
        self.retried_count = 0
        self.escalated_count = 0
        self.idempotent_skipped = 0
        self.scanned_count = 0
        self.delegate_count = 0

    # ---- write helpers (no-op when dry-run) -----------------------------

    def _emit_log(self, row: dict[str, Any]) -> None:
        if self.verbose:
            print(f"[delegate_watchdog] {row.get('event')}: {row}", file=sys.stderr)
        if self.dry_run:
            return
        append_log(row)

    def _write_inbox_copy(
        self, target_slug: str, msg: dict[str, Any], origin_path: Path
    ) -> Path | None:
        if not is_safe_slug(target_slug):
            print(
                f"[delegate_watchdog] WARN: unsafe slug refused: {target_slug!r}",
                file=sys.stderr,
            )
            return None
        target_dir = INBOX_ROOT / target_slug
        ts = now_utc().strftime("%Y%m%dT%H%M%SZ")
        did = msg.get("delegate_id", "unknown")
        # safe filename component for delegate_id
        did_safe = re.sub(r"[^A-Za-z0-9._-]", "_", str(did))[:80]
        fname = f"{ts}-delegate-retry-{did_safe}.json"
        dest = target_dir / fname
        if self.dry_run:
            return dest
        target_dir.mkdir(parents=True, exist_ok=True)
        # Embed retry provenance
        copy = dict(msg)
        copy["_watchdog_retry"] = {
            "from_origin": str(origin_path.relative_to(SANCTUM_ROOT)),
            "rewritten_at_utc": now_iso(),
            "rewritten_to_slug": target_slug,
        }
        atomic_write_json(dest, copy)
        return dest

    def _persist_attempts(self, path: Path, msg: dict[str, Any]) -> None:
        if self.dry_run:
            return
        try:
            atomic_write_json(path, msg)
        except Exception as e:
            print(
                f"[delegate_watchdog] WARN: could not persist attempts to {path}: {e}",
                file=sys.stderr,
            )

    def _maybe_move_to_acked(self, inbox_slug_dir: Path, path: Path) -> None:
        """Only move to _acked/ if that subdir already exists (per spec)."""
        acked_dir = inbox_slug_dir / "_acked"
        if not acked_dir.exists() or not acked_dir.is_dir():
            return
        if self.dry_run:
            return
        try:
            shutil.move(str(path), str(acked_dir / path.name))
        except Exception as e:
            print(
                f"[delegate_watchdog] WARN: could not move {path} -> _acked/: {e}",
                file=sys.stderr,
            )

    # ---- per-message processing ----------------------------------------

    def process_message(
        self, inbox_slug_dir: Path, path: Path, msg: dict[str, Any]
    ) -> None:
        self.scanned_count += 1
        if msg.get("kind") != "delegate":
            return
        delegate_id = msg.get("delegate_id")
        if not delegate_id or not isinstance(delegate_id, str):
            # forward-compatible: pre-schema delegates without delegate_id
            return
        self.delegate_count += 1
        remember_seen(self.state, delegate_id)

        # 1. Completion check
        comp_path = COMPLETIONS_DIR / f"{delegate_id}.json"
        if comp_path.exists():
            self.completed_count += 1
            self._emit_log(
                {
                    "ts_utc": now_iso(),
                    "event": "acked",
                    "delegate_id": delegate_id,
                    "inbox_slug": inbox_slug_dir.name,
                    "completion_path": str(
                        comp_path.relative_to(SANCTUM_ROOT)
                    ),
                }
            )
            self._maybe_move_to_acked(inbox_slug_dir, path)
            return

        # 2. Timeout / retry path
        created_at = parse_iso(str(msg.get("created_at_utc", "")))
        if created_at is None:
            # Without a parseable created_at_utc we can't compute age — skip
            return
        ack_timeout_ms = msg.get("ack_timeout_ms")
        if not isinstance(ack_timeout_ms, (int, float)) or ack_timeout_ms <= 0:
            return
        age_ms = int((now_utc() - created_at).total_seconds() * 1000)
        if age_ms <= ack_timeout_ms:
            return  # still within the ack window

        attempts = int(msg.get("attempts", 0))
        max_retries = int(msg.get("max_retries", 0))
        fallback_slugs = msg.get("fallback_slugs") or []
        if not isinstance(fallback_slugs, list):
            fallback_slugs = []

        target_slug = str(msg.get("to") or "").strip()

        # Only retry while the original target is stale or completion missing.
        # (Spec says: if target heartbeat is stale OR completion absent.
        # Completion absence is implied by reaching this branch.)
        target_stale = (
            heartbeat_is_stale(target_slug) if is_safe_slug(target_slug) else True
        )

        if attempts < max_retries:
            # Need at least one more fallback slot to retry
            fb_idx = attempts  # 0-indexed pick of fallback_slugs
            if fb_idx >= len(fallback_slugs):
                # No more fallbacks even though attempts < max_retries — escalate
                self._escalate(path, msg, delegate_id, reason="no-more-fallbacks")
                return
            fallback_slug = str(fallback_slugs[fb_idx]).strip()
            if not is_safe_slug(fallback_slug):
                self._emit_log(
                    {
                        "ts_utc": now_iso(),
                        "event": "skip-unsafe-fallback-slug",
                        "delegate_id": delegate_id,
                        "fallback_slug": fallback_slug,
                    }
                )
                return

            # Per spec: condition for retry is stale heartbeat OR completion absent.
            # We've already established completion is absent. If the heartbeat
            # is fresh but ack still missing past timeout, we still retry per
            # spec wording ("If stale (>30 min) OR completion absent").
            del target_stale  # documented; semantically completion-absent is sufficient

            # Idempotency check on destination inbox
            idem = str(msg.get("idempotency_key") or "").strip()
            target_inbox = INBOX_ROOT / fallback_slug
            if idem:
                dup = find_idempotent_dup(target_inbox, idem)
                if dup is not None:
                    self.idempotent_skipped += 1
                    self._emit_log(
                        {
                            "ts_utc": now_iso(),
                            "event": "idempotent-skip",
                            "delegate_id": delegate_id,
                            "idempotency_key": idem,
                            "fallback_slug": fallback_slug,
                            "dup_path": str(dup.relative_to(SANCTUM_ROOT)),
                        }
                    )
                    return

            # Increment + persist attempts on the original message
            new_attempts = attempts + 1
            msg["attempts"] = new_attempts
            self._persist_attempts(path, msg)

            # Drop a copy into the fallback inbox
            dest = self._write_inbox_copy(fallback_slug, msg, path)
            self.retried_count += 1
            self._emit_log(
                {
                    "ts_utc": now_iso(),
                    "event": "retry",
                    "delegate_id": delegate_id,
                    "original_target": target_slug,
                    "new_target": fallback_slug,
                    "attempt": new_attempts,
                    "max_retries": max_retries,
                    "reason": "ack-timeout-exceeded",
                    "destination_path": (
                        str(dest.relative_to(SANCTUM_ROOT)) if dest else None
                    ),
                    "dry_run": self.dry_run,
                }
            )
        else:
            # attempts >= max_retries -> escalate (once per tick at most)
            self._escalate(path, msg, delegate_id, reason="max-retries-exceeded")

    def _escalate(
        self,
        origin_path: Path,
        msg: dict[str, Any],
        delegate_id: str,
        reason: str,
    ) -> None:
        # Avoid spamming: only escalate if no prior escalation marker file exists.
        marker_dir = INBOX_ROOT / MASTER_INBOX_SLUG
        already = False
        if marker_dir.exists():
            # Match by delegate_id in filename
            did_safe = re.sub(r"[^A-Za-z0-9._-]", "_", delegate_id)[:80]
            try:
                for entry in marker_dir.iterdir():
                    if (
                        entry.is_file()
                        and entry.suffix.lower() == ".json"
                        and did_safe in entry.name
                        and "escalation" in entry.name.lower()
                    ):
                        already = True
                        break
            except Exception:
                pass
        if already:
            self._emit_log(
                {
                    "ts_utc": now_iso(),
                    "event": "escalation-already-pending",
                    "delegate_id": delegate_id,
                }
            )
            return

        escalation = {
            "kind": "delegate-escalation",
            "subject": "[ESCALATION] delegate-failed",
            "from": "delegate-watchdog",
            "to": MASTER_INBOX_SLUG,
            "delegate_id": delegate_id,
            "original_message_path": str(origin_path.relative_to(SANCTUM_ROOT)),
            "reason": reason,
            "attempts": int(msg.get("attempts", 0)),
            "max_retries": int(msg.get("max_retries", 0)),
            "fallback_slugs": msg.get("fallback_slugs") or [],
            "original_target": msg.get("to"),
            "created_at_utc": msg.get("created_at_utc"),
            "escalated_at_utc": now_iso(),
            "original_subject": msg.get("subject"),
            "idempotency_key": msg.get("idempotency_key"),
        }
        if self.dry_run:
            dest = (
                marker_dir
                / f"{now_utc().strftime('%Y%m%dT%H%M%SZ')}-escalation-{re.sub(r'[^A-Za-z0-9._-]', '_', delegate_id)[:80]}.json"
            )
        else:
            marker_dir.mkdir(parents=True, exist_ok=True)
            ts = now_utc().strftime("%Y%m%dT%H%M%SZ")
            did_safe = re.sub(r"[^A-Za-z0-9._-]", "_", delegate_id)[:80]
            dest = marker_dir / f"{ts}-escalation-{did_safe}.json"
            atomic_write_json(dest, escalation)
        self.escalated_count += 1
        self._emit_log(
            {
                "ts_utc": now_iso(),
                "event": "escalated",
                "delegate_id": delegate_id,
                "destination_path": str(dest.relative_to(SANCTUM_ROOT)),
                "reason": reason,
                "dry_run": self.dry_run,
            }
        )

    # ---- entry point ----------------------------------------------------

    def run(self) -> None:
        # Auto-create completions dir + gitkeep (idempotent, only when not dry-run)
        if not self.dry_run:
            try:
                COMPLETIONS_DIR.mkdir(parents=True, exist_ok=True)
                gitkeep = COMPLETIONS_DIR / ".gitkeep"
                if not gitkeep.exists():
                    gitkeep.write_text("", encoding="utf-8")
            except Exception as e:
                print(
                    f"[delegate_watchdog] WARN: could not create completions dir: {e}",
                    file=sys.stderr,
                )

        for slug_dir in iter_inbox_slugs():
            try:
                entries = list(slug_dir.iterdir())
            except Exception as e:
                print(
                    f"[delegate_watchdog] WARN: cannot list {slug_dir}: {e}",
                    file=sys.stderr,
                )
                continue
            for entry in entries:
                if not entry.is_file():
                    continue
                if entry.suffix.lower() != ".json":
                    continue
                msg = load_inbox_message(entry)
                if not msg:
                    continue
                try:
                    self.process_message(slug_dir, entry, msg)
                except Exception as e:
                    # Never raise on a single bad msg
                    print(
                        f"[delegate_watchdog] ERROR processing {entry}: {e}",
                        file=sys.stderr,
                    )
                    continue

        # Update state
        self.state["last_tick_utc"] = now_iso()
        self.state["total_acked"] = int(self.state.get("total_acked", 0)) + self.completed_count
        self.state["total_retried"] = int(self.state.get("total_retried", 0)) + self.retried_count
        self.state["total_escalated"] = (
            int(self.state.get("total_escalated", 0)) + self.escalated_count
        )
        if not self.dry_run:
            try:
                save_state(self.state)
            except Exception as e:
                print(
                    f"[delegate_watchdog] WARN: could not save state: {e}",
                    file=sys.stderr,
                )

        # Tick summary
        print(
            json.dumps(
                {
                    "ts_utc": self.state["last_tick_utc"],
                    "event": "tick-summary",
                    "scanned_messages": self.scanned_count,
                    "delegate_messages": self.delegate_count,
                    "acked_this_tick": self.completed_count,
                    "retried_this_tick": self.retried_count,
                    "escalated_this_tick": self.escalated_count,
                    "idempotent_skipped_this_tick": self.idempotent_skipped,
                    "dry_run": self.dry_run,
                }
            )
        )


# --------------------------------------------------------------------------
# Manual completion (CLI flag)
# --------------------------------------------------------------------------


def manual_complete(
    delegate_id: str, by_slug: str, summary: str, dry_run: bool = False
) -> int:
    if not delegate_id:
        print("--complete requires a non-empty delegate_id", file=sys.stderr)
        return 2
    if not is_safe_slug(by_slug):
        print(f"--by slug invalid: {by_slug!r}", file=sys.stderr)
        return 2
    payload = {
        "delegate_id": delegate_id,
        "idempotency_key": None,
        "completed_by": by_slug,
        "completed_at_utc": now_iso(),
        "status": "completed",
        "result_summary": summary,
        "_origin": "delegate_watchdog --complete (manual)",
    }
    did_safe = re.sub(r"[^A-Za-z0-9._-]", "_", delegate_id)[:120]
    dest = COMPLETIONS_DIR / f"{did_safe}.json"
    if dest.exists():
        print(
            f"completion already exists at {dest.relative_to(SANCTUM_ROOT)} — refusing to overwrite",
            file=sys.stderr,
        )
        return 1
    if dry_run:
        print(
            json.dumps(
                {"would_write": str(dest.relative_to(SANCTUM_ROOT)), "payload": payload},
                indent=2,
            )
        )
        return 0
    COMPLETIONS_DIR.mkdir(parents=True, exist_ok=True)
    atomic_write_json(dest, payload)
    append_log(
        {
            "ts_utc": now_iso(),
            "event": "manual-complete",
            "delegate_id": delegate_id,
            "completed_by": by_slug,
            "completion_path": str(dest.relative_to(SANCTUM_ROOT)),
        }
    )
    print(
        json.dumps(
            {
                "ok": True,
                "completion_path": str(dest.relative_to(SANCTUM_ROOT)),
                "delegate_id": delegate_id,
            },
            indent=2,
        )
    )
    return 0


def print_status() -> int:
    state = load_state()
    # Augment with live counts
    completions_count = 0
    try:
        if COMPLETIONS_DIR.exists():
            completions_count = sum(
                1
                for p in COMPLETIONS_DIR.iterdir()
                if p.is_file() and p.suffix == ".json"
            )
    except Exception:
        pass
    out = dict(state)
    out["completions_on_disk"] = completions_count
    out["state_file"] = str(STATE_FILE.relative_to(SANCTUM_ROOT))
    out["log_file"] = str(LOG_FILE.relative_to(SANCTUM_ROOT))
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


# --------------------------------------------------------------------------
# argparse
# --------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="delegate_watchdog.py",
        description=(
            "Watchdog for [DELEGATE] inbox messages: ACK detection via "
            "_shared-memory/completions/<delegate_id>.json, retry on ack_timeout "
            "via fallback_slugs, escalation to sinister-sanctum inbox after "
            "max_retries. Idempotency-key dedup on fallback writes."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Walk inboxes and log decisions to stdout; do not write any files.",
    )
    p.add_argument(
        "--loop",
        action="store_true",
        help="Long-running mode: tick every --interval-seconds (default 60).",
    )
    p.add_argument(
        "--interval-seconds",
        type=int,
        default=60,
        help="Tick interval in --loop mode (default 60).",
    )
    p.add_argument(
        "--status",
        action="store_true",
        help="Print current watchdog state as JSON and exit.",
    )
    p.add_argument(
        "--verbose",
        action="store_true",
        help="Echo per-event log rows to stderr.",
    )
    # Manual completion
    p.add_argument(
        "--complete",
        metavar="DELEGATE_ID",
        help="Manually write a completion file for a delegate_id and exit.",
    )
    p.add_argument(
        "--by",
        metavar="SLUG",
        help="Slug to record as completed_by when using --complete.",
    )
    p.add_argument(
        "--summary",
        metavar="TEXT",
        default="",
        help="result_summary text when using --complete.",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    # Validate sanctum root early
    if not SHARED_MEM.exists():
        print(
            f"[delegate_watchdog] FATAL: _shared-memory not found under {SANCTUM_ROOT}. "
            "Set SINISTER_SANCTUM_ROOT env var if launched from a non-default cwd.",
            file=sys.stderr,
        )
        return 2

    if args.status:
        return print_status()

    if args.complete:
        if not args.by:
            print("--complete requires --by <slug>", file=sys.stderr)
            return 2
        return manual_complete(
            delegate_id=args.complete,
            by_slug=args.by,
            summary=args.summary or "",
            dry_run=args.dry_run,
        )

    if args.loop:
        interval = max(5, int(args.interval_seconds))
        print(
            f"[delegate_watchdog] loop mode, interval={interval}s, dry_run={args.dry_run}",
            file=sys.stderr,
        )
        try:
            while True:
                Tick(dry_run=args.dry_run, verbose=args.verbose).run()
                time.sleep(interval)
        except KeyboardInterrupt:
            print("[delegate_watchdog] interrupted; exiting", file=sys.stderr)
            return 0

    Tick(dry_run=args.dry_run, verbose=args.verbose).run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
