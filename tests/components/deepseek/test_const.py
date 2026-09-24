"""Test constants for DeepSeek integration."""

from __future__ import annotations

from custom_components.deepseek.const import (
    CONF_API_KEY,
    CONF_BASE_URL,
    CONF_CHAT_MODEL,
    CONF_MAX_TOKENS,
    CONF_PROMPT,
    CONF_TEMPERATURE,
    CONF_TOP_P,
    DEFAULT_BASE_URL,
    DEFAULT_NAME,
    DOMAIN,
    LEGACY_MODELS,
    MODELS,
    REASONING_EFFORTS,
    RECOMMENDED_CHAT_MODEL,
    RECOMMENDED_MAX_TOKENS,
    RECOMMENDED_REASONING_EFFORT,
    RECOMMENDED_TEMPERATURE,
    RECOMMENDED_TOP_P,
)


def test_constants() -> None:
    """Constants are correctly defined."""
    assert DOMAIN == "deepseek"
    assert DEFAULT_NAME == "DeepSeek"

    # Configuration keys.
    assert CONF_API_KEY == "api_key"
    assert CONF_BASE_URL == "base_url"
    assert CONF_CHAT_MODEL == "chat_model"
    assert CONF_MAX_TOKENS == "max_tokens"
    assert CONF_TEMPERATURE == "temperature"
    assert CONF_TOP_P == "top_p"
    assert CONF_PROMPT == "prompt"

    # Defaults / recommended values.
    assert DEFAULT_BASE_URL == "https://api.deepseek.com"
    assert RECOMMENDED_CHAT_MODEL == "deepseek-v4-flash"
    assert RECOMMENDED_REASONING_EFFORT in REASONING_EFFORTS
    assert RECOMMENDED_MAX_TOKENS == 2048
    assert 0.0 <= RECOMMENDED_TEMPERATURE <= 2.0
    assert 0.0 <= RECOMMENDED_TOP_P <= 1.0


def test_models_catalogue() -> None:
    """Only current DeepSeek IDs are offered; retired ones map onto V4."""
    assert MODELS == ["deepseek-v4-flash", "deepseek-v4-pro"]
    assert MODELS[0] == RECOMMENDED_CHAT_MODEL
    # Retired 2026-07-24 — must not be offered, only migrated.
    for legacy in ("deepseek-chat", "deepseek-reasoner", "deepseek-coder"):
        assert legacy not in MODELS
        model, effort = LEGACY_MODELS[legacy]
        assert model in MODELS
        assert effort in REASONING_EFFORTS
    assert LEGACY_MODELS["deepseek-chat"] == ("deepseek-v4-flash", "none")
    assert LEGACY_MODELS["deepseek-reasoner"] == ("deepseek-v4-flash", "high")
