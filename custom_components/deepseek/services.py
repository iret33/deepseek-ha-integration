"""DeepSeek services callable from automations, scripts, and other integrations."""

from __future__ import annotations

from typing import Any

import openai
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
)
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv

from .const import (
    CONF_CHAT_MODEL,
    CONF_MAX_TOKENS,
    CONF_TEMPERATURE,
    CONF_TOP_P,
    DOMAIN,
    LOGGER,
    MODELS,
    RECOMMENDED_CHAT_MODEL,
    RECOMMENDED_MAX_TOKENS,
    RECOMMENDED_TEMPERATURE,
    RECOMMENDED_TOP_P,
)

SERVICE_GENERATE = "generate"

ATTR_CONFIG_ENTRY = "config_entry"
ATTR_PROMPT = "prompt"
ATTR_SYSTEM_PROMPT = "system_prompt"
ATTR_MODEL = "model"
ATTR_MAX_TOKENS = "max_tokens"
ATTR_TEMPERATURE = "temperature"
ATTR_TOP_P = "top_p"


GENERATE_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_CONFIG_ENTRY): cv.string,
        vol.Required(ATTR_PROMPT): cv.string,
        vol.Optional(ATTR_SYSTEM_PROMPT): cv.string,
        vol.Optional(ATTR_MODEL): vol.Any(vol.In(MODELS), cv.string),
        vol.Optional(ATTR_MAX_TOKENS): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=8192)
        ),
        vol.Optional(ATTR_TEMPERATURE): vol.All(
            vol.Coerce(float), vol.Range(min=0, max=2)
        ),
        vol.Optional(ATTR_TOP_P): vol.All(vol.Coerce(float), vol.Range(min=0, max=1)),
    }
)


def _resolve_entry(hass: HomeAssistant, entry_id: str | None) -> ConfigEntry:
    """Pick the DeepSeek config entry to use for the service call."""
    loaded = [
        e
        for e in hass.config_entries.async_entries(DOMAIN)
        if e.runtime_data is not None
    ]
    if not loaded:
        raise ServiceValidationError(
            "DeepSeek is not configured. Add the integration first."
        )

    if entry_id is None:
        return loaded[0]

    for entry in loaded:
        if entry.entry_id == entry_id:
            return entry
    raise ServiceValidationError(
        f"No loaded DeepSeek config entry with id {entry_id!r}."
    )


async def _async_generate(call: ServiceCall) -> ServiceResponse:
    """Send a one-shot prompt to DeepSeek and return the reply."""
    hass = call.hass
    data = call.data

    entry = _resolve_entry(hass, data.get(ATTR_CONFIG_ENTRY))
    client: openai.AsyncOpenAI = entry.runtime_data
    options = entry.options

    messages: list[dict[str, Any]] = []
    if system := data.get(ATTR_SYSTEM_PROMPT):
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": data[ATTR_PROMPT]})

    model = data.get(ATTR_MODEL) or options.get(CONF_CHAT_MODEL, RECOMMENDED_CHAT_MODEL)

    try:
        result = await client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=int(
                data.get(ATTR_MAX_TOKENS)
                or options.get(CONF_MAX_TOKENS, RECOMMENDED_MAX_TOKENS)
            ),
            temperature=float(
                data[ATTR_TEMPERATURE]
                if ATTR_TEMPERATURE in data
                else options.get(CONF_TEMPERATURE, RECOMMENDED_TEMPERATURE)
            ),
            top_p=float(
                data[ATTR_TOP_P]
                if ATTR_TOP_P in data
                else options.get(CONF_TOP_P, RECOMMENDED_TOP_P)
            ),
        )
    except openai.OpenAIError as err:
        LOGGER.error("DeepSeek generate service failed: %s", err)
        raise HomeAssistantError(f"DeepSeek API error: {err}") from err

    choice = result.choices[0]
    response: ServiceResponse = {
        "text": choice.message.content or "",
        "model": result.model,
        "finish_reason": choice.finish_reason,
    }
    if result.usage is not None:
        response["usage"] = {
            "prompt_tokens": result.usage.prompt_tokens,
            "completion_tokens": result.usage.completion_tokens,
            "total_tokens": result.usage.total_tokens,
        }
    return response


def async_setup_services(hass: HomeAssistant) -> None:
    """Register DeepSeek services. Idempotent — safe to call repeatedly."""
    if hass.services.has_service(DOMAIN, SERVICE_GENERATE):
        return

    hass.services.async_register(
        DOMAIN,
        SERVICE_GENERATE,
        _async_generate,
        schema=GENERATE_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )


def async_unload_services(hass: HomeAssistant) -> None:
    """Remove DeepSeek services (called when the last entry unloads)."""
    if not hass.config_entries.async_entries(DOMAIN):
        hass.services.async_remove(DOMAIN, SERVICE_GENERATE)
