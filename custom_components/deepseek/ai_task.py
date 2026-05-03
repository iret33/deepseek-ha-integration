"""AI Task support for DeepSeek."""

from __future__ import annotations

from json import JSONDecodeError
import logging

from homeassistant.components import ai_task, conversation
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util.json import json_loads

from . import DeepSeekConfigEntry
from .const import CONF_CHAT_MODEL, DOMAIN, RECOMMENDED_CHAT_MODEL
from .conversation import run_chat_loop

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: DeepSeekConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the DeepSeek AI Task entity."""
    async_add_entities([DeepSeekTaskEntity(config_entry)])


class DeepSeekTaskEntity(ai_task.AITaskEntity):
    """DeepSeek AI Task entity — exposes generate_data to automations."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_supported_features = ai_task.AITaskEntityFeature.GENERATE_DATA

    def __init__(self, entry: DeepSeekConfigEntry) -> None:
        """Initialise the entity, sharing the device with the conversation entity."""
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_ai_task"
        self._attr_device_info = dr.DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="DeepSeek",
            model=entry.options.get(CONF_CHAT_MODEL, RECOMMENDED_CHAT_MODEL),
            entry_type=dr.DeviceEntryType.SERVICE,
        )

    async def _async_generate_data(
        self,
        task: ai_task.GenDataTask,
        chat_log: conversation.ChatLog,
    ) -> ai_task.GenDataTaskResult:
        """Run a generate-data task; return text or parsed JSON."""
        await run_chat_loop(
            client=self.entry.runtime_data,
            options=self.entry.options,
            chat_log=chat_log,
            agent_id=self.entity_id,
            force_json=task.structure is not None,
        )

        if not isinstance(chat_log.content[-1], conversation.AssistantContent):
            raise HomeAssistantError(
                "Last content in chat log is not an AssistantContent"
            )

        text = chat_log.content[-1].content or ""

        if task.structure is None:
            return ai_task.GenDataTaskResult(
                conversation_id=chat_log.conversation_id,
                data=text,
            )

        # Structured task — DeepSeek returned JSON because we set
        # response_format=json_object. Parse it; raise a clear error if it
        # somehow isn't valid JSON so the automation surfaces the failure.
        try:
            data = json_loads(text)
        except JSONDecodeError as err:
            _LOGGER.error(
                "Failed to parse DeepSeek JSON response: %s. Response: %s",
                err,
                text,
            )
            raise HomeAssistantError(
                "DeepSeek returned a non-JSON response for a structured task"
            ) from err

        return ai_task.GenDataTaskResult(
            conversation_id=chat_log.conversation_id,
            data=data,
        )
