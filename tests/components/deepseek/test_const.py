"""Test constants for DeepSeek integration."""
from __future__ import annotations

from custom_components.deepseek.const import (
    CONF_API_KEY,
    CONF_BASE_URL,
    CONF_MAX_TOKENS,
    CONF_MODEL,
    CONF_REASONING,
    CONF_TEMPERATURE,
    DEFAULT_BASE_URL,
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL,
    DEFAULT_REASONING,
    DEFAULT_TEMPERATURE,
    DOMAIN,
    MODELS,
)


def test_constants() -> None:
    """Test that constants are correctly defined."""
    
    # Domain
    assert DOMAIN == "deepseek"
    
    # Configuration keys
    assert CONF_API_KEY == "api_key"
    assert CONF_MODEL == "model"
    assert CONF_BASE_URL == "base_url"
    assert CONF_MAX_TOKENS == "max_tokens"
    assert CONF_TEMPERATURE == "temperature"
    assert CONF_REASONING == "show_reasoning"
    
    # Default values
    assert DEFAULT_MODEL == "deepseek-chat"
    assert DEFAULT_BASE_URL == "https://api.deepseek.com"
    assert DEFAULT_MAX_TOKENS == 2048
    assert DEFAULT_TEMPERATURE == 0.7
    assert DEFAULT_REASONING is False
    
    # Available models
    assert isinstance(MODELS, list)
    assert len(MODELS) >= 3
    assert "deepseek-chat" in MODELS
    assert "deepseek-reasoner" in MODELS
    assert "deepseek-coder" in MODELS
    
    # Verify model names are strings
    for model in MODELS:
        assert isinstance(model, str)
        assert model.startswith("deepseek-")