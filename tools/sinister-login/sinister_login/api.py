# Sinister Sanctum :: sinister-login :: API
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
"""
Programmatic API for the sinister-login wallet.

Default routing matches `automations/agent-host-routing.md`: claude is the
fleet-wide primary; openai-compatible is the catch-all fallback. The
`resolve_active()` function returns the first configured provider in the
operator's preference order (env var `SINISTER_LOGIN_PREFERENCE` overrides;
otherwise the doctrine order below).
"""
from __future__ import annotations
import json
import os
import socket
import urllib.error
import urllib.request
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

from .providers import (
    PROVIDERS,
    Provider,
    PROVIDER_BY_SLUG,
    get_provider,
    provider_status,
)

# Operator-preference order. Override with env SINISTER_LOGIN_PREFERENCE=a,b,c.
DEFAULT_PREFERENCE: tuple[str, ...] = (
    "claude",
    "openai",
    "gemini",
    "fireworks",
    "openai-compatible",
    "lmstudio",
    "ollama",
    "copilot",
    "azure",
    "minimax",
    "alibaba-coding-plan",
)


def _preference_order() -> tuple[str, ...]:
    raw = os.environ.get("SINISTER_LOGIN_PREFERENCE", "").strip()
    if not raw:
        return DEFAULT_PREFERENCE
    items = tuple(s.strip() for s in raw.split(",") if s.strip())
    return items or DEFAULT_PREFERENCE


def status_all() -> list[dict]:
    return [provider_status(p) for p in PROVIDERS]


def resolve_active() -> dict | None:
    for slug in _preference_order():
        p = get_provider(slug)
        if p is None:
            continue
        s = provider_status(p)
        if s["configured"]:
            return s
    return None


def doctor(slug: str, probe: bool = False, timeout_s: float = 3.0) -> dict:
    p = get_provider(slug)
    if p is None:
        return {"ok": False, "slug": slug, "error": "unknown provider"}
    s = provider_status(p)
    s["probed"] = False
    s["reachable"] = None
    if not probe:
        s["ok"] = bool(s["configured"])
        return s
    endpoint = s.get("endpoint")
    if not endpoint:
        s["ok"] = False
        s["error"] = "no endpoint to probe"
        return s
    s["probed"] = True
    s["reachable"] = _tcp_reachable(endpoint, timeout_s=timeout_s)
    s["ok"] = bool(s["configured"]) and bool(s["reachable"])
    return s


def _tcp_reachable(url_or_host: str, timeout_s: float = 3.0) -> bool:
    """TCP-handshake probe (no HTTP body, no auth) — the lightest possible
    'is this host taking connections' check. Read-only by definition."""
    try:
        if "://" in url_or_host:
            u = urlparse(url_or_host)
            host = u.hostname or ""
            port = u.port or (443 if (u.scheme or "https") == "https" else 80)
        else:
            host, _, port_s = url_or_host.partition(":")
            port = int(port_s) if port_s else 443
        if not host:
            return False
        with socket.create_connection((host, port), timeout=timeout_s):
            return True
    except (OSError, ValueError):
        return False


def print_env_for(slug: str) -> list[str]:
    p = get_provider(slug)
    if p is None:
        return []
    lines: list[str] = []
    for env in p.key_envs:
        v = os.environ.get(env, "")
        masked = (v[:4] + "..." + v[-2:]) if v else "<unset>"
        lines.append(f"# {env} = {masked}")
        lines.append(f'$env:{env} = "<paste-your-key>"')
    for env in p.endpoint_envs:
        v = os.environ.get(env, "")
        lines.append(f"# {env} = {v or '<unset>'}")
        lines.append(f'$env:{env} = "<paste-endpoint>"')
    if p.auth == "local":
        lines.append(f"# {p.slug} is local-only; default base: {p.base_url}")
    if not lines:
        lines.append(f"# {p.slug}: no env vars defined.")
    return lines


def add_to_envfile(slug: str, key_value: str, envfile_path: Path | str | None = None,
                   allow_plaintext: bool = False) -> dict:
    """Write a provider key into an env-file. Defaults to ~/.sinister/login.env.
    Refuses to write plaintext unless allow_plaintext=True (canonical-11 reversibility).
    """
    p = get_provider(slug)
    if p is None:
        return {"ok": False, "error": f"unknown provider {slug!r}"}
    if not p.key_envs:
        return {"ok": False, "error": f"{slug} is local-only; no key env to write"}
    if not allow_plaintext:
        return {
            "ok": False,
            "error": "refusing to write plaintext without --allow-plaintext. "
                     "Prefer storing in OS env vars or _vault/ once vault-MCP wired.",
            "key_env": p.key_envs[0],
        }
    path = Path(envfile_path) if envfile_path else (Path.home() / ".sinister" / "login.env")
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    env_name = p.key_envs[0]
    new_line = f"{env_name}={key_value}\n"
    if env_name in existing:
        lines = [(new_line.rstrip("\n") if ln.startswith(env_name + "=") else ln)
                 for ln in existing.splitlines()]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    else:
        path.write_text(existing + new_line, encoding="utf-8")
    return {"ok": True, "path": str(path), "env_name": env_name, "wrote_bytes": path.stat().st_size}
