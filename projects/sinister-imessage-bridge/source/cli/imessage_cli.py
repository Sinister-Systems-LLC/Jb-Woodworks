"""Operator CLI: list threads, show a thread, send (with --dry-run).

RKOJ-ELENO :: 2026-05-24

Usage:
  imessage threads --chatdb fixtures/canned-chat.db
  imessage show 1 --chatdb fixtures/canned-chat.db --limit 5
  imessage send --to "+15551112222" --body "ping" --dry-run
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import click

from recv_worker.poll import fetch_threads, poll_new, schema_fingerprint, verify_baseline_schema
from send_worker.send import send as send_msg


def _fmt_ts(unix_s: float) -> str:
    if not unix_s:
        return "-"
    return datetime.fromtimestamp(unix_s, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")


@click.group(help="Sinister iMessage Bridge operator CLI.")
def main() -> None:
    pass


@main.command(help="List all threads in the chat.db.")
@click.option("--chatdb", "chatdb_path", required=True, type=click.Path(exists=True, path_type=Path))
@click.option("--json", "as_json", is_flag=True, help="Emit JSON instead of table.")
def threads(chatdb_path: Path, as_json: bool) -> None:
    rows = fetch_threads(chatdb_path, limit_per_thread=1)
    if as_json:
        click.echo(json.dumps(rows, indent=2))
        return
    click.echo(f"{'chat_id':>8}  {'last_read_utc':<20}  {'service':<10}  {'identifier'}")
    click.echo("-" * 72)
    for t in rows:
        click.echo(
            f"{t['chat_id']:>8}  {_fmt_ts(t['last_read_unix']):<20}  "
            f"{(t['service'] or '-'):<10}  {t['chat_identifier']}"
        )
    click.echo(f"\n{len(rows)} thread(s).")


@main.command(help="Show recent messages in one thread.")
@click.argument("chat_id", type=int)
@click.option("--chatdb", "chatdb_path", required=True, type=click.Path(exists=True, path_type=Path))
@click.option("--limit", default=20, type=int)
def show(chat_id: int, chatdb_path: Path, limit: int) -> None:
    all_threads = fetch_threads(chatdb_path, limit_per_thread=limit)
    match = next((t for t in all_threads if t["chat_id"] == chat_id), None)
    if not match:
        click.echo(f"no such chat_id {chat_id}", err=True)
        sys.exit(1)
    click.echo(f"# chat {chat_id} :: {match['chat_identifier']} ({match['service']})")
    for m in reversed(match["messages"]):
        arrow = "→" if m["is_from_me"] else "←"
        click.echo(f"  [{_fmt_ts(m['sent_unix'])}] {arrow} {m['body']!r}")


@main.command(help="Send a message (use --dry-run to test without sending).")
@click.option("--service", default="iMessage", type=click.Choice(["iMessage", "SMS"]))
@click.option("--to", "recipient", required=True)
@click.option("--body", required=True)
@click.option("--operator-ok", is_flag=True, help="Acknowledge per-thread OK (required for live send).")
@click.option("--dry-run", is_flag=True, help="Do not invoke AppleScript; just validate guards.")
@click.option("--ssh", "ssh_target", default=None, help="SSH target (e.g. user@farm-host).")
def send(service: str, recipient: str, body: str, operator_ok: bool, dry_run: bool, ssh_target: str | None) -> None:
    result = send_msg(
        service, recipient, body,
        operator_ok=operator_ok,
        dry_run=dry_run,
        ssh_target=ssh_target,
    )
    click.echo(json.dumps(result, indent=2))
    if result.get("status") not in ("ok", "dry_run"):
        sys.exit(1)


@main.command(help="P1 §4 — schema fingerprint check on the chat.db.")
@click.option("--chatdb", "chatdb_path", required=True, type=click.Path(exists=True, path_type=Path))
def schema(chatdb_path: Path) -> None:
    result = verify_baseline_schema(chatdb_path)
    click.echo(json.dumps(result, indent=2))
    if not result["pass"]:
        sys.exit(2)


@main.command(help="Poll for new messages since ROWID.")
@click.option("--chatdb", "chatdb_path", required=True, type=click.Path(exists=True, path_type=Path))
@click.option("--since", default=0, type=int)
@click.option("--limit", default=50, type=int)
def poll(chatdb_path: Path, since: int, limit: int) -> None:
    rows = poll_new(chatdb_path, since_rowid=since, limit=limit)
    click.echo(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
