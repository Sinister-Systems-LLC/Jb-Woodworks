# Sinister Sanctum :: sinister-jcode-shim :: CLI
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
"""
Click-based CLI that locates the prebuilt jcode binary, injects Sinister
config + auth + model env, and execs it with passed-through argv.

Resolution order for the jcode binary:
    1. $JCODE_BIN env var (if set and exists)
    2. C:/Users/Zonia/Desktop/jcode-windows-x86_64.exe  (operator's known drop)
    3. shutil.which("jcode-windows-x86_64.exe")
    4. shutil.which("jcode")

Env vars injected (only if not already set in the caller's env):
    JCODE_CONFIG_DIR    -> ~/.sinister/jcode/
    JCODE_SKILLS_DIR    -> D:/Sinister Sanctum/skills/
    JCODE_SESSIONS_DIR  -> <sanctum>/_shared-memory/forge-memory/jcode-sessions/

Optional bridges (best-effort, never blocking):
    - sinister-login wallet -> ANTHROPIC_API_KEY / OPENAI_API_KEY
    - sinister-model state  -> JCODE_MODEL
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import click

from . import __version__

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SANCTUM_ROOT_DEFAULT = Path(r"D:\Sinister\Sanctum")
LEGACY_SANCTUM_ROOT = Path(r"D:\Sinister Sanctum")
DESKTOP_BIN = Path(r"C:\Users\Zonia\Desktop\jcode-windows-x86_64.exe")
BIN_NAMES = ("jcode-windows-x86_64.exe", "jcode-windows-x86_64", "jcode.exe", "jcode")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sanctum_root() -> Path:
    """Resolve the Sinister Sanctum root.

    Search order: $SANCTUM_ROOT, D:\\Sinister Sanctum, C:\\Sinister Sanctum,
    ~/Sinister Sanctum. Falls back to the default D:\\ path if none match.
    """
    for c in (
        os.environ.get("SANCTUM_ROOT"),
        str(SANCTUM_ROOT_DEFAULT),
        str(LEGACY_SANCTUM_ROOT),
        r"C:\Sinister Sanctum",
        str(Path.home() / "Sinister" / "Sanctum"),
        str(Path.home() / "Sinister Sanctum"),
    ):
        if c:
            root = Path(c)
            if (root / "SESSION-START").exists() or (root / "CLAUDE.md").exists():
                return root
    return SANCTUM_ROOT_DEFAULT


def find_jcode_binary() -> Path | None:
    """Return the resolved path to the jcode binary, or None if not found."""
    # 1. $JCODE_BIN takes precedence.
    env_bin = os.environ.get("JCODE_BIN", "").strip()
    if env_bin:
        p = Path(env_bin)
        if p.exists() and p.is_file():
            return p

    # 2. Operator's canonical Desktop drop.
    if DESKTOP_BIN.exists() and DESKTOP_BIN.is_file():
        return DESKTOP_BIN

    # 3. PATH search across common names.
    for name in BIN_NAMES:
        hit = shutil.which(name)
        if hit:
            return Path(hit)

    return None


def _ensure_dir(p: Path) -> Path:
    """mkdir -p and return the path (best-effort, swallows OSError)."""
    try:
        p.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass
    return p


def _build_env(sanctum: Path) -> dict[str, str]:
    """Return a copy of os.environ with Sinister injections applied.

    Pre-existing values in the caller's env are NEVER overwritten — operator
    overrides win. We only fill blanks.
    """
    env = os.environ.copy()

    config_dir = _ensure_dir(Path.home() / ".sinister" / "jcode")
    skills_dir = sanctum / "skills"
    sessions_dir = _ensure_dir(
        sanctum / "_shared-memory" / "forge-memory" / "jcode-sessions"
    )

    defaults = {
        "JCODE_CONFIG_DIR": str(config_dir),
        "JCODE_SKILLS_DIR": str(skills_dir),
        "JCODE_SESSIONS_DIR": str(sessions_dir),
        # Sinister branding marker — jcode telemetry / startup banner can key off.
        "JCODE_BRANDING": "sinister",
        "JCODE_VENDOR": "RKOJ-ELENO",
    }
    for k, v in defaults.items():
        env.setdefault(k, v)

    # ---- API keys via sinister-login wallet (best-effort) ------------------
    try:
        from sinister_login import resolve_active, status_all  # type: ignore

        # If ANTHROPIC_API_KEY / OPENAI_API_KEY are already set, do nothing.
        # Otherwise, walk the wallet looking for a configured provider whose
        # canonical env-var name maps onto one of jcode's known auth slots.
        provider_to_env = {
            "claude": "ANTHROPIC_API_KEY",
            "openai": "OPENAI_API_KEY",
            "gemini": "GEMINI_API_KEY",
            "fireworks": "FIREWORKS_API_KEY",
        }
        for row in status_all():
            if not row.get("configured"):
                continue
            target_env = provider_to_env.get(row.get("slug", ""))
            if not target_env or env.get(target_env):
                continue
            # status_all returns the env-var name actually found, e.g.
            # "ANTHROPIC_API_KEY". Pass through the live value.
            source_env = row.get("key_env_found")
            if source_env and os.environ.get(source_env):
                env[target_env] = os.environ[source_env]
        # Best-effort active-provider hint.
        active = resolve_active() if env.get("ANTHROPIC_API_KEY") is None else None
        if active:
            env.setdefault("SINISTER_LOGIN_ACTIVE", active.get("slug", ""))
    except Exception:
        # sinister-login not installed in this env — fine, jcode reads its
        # own env vars natively.
        pass

    # ---- Active model via sinister-model state (best-effort) --------------
    if not env.get("JCODE_MODEL"):
        try:
            from sinister_model import get_current  # type: ignore

            cur = get_current()
            if cur and cur.get("model_id"):
                env["JCODE_MODEL"] = cur["model_id"]
                if cur.get("provider"):
                    env.setdefault("SINISTER_MODEL_PROVIDER", cur["provider"])
        except Exception:
            pass

    return env


# ---------------------------------------------------------------------------
# CLI surface
# ---------------------------------------------------------------------------

@click.group(
    context_settings={
        "help_option_names": ["-h", "--help"],
        # Pass-through unknown args to the `run` subcommand by default.
        "allow_interspersed_args": False,
    }
)
@click.version_option(__version__, prog_name="sinister-jcode-shim")
def cli() -> None:
    """Sinister Sanctum :: sidecar launcher for the prebuilt jcode binary.

    Until we fork jcode source-level (operator-gated; needs Rust toolchain),
    this shim wraps `jcode-windows-x86_64.exe` with Sinister env config.
    """


@cli.command(
    context_settings={
        # Forward unknown flags to jcode untouched.
        "ignore_unknown_options": True,
        "allow_extra_args": True,
    }
)
@click.option("--dry-run", is_flag=True,
              help="Print the resolved env + argv and exit without executing.")
@click.option("--print-bin", is_flag=True,
              help="Print the resolved jcode binary path and exit.")
@click.option("--sanctum-root", type=click.Path(file_okay=False), default=None,
              help="Override Sanctum root (else: $SANCTUM_ROOT or D:\\Sinister Sanctum).")
@click.argument("jcode_args", nargs=-1, type=click.UNPROCESSED)
def run(dry_run: bool, print_bin: bool,
        sanctum_root: str | None, jcode_args: tuple[str, ...]) -> None:
    """Exec the prebuilt jcode binary with Sinister env injected.

    Any args after `--` (or any unknown flags) are passed straight to jcode:

        sinister-jcode-shim run -- --help
        sinister-jcode-shim run resume
        sinister-jcode-shim run --print-bin
    """
    sanctum = Path(sanctum_root) if sanctum_root else _sanctum_root()
    binary = find_jcode_binary()

    if print_bin:
        if binary is None:
            click.echo("(not found)")
            sys.exit(2)
        click.echo(str(binary))
        return

    if binary is None:
        click.echo(
            "sinister-jcode-shim: cannot find jcode binary.\n"
            "  searched: $JCODE_BIN, "
            f"{DESKTOP_BIN}, PATH for {', '.join(BIN_NAMES)}",
            err=True,
        )
        sys.exit(127)

    env = _build_env(sanctum)
    argv = [str(binary), *jcode_args]

    if dry_run:
        click.echo(f"[dry-run] binary: {binary}")
        click.echo(f"[dry-run] sanctum: {sanctum}")
        click.echo(f"[dry-run] argv:    {argv}")
        for k in (
            "JCODE_CONFIG_DIR", "JCODE_SKILLS_DIR", "JCODE_SESSIONS_DIR",
            "JCODE_BRANDING", "JCODE_VENDOR", "JCODE_MODEL",
            "ANTHROPIC_API_KEY", "OPENAI_API_KEY",
            "SINISTER_LOGIN_ACTIVE", "SINISTER_MODEL_PROVIDER",
        ):
            v = env.get(k)
            if v is None:
                continue
            shown = "***SET***" if k.endswith("_API_KEY") else v
            click.echo(f"[dry-run] env.{k}={shown}")
        return

    # Spawn jcode and forward its exit code. Using subprocess.run instead of
    # os.execvpe keeps Click's Windows-side cleanup working and lets us
    # propagate the child's exit code cleanly.
    try:
        result = subprocess.run(argv, env=env, check=False)
    except FileNotFoundError as e:
        click.echo(f"sinister-jcode-shim: failed to exec {binary}: {e}", err=True)
        sys.exit(127)
    sys.exit(result.returncode)


@cli.command()
def doctor() -> None:
    """Diagnose shim readiness: binary discovery + env + optional sidecars."""
    sanctum = _sanctum_root()
    click.echo(f"sanctum-root:    {sanctum}")
    binary = find_jcode_binary()
    click.echo(f"jcode-binary:    {binary or '(not found)'}")
    if binary is None:
        click.echo("  -> drop jcode-windows-x86_64.exe on Desktop or set $JCODE_BIN")
    # sidecar probes
    for mod in ("sinister_login", "sinister_model"):
        try:
            __import__(mod)
            click.echo(f"  {mod:<18} ok")
        except Exception as e:
            click.echo(f"  {mod:<18} missing ({e.__class__.__name__})")
    # surface key env if set
    for k in ("JCODE_BIN", "JCODE_CONFIG_DIR", "JCODE_SKILLS_DIR",
              "JCODE_SESSIONS_DIR", "JCODE_MODEL"):
        v = os.environ.get(k)
        if v:
            click.echo(f"  env.{k}={v}")
