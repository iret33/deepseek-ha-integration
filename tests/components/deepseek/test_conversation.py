"""Test the DeepSeek conversation integration."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.components import conversation
from homeassistant.components.deepseek.const import DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import intent

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
        },
        source="user",
        options={
            "model": "deepseek-chat",
            "max_tokens": 2048,
            "temperature": 0.7,
            "show_reasoning": False,
        },
        entry_id="test",
    )


async def test_conversation_entity(
    hass: HomeAssistant, config_entry: ConfigEntry, mock_deepseek_client
) -> None:
    """Test conversation entity setup."""
    
    # Mock the OpenAI API response
    mock_response = AsyncMock()
    mock_response.choices = [AsyncMock(message=AsyncMock(content="Hello! How can I help you?"))]
    mock_response.usage = AsyncMock(total_tokens=10)
    mock_deepseek_client.chat.completions.create.return_value = mock_response
    
    # Create conversation entity
    from custom_components.deepseek.conversation import DeepSeekConversationEntity
    entity = DeepSeekConversationEntity(config_entry)
    
    # Test conversation processing
    result = await entity.async_process(
        text="Hello",
        conversation_id="test-conversation",
    )
    
    assert result.response == "Hello! How can I help you?"
    assert result.conversation_id == "test-conversation"
    assert hasattr(result, "tokens_used")
    assert result.tokens_used == 10
    
    # Verify API was called with correct parameters
    mock_deepseek_client.chat.completions.create.assert_called_once()
    call_args = mock_deepseek_client.chat.completions.create.call_args
    assert call_args.kwargs["model"] == "deepseek-chat"
    assert call_args.kwargs["max_tokens"] == 2048
    assert call_args.kwargs["temperature"] == 0.7


async def test_conversation_with_reasoning(
    hass: HomeAssistant, config_entry: ConfigEntry, mock_deepseek_client
) -> None:
    """Test conversation with reasoning model."""
    
    # Update config to use reasoning model
    config_entry.options["model"] = "deepseek-reasoner"
    config_entry.options["show_reasoning"] = True
    
    # Mock response with reasoning
    mock_response = AsyncMock()
    mock_message = AsyncMock()
    mock_message.content = "The answer is 42"
    mock_message.reasoning_content = "Let me think... 40 + 2 = 42"
    mock_response.choices = [AsyncMock(message=mock_message)]
    mock_response.usage = AsyncMock(total_tokens=20)
    mock_deepseek_client.chat.completions.create.return_value = mock_response
    
    # Create conversation entity
    from custom_components.deepseek.conversation import DeepSeekConversationEntity
    entity = DeepSeekConversationEntity(config_entry)
    
    # Test conversation processing
    result = await entity.async_process(
        text="What is 40 + 2?",
        conversation_id="test-conversation",
    )
    
    assert result.response == "The answer is 42"
    assert hasattr(result, "reasoning")
    assert result.reasoning == "Let me think... 40 + 2 = 42"
    
    # Verify API was called with reasoning parameter
    mock_deepseek_client.chat.completions.create.assert_called_once()
    call_args = mock_deepseek_client.chat.completions.create.call_args
    assert call_args.kwargs["model"] == "deepseek-reasoner"
    assert "reasoning" in call_args.kwargs
    assert call_args.kwargs["reasoning"] is True


async def test_conversation_error_handling(
    hass: HomeAssistant, config_entry: ConfigEntry, mock_deepseek_client
) -> None:
    """Test conversation error handling."""
    
    # Mock API error
    mock_deepseek_client.chat.completions.create.side_effect = Exception("API Error")
    
    # Create conversation entity
    from custom_components.deepseek.conversation import DeepSeekConversationEntity
    entity = DeepSeekConversationEntity(config_entry)
    
    # Test conversation processing with error
    result = await entity.async_process(
        text="Hello",
        conversation_id="test-conversation",
    )
    
    # Should return error message
    assert "Sorry, I encountered an error" in result.response
    assert result.conversation_id == "test-conversation"


async def test_conversation_history(
    hass: HomeAssistant, config_entry: ConfigEntry, mock_deepseek_client
) -> None:
    """Test conversation history management."""
    
    # Mock responses
    mock_response = AsyncMock()
    mock_response.choices = [AsyncMock(message=AsyncMock(content="Response"))]
    mock_response.usage = AsyncMock(total_tokens=5)
    mock_deepseek_client.chat.completions.create.return_value = mock_response
    
    # Create conversation entity
    from custom_components.deepseek.conversation import DeepSeekConversationEntity
    entity = DeepSeekConversationEntity(config_entry)
    
    # Have multiple conversations
    conversation_id = "test-conversation"
    
    # First message
    result1 = await entity.async_process(
        text="First message",
        conversation_id=conversation_id,
    )
    
    # Second message (should have history)
    result2 = await entity.async_process(
        text="Second message",
        conversation_id=conversation_id,
    )
    
    # Verify API was called twice
    assert mock_deepseek_client.chat.completions.create.call_count == 2
    
    # Check that history was maintained
    call_args = mock_deepseek_client.chat.completions.create.call_args_list[1]
    messages = call_args.kwargs["messages"]
    assert len(messages) >= 3  # System + First user + First assistant + Second user


async def test_conversation_agent_registration(
    hass: HomeAssistant, config_entry: ConfigEntry
) -> None:
    """Test conversation agent registration."""
    
    with patch(
        "custom_components.deepseek.conversation.DeepSeekConversationEntity"
    ) as mock_entity_class:
        mock_entity = AsyncMock()
        mock_entity_class.return_value = mock_entity
        
        # Set up the integration
        from custom_components.deepseek import async_setup_entry
        await async_setup_entry(hass, config_entry)
        
        # Verify entity was created
        mock_entity_class.assert_called_once_with(config_entry)
        
        # Verify agent was registered
        assert conversation.async_get_agent(hass, config_entry.entry_id) is not None


async def test_conversation_supported_languages(
    hass: HomeAssistant, config_entry: ConfigEntry
) -> None:
    """Test conversation agent supports all languages."""
    
    from custom_components.deepseek.conversation import DeepSeekConversationEntity
    entity = DeepSeekConversationEntity(config_entry)
    
    # DeepSeek should support all languages
    assert entity.supported_languages == "*"