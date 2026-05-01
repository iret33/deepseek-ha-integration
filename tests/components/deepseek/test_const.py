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
    MODELS,
    RECOMMENDED_CHAT_MODEL,
    RECOMMENDED_MAX_TOKENS,
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
    assert RECOMMENDED_MAX_TOKENS == 2048
    assert 0.0 <= RECOMMENDED_TEMPERATURE <= 2.0
    assert 0.0 <= RECOMMENDED_TOP_P <= 1.0


def test_models_catalogue() -> None:
    """Model catalogue includes current + deprecated DeepSeek IDs."""
    assert "deepseek-v4-flash" in MODELS
    assert "deepseek-v4-pro" in MODELS
    # Deprecated IDs kept for backward compatibility with existing entries.
    assert "deepseek-chat" in MODELS
    assert "deepseek-reasoner" in MODELS
    # Discontinued IDs must not be offered.
    assert "deepseek-coder" not in MODELS
    assert MODELS[0] == RECOMMENDED_CHAT_MODEL
