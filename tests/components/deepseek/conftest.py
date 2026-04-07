"""Fixtures for DeepSeek tests."""
from __future__ import annotations

from unittest.mock import AsyncMock, Mock, patch

import pytest

from homeassistant.core import HomeAssistant


@pytest.fixture
def mock_deepseek_client():
    """Mock the DeepSeek API client."""
    with patch(
        "custom_components.deepseek.config_flow.AsyncOpenAI",
        autospec=True,
    ) as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        
        # Mock models list
        mock_models_response = Mock()
        mock_models_response.data = [
            Mock(id="deepseek-chat"),
            Mock(id="deepseek-reasoner"),
            Mock(id="deepseek-coder"),
        ]
        mock_client.models.list.return_value = mock_models_response
        
        yield mock_client


@pytest.fixture
def mock_setup_entry():
    """Mock setting up a config entry."""
    with patch(
        "custom_components.deepseek.async_setup_entry",
        return_value=True,
    ) as mock_setup:
        yield mock_setup