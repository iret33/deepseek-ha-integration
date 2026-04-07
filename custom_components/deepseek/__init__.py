"""The DeepSeek integration."""
from __future__ import annotations

import logging
from typing import Any

from openai import AsyncOpenAI
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, Platform
from homeassistant.core import HomeAssistant
from homeassistant.components import conversation
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_BASE_URL,
    CONF_MAX_TOKENS,
    CONF_MODEL,
    CONF_TEMPERATURE,
    CONF_REASONING,
    DEFAULT_BASE_URL,
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    DEFAULT_REASONING,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = []

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_API_KEY): cv.string,
                vol.Optional(CONF_MODEL, default=DEFAULT_MODEL): cv.string,
                vol.Optional(CONF_BASE_URL, default=DEFAULT_BASE_URL): cv.string,
                vol.Optional(CONF_MAX_TOKENS, default=DEFAULT_MAX_TOKENS): cv.positive_int,
                vol.Optional(CONF_TEMPERATURE, default=DEFAULT_TEMPERATURE): vol.All(
                    vol.Coerce(float), vol.Range(min=0.0, max=2.0)
                ),
                vol.Optional(CONF_REASONING, default=DEFAULT_REASONING): cv.boolean,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the DeepSeek integration."""
    if DOMAIN not in config:
        return True
    
    _LOGGER.info("Setting up DeepSeek integration")
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up DeepSeek from a config entry."""
    
    try:
        _LOGGER.debug("Setting up DeepSeek integration for entry: %s", entry.entry_id)
        
        # Create OpenAI client with DeepSeek configuration
        client = AsyncOpenAI(
            api_key=entry.data[CONF_API_KEY],
            base_url=entry.data.get(CONF_BASE_URL, DEFAULT_BASE_URL),
        )
        
        # Test the connection by fetching available models
        _LOGGER.debug("Testing DeepSeek API connection...")
        try:
            models = await client.models.list()
            available_models = [model.id for model in models.data]
            _LOGGER.debug("Available models: %s", available_models)
            
            # Check if configured model is available
            configured_model = entry.data.get(CONF_MODEL, DEFAULT_MODEL)
            if configured_model not in available_models:
                _LOGGER.warning(
                    "Configured model '%s' not in available models. Available: %s",
                    configured_model, available_models
                )
        except Exception as err:
            _LOGGER.warning("Could not fetch models list: %s", err)
        
        # Store client and config in hass data
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][entry.entry_id] = {
            "client": client,
            "config": entry.data,
            "options": entry.options,
        }
        
        # Register conversation agent
        from .conversation import DeepSeekConversationEntity
        conversation_entity = DeepSeekConversationEntity(entry)
        
        conversation.async_set_agent(
            hass,
            entry,
            conversation_entity,
        )
        
        # Store conversation entity
        hass.data[DOMAIN][entry.entry_id]["conversation_entity"] = conversation_entity
        
        # Register services
        await _register_services(hass, entry)
        
        _LOGGER.info("DeepSeek integration setup complete for '%s'", entry.title)
        return True
        
    except Exception as err:
        _LOGGER.error("Failed to set up DeepSeek integration: %s", err, exc_info=True)
        return False


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unregister conversation agent
    conversation.async_unset_agent(hass, entry)
    
    # Remove from hass data
    hass.data[DOMAIN].pop(entry.entry_id, None)
    
    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options."""
    await hass.config_entries.async_reload(entry.entry_id)


async def _register_services(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Register services for the DeepSeek integration."""
    
    async def handle_chat(call):
        """Handle chat service call."""
        from .conversation import DeepSeekConversationEntity
        
        entity_id = f"{DOMAIN}.{entry.entry_id}"
        entity = hass.data[DOMAIN][entry.entry_id].get("conversation_entity")
        
        if not entity:
            # Create entity if it doesn't exist
            entity = DeepSeekConversationEntity(hass, entry)
            hass.data[DOMAIN][entry.entry_id]["conversation_entity"] = entity
        
        message = call.data.get("message", "")
        conversation_id = call.data.get("conversation_id")
        
        if not message:
            _LOGGER.error("No message provided for chat service")
            return
        
        # Call the conversation entity
        result = await entity.async_process(
            text=message,
            conversation_id=conversation_id,
            context=call.context,
        )
        
        # Store response in call data
        call.data[ATTR_RESPONSE] = result.response
        call.data[ATTR_CONVERSATION_ID] = result.conversation_id
        call.data[ATTR_TOKENS_USED] = getattr(result, "tokens_used", 0)
        
        if hasattr(result, "reasoning"):
            call.data[ATTR_REASONING] = result.reasoning
    
    async def handle_summarize(call):
        """Handle summarize service call."""
        client = hass.data[DOMAIN][entry.entry_id]["client"]
        config = hass.data[DOMAIN][entry.entry_id]["config"]
        
        text = call.data.get("text", "")
        max_length = call.data.get("max_length", 100)
        
        if not text:
            _LOGGER.error("No text provided for summarize service")
            return
        
        prompt = f"Please summarize the following text in {max_length} words or less:\n\n{text}"
        
        try:
            response = await client.chat.completions.create(
                model=config.get(CONF_MODEL, DEFAULT_MODEL),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=config.get(CONF_MAX_TOKENS, DEFAULT_MAX_TOKENS),
                temperature=config.get(CONF_TEMPERATURE, DEFAULT_TEMPERATURE),
            )
            
            summary = response.choices[0].message.content
            call.data[ATTR_RESPONSE] = summary
            call.data[ATTR_TOKENS_USED] = response.usage.total_tokens if response.usage else 0
            
        except Exception as err:
            _LOGGER.error("Error summarizing text: %s", err)
            call.data[ATTR_RESPONSE] = f"Error: {err}"
    
    async def handle_translate(call):
        """Handle translate service call."""
        client = hass.data[DOMAIN][entry.entry_id]["client"]
        config = hass.data[DOMAIN][entry.entry_id]["config"]
        
        text = call.data.get("text", "")
        target_language = call.data.get("target_language", "English")
        source_language = call.data.get("source_language", "auto")
        
        if not text:
            _LOGGER.error("No text provided for translate service")
            return
        
        prompt = f"Translate the following text from {source_language} to {target_language}:\n\n{text}"
        
        try:
            response = await client.chat.completions.create(
                model=config.get(CONF_MODEL, DEFAULT_MODEL),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=config.get(CONF_MAX_TOKENS, DEFAULT_MAX_TOKENS),
                temperature=config.get(CONF_TEMPERATURE, DEFAULT_TEMPERATURE),
            )
            
            translation = response.choices[0].message.content
            call.data[ATTR_RESPONSE] = translation
            call.data[ATTR_TOKENS_USED] = response.usage.total_tokens if response.usage else 0
            
        except Exception as err:
            _LOGGER.error("Error translating text: %s", err)
            call.data[ATTR_RESPONSE] = f"Error: {err}"
    
    # Register services
    hass.services.async_register(
        DOMAIN,
        "chat",
        handle_chat,
        schema=vol.Schema({
            vol.Required("message"): cv.string,
            vol.Optional("conversation_id"): cv.string,
        }),
    )
    
    hass.services.async_register(
        DOMAIN,
        "summarize",
        handle_summarize,
        schema=vol.Schema({
            vol.Required("text"): cv.string,
            vol.Optional("max_length", default=100): cv.positive_int,
        }),
    )
    
    hass.services.async_register(
        DOMAIN,
        "translate",
        handle_translate,
        schema=vol.Schema({
            vol.Required("text"): cv.string,
            vol.Required("target_language"): cv.string,
            vol.Optional("source_language", default="auto"): cv.string,
        }),
    )