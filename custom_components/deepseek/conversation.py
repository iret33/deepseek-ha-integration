"""Conversation support for DeepSeek."""

from __future__ import annotations

import logging
from typing import Literal

import openai

from homeassistant.components import conversation
from homeassistant.const import MATCH_ALL
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, intent
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import ulid

from . import DeepSeekConfigEntry
from .const import (
    CONF_MAX_TOKENS,
    CONF_MODEL,
    CONF_TEMPERATURE,
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are DeepSeek, a helpful AI assistant integrated with Home Assistant. "
    "Be concise, accurate, and friendly."
)
MAX_HISTORY = 10


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: DeepSeekConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the DeepSeek conversation entity."""
    async_add_entities([DeepSeekConversationEntity(config_entry)])


class DeepSeekConversationEntity(
    conversation.ConversationEntity, conversation.AbstractConversationAgent
):
    """DeepSeek conversation agent."""

    _attr_has_entity_name = True
    _attr_name = None

    def __init__(self, entry: DeepSeekConfigEntry) -> None:
        """Initialize the agent."""
        self.entry = entry
        self.history: dict[str, list[dict]] = {}
        self._attr_unique_id = entry.entry_id
        self._attr_device_info = dr.DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="DeepSeek",
            model=entry.options.get(
                CONF_MODEL, entry.data.get(CONF_MODEL, DEFAULT_MODEL)
            ),
            entry_type=dr.DeviceEntryType.SERVICE,
        )

    @property
    def supported_languages(self) -> list[str] | Literal["*"]:
        """Return a list of supported languages."""
        return MATCH_ALL

    async def async_added_to_hass(self) -> None:
        """When entity is added to Home Assistant."""
        await super().async_added_to_hass()
        conversation.async_set_agent(self.hass, self.entry, self)

    async def async_will_remove_from_hass(self) -> None:
        """When entity will be removed from Home Assistant."""
        conversation.async_unset_agent(self.hass, self.entry)
        await super().async_will_remove_from_hass()

    async def async_process(
        self, user_input: conversation.ConversationInput
    ) -> conversation.ConversationResult:
        """Process a sentence."""
        options = self.entry.options
        data = self.entry.data
        model = options.get(CONF_MODEL, data.get(CONF_MODEL, DEFAULT_MODEL))
        max_tokens = options.get(
            CONF_MAX_TOKENS, data.get(CONF_MAX_TOKENS, DEFAULT_MAX_TOKENS)
        )
        temperature = options.get(
            CONF_TEMPERATURE, data.get(CONF_TEMPERATURE, DEFAULT_TEMPERATURE)
        )

        if user_input.conversation_id and user_input.conversation_id in self.history:
            conversation_id = user_input.conversation_id
            messages = list(self.history[conversation_id])
        else:
            conversation_id = user_input.conversation_id or ulid.ulid_now()
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        messages.append({"role": "user", "content": user_input.text})

        intent_response = intent.IntentResponse(language=user_input.language)
        client: openai.AsyncOpenAI = self.entry.runtime_data

        try:
            result = await client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                user=conversation_id,
            )
        except openai.OpenAIError as err:
            _LOGGER.error("Error talking to DeepSeek: %s", err)
            intent_response.async_set_error(
                intent.IntentResponseErrorCode.UNKNOWN,
                "Sorry, I had a problem talking to DeepSeek",
            )
            return conversation.ConversationResult(
                response=intent_response, conversation_id=conversation_id
            )

        response_text = result.choices[0].message.content or ""
        messages.append({"role": "assistant", "content": response_text})

        # Trim history: keep system + last (MAX_HISTORY - 1) turns.
        if len(messages) > MAX_HISTORY:
            messages = [messages[0]] + messages[-(MAX_HISTORY - 1) :]
        self.history[conversation_id] = messages

        intent_response.async_set_speech(response_text)
        return conversation.ConversationResult(
            response=intent_response, conversation_id=conversation_id
        )
