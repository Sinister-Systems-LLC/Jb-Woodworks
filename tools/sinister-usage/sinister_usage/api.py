# Sinister Sanctum :: sinister-usage :: API
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
"""
Programmatic API. Honors canonical-11 reversibility: NO network calls in
v0.1.0. The `check` family only inspects env + endpoint-known state. v0.2.0
will add `report()` gated on explicit `--allow-network`.

If sinister-login is installed, `check()` cross-references its
`provider_status()` to flag which providers actually have keys configured.
If sinister-login is missing, the cross-ref is gracefully skipped.
"""
from __future__ import annotations
from typing import Any

from .endpoints import USAGE_ENDPOINTS, UsageEndpoint, get_endpoint


def _provider_configured(slug: str) -> bool | None:
    """Soft cross-tool dep on sinister-login. Returns None when sinister-login
    is not installed (so callers can render '—' instead of yes/no)."""
    try:
        from sinister_login import get_provider, provider_status  # type: ignore
    except Exception:
        return None
    p = get_provider(slug)
    if p is None:
        return None
    return bool(provider_status(p)["configured"])


def check(slug: str) -> dict[str, Any]:
    e = get_endpoint(slug)
    if e is None:
        return {"ok": False, "slug": slug, "error": "unknown provider"}
    return {
        "ok": True,
        "slug": e.slug,
        "display": e.display,
        "endpoint_url": e.endpoint_url,
        "endpoint_known": e.endpoint_url is not None,
        "auth_method": e.auth_method,
        "configured": _provider_configured(e.slug),
        "docs_url": e.docs_url,
        "notes": e.notes,
    }


def check_all() -> list[dict[str, Any]]:
    return [check(e.slug) for e in USAGE_ENDPOINTS]


def list_endpoints() -> list[dict[str, Any]]:
    """Endpoint-registry shape (no env lookup, no cross-tool dep). Useful for
    docs-generation and grep."""
    return [
        {
            "slug": e.slug,
            "display": e.display,
            "endpoint_url": e.endpoint_url,
            "endpoint_known": e.endpoint_url is not None,
            "auth_method": e.auth_method,
            "docs_url": e.docs_url,
            "notes": e.notes,
        }
        for e in USAGE_ENDPOINTS
    ]
