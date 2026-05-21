# Sinister Sanctum :: sinister-model :: registry tests
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
from __future__ import annotations
import pytest

from sinister_model import (
    PROVIDER_MODELS,
    Model,
    list_providers,
    list_models,
    get_model,
    find_provider_for_model,
    SCHEMA_VERSION,
    __version__,
)
from sinister_model.registry import total_model_count, _normalize_provider


# ---------- Schema + version --------------------------------------------------

def test_version_is_v0_1_0():
    assert __version__ == "0.1.0"


def test_schema_version_is_v1():
    assert SCHEMA_VERSION == "sinister.model.registry.v1"


# ---------- Provider coverage -------------------------------------------------

EXPECTED_PROVIDERS = {
    "anthropic", "openai", "google", "xai", "mistral",
    "groq", "deepseek", "openrouter", "cohere", "perplexity", "together",
}


def test_eleven_providers_exactly():
    assert len(PROVIDER_MODELS) == 11
    assert set(PROVIDER_MODELS) == EXPECTED_PROVIDERS


def test_list_providers_returns_all():
    assert set(list_providers()) == EXPECTED_PROVIDERS


def test_every_provider_has_at_least_one_model():
    for slug, models in PROVIDER_MODELS.items():
        assert len(models) >= 1, f"provider {slug} has no models"


def test_total_model_count_nonzero():
    # Sanity: we expect at least ~30 models across 11 providers.
    assert total_model_count() >= 30


# ---------- Anthropic models (operator-spec verbatim) -------------------------

@pytest.mark.parametrize("model_id", [
    "claude-opus-4-7",
    "claude-opus-4-7[1m]",
    "claude-sonnet-4-6",
    "claude-haiku-4-5-20251001",
    "claude-3-5-sonnet-20241022",
    "claude-3-5-haiku-20241022",
])
def test_anthropic_has_spec_model(model_id):
    ids = {m.model_id for m in list_models("anthropic")}
    assert model_id in ids


def test_claude_opus_1m_has_1m_context():
    m = get_model("claude-opus-4-7[1m]")
    assert m is not None
    assert m.context_window == 1_000_000
    assert "1m-context" in m.capabilities


# ---------- OpenAI models -----------------------------------------------------

@pytest.mark.parametrize("model_id", [
    "gpt-5", "gpt-5-mini", "gpt-4o", "gpt-4o-mini", "o1", "o1-mini", "o3",
])
def test_openai_has_spec_model(model_id):
    ids = {m.model_id for m in list_models("openai")}
    assert model_id in ids


# ---------- Google / xAI / mistral / groq / deepseek / openrouter -------------

def test_google_has_gemini_2_flash():
    ids = {m.model_id for m in list_models("google")}
    assert "gemini-2.0-flash-exp" in ids


def test_xai_has_grok_2():
    ids = {m.model_id for m in list_models("xai")}
    assert "grok-2" in ids and "grok-2-mini" in ids and "grok-beta" in ids


def test_mistral_has_codestral():
    ids = {m.model_id for m in list_models("mistral")}
    assert "codestral-latest" in ids


def test_groq_has_llama_3_3_70b():
    ids = {m.model_id for m in list_models("groq")}
    assert "llama-3.3-70b-versatile" in ids


def test_deepseek_has_reasoner():
    ids = {m.model_id for m in list_models("deepseek")}
    assert "deepseek-reasoner" in ids


def test_openrouter_models_are_namespaced():
    for m in list_models("openrouter"):
        assert "/" in m.model_id, f"openrouter model {m.model_id} should be vendor/model"


# ---------- cohere / perplexity / together -----------------------------------

def test_cohere_has_command_r_plus():
    ids = {m.model_id for m in list_models("cohere")}
    assert "command-r-plus" in ids


def test_perplexity_has_sonar_online():
    ids = {m.model_id for m in list_models("perplexity")}
    assert any("sonar" in mid and "online" in mid for mid in ids)


def test_together_has_llama_3_3_turbo():
    ids = {m.model_id for m in list_models("together")}
    assert "meta-llama/Llama-3.3-70B-Instruct-Turbo" in ids


# ---------- Lookup helpers ----------------------------------------------------

def test_get_model_known():
    m = get_model("claude-sonnet-4-6")
    assert m is not None
    assert m.display.startswith("Claude Sonnet")


def test_get_model_unknown_returns_none():
    assert get_model("nonsense-model-xyz") is None


def test_get_model_empty_returns_none():
    assert get_model("") is None


def test_find_provider_for_known_model():
    assert find_provider_for_model("gpt-4o") == "openai"
    assert find_provider_for_model("claude-opus-4-7") == "anthropic"
    assert find_provider_for_model("gemini-1.5-pro") == "google"


def test_find_provider_for_unknown_returns_none():
    assert find_provider_for_model("nonsense") is None


# ---------- Login-slug alias normalization -----------------------------------

def test_login_slug_claude_resolves_to_anthropic():
    # sinister-login uses 'claude' but registry uses 'anthropic'
    assert _normalize_provider("claude") == "anthropic"
    assert len(list_models("claude")) == len(list_models("anthropic"))


def test_login_slug_gemini_resolves_to_google():
    assert _normalize_provider("gemini") == "google"
    assert len(list_models("gemini")) == len(list_models("google"))


def test_unknown_provider_returns_empty():
    assert list_models("nonsense") == ()


# ---------- Model dataclass invariants ---------------------------------------

def test_every_model_has_required_fields():
    for slug, models in PROVIDER_MODELS.items():
        for m in models:
            assert isinstance(m, Model)
            assert m.model_id, f"empty model_id in {slug}"
            assert m.display, f"empty display in {slug}:{m.model_id}"
            assert isinstance(m.context_window, int)
            assert isinstance(m.capabilities, tuple)


def test_model_to_dict_roundtrip():
    m = get_model("claude-opus-4-7")
    d = m.to_dict()
    assert d["model_id"] == "claude-opus-4-7"
    assert d["display"] == m.display
    assert d["context_window"] == m.context_window
    assert d["capabilities"] == list(m.capabilities)


def test_model_ids_are_unique_within_provider():
    for slug, models in PROVIDER_MODELS.items():
        ids = [m.model_id for m in models]
        assert len(ids) == len(set(ids)), f"duplicate model_id in {slug}"
