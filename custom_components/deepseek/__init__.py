"""The DeepSeek integration."""

from __future__ import annotations

import logging

import openai

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.httpx_client import get_async_client
from homeassistant.helpers.typing import ConfigType

from .const import CONF_BASE_URL, DEFAULT_BASE_URL, DOMAIN
from .services import async_setup_services, async_unload_services

_LOGGER = logging.getLogger(__name__)

PLATFORMS: tuple[Platform, ...] = (Platform.AI_TASK, Platform.CONVERSATION)
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

type DeepSeekConfigEntry = ConfigEntry[openai.AsyncOpenAI]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the DeepSeek integration (no YAML)."""
    async_setup_services(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: DeepSeekConfigEntry) -> bool:
    """Set up DeepSeek from a config entry."""
    client = openai.AsyncOpenAI(
        api_key=entry.data[CONF_API_KEY],
        base_url=entry.data.get(CONF_BASE_URL, DEFAULT_BASE_URL),
        http_client=get_async_client(hass),
    )

    try:
        await client.with_options(timeout=10.0).models.list()
    except openai.AuthenticationError as err:
        # Wrong / revoked API key — prompt the user to reconfigure rather
        # than silently failing the integration.
        raise ConfigEntryAuthFailed("Invalid DeepSeek API key") from err
    except openai.OpenAIError as err:
        # Transient network / upstream issue — let HA retry the setup.
        raise ConfigEntryNotReady(str(err)) from err

    entry.runtime_data = client

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: DeepSeekConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        async_unload_services(hass)
    return unloaded


async def _async_update_listener(
    hass: HomeAssistant, entry: DeepSeekConfigEntry
) -> None:
    """Reload on options change."""
    await hass.config_entries.async_reload(entry.entry_id)
