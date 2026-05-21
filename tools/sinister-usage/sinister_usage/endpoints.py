# Sinister Sanctum :: sinister-usage :: known endpoint registry
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
"""
Per-provider token-usage / billing endpoint registry.

v0.1.0 holds public-doc URLs + the auth method each endpoint expects. No HTTP
is performed at this version — `sinister usage check` is env + endpoint-known
only. v0.2.0 will add `sinister usage report` that actually queries with the
operator's key behind `--allow-network`.

`None` for `endpoint_url` means the provider has no public per-key usage API
(only console / dashboard). Sinister surfaces this honestly instead of
inventing a fake endpoint.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable

SCHEMA_VERSION = "sinister.usage.endpoints.v1"


@dataclass(frozen=True)
class UsageEndpoint:
    slug: str
    display: str
    endpoint_url: str | None
    auth_method: str       # "bearer" / "header" / "console-only" / "local"
    docs_url: str
    notes: str = ""


USAGE_ENDPOINTS: tuple[UsageEndpoint, ...] = (
    UsageEndpoint(
        slug="claude",
        display="Anthropic Claude",
        endpoint_url=None,
        auth_method="console-only",
        docs_url="https://console.anthropic.com/settings/usage",
        notes="No public per-key usage API as of 2026-05-21; check console.",
    ),
    UsageEndpoint(
        slug="openai",
        display="OpenAI",
        endpoint_url="https://api.openai.com/v1/usage",
        auth_method="bearer",
        docs_url="https://platform.openai.com/docs/api-reference/usage",
        notes="Requires date query-string param. Use `?date=YYYY-MM-DD`.",
    ),
    UsageEndpoint(
        slug="gemini",
        display="Google Gemini",
        endpoint_url=None,
        auth_method="console-only",
        docs_url="https://console.cloud.google.com/billing",
        notes="Usage is GCP-billing-aggregated; per-key endpoint not exposed.",
    ),
    UsageEndpoint(
        slug="copilot",
        display="GitHub Copilot",
        endpoint_url="https://api.github.com/user/copilot/billing",
        auth_method="bearer",
        docs_url="https://docs.github.com/en/rest/copilot/copilot-user-management",
        notes="Personal-account endpoint; enterprise uses different path.",
    ),
    UsageEndpoint(
        slug="azure",
        display="Azure OpenAI",
        endpoint_url=None,
        auth_method="console-only",
        docs_url="https://portal.azure.com",
        notes="Cost tracked via Azure Cost Management; not the OpenAI-shape API.",
    ),
    UsageEndpoint(
        slug="alibaba-coding-plan",
        display="Alibaba Qwen (DashScope)",
        endpoint_url=None,
        auth_method="console-only",
        docs_url="https://dashscope.aliyuncs.com/billing",
    ),
    UsageEndpoint(
        slug="fireworks",
        display="Fireworks AI",
        endpoint_url="https://api.fireworks.ai/inference/v1/usage",
        auth_method="bearer",
        docs_url="https://docs.fireworks.ai/api-reference/introduction",
        notes="Confirm field exposed on current plan tier.",
    ),
    UsageEndpoint(
        slug="minimax",
        display="MiniMax",
        endpoint_url=None,
        auth_method="console-only",
        docs_url="https://platform.minimaxi.com",
    ),
    UsageEndpoint(
        slug="lmstudio",
        display="LM Studio (local)",
        endpoint_url=None,
        auth_method="local",
        docs_url="https://lmstudio.ai/docs",
        notes="Local server — no cost / no quota. Skipped from quota reports.",
    ),
    UsageEndpoint(
        slug="ollama",
        display="Ollama (local)",
        endpoint_url=None,
        auth_method="local",
        docs_url="https://github.com/ollama/ollama",
        notes="Local server — no cost / no quota. Skipped from quota reports.",
    ),
    UsageEndpoint(
        slug="openai-compatible",
        display="OpenAI-compatible (generic)",
        endpoint_url=None,
        auth_method="bearer",
        docs_url="",
        notes="Varies per host. Set SINISTER_USAGE_OAI_COMPAT_URL to override.",
    ),
)

_BY_SLUG = {e.slug: e for e in USAGE_ENDPOINTS}


def get_endpoint(slug: str) -> UsageEndpoint | None:
    return _BY_SLUG.get(slug)


def iter_endpoints() -> Iterable[UsageEndpoint]:
    return USAGE_ENDPOINTS
