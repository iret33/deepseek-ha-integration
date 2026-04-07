"""Test the DeepSeek integration setup."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.components.deepseek.const import DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .conftest import mock_deepseek_client


@pytest.fixture
def config_entry() -> ConfigEntry:
    """Create a mock config entry."""
    return ConfigEntry(
        version=1,
        domain=DOMAIN,
        title="DeepSeek",
        data={
            "api_key": "test-api-key",
            "name": "DeepSeek",
            "model": "deepseek-chat",
            "max_tokens": 2048,
            "temperature": 0.7,
            "show_reasoning": False,
        },
        source="user",
        options={},
        entry_id="test",
    )


async def test_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, mock_deepseek_client
) -> None:
    """Test setting up the integration."""
    
    with patch(
        "custom_components.deepseek.async_setup_entry",
        return_value=True,
    ) as mock_setup:
        # Set up the integration
        from custom_components.deepseek import async_setup_entry
        result = await async_setup_entry(hass, config_entry)
        
        assert result is True
        mock_setup.assert_called_once_with(hass, config_entry)
        
        # Verify client was created
        assert DOMAIN in hass.data
        assert config_entry.entry_id in hass.data[DOMAIN]
        assert "client" in hass.data[DOMAIN][config_entry.entry_id]
        assert "config" in hass.data[DOMAIN][config_entry.entry_id]


async def test_unload_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, mock_deepseek_client
) -> None:
    """Test unloading the integration."""
    
    # First set up the integration
    from custom_components.deepseek import async_setup_entry
    await async_setup_entry(hass, config_entry)
    
    # Verify it's set up
    assert DOMAIN in hass.data
    assert config_entry.entry_id in hass.data[DOMAIN]
    
    # Now unload it
    from custom_components.deepseek import async_unload_entry
    result = await async_unload_entry(hass, config_entry)
    
    assert result is True
    assert config_entry.entry_id not in hass.data[DOMAIN]


async def test_services_registration(
    hass: HomeAssistant, config_entry: ConfigEntry, mock_deepseek_client
) -> None:
    """Test that services are registered."""
    
    # Set up the integration
    from custom_components.deepseek import async_setup_entry
    await async_setup_entry(hass, config_entry)
    
    # Verify services are registered
    assert hass.services.has_service(DOMAIN, "chat")
    assert hass.services.has_service(DOMAIN, "summarize")
    assert hass.services.has_service(DOMAIN, "translate")


async def test_chat_service(
    hass: HomeAssistant, config_entry: ConfigEntry, mock_deepseek_client
) -> None:
    """Test the chat service."""
    
    # Mock conversation response
    mock_response = AsyncMock()
    mock_response.choices = [AsyncMock(message=AsyncMock(content="Service response"))]
    mock_response.usage = AsyncMock(total_tokens=15)
    mock_deepseek_client.chat.completions.create.return_value = mock_response
    
    # Set up the integration
    from custom_components.deepseek import async_setup_entry
    await async_setup_entry(hass, config_entry)
    
    # Call the chat service
    await hass.services.async_call(
        DOMAIN,
        "chat",
        {
            "message": "Test message",
            "conversation_id": "service-test",
        },
        blocking=True,
    )
    
    # Verify API was called
    mock_deepseek_client.chat.completions.create.assert_called_once()


async def test_summarize_service(
    hass: HomeAssistant, config_entry: ConfigEntry, mock_deepseek_client
) -> None:
    """Test the summarize service."""
    
    # Mock API response
    mock_response = AsyncMock()
    mock_response.choices = [AsyncMock(message=AsyncMock(content="Summary text"))]
    mock_response.usage = AsyncMock(total_tokens=20)
    mock_deepseek_client.chat.completions.create.return_value = mock_response
    
    # Set up the integration
    from custom_components.deepseek import async_setup_entry
    await async_setup_entry(hass, config_entry)
    
    # Call the summarize service
    await hass.services.async_call(
        DOMAIN,
        "summarize",
        {
            "text": "Long text to summarize here...",
            "max_length": 100,
        },
        blocking=True,
    )
    
    # Verify API was called with correct prompt
    mock_deepseek_client.chat.completions.create.assert_called_once()
    call_args = mock_deepseek_client.chat.completions.create.call_args
    assert "summarize" in call_args.kwargs["messages"][0]["content"].lower()


async def test_translate_service(
    hass: HomeAssistant, config_entry: ConfigEntry, mock_deepseek_client
) -> None:
    """Test the translate service."""
    
    # Mock API response
    mock_response = AsyncMock()
    mock_response.choices = [AsyncMock(message=AsyncMock(content="Translated text"))]
    mock_response.usage = AsyncMock(total_tokens=25)
    mock_deepseek_client.chat.completions.create.return_value = mock_response
    
    # Set up the integration
    from custom_components.deepseek import async_setup_entry
    await async_setup_entry(hass, config_entry)
    
    # Call the translate service
    await hass.services.async_call(
        DOMAIN,
        "translate",
        {
            "text": "Hello world",
            "target_language": "Spanish",
            "source_language": "auto",
        },
        blocking=True,
    )
    
    # Verify API was called with correct prompt
    mock_deepseek_client.chat.completions.create.assert_called_once()
    call_args = mock_deepseek_client.chat.completions.create.call_args
    assert "translate" in call_args.kwargs["messages"][0]["content"].lower()
    assert "spanish" in call_args.kwargs["messages"][0]["content"].lower()


async def test_diagnostics(
    hass: HomeAssistant, config_entry: ConfigEntry, mock_deepseek_client
) -> None:
    """Test diagnostics."""
    
    # Set up the integration
    from custom_components.deepseek import async_setup_entry
    await async_setup_entry(hass, config_entry)
    
    # Get diagnostics
    from custom_components.deepseek.diagnostics import async_get_config_entry_diagnostics
    diagnostics = await async_get_config_entry_diagnostics(hass, config_entry)
    
    # Verify diagnostics structure
    assert "entry" in diagnostics
    assert "integration_data" in diagnostics
    assert diagnostics["entry"]["entry_id"] == config_entry.entry_id
    
    # API key should be redacted
    assert diagnostics["entry"]["data"]["api_key"] != "test-api-key"
    assert "***" in diagnostics["entry"]["data"]["api_key"]