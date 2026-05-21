# Sinister Sanctum :: sinister-model :: 11-provider model registry
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
"""
Per-provider model catalog. Mirrors jcode v0.12.3 `jcode model list`
matrix shape but scoped to the 11 providers that Sinister Sanctum
actually routes to (see automations/agent-host-routing.md).

Each model row records: model_id, display, context_window, capability
tags, optional pricing hint. No network at import time. v0.1.0 is
hardcoded; v0.2.0 will pull provider-shipped JSON catalogs at runtime
behind an opt-in --refresh flag.

Composes with:
- tools/sinister-login/ (provider configured-ness)
- tools/sinister-usage/ (per-provider quota visibility)
- automations/agent-host-routing.md (task-class -> model selection)
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Iterable

SCHEMA_VERSION = "sinister.model.registry.v1"


@dataclass(frozen=True)
class Model:
    model_id: str
    display: str
    context_window: int = 0
    capabilities: tuple[str, ...] = field(default_factory=tuple)
    pricing_hint: str = ""
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "model_id": self.model_id,
            "display": self.display,
            "context_window": self.context_window,
            "capabilities": list(self.capabilities),
            "pricing_hint": self.pricing_hint,
            "notes": self.notes,
        }


# Provider slugs mirror sinister-login where possible. Note:
# sinister-login uses "claude" for anthropic and "gemini" for google;
# we keep the provider-vendor name here (anthropic / google) because
# operators talk about models in terms of the vendor (anthropic models,
# google models). The lookup helpers below accept both forms.
PROVIDER_MODELS: dict[str, tuple[Model, ...]] = {
    "anthropic": (
        Model(
            model_id="claude-opus-4-7",
            display="Claude Opus 4.7",
            context_window=200_000,
            capabilities=("reasoning", "tools", "vision", "code"),
            pricing_hint="$15/MTok in, $75/MTok out (est)",
            notes="Sanctum fleet default per agent-host-routing.md.",
        ),
        Model(
            model_id="claude-opus-4-7[1m]",
            display="Claude Opus 4.7 (1M context)",
            context_window=1_000_000,
            capabilities=("reasoning", "tools", "vision", "code", "1m-context"),
            pricing_hint="$15/MTok in, $75/MTok out (1M variant; est)",
            notes="1M context window; preferred for whole-codebase sweeps.",
        ),
        Model(
            model_id="claude-sonnet-4-6",
            display="Claude Sonnet 4.6",
            context_window=200_000,
            capabilities=("reasoning", "tools", "vision", "code"),
            pricing_hint="$3/MTok in, $15/MTok out (est)",
            notes="Sweet-spot for code-gen + single-file patches.",
        ),
        Model(
            model_id="claude-haiku-4-5-20251001",
            display="Claude Haiku 4.5",
            context_window=200_000,
            capabilities=("tools", "vision", "code", "fast"),
            pricing_hint="$1/MTok in, $5/MTok out (est)",
            notes="Cost + latency for narrow patches; bulk classification.",
        ),
        Model(
            model_id="claude-3-5-sonnet-20241022",
            display="Claude 3.5 Sonnet (legacy)",
            context_window=200_000,
            capabilities=("reasoning", "tools", "vision", "code", "legacy"),
            notes="Legacy 3.5 family; retained for compat.",
        ),
        Model(
            model_id="claude-3-5-haiku-20241022",
            display="Claude 3.5 Haiku (legacy)",
            context_window=200_000,
            capabilities=("tools", "code", "fast", "legacy"),
            notes="Legacy 3.5 family; retained for compat.",
        ),
    ),
    "openai": (
        Model(
            model_id="gpt-5",
            display="GPT-5",
            context_window=400_000,
            capabilities=("reasoning", "tools", "vision", "code"),
            notes="Flagship; multi-step reasoning peer for codex-companion.",
        ),
        Model(
            model_id="gpt-5-mini",
            display="GPT-5 Mini",
            context_window=400_000,
            capabilities=("tools", "code", "fast"),
            notes="Cheap fast peer-review path.",
        ),
        Model(
            model_id="gpt-4o",
            display="GPT-4o",
            context_window=128_000,
            capabilities=("reasoning", "tools", "vision", "code"),
            pricing_hint="$2.50/MTok in, $10/MTok out",
        ),
        Model(
            model_id="gpt-4o-mini",
            display="GPT-4o Mini",
            context_window=128_000,
            capabilities=("tools", "vision", "code", "fast"),
            pricing_hint="$0.15/MTok in, $0.60/MTok out",
        ),
        Model(
            model_id="o1",
            display="o1 (reasoning)",
            context_window=200_000,
            capabilities=("reasoning", "code"),
            notes="Long chain-of-thought reasoning model.",
        ),
        Model(
            model_id="o1-mini",
            display="o1-mini (reasoning)",
            context_window=128_000,
            capabilities=("reasoning", "code", "fast"),
        ),
        Model(
            model_id="o3",
            display="o3 (reasoning)",
            context_window=200_000,
            capabilities=("reasoning", "tools", "code"),
            notes="Latest reasoning family.",
        ),
    ),
    "google": (
        Model(
            model_id="gemini-2.0-flash-exp",
            display="Gemini 2.0 Flash (experimental)",
            context_window=1_000_000,
            capabilities=("tools", "vision", "code", "fast", "1m-context"),
        ),
        Model(
            model_id="gemini-1.5-pro",
            display="Gemini 1.5 Pro",
            context_window=2_000_000,
            capabilities=("reasoning", "tools", "vision", "code", "2m-context"),
        ),
        Model(
            model_id="gemini-1.5-flash",
            display="Gemini 1.5 Flash",
            context_window=1_000_000,
            capabilities=("tools", "vision", "code", "fast"),
        ),
    ),
    "xai": (
        Model(
            model_id="grok-2",
            display="Grok 2",
            context_window=131_072,
            capabilities=("reasoning", "tools", "code"),
        ),
        Model(
            model_id="grok-2-mini",
            display="Grok 2 Mini",
            context_window=131_072,
            capabilities=("tools", "code", "fast"),
        ),
        Model(
            model_id="grok-beta",
            display="Grok Beta",
            context_window=131_072,
            capabilities=("reasoning", "code"),
        ),
    ),
    "mistral": (
        Model(
            model_id="mistral-large-latest",
            display="Mistral Large (latest)",
            context_window=128_000,
            capabilities=("reasoning", "tools", "code"),
        ),
        Model(
            model_id="mistral-small-latest",
            display="Mistral Small (latest)",
            context_window=128_000,
            capabilities=("tools", "code", "fast"),
        ),
        Model(
            model_id="codestral-latest",
            display="Codestral (latest)",
            context_window=32_000,
            capabilities=("code",),
            notes="Code-specialized model.",
        ),
    ),
    "groq": (
        Model(
            model_id="llama-3.3-70b-versatile",
            display="Llama 3.3 70B Versatile",
            context_window=131_072,
            capabilities=("reasoning", "tools", "code"),
            notes="Hosted on Groq LPU; very fast inference.",
        ),
        Model(
            model_id="mixtral-8x7b",
            display="Mixtral 8x7B",
            context_window=32_768,
            capabilities=("tools", "code", "fast"),
        ),
        Model(
            model_id="deepseek-r1-distill-llama-70b",
            display="DeepSeek R1 Distill Llama 70B",
            context_window=131_072,
            capabilities=("reasoning", "code"),
            notes="Reasoning distillation of DeepSeek R1.",
        ),
    ),
    "deepseek": (
        Model(
            model_id="deepseek-chat",
            display="DeepSeek Chat",
            context_window=64_000,
            capabilities=("tools", "code"),
        ),
        Model(
            model_id="deepseek-reasoner",
            display="DeepSeek Reasoner",
            context_window=64_000,
            capabilities=("reasoning", "code"),
        ),
        Model(
            model_id="deepseek-coder",
            display="DeepSeek Coder",
            context_window=64_000,
            capabilities=("code",),
        ),
    ),
    "openrouter": (
        Model(
            model_id="anthropic/claude-opus-4-7",
            display="Claude Opus 4.7 (via OpenRouter)",
            context_window=200_000,
            capabilities=("reasoning", "tools", "vision", "code"),
        ),
        Model(
            model_id="openai/gpt-5",
            display="GPT-5 (via OpenRouter)",
            context_window=400_000,
            capabilities=("reasoning", "tools", "vision", "code"),
        ),
        Model(
            model_id="google/gemini-2.0-flash-exp",
            display="Gemini 2.0 Flash (via OpenRouter)",
            context_window=1_000_000,
            capabilities=("tools", "vision", "code", "fast", "1m-context"),
        ),
        Model(
            model_id="meta-llama/llama-3.3-70b-instruct",
            display="Llama 3.3 70B Instruct (via OpenRouter)",
            context_window=131_072,
            capabilities=("reasoning", "tools", "code"),
        ),
    ),
    "cohere": (
        Model(
            model_id="command-r-plus",
            display="Command R+",
            context_window=128_000,
            capabilities=("reasoning", "tools", "code"),
        ),
        Model(
            model_id="command-r",
            display="Command R",
            context_window=128_000,
            capabilities=("tools", "code"),
        ),
        Model(
            model_id="command-light",
            display="Command Light",
            context_window=4_000,
            capabilities=("fast",),
        ),
    ),
    "perplexity": (
        Model(
            model_id="llama-3.1-sonar-large-128k-online",
            display="Llama 3.1 Sonar Large (128k online)",
            context_window=128_000,
            capabilities=("reasoning", "web-search", "code"),
            notes="Online search-augmented model.",
        ),
        Model(
            model_id="llama-3.1-sonar-small-128k-online",
            display="Llama 3.1 Sonar Small (128k online)",
            context_window=128_000,
            capabilities=("web-search", "code", "fast"),
        ),
    ),
    "together": (
        Model(
            model_id="meta-llama/Llama-3.3-70B-Instruct-Turbo",
            display="Llama 3.3 70B Instruct Turbo",
            context_window=131_072,
            capabilities=("reasoning", "tools", "code"),
            notes="Together AI hosted Llama 3.3.",
        ),
    ),
}

# Alias map: sinister-login provider slug -> sinister-model provider slug.
# sinister-login calls anthropic "claude" and google "gemini"; allow either form.
LOGIN_SLUG_ALIASES: dict[str, str] = {
    "claude": "anthropic",
    "gemini": "google",
}


def _normalize_provider(slug: str) -> str:
    slug = (slug or "").strip().lower()
    return LOGIN_SLUG_ALIASES.get(slug, slug)


def list_providers() -> tuple[str, ...]:
    """All known provider slugs (sinister-model form)."""
    return tuple(PROVIDER_MODELS.keys())


def list_models(provider: str) -> tuple[Model, ...]:
    """Return all models for a provider. Empty tuple if provider unknown."""
    return PROVIDER_MODELS.get(_normalize_provider(provider), ())


def get_model(model_id: str) -> Model | None:
    """Look up a model by its id across every provider."""
    if not model_id:
        return None
    for models in PROVIDER_MODELS.values():
        for m in models:
            if m.model_id == model_id:
                return m
    return None


def find_provider_for_model(model_id: str) -> str | None:
    """Reverse lookup: which provider owns this model id?"""
    if not model_id:
        return None
    for provider, models in PROVIDER_MODELS.items():
        for m in models:
            if m.model_id == model_id:
                return provider
    return None


def total_model_count() -> int:
    return sum(len(v) for v in PROVIDER_MODELS.values())
