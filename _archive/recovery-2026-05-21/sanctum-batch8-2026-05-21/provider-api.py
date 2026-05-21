# Sinister Sanctum :: sinister-provider :: core API
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later

from __future__ import annotations

SCHEMA_VERSION = "sinister.provider.v1"
_AUTHOR = "RKOJ-ELENO :: 2026-05-21"


def _import_login():
    try:
        from sinister_login import (
            list_providers as _ll,
            add_provider as _add,
            use_env as _use_env,
            logout as _logout,
            show_provider as _show,
        )
        return _ll, _add, _use_env, _logout, _show
    except (ImportError, ModuleNotFoundError):
        return None, None, None, None, None


def list_providers():
    ll, _, _, _, _ = _import_login()
    if not ll:
        return {"ok": False, "error": "sinister-login not installed"}
    return ll()


def current():
    """Heuristic: most-recently-configured provider per stored_at timestamp."""
    ll, _, _, _, _ = _import_login()
    if not ll:
        return {"ok": False, "error": "sinister-login not installed"}
    items = ll()
    configured = [i for i in items if i.get("configured")]
    if not configured:
        return {"ok": False, "error": "no providers configured"}
    configured.sort(key=lambda x: (x.get("stored_at") or ""), reverse=True)
    return configured[0]


def add_provider(provider, *, key=None, endpoint=None, base_url=None, use_env=False, env_var=None):
    _, _add, _use, _, _ = _import_login()
    if not _add:
        return {"ok": False, "error": "sinister-login not installed"}
    if use_env:
        return _use(provider, env_var=env_var)
    return _add(provider, key=key, endpoint=endpoint, base_url=base_url)


def remove_provider(provider):
    _, _, _, _logout, _ = _import_login()
    if not _logout:
        return {"ok": False, "error": "sinister-login not installed"}
    return {"ok": _logout(provider), "provider": provider}
