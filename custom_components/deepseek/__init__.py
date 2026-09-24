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

from .const import (
    CONF_BASE_URL,
    CONF_CHAT_MODEL,
    CONF_REASONING_EFFORT,
    DEFAULT_BASE_URL,
    DOMAIN,
    LEGACY_MODELS,
)
from .services import async_setup_services, async_unload_services

_LOGGER = logging.getLogger(__name__)

# AI Task was added in HA 2025.7. On older Home Assistant cores the
# Platform.AI_TASK enum value doesn't exist, so add it conditionally —
# users on older HA still get the conversation entity and the
# `deepseek.generate` service; the AI Task entity is opted in only
# when the host HA supports it.
PLATFORMS: tuple[Platform, ...] = (
    *((Platform.AI_TASK,) if hasattr(Platform, "AI_TASK") else ()),
    Platform.CONVERSATION,
)
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

type DeepSeekConfigEntry = ConfigEntry[openai.AsyncOpenAI]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the DeepSeek integration (no YAML)."""
    async_setup_services(hass)
    return True


async def async_migrate_entry(hass: HomeAssistant, entry: DeepSeekConfigEntry) -> bool:
    """Migrate old config entries.

    1.2: DeepSeek retired `deepseek-chat` / `deepseek-reasoner` on
    2026-07-24. Move them to `deepseek-v4-flash` with the matching
    thinking setting so existing installs keep working.
    """
    if entry.version > 1:
        # Downgraded from a future version we can't read.
        return False

    if entry.minor_version < 2:
        options = dict(entry.options)
        model = options.get(CONF_CHAT_MODEL)
        if model in LEGACY_MODELS:
            options[CONF_CHAT_MODEL], effort = LEGACY_MODELS[model]
            options.setdefault(CONF_REASONING_EFFORT, effort)
            _LOGGER.info(
                "Migrated retired DeepSeek model %s to %s (thinking: %s)",
                model,
                options[CONF_CHAT_MODEL],
                options[CONF_REASONING_EFFORT],
            )
        hass.config_entries.async_update_entry(
            entry, options=options, version=1, minor_version=2
        )

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
