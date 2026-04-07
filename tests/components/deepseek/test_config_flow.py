"""Test the DeepSeek config flow."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant import config_entries
from custom_components.deepseek.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from .conftest import mock_deepseek_client

pytestmark = pytest.mark.usefixtures("mock_setup_entry")


async def test_form(hass: HomeAssistant, mock_deepseek_client) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {}

    # Test valid input
    with patch(
        "custom_components.deepseek.config_flow.validate_input",
        return_value={"title": "DeepSeek", "models": ["deepseek-chat"]},
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "api_key": "test-api-key",
                "name": "DeepSeek",
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] == FlowResultType.FORM
    assert result2["step_id"] == "options"


async def test_form_invalid_auth(hass: HomeAssistant) -> None:
    """Test we handle invalid auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.deepseek.config_flow.validate_input",
        side_effect=config_entries.ConfigEntryAuthFailed,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "api_key": "invalid-key",
                "name": "DeepSeek",
            },
        )

    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {"base": "invalid_auth"}


async def test_form_cannot_connect(hass: HomeAssistant) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.deepseek.config_flow.validate_input",
        side_effect=config_entries.ConfigEntryNotReady,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "api_key": "test-api-key",
                "name": "DeepSeek",
            },
        )

    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_form_unknown_error(hass: HomeAssistant) -> None:
    """Test we handle unknown errors."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.deepseek.config_flow.validate_input",
        side_effect=Exception,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "api_key": "test-api-key",
                "name": "DeepSeek",
            },
        )

    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {"base": "unknown"}


async def test_options_flow(hass: HomeAssistant) -> None:
    """Test options flow."""
    # Create a mock config entry
    entry = config_entries.ConfigEntry(
        version=1,
        domain=DOMAIN,
        title="DeepSeek",
        data={
            "api_key": "test-api-key",
            "name": "DeepSeek",
        },
        source="user",
        options={},
        entry_id="test",
    )

    # Test options flow
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "init"

    # Update options
    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "model": "deepseek-chat",
            "max_tokens": 2048,
            "temperature": 0.7,
            "show_reasoning": False,
        },
    )
    
    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert entry.options == {
        "model": "deepseek-chat",
        "max_tokens": 2048,
        "temperature": 0.7,
        "show_reasoning": False,
    }


async def test_reauth_flow(hass: HomeAssistant) -> None:
    """Test reauthentication flow."""
    # Create a mock config entry that needs reauth
    entry = config_entries.ConfigEntry(
        version=1,
        domain=DOMAIN,
        title="DeepSeek",
        data={
            "api_key": "old-key",
            "name": "DeepSeek",
        },
        source="user",
        options={},
        entry_id="test",
    )

    # Start reauth flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_REAUTH, "entry_id": entry.entry_id},
        data=entry.data,
    )
    
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    # Update with new API key
    with patch(
        "custom_components.deepseek.config_flow.validate_input",
        return_value={"title": "DeepSeek", "models": ["deepseek-chat"]},
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"api_key": "new-api-key"},
        )
    
    assert result2["type"] == FlowResultType.ABORT
    assert result2["reason"] == "reauth_successful"