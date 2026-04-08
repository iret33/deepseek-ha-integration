"""Fixtures for DeepSeek tests."""
from __future__ import annotations

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.deepseek.const import DOMAIN


@pytest.fixture(autouse=True)
async def _setup_ha_core(hass: HomeAssistant) -> None:
    """Set up the homeassistant core component so conversation can load."""
    await async_setup_component(hass, "homeassistant", {})
    await async_setup_component(hass, "conversation", {})


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """A fully-populated config entry for DeepSeek."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="DeepSeek",
        data={"api_key": "sk-test", "base_url": "https://api.deepseek.com"},
        options={"recommended": True, "prompt": "You are a helpful assistant."},
    )


@pytest.fixture
async def mock_openai_client() -> AsyncGenerator[AsyncMock, None]:
    """Patch openai.AsyncOpenAI so tests never hit the network."""
    client = MagicMock()
    client.with_options = MagicMock(return_value=client)
    client.models.list = AsyncMock(return_value=MagicMock(data=[]))
    client.chat.completions.create = AsyncMock()
    with patch("openai.AsyncOpenAI", return_value=client):
        yield client
