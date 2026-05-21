"""
Sinister RKOJ extension :: vault

Author: RKOJ-ELENO :: 2026-05-21

Bridges the RKOJ PyQt6 shell to the sinister-vault tool (1 TB collab store at :5078).
Self-contained — no imports from sinister_rkoj_qt.*. All Qt/vault imports are deferred
inside functions or guarded by TYPE_CHECKING so manifest.json can be parsed without
PyQt6 or sinister-vault installed.

Hooks implemented:
  - hook_kpi()                : returns vault usage in MB for the KPI tile
  - hook_workstation_action() : opens vault dashboard in default browser (or launches daemon)
  - hook_slash(args, pane, app): dispatches /vault status|list|search|push subcommands
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    # PyQt6 widgets are only typed; never imported at module load.
    from PyQt6.QtWidgets import QWidget  # noqa: F401


VAULT_BASE_URL = "http://127.0.0.1:5078"
VAULT_TOOL_PKG = "sinister_vault"  # tools/sinister-vault/sinister_vault


class VaultExtension:
    """Plugin entry-point. Instantiated once at RKOJ startup by the extension loader."""

    id = "sinister-vault"
    version = "0.1.0"

    # ------------------------------------------------------------------ KPI
    def hook_kpi(self) -> dict[str, Any]:
        """Return KPI tile payload: {value, unit, ok, detail}."""
        usage_mb = self._usage_mb()
        if usage_mb is None:
            return {"value": "--", "unit": "MB", "ok": False, "detail": "vault offline"}
        return {"value": f"{usage_mb:.0f}", "unit": "MB", "ok": True, "detail": f"{VAULT_BASE_URL}"}

    def _usage_mb(self) -> float | None:
        """Probe the vault HTTP endpoint for usage stats; fall back to None if offline."""
        # 1) try the tool's own API if it's importable
        api = self._load_vault_api()
        if api is not None and hasattr(api, "usage_mb"):
            try:
                return float(api.usage_mb())
            except Exception:
                pass
        # 2) fall back to HTTP probe
        try:
            with urllib.request.urlopen(f"{VAULT_BASE_URL}/api/stats", timeout=1.5) as resp:
                import json
                data = json.loads(resp.read().decode("utf-8"))
                return float(data.get("usage_mb", 0))
        except (urllib.error.URLError, TimeoutError, OSError, ValueError):
            return None

    # ----------------------------------------------------- workstation card
    def hook_workstation_action(self) -> dict[str, Any]:
        """Open vault dashboard in default browser. Returns status dict for toast."""
        # Use default-browser launch — works on Win/Mac/Linux without Qt deps.
        url = VAULT_BASE_URL
        try:
            if sys.platform.startswith("win"):
                os.startfile(url)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", url])
            else:
                subprocess.Popen(["xdg-open", url])
            return {"ok": True, "message": f"Opening {url}"}
        except Exception as exc:
            return {"ok": False, "message": f"Failed to open vault: {exc}"}

    # ----------------------------------------------------------- /vault ...
    def hook_slash(self, args: list[str], pane: "QWidget | None", app: Any) -> str:
        """
        /vault <subcommand> [args]
          status            — show daemon status + usage
          list [path]       — list vault entries (root if no path)
          search <query>    — full-text search across vault
          push <file>       — upload a local file to the vault
        """
        api = self._load_vault_api()
        if api is None:
            return "[vault] tool not installed — see tools/sinister-vault/INSTALL-MCP.md"

        sub = (args[0] if args else "status").lower()
        rest = args[1:] if len(args) > 1 else []

        try:
            if sub == "status":
                return self._render_status(api)
            if sub == "list":
                path = rest[0] if rest else "/"
                entries = api.list(path) if hasattr(api, "list") else []
                return self._render_list(path, entries)
            if sub == "search":
                if not rest:
                    return "[vault] usage: /vault search <query>"
                results = api.search(" ".join(rest)) if hasattr(api, "search") else []
                return self._render_search(" ".join(rest), results)
            if sub == "push":
                if not rest:
                    return "[vault] usage: /vault push <file>"
                src = rest[0]
                if not os.path.exists(src):
                    return f"[vault] file not found: {src}"
                if hasattr(api, "push"):
                    res = api.push(src)
                    return f"[vault] pushed {src} -> {res}"
                return "[vault] vault.push() not implemented in installed sinister_vault"
            return f"[vault] unknown subcommand: {sub} (try: status|list|search|push)"
        except Exception as exc:
            return f"[vault] error: {exc}"

    # --------------------------------------------------------------- helpers
    def _load_vault_api(self) -> Any | None:
        """Late-import sinister_vault; return None if unavailable so callers can degrade."""
        try:
            # Walk up looking for tools/sinister-vault on sys.path
            self._ensure_sinister_vault_on_path()
            import importlib
            return importlib.import_module(VAULT_TOOL_PKG)
        except Exception:
            return None

    def _ensure_sinister_vault_on_path(self) -> None:
        here = os.path.abspath(os.path.dirname(__file__))
        # extensions/vault/ -> tools/sinister-rkoj-qt/extensions/vault/ ; walk up to tools/
        for _ in range(6):
            here = os.path.dirname(here)
            cand = os.path.join(here, "sinister-vault")
            if os.path.isdir(cand) and cand not in sys.path:
                sys.path.insert(0, cand)
                return

    def _render_status(self, api: Any) -> str:
        usage = self._usage_mb()
        usage_s = f"{usage:.1f} MB" if usage is not None else "offline"
        daemon = "up" if shutil.which("sinister-vault") else "(cli not on PATH)"
        return f"[vault] status\n  url:    {VAULT_BASE_URL}\n  usage:  {usage_s}\n  daemon: {daemon}"

    def _render_list(self, path: str, entries: list[Any]) -> str:
        if not entries:
            return f"[vault] list {path} :: (empty)"
        lines = [f"[vault] list {path}"]
        for e in entries[:50]:
            lines.append(f"  - {e}")
        if len(entries) > 50:
            lines.append(f"  ... and {len(entries) - 50} more")
        return "\n".join(lines)

    def _render_search(self, query: str, results: list[Any]) -> str:
        if not results:
            return f"[vault] search '{query}' :: 0 hits"
        lines = [f"[vault] search '{query}' :: {len(results)} hits"]
        for r in results[:20]:
            lines.append(f"  - {r}")
        return "\n".join(lines)


# Module-level shim so the loader can do `from handler import handle` if it
# prefers the bare-function pattern shown in the doctrine recipe.
_singleton = VaultExtension()


def handle(args: list[str], pane: Any, app: Any) -> str:  # doctrine-pattern fallback
    return _singleton.hook_slash(args, pane, app)
