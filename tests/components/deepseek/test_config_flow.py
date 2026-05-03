"""Test the DeepSeek config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, Mock

import httpx
import openai
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant import config_entries
from homeassistant.const import CONF_LLM_HASS_API
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.deepseek.const import (
    CONF_CHAT_MODEL,
    DOMAIN,
    RECOMMENDED_CHAT_MODEL,
)


async def test_user_flow_success(
    hass: HomeAssistant, mock_openai_client: AsyncMock
) -> None:
    """User provides API key + model -> entry created with options pre-filled."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "api_key": "sk-valid",
            CONF_CHAT_MODEL: RECOMMENDED_CHAT_MODEL,
            "base_url": "https://api.deepseek.com",
        },
    )
    await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "DeepSeek"
    assert result2["data"]["api_key"] == "sk-valid"
    # Model is captured into options at install so it can be edited later.
    assert result2["options"][CONF_CHAT_MODEL] == RECOMMENDED_CHAT_MODEL


def _auth_error() -> openai.AuthenticationError:
    response = Mock(spec=httpx.Response)
    response.request = Mock(spec=httpx.Request)
    response.status_code = 401
    response.headers = {}
    return openai.AuthenticationError("bad", response=response, body=None)


def _conn_error() -> openai.APIConnectionError:
    return openai.APIConnectionError(request=Mock(spec=httpx.Request))


@pytest.mark.parametrize(
    ("exc_factory", "expected_error"),
    [
        (_auth_error, "invalid_auth"),
        (_conn_error, "cannot_connect"),
        (lambda: ValueError("boom"), "unknown"),
    ],
)
async def test_user_flow_errors(
    hass: HomeAssistant,
    mock_openai_client: AsyncMock,
    exc_factory,
    expected_error: str,
) -> None:
    """Invalid inputs surface the right error keys."""
    mock_openai_client.models.list.side_effect = exc_factory()

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"api_key": "sk-bad", CONF_CHAT_MODEL: RECOMMENDED_CHAT_MODEL},
    )

    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"] == {"base": expected_error}


async def test_options_flow_save(
    hass: HomeAssistant,
    mock_openai_client: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Options flow accepts model + tuning parameters in a single screen."""
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_CHAT_MODEL: "deepseek-v4-pro",
            "prompt": "You are a helpful assistant.",
            CONF_LLM_HASS_API: "none",
            "max_tokens": 1024,
            "temperature": 0.5,
            "top_p": 0.9,
        },
    )
    assert result2["type"] is FlowResultType.CREATE_ENTRY
    # The "none" sentinel is stripped so HA stores the absence of an LLM API.
    assert CONF_LLM_HASS_API not in result2["data"]
    assert result2["data"][CONF_CHAT_MODEL] == "deepseek-v4-pro"
    assert result2["data"]["temperature"] == 0.5
