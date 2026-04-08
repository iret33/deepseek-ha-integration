"""Test the DeepSeek config flow."""
from __future__ import annotations

from unittest.mock import AsyncMock, Mock

import httpx
import openai
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.deepseek.const import DOMAIN


async def test_user_flow_success(
    hass: HomeAssistant, mock_openai_client: AsyncMock
) -> None:
    """User provides a valid API key -> entry created."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"api_key": "sk-valid", "base_url": "https://api.deepseek.com"},
    )
    await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "DeepSeek"
    assert result2["data"]["api_key"] == "sk-valid"
    assert result2["options"]["recommended"] is True


def _auth_error() -> openai.AuthenticationError:
    response = Mock(spec=httpx.Response)
    response.request = Mock(spec=httpx.Request)
    response.status_code = 401
    response.headers = {}
    return openai.AuthenticationError("bad key", response=response, body=None)


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
        result["flow_id"], {"api_key": "sk-bad"}
    )

    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"] == {"base": expected_error}


async def test_options_flow_recommended(
    hass: HomeAssistant,
    mock_openai_client: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Options flow in recommended mode saves cleanly."""
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            "prompt": "You are a helpful assistant.",
            "llm_hass_api": "none",
            "recommended": True,
        },
    )
    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert "llm_hass_api" not in result2["data"]
