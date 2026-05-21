# Sinister Term :: login_stub.py
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
#
# Per-provider auth flow STUBS. These do NOT execute auth — they print the
# operator-facing instructions + log a TODO into OPERATOR-ACTION-QUEUE.md.
#
# Why a stub:
#   - canonical-3 AUP-RESPECT: tokens / API keys / OAuth flows belong to the
#     operator. Agents must never auto-mint credentials.
#   - canonical-10 lane discipline: _vault/ is operator-owned.
#
# jcode parity per github.com/1jehuang/jcode `jcode login --provider <name>`,
# attribution per canonical-20.

from __future__ import annotations

import json
import os
import time
from pathlib import Path


SANCTUM_ROOT = Path(os.environ.get("SANCTUM_ROOT") or "D:/Sinister Sanctum")
OPERATOR_QUEUE = SANCTUM_ROOT / "_shared-memory" / "OPERATOR-ACTION-QUEUE.md"
LOGIN_PENDING_DIR = SANCTUM_ROOT / "_shared-memory" / "sinister-login-pending"


PROVIDER_HINTS: dict[str, dict] = {
    "claude": {
        "url": "https://console.anthropic.com/account/keys",
        "env_var": "ANTHROPIC_API_KEY",
        "vault_key": "anthropic_api_key",
        "notes": "Use the Anthropic console to mint a key. Sanctum env-vars doc: docs/ENV-VARIABLES.md",
    },
    "openai": {
        "url": "https://platform.openai.com/api-keys",
        "env_var": "OPENAI_API_KEY",
        "vault_key": "openai_api_key",
    },
    "copilot": {
        "url": "https://github.com/login/oauth/authorize (device flow)",
        "env_var": "GITHUB_TOKEN (PAT scoped to Copilot)",
        "vault_key": "github_copilot_token",
    },
    "gemini": {
        "url": "https://aistudio.google.com/app/apikey",
        "env_var": "GEMINI_API_KEY",
        "vault_key": "gemini_api_key",
    },
    "azure": {
        "url": "https://portal.azure.com (Azure OpenAI Studio)",
        "env_var": "AZURE_OPENAI_KEY + AZURE_OPENAI_ENDPOINT",
        "vault_key": "azure_openai_*",
    },
    "openrouter": {
        "url": "https://openrouter.ai/keys",
        "env_var": "OPENROUTER_API_KEY",
        "vault_key": "openrouter_api_key",
    },
    "ollama": {
        "url": "http://localhost:11434 (local — no key needed)",
        "env_var": "OLLAMA_HOST (optional, default http://localhost:11434)",
        "vault_key": None,
    },
    "lmstudio": {
        "url": "http://localhost:1234 (local — no key needed by default)",
        "env_var": "LMSTUDIO_HOST (optional)",
        "vault_key": None,
    },
    "openai-compatible": {
        "url": "<your custom endpoint>",
        "env_var": "OPENAI_COMPATIBLE_BASE_URL + OPENAI_COMPATIBLE_API_KEY",
        "vault_key": "openai_compatible_*",
    },
}


def _hint_for(provider: str) -> dict:
    return PROVIDER_HINTS.get(provider, {
        "url": "(provider not in our hint table — see provider docs)",
        "env_var": f"(provider-specific; see github.com/1jehuang/jcode docs)",
        "vault_key": f"{provider}_api_key",
    })


def _write_pending(provider: str, args) -> Path:
    LOGIN_PENDING_DIR.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y-%m-%dT%H%MZ", time.gmtime())
    body = {
        "_author": "RKOJ-ELENO :: 2026-05-21",
        "provider": provider,
        "ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "via": "sinister login --provider",
        "args": {
            "no_browser": getattr(args, "no_browser", False) or getattr(args, "headless", False),
            "print_auth_url": getattr(args, "print_auth_url", False),
            "json": getattr(args, "json_out", False),
            "callback_url": getattr(args, "callback_url", None),
            "auth_code": getattr(args, "auth_code", None),
            "complete": getattr(args, "complete", False),
        },
        "hint": _hint_for(provider),
        "status": "pending-operator-action",
    }
    path = LOGIN_PENDING_DIR / f"{ts}-{provider}-login-request.json"
    path.write_text(json.dumps(body, indent=2), encoding="utf-8")
    return path


def _append_operator_queue(provider: str, hint: dict) -> None:
    OPERATOR_QUEUE.parent.mkdir(parents=True, exist_ok=True)
    entry = (
        f"\n- [ ] **`sinister login --provider {provider}`** "
        f"({time.strftime('%Y-%m-%d', time.gmtime())}). "
        f"Mint a key at {hint.get('url')} and set env var `{hint.get('env_var')}`. "
        f"Pending request: `_shared-memory/sinister-login-pending/`.\n"
    )
    try:
        with OPERATOR_QUEUE.open("a", encoding="utf-8") as f:
            f.write(entry)
    except OSError as e:
        print(f"(could not append to OPERATOR-ACTION-QUEUE.md: {e})")


def run(args) -> int:
    provider = args.provider
    hint = _hint_for(provider)
    no_browser = args.no_browser or args.headless
    print_auth_url = args.print_auth_url
    json_out = args.json_out

    path = _write_pending(provider, args)
    _append_operator_queue(provider, hint)

    if json_out:
        out = {
            "provider": provider,
            "status": "pending-operator-action",
            "hint": hint,
            "pending_request_path": str(path.relative_to(SANCTUM_ROOT)),
            "no_browser": no_browser,
            "print_auth_url": print_auth_url,
        }
        print(json.dumps(out, indent=2))
        return 0

    print(f"sinister login --provider {provider}")
    print()
    print(f"  AUTH FLOW STATUS: pending operator action (canonical-3 AUP-RESPECT).")
    print(f"  Sinister Term does NOT auto-mint credentials.")
    print()
    print(f"  Where to mint a key: {hint.get('url')}")
    print(f"  Env var to set:      {hint.get('env_var')}")
    if hint.get("vault_key"):
        print(f"  Sinister Vault key:  {hint.get('vault_key')}")
    if hint.get("notes"):
        print(f"  Notes:               {hint.get('notes')}")
    print()
    if no_browser:
        print(f"  [--no-browser/--headless mode] No interactive auth will be opened.")
    if print_auth_url:
        print(f"  [--print-auth-url mode] In a future PH-LOGIN session we'd emit the")
        print(f"                          OAuth URL here. Currently a stub.")
    if args.callback_url:
        print(f"  [--callback-url] {args.callback_url} (recorded for future flow)")
    if args.auth_code:
        print(f"  [--auth-code] (recorded for future device-flow completion)")
    if args.complete:
        print(f"  [--complete] (Copilot device flow resume requested — stub)")
    print()
    print(f"  Logged to:           {path.relative_to(SANCTUM_ROOT)}")
    print(f"  Appended to:         _shared-memory/OPERATOR-ACTION-QUEUE.md")
    return 0


def auth_test() -> int:
    """Verify provider auth — stub. Checks env vars + Vault keys."""
    print("sinister auth-test")
    print()
    print("  STUB: in a future PH-LOGIN session we'd actually ping each provider.")
    print()
    print("  Currently we just enumerate which env vars + Vault keys are populated.")
    print()
    populated_env = []
    for prov, hint in PROVIDER_HINTS.items():
        env = hint.get("env_var") or ""
        # Strip noise like " (PAT scoped to Copilot)"
        env_name = env.split()[0] if env else ""
        if env_name and os.environ.get(env_name):
            populated_env.append((prov, env_name))
    if not populated_env:
        print("  no provider env vars set in current process.")
    else:
        print("  populated env vars:")
        for prov, env in populated_env:
            print(f"    · {prov:<20} {env}=<set>")
    return 0


def provider_add(args: list[str]) -> int:
    """Custom provider add — stub. Mirrors jcode `jcode provider add`."""
    print("sinister provider add")
    print()
    print("  STUB: in a future PH-LOGIN session we'd write a custom provider")
    print("  profile to ~/.sinister/providers.toml. Currently:")
    print()
    print(f"  args: {args}")
    print(f"  See: github.com/1jehuang/jcode docs for the profile schema we'll port.")
    return 1
