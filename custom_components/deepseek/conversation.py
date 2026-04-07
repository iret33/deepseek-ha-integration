"""Conversation support for DeepSeek."""

from __future__ import annotations

import logging
from typing import Literal

from openai import AsyncOpenAI

from homeassistant.components import conversation
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, MATCH_ALL
from homeassistant.core import HomeAssistant
from homeassistant.helpers import intent
from homeassistant.util import ulid

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
)
from .entity import DeepSeekBaseEntity

_LOGGER = logging.getLogger(__name__)

# Conversation agent ID
AGENT_ID = "deepseek"


class DeepSeekConversationEntity(
    conversation.ConversationEntity,
    conversation.AbstractConversationAgent,
    DeepSeekBaseEntity,
):
    """DeepSeek conversation agent."""

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize the agent."""
        super().__init__(entry)
        self.history: dict[str, list[dict]] = {}

    @property
    def supported_languages(self) -> list[str] | Literal["*"]:
        """Return supported languages."""
        return MATCH_ALL

    @property
    def attribution(self) -> conversation.Attribution | None:
        """Return the attribution."""
        return conversation.Attribution(
            name="DeepSeek AI",
            url="https://www.deepseek.com",
        )

    async def async_added_to_hass(self) -> None:
        """When entity is added to Home Assistant."""
        await super().async_added_to_hass()
        conversation.async_set_agent(self.hass, self.entry, self)

    async def async_will_remove_from_hass(self) -> None:
        """When entity will be removed from Home Assistant."""
        conversation.async_unset_agent(self.hass, self.entry)
        await super().async_will_remove_from_hass()

    async def async_process(
        self,
        text: str,
        conversation_id: str | None = None,
        context: intent.TurnContext | None = None,
        language: str | None = None,
        agent_id: str | None = None,
        device_id: str | None = None,
    ) -> conversation.ConversationResult:
        """Process a sentence."""

        _LOGGER.debug("Processing conversation: %s", text)

        # Get or create conversation ID
        if conversation_id is None:
            conversation_id = ulid.ulid_now()

        # Get configuration
        config = self.entry.data
        options = self.entry.options

        model = options.get(CONF_MODEL, config.get(CONF_MODEL, DEFAULT_MODEL))
        base_url = options.get(
            CONF_BASE_URL, config.get(CONF_BASE_URL, DEFAULT_BASE_URL)
        )
        max_tokens = options.get(
            CONF_MAX_TOKENS, config.get(CONF_MAX_TOKENS, DEFAULT_MAX_TOKENS)
        )
        temperature = options.get(
            CONF_TEMPERATURE, config.get(CONF_TEMPERATURE, DEFAULT_TEMPERATURE)
        )
        show_reasoning = options.get(
            CONF_REASONING, config.get(CONF_REASONING, DEFAULT_REASONING)
        )
        api_key = config[CONF_API_KEY]

        # Get conversation history
        messages = self.history.get(conversation_id, [])

        # Add system message for Home Assistant context
        system_message = """You are DeepSeek AI integrated with Home Assistant. You can help users control their smart home, answer questions about their devices, and provide general assistance.

Home Assistant is an open-source home automation platform. Users can control lights, switches, thermostats, cameras, and other smart devices.

When users ask about their home:
1. If they want to control devices, suggest using voice commands or automations
2. If they want information, provide helpful guidance
3. If they need troubleshooting, offer step-by-step help

Be concise, helpful, and friendly. If you're not sure about something, say so."""

        if not messages:
            messages.append({"role": "system", "content": system_message})

        # Add user message
        messages.append({"role": "user", "content": text})

        # Create OpenAI client
        client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
        )

        try:
            # Prepare request parameters
            request_params = {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }

            # Add reasoning parameters for deepseek-reasoner
            if model == "deepseek-reasoner" and show_reasoning:
                request_params["reasoning"] = True

            # Make API call
            response = await client.chat.completions.create(**request_params)

            # Get response
            assistant_message = response.choices[0].message

            # Extract reasoning if available
            reasoning = None
            if hasattr(assistant_message, "reasoning_content"):
                reasoning = assistant_message.reasoning_content

            response_text = assistant_message.content

            # Add assistant message to history
            messages.append({"role": "assistant", "content": response_text})

            # Limit history to last 10 messages to avoid token limits
            if len(messages) > 10:
                # Keep system message and last 9 messages
                messages = [messages[0]] + messages[-9:]

            # Save updated history
            self.history[conversation_id] = messages

            # Create result
            result = conversation.ConversationResult(
                response=response_text,
                conversation_id=conversation_id,
            )

            # Add additional data
            result.response_type = "action_done"

            # Add tokens used
            if response.usage:
                setattr(result, "tokens_used", response.usage.total_tokens)

            # Add reasoning if available
            if reasoning:
                setattr(result, "reasoning", reasoning)
                _LOGGER.debug("Reasoning content: %s", reasoning)

            _LOGGER.debug(
                "Conversation processed. Tokens: %s, Model: %s",
                getattr(result, "tokens_used", "unknown"),
                model,
            )

            return result

        except Exception as err:
            _LOGGER.error("Error processing conversation: %s", err)

            # Return error response
            error_message = f"Sorry, I encountered an error: {err}"

            return conversation.ConversationResult(
                response=error_message,
                conversation_id=conversation_id,
            )

    async def async_prepare(
        self,
        hass: HomeAssistant,
        config: conversation.ConversationAgentConfig,
        supported_languages: list[str] | Literal["*"],
    ) -> conversation.PrepareResult:
        """Prepare the agent."""
        return conversation.PrepareResult(supported_languages=supported_languages)

    async def async_reload(
        self, hass: HomeAssistant, config: conversation.ConversationAgentConfig
    ) -> None:
        """Reload the agent."""
        # Nothing to reload
        pass

    async def async_get_debug_info(
        self, hass: HomeAssistant, config: conversation.ConversationAgentConfig
    ) -> dict:
        """Get debug information."""
        return {
            "agent_id": AGENT_ID,
            "entry_id": self.entry.entry_id,
            "model": self.entry.options.get(CONF_MODEL, DEFAULT_MODEL),
            "active_conversations": len(self.history),
            "total_messages": sum(len(msgs) for msgs in self.history.values()),
        }
