# Sinister Sanctum :: sinister-login :: 11-provider registry
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
"""
Provider registry mirroring jcode v0.12.3 `jcode login --provider X` matrix.

Operator screenshot 2026-05-21T11:50Z listed 11 providers. Each provider row
records: slug, display, key-env-var(s), optional endpoint-env-var, base URL,
auth scheme (apikey / oauth / local), brief doc URL. No network is touched
at import time. `provider_status()` only reads env-vars; `api.doctor()` is
where opt-in reachability probes live.

Composes with:
- automations/agent-host-routing.md (which provider each task-class routes to)
- _vault/ (operator-owned secret storage; future vault-MCP integration)
- _shared-memory/knowledge/jcode-feature-matrix.md (row 1 / 11-provider wallet)
"""
from __future__ import annotations
import os
from dataclasses import dataclass, field
from typing import Iterable

SCHEMA_VERSION = "sinister.login.providers.v1"


@dataclass(frozen=True)
class Provider:
    slug: str
    display: str
    auth: str
    key_envs: tuple[str, ...] = field(default_factory=tuple)
    endpoint_envs: tuple[str, ...] = field(default_factory=tuple)
    base_url: str = ""
    docs_url: str = ""
    notes: str = ""

    def key_value(self) -> str | None:
        for env in self.key_envs:
            v = os.environ.get(env)
            if v:
                return v
        return None

    def endpoint_value(self) -> str | None:
        for env in self.endpoint_envs:
            v = os.environ.get(env)
            if v:
                return v
        return self.base_url or None


PROVIDERS: tuple[Provider, ...] = (
    Provider(
        slug="claude",
        display="Anthropic Claude",
        auth="apikey",
        key_envs=("ANTHROPIC_API_KEY",),
        base_url="https://api.anthropic.com",
        docs_url="https://docs.anthropic.com/en/api/getting-started",
        notes="Default for Forge / Term / Sanctum master per agent-host-routing.md. claude-opus-4-7 preferred.",
    ),
    Provider(
        slug="openai",
        display="OpenAI",
        auth="apikey",
        key_envs=("OPENAI_API_KEY",),
        endpoint_envs=("OPENAI_BASE_URL",),
        base_url="https://api.openai.com",
        docs_url="https://platform.openai.com/docs/api-reference/introduction",
    ),
    Provider(
        slug="gemini",
        display="Google Gemini",
        auth="apikey",
        key_envs=("GEMINI_API_KEY", "GOOGLE_API_KEY"),
        base_url="https://generativelanguage.googleapis.com",
        docs_url="https://ai.google.dev/api/rest",
    ),
    Provider(
        slug="copilot",
        display="GitHub Copilot",
        auth="oauth",
        key_envs=("GITHUB_TOKEN", "GH_TOKEN"),
        base_url="https://api.githubcopilot.com",
        docs_url="https://docs.github.com/en/copilot",
        notes="Requires GitHub OAuth with copilot scope. `gh auth refresh -s copilot` to grant.",
    ),
    Provider(
        slug="azure",
        display="Azure OpenAI",
        auth="apikey",
        key_envs=("AZURE_OPENAI_API_KEY",),
        endpoint_envs=("AZURE_OPENAI_ENDPOINT",),
        base_url="",
        docs_url="https://learn.microsoft.com/azure/ai-services/openai/reference",
        notes="Endpoint is tenant-specific; user MUST set AZURE_OPENAI_ENDPOINT.",
    ),
    Provider(
        slug="alibaba-coding-plan",
        display="Alibaba Qwen (DashScope coding plan)",
        auth="apikey",
        key_envs=("DASHSCOPE_API_KEY",),
        base_url="https://dashscope.aliyuncs.com/api/v1",
        docs_url="https://help.aliyun.com/zh/dashscope/",
    ),
    Provider(
        slug="fireworks",
        display="Fireworks AI",
        auth="apikey",
        key_envs=("FIREWORKS_API_KEY",),
        base_url="https://api.fireworks.ai/inference/v1",
        docs_url="https://docs.fireworks.ai/api-reference/introduction",
    ),
    Provider(
        slug="minimax",
        display="MiniMax",
        auth="apikey",
        key_envs=("MINIMAX_API_KEY",),
        endpoint_envs=("MINIMAX_GROUP_ID",),
        base_url="https://api.minimax.chat/v1",
        docs_url="https://platform.minimaxi.com/document/guides/api",
        notes="MINIMAX_GROUP_ID required alongside the key.",
    ),
    Provider(
        slug="lmstudio",
        display="LM Studio (local)",
        auth="local",
        key_envs=(),
        endpoint_envs=("LMSTUDIO_BASE_URL",),
        base_url="http://localhost:1234/v1",
        docs_url="https://lmstudio.ai/docs/local-server",
        notes="Local server. No API key required by default. Override port via LMSTUDIO_BASE_URL.",
    ),
    Provider(
        slug="ollama",
        display="Ollama (local)",
        auth="local",
        key_envs=(),
        endpoint_envs=("OLLAMA_HOST", "OLLAMA_BASE_URL"),
        base_url="http://localhost:11434",
        docs_url="https://github.com/ollama/ollama/blob/main/docs/api.md",
    ),
    Provider(
        slug="openai-compatible",
        display="OpenAI-compatible (generic)",
        auth="apikey",
        key_envs=("SINISTER_OAI_COMPAT_KEY", "OPENAI_API_KEY"),
        endpoint_envs=("SINISTER_OAI_COMPAT_BASE_URL", "OPENAI_BASE_URL"),
        base_url="",
        docs_url="",
        notes="Catch-all for any provider speaking the OpenAI v1 protocol (Groq, Together, DeepInfra, OpenRouter, etc). Set BOTH key + base-url.",
    ),
)

PROVIDER_BY_SLUG: dict[str, Provider] = {p.slug: p for p in PROVIDERS}


def list_providers() -> Iterable[Provider]:
    return PROVIDERS


def get_provider(slug: str) -> Provider | None:
    return PROVIDER_BY_SLUG.get(slug)


def provider_status(p: Provider) -> dict:
    key = p.key_value()
    endpoint = p.endpoint_value()
    configured = (p.auth == "local") or bool(key)
    missing: list[str] = []
    if p.auth != "local" and not key:
        missing.extend(p.key_envs)
    if p.auth == "local" or p.base_url:
        pass
    else:
        if not endpoint:
            missing.extend(p.endpoint_envs)
    return {
        "slug": p.slug,
        "display": p.display,
        "auth": p.auth,
        "configured": configured and (p.base_url or endpoint or p.auth == "local"),
        "key_present": bool(key),
        "key_env_found": next((e for e in p.key_envs if os.environ.get(e)), None),
        "endpoint": endpoint,
        "missing_envs": missing,
        "docs_url": p.docs_url,
        "notes": p.notes,
    }
