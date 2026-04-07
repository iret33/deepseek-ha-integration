"""Diagnostics support for DeepSeek."""
from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_API_KEY, DOMAIN

TO_REDACT = {CONF_API_KEY}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    
    data = {
        "entry": {
            "title": entry.title,
            "data": async_redact_data(entry.data, TO_REDACT),
            "options": entry.options,
            "unique_id": entry.unique_id,
            "entry_id": entry.entry_id,
        },
        "integration_data": hass.data.get(DOMAIN, {}).get(entry.entry_id, {}),
    }
    
    # Add conversation history stats if available
    conversation_entity = hass.data.get(DOMAIN, {}).get(entry.entry_id, {}).get("conversation_entity")
    if conversation_entity and hasattr(conversation_entity, "history"):
        data["conversation_stats"] = {
            "active_conversations": len(conversation_entity.history),
            "total_messages": sum(len(msgs) for msgs in conversation_entity.history.values()),
        }
    
    return data