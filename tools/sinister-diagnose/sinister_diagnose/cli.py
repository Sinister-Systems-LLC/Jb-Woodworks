# Sinister Sanctum :: sinister-diagnose :: click CLI
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
"""
Click-based CLI surface.

Surfaces:
    sinister-diagnose run                     full health check (colored)
    sinister-diagnose run --json              full health check (machine-readable)
    sinister-diagnose <slug>                  run one check (e.g. `python`, `rust`)
    sinister-diagnose list                    enumerate every check slug
    sinister-diagnose --version

The dispatcher umbrella (`sinister diagnose ...`) hits __main__.main(argv).
"""
from __future__ import annotations

import json as _json
import sys
from typing import List

import click

from . import __version__
from .checks import (
    ALL_CHECKS,
    CheckResult,
    now_utc_iso,
    overall_status,
    run_all,
)

# ---- rich, with graceful fallback if not installed -------------------------

try:
    from rich.console import Console
    _RICH_OK = True
except ImportError:  # pragma: no cover - rich is declared required
    Console = None  # type: ignore
    _RICH_OK = False


_STATUS_STYLES = {
    "ok": ("bold green", "[ok]  "),
    "warn": ("bold yellow", "[warn]"),
    "fail": ("bold red", "[fail]"),
    "info": ("bold cyan", "[info]"),
}


def _render_console(results: List[CheckResult], console=None) -> None:
    """Pretty-print results via rich; falls back to ascii when rich is absent."""
    if _RICH_OK and console is None:
        console = Console()

    # Compute name column width for alignment.
    name_w = max((len(r["name"]) for r in results), default=10)
    name_w = max(name_w, 14)

    for r in results:
        style, prefix = _STATUS_STYLES.get(r["status"], ("white", "[?]   "))
        line = f"{prefix} {r['name'].ljust(name_w)}  {r['message']}"
        if _RICH_OK and console is not None:
            console.print(f"[{style}]{prefix}[/] {r['name'].ljust(name_w)}  {r['message']}")
        else:
            print(line)
        if r["status"] in ("warn", "fail") and r.get("fix_hint"):
            indent = " " * (len(prefix) + 1 + name_w + 2)
            hint = f"{indent}fix: {r['fix_hint']}"
            if _RICH_OK and console is not None:
                console.print(f"[dim]{hint}[/]")
            else:
                print(hint)

    summary = overall_status(results)
    style, _ = _STATUS_STYLES.get(summary, ("white", ""))
    counts = {"ok": 0, "warn": 0, "fail": 0, "info": 0}
    for r in results:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    msg = (f"summary: {summary.upper()}  "
           f"({counts['ok']} ok, {counts['warn']} warn, "
           f"{counts['fail']} fail, {counts['info']} info)")
    if _RICH_OK and console is not None:
        console.print()
        console.print(f"[{style}]{msg}[/]")
    else:
        print()
        print(msg)


def _emit_json(results: List[CheckResult]) -> None:
    doc = {
        "tool": "sinister-diagnose",
        "version": __version__,
        "generated_at": now_utc_iso(),
        "overall": overall_status(results),
        "checks": results,
    }
    print(_json.dumps(doc, indent=2))


def _exit_code_for(results: List[CheckResult]) -> int:
    """0 ok, 1 warn, 2 fail. Mirrors npm doctor / brew doctor convention."""
    s = overall_status(results)
    return {"ok": 0, "warn": 1, "fail": 2}.get(s, 2)


# ---- click group -----------------------------------------------------------

@click.group(invoke_without_command=True,
             context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, prog_name="sinister-diagnose")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """Sinister Sanctum :: RKOJ/Sanctum health checker."""
    if ctx.invoked_subcommand is None:
        # `sinister-diagnose` with no subcommand → run full report.
        ctx.invoke(run)


@cli.command()
@click.option("--json", "as_json", is_flag=True, default=False,
              help="Emit a JSON document instead of the colored report.")
@click.option("--strict", is_flag=True, default=False,
              help="Treat warn as failure (exit code 2 on any warn).")
def run(as_json: bool, strict: bool) -> None:
    """Run every check and print a report."""
    results = run_all()
    if as_json:
        _emit_json(results)
    else:
        _render_console(results)
    code = _exit_code_for(results)
    if strict and any(r["status"] == "warn" for r in results):
        code = 2
    sys.exit(code)


@cli.command("list")
def list_checks() -> None:
    """List every check slug callable via `sinister-diagnose <slug>`."""
    width = max(len(s) for s in ALL_CHECKS)
    click.echo(f"sinister-diagnose v{__version__}  —  {len(ALL_CHECKS)} checks")
    click.echo()
    for slug, fn in ALL_CHECKS.items():
        doc = (fn.__doc__ or "").strip().splitlines()[0] if fn.__doc__ else ""
        click.echo(f"  {slug.ljust(width)}  {doc}")


@cli.command("check")
@click.argument("slug")
@click.option("--json", "as_json", is_flag=True, default=False)
def run_one(slug: str, as_json: bool) -> None:
    """Run a single check by slug (e.g. `python`, `rust`, `backups`)."""
    if slug not in ALL_CHECKS:
        click.echo(f"sinister-diagnose: unknown check `{slug}`. "
                   f"Run `sinister-diagnose list` to see all.", err=True)
        sys.exit(2)
    r = ALL_CHECKS[slug]()
    if as_json:
        print(_json.dumps(r, indent=2))
    else:
        _render_console([r])
    sys.exit(_exit_code_for([r]))


def dispatch(argv: List[str] | None = None) -> int:
    """argv → exit code. Used by __main__.main() for umbrella integration.

    Handles a small UX nicety: if argv[0] is a known check slug AND not a
    registered click command, treat it as `check <slug>` so that
    `sinister diagnose python` works the same as `sinister diagnose check python`.
    """
    argv = list(sys.argv[1:] if argv is None else argv)

    # Promote bare slug invocations to `check <slug>` for ergonomics.
    if argv and argv[0] in ALL_CHECKS:
        argv = ["check"] + argv

    try:
        cli.main(args=argv, standalone_mode=False)
    except SystemExit as e:
        return int(e.code or 0)
    except click.ClickException as e:
        e.show()
        return e.exit_code
    except Exception as e:  # pragma: no cover - defensive
        print(f"sinister-diagnose: error: {e}", file=sys.stderr)
        return 2
    return 0
