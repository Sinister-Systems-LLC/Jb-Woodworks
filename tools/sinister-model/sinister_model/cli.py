# Sinister Sanctum :: sinister-model :: CLI (click + rich)
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
"""
Subcommands:
    sinister-model list [provider]      — models for a provider (default: logged-in)
    sinister-model current              — show active model
    sinister-model set <model-id>       — set the active model
    sinister-model info <model-id>      — show model details

Reads "currently logged-in provider" from sinister-login (soft dep). If
sinister-login is not installed or no provider is configured, falls back
to anthropic (Sanctum fleet default per agent-host-routing.md).
"""
from __future__ import annotations
import json as _json
import sys
from typing import Any

import click
from rich.console import Console
from rich.table import Table

from . import __version__
from .registry import (
    PROVIDER_MODELS,
    Model,
    list_providers,
    list_models,
    get_model,
    find_provider_for_model,
    total_model_count,
    _normalize_provider,
)
from .state import get_current, set_current, clear_current, state_path

_console = Console()

# Provider used when sinister-login is unavailable / no provider configured.
DEFAULT_FALLBACK_PROVIDER = "anthropic"


def _detect_logged_in_provider() -> str | None:
    """Read the active provider from sinister-login. Returns None if the
    tool isn't installed, no provider is configured, or any import error."""
    try:
        from sinister_login import resolve_active  # type: ignore
    except Exception:
        return None
    try:
        active = resolve_active()
    except Exception:
        return None
    if not active:
        return None
    slug = active.get("slug")
    if not slug:
        return None
    # sinister-login uses "claude" / "gemini"; normalize to sinister-model slugs.
    return _normalize_provider(slug)


def _resolve_provider_arg(provider_arg: str | None) -> tuple[str, str]:
    """Returns (provider_slug, source) where source is 'arg', 'login', or 'fallback'."""
    if provider_arg:
        return _normalize_provider(provider_arg), "arg"
    detected = _detect_logged_in_provider()
    if detected and detected in PROVIDER_MODELS:
        return detected, "login"
    return DEFAULT_FALLBACK_PROVIDER, "fallback"


def _render_models_table(provider: str, models: tuple[Model, ...]) -> None:
    table = Table(title=f"models :: {provider}", title_style="bold magenta")
    table.add_column("model_id", style="cyan", no_wrap=True)
    table.add_column("display", style="white")
    table.add_column("ctx", justify="right", style="green")
    table.add_column("capabilities", style="yellow")
    for m in models:
        ctx = f"{m.context_window:,}" if m.context_window else "—"
        caps = ", ".join(m.capabilities) if m.capabilities else "—"
        table.add_row(m.model_id, m.display, ctx, caps)
    _console.print(table)


def _render_model_detail(provider: str, m: Model) -> None:
    table = Table(title=f"model :: {m.model_id}", title_style="bold magenta", show_header=False)
    table.add_column("field", style="cyan", no_wrap=True)
    table.add_column("value", style="white")
    table.add_row("provider", provider)
    table.add_row("display", m.display)
    table.add_row("context_window", f"{m.context_window:,}" if m.context_window else "—")
    table.add_row("capabilities", ", ".join(m.capabilities) if m.capabilities else "—")
    table.add_row("pricing_hint", m.pricing_hint or "—")
    table.add_row("notes", m.notes or "—")
    _console.print(table)


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, prog_name="sinister-model")
def cli() -> None:
    """Sinister Sanctum :: jcode-model parity. Per-provider model registry + active-model state."""


@cli.command("list")
@click.argument("provider", required=False)
@click.option("--json", "json_out", is_flag=True, help="Emit JSON instead of a table.")
def cmd_list(provider: str | None, json_out: bool) -> None:
    """List models for PROVIDER (defaults to currently logged-in provider)."""
    slug, source = _resolve_provider_arg(provider)
    models = list_models(slug)
    if not models:
        if json_out:
            click.echo(_json.dumps({"ok": False, "provider": slug, "error": "unknown provider",
                                    "known_providers": list(list_providers())}, indent=2))
        else:
            _console.print(f"[red]unknown provider:[/] {slug}")
            _console.print(f"  known: {', '.join(list_providers())}")
        sys.exit(2)
    if json_out:
        payload = {
            "ok": True,
            "provider": slug,
            "source": source,
            "model_count": len(models),
            "models": [m.to_dict() for m in models],
        }
        click.echo(_json.dumps(payload, indent=2))
        return
    if source == "login":
        _console.print(f"[dim]provider resolved from sinister-login: {slug}[/]")
    elif source == "fallback":
        _console.print(f"[dim]no provider arg + sinister-login unavailable; defaulting to {slug}[/]")
    _render_models_table(slug, models)


@cli.command("current")
@click.option("--json", "json_out", is_flag=True, help="Emit JSON instead of plain text.")
def cmd_current(json_out: bool) -> None:
    """Show the currently selected model."""
    state = get_current()
    if not state:
        if json_out:
            click.echo(_json.dumps({"ok": False, "error": "no model set",
                                    "state_path": str(state_path())}, indent=2))
        else:
            _console.print("[yellow]no model set.[/] use `sinister-model set <model-id>`")
            _console.print(f"  state path: {state_path()}")
        sys.exit(2)
    model_id = state.get("model_id", "")
    m = get_model(model_id)
    provider = state.get("provider") or (find_provider_for_model(model_id) or "?")
    if json_out:
        payload: dict[str, Any] = dict(state)
        payload["ok"] = True
        payload["known"] = m is not None
        if m:
            payload["details"] = m.to_dict()
        click.echo(_json.dumps(payload, indent=2))
        return
    _console.print(f"[bold]current model:[/] [cyan]{model_id}[/]")
    _console.print(f"  provider: {provider}")
    _console.print(f"  set_at:   {state.get('set_at', '—')}")
    if m is None:
        _console.print(f"  [yellow]warning: model not in registry — may be stale or custom[/]")
    else:
        _console.print(f"  display:  {m.display}")
        _console.print(f"  context:  {m.context_window:,}")


@cli.command("set")
@click.argument("model_id")
@click.option("--force", is_flag=True, help="Allow setting a model id not in the registry.")
@click.option("--json", "json_out", is_flag=True, help="Emit JSON instead of plain text.")
def cmd_set(model_id: str, force: bool, json_out: bool) -> None:
    """Set the active MODEL_ID."""
    m = get_model(model_id)
    if m is None and not force:
        if json_out:
            click.echo(_json.dumps({"ok": False, "error": "unknown model_id",
                                    "model_id": model_id,
                                    "hint": "use --force to set a custom model id"}, indent=2))
        else:
            _console.print(f"[red]unknown model_id:[/] {model_id}")
            _console.print("  use --force to set a model id not in the registry")
        sys.exit(2)
    provider = find_provider_for_model(model_id)
    payload = set_current(model_id, provider=provider)
    if json_out:
        out = dict(payload)
        out["ok"] = True
        out["state_path"] = str(state_path())
        click.echo(_json.dumps(out, indent=2))
        return
    _console.print(f"[green]set active model:[/] [cyan]{model_id}[/]")
    if provider:
        _console.print(f"  provider: {provider}")
    if m is None:
        _console.print("  [yellow](custom; not in registry)[/]")
    _console.print(f"  written:  {state_path()}")


@cli.command("info")
@click.argument("model_id")
@click.option("--json", "json_out", is_flag=True, help="Emit JSON instead of a table.")
def cmd_info(model_id: str, json_out: bool) -> None:
    """Show details for MODEL_ID."""
    m = get_model(model_id)
    if m is None:
        if json_out:
            click.echo(_json.dumps({"ok": False, "error": "unknown model_id",
                                    "model_id": model_id}, indent=2))
        else:
            _console.print(f"[red]unknown model_id:[/] {model_id}")
        sys.exit(2)
    provider = find_provider_for_model(model_id) or "?"
    if json_out:
        payload = m.to_dict()
        payload["provider"] = provider
        payload["ok"] = True
        click.echo(_json.dumps(payload, indent=2))
        return
    _render_model_detail(provider, m)


@cli.command("providers")
@click.option("--json", "json_out", is_flag=True, help="Emit JSON instead of plain text.")
def cmd_providers(json_out: bool) -> None:
    """List all providers + model counts."""
    rows = [(p, len(list_models(p))) for p in list_providers()]
    if json_out:
        click.echo(_json.dumps({
            "ok": True,
            "providers": [{"slug": p, "model_count": n} for p, n in rows],
            "total_models": total_model_count(),
        }, indent=2))
        return
    table = Table(title="sinister-model :: providers", title_style="bold magenta")
    table.add_column("provider", style="cyan")
    table.add_column("models", justify="right", style="green")
    for p, n in rows:
        table.add_row(p, str(n))
    _console.print(table)
    _console.print(f"[dim]total models: {total_model_count()}[/]")


@cli.command("clear")
@click.option("--json", "json_out", is_flag=True)
def cmd_clear(json_out: bool) -> None:
    """Clear the persisted active-model selection."""
    removed = clear_current()
    if json_out:
        click.echo(_json.dumps({"ok": True, "removed": removed,
                                "state_path": str(state_path())}, indent=2))
        return
    if removed:
        _console.print("[green]cleared active model[/]")
    else:
        _console.print("[dim]no active model to clear[/]")


def main(argv: list[str] | None = None) -> int:
    """Stdlib-style entry point for the sinister-cli umbrella dispatcher.

    Click normally calls sys.exit on its own; we intercept SystemExit so
    the umbrella dispatcher can chain return codes cleanly.
    """
    try:
        cli(args=argv, standalone_mode=False)
        return 0
    except click.exceptions.UsageError as e:
        click.echo(f"sinister-model: {e.format_message()}", err=True)
        return 2
    except click.exceptions.ClickException as e:
        e.show()
        return e.exit_code
    except SystemExit as e:
        code = e.code
        if code is None:
            return 0
        if isinstance(code, int):
            return code
        return 1


if __name__ == "__main__":
    sys.exit(main())
