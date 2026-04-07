"""Base entity for DeepSeek."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity import Entity

from .const import CONF_MODEL, DEFAULT_MODEL, DOMAIN


class DeepSeekBaseEntity(Entity):
    """Base entity for DeepSeek integration."""

    _attr_has_entity_name = True
    _attr_name: str | None = None

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize the entity."""
        self.entry = entry
        self._attr_unique_id = entry.entry_id
        self._attr_device_info = dr.DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="DeepSeek",
            model=entry.data.get(CONF_MODEL, DEFAULT_MODEL),
            entry_type=dr.DeviceEntryType.SERVICE,
        )
