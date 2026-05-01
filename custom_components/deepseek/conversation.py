"""Conversation support for DeepSeek (chat-completions API)."""

from __future__ import annotations

from collections.abc import Callable, Iterable
import json
from typing import Any, Literal

import openai
from openai._types import NOT_GIVEN
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessageParam,
    ChatCompletionMessageToolCallParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionToolParam,
    ChatCompletionUserMessageParam,
)
from openai.types.chat.chat_completion_message_tool_call_param import Function
from openai.types.shared_params import FunctionDefinition
from voluptuous_openapi import convert

from homeassistant.components import conversation
from homeassistant.const import CONF_LLM_HASS_API, MATCH_ALL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr, llm
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DeepSeekConfigEntry
from .const import (
    CONF_CHAT_MODEL,
    CONF_MAX_TOKENS,
    CONF_PROMPT,
    CONF_TEMPERATURE,
    CONF_TOP_P,
    DOMAIN,
    LOGGER,
    RECOMMENDED_CHAT_MODEL,
    RECOMMENDED_MAX_TOKENS,
    RECOMMENDED_TEMPERATURE,
    RECOMMENDED_TOP_P,
)

# Cap loops where the model keeps issuing tool calls — prevents infinite
# back-and-forth on a misbehaving plan.
MAX_TOOL_ITERATIONS = 10


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: DeepSeekConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the DeepSeek conversation entity."""
    async_add_entities([DeepSeekConversationEntity(config_entry)])


def _format_tool(
    tool: llm.Tool, custom_serializer: Callable[[Any], Any] | None
) -> ChatCompletionToolParam:
    """Convert an HA LLM tool to the OpenAI/DeepSeek function-tool schema."""
    spec = FunctionDefinition(
        name=tool.name,
        parameters=convert(tool.parameters, custom_serializer=custom_serializer),
    )
    if tool.description:
        spec["description"] = tool.description
    return ChatCompletionToolParam(type="function", function=spec)


def _content_to_messages(
    contents: Iterable[conversation.Content],
) -> list[ChatCompletionMessageParam]:
    """Translate HA chat-log content into chat-completions messages."""
    out: list[ChatCompletionMessageParam] = []
    for c in contents:
        if isinstance(c, conversation.SystemContent):
            out.append(
                ChatCompletionSystemMessageParam(role="system", content=c.content)
            )
        elif isinstance(c, conversation.UserContent):
            out.append(ChatCompletionUserMessageParam(role="user", content=c.content))
        elif isinstance(c, conversation.AssistantContent):
            param = ChatCompletionAssistantMessageParam(
                role="assistant", content=c.content or ""
            )
            if c.tool_calls:
                param["tool_calls"] = [
                    ChatCompletionMessageToolCallParam(
                        id=tc.id,
                        type="function",
                        function=Function(
                            name=tc.tool_name,
                            arguments=json.dumps(tc.tool_args),
                        ),
                    )
                    for tc in c.tool_calls
                    if not tc.external
                ]
            out.append(param)
        elif isinstance(c, conversation.ToolResultContent):
            out.append(
                ChatCompletionToolMessageParam(
                    role="tool",
                    tool_call_id=c.tool_call_id,
                    content=json.dumps(c.tool_result),
                )
            )
    return out


class DeepSeekConversationEntity(
    conversation.ConversationEntity, conversation.AbstractConversationAgent
):
    """DeepSeek conversation agent (chat-completions API)."""

    _attr_has_entity_name = True
    _attr_name = None

    def __init__(self, entry: DeepSeekConfigEntry) -> None:
        """Initialise the agent."""
        self.entry = entry
        self._attr_unique_id = entry.entry_id
        self._attr_device_info = dr.DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="DeepSeek",
            model=entry.options.get(CONF_CHAT_MODEL, RECOMMENDED_CHAT_MODEL),
            entry_type=dr.DeviceEntryType.SERVICE,
        )
        if entry.options.get(CONF_LLM_HASS_API):
            self._attr_supported_features = (
                conversation.ConversationEntityFeature.CONTROL
            )

    @property
    def supported_languages(self) -> list[str] | Literal["*"]:
        """Return a list of supported languages."""
        return MATCH_ALL

    async def async_added_to_hass(self) -> None:
        """Register as the conversation agent for this entry."""
        await super().async_added_to_hass()
        conversation.async_set_agent(self.hass, self.entry, self)

    async def async_will_remove_from_hass(self) -> None:
        """Unregister the conversation agent."""
        conversation.async_unset_agent(self.hass, self.entry)
        await super().async_will_remove_from_hass()

    async def _async_handle_message(
        self,
        user_input: conversation.ConversationInput,
        chat_log: conversation.ChatLog,
    ) -> conversation.ConversationResult:
        """Handle one user turn against the chat log."""
        options = self.entry.options
        try:
            await chat_log.async_provide_llm_data(
                user_input.as_llm_context(DOMAIN),
                options.get(CONF_LLM_HASS_API),
                options.get(CONF_PROMPT),
                user_input.extra_system_prompt,
            )
        except conversation.ConverseError as err:
            return err.as_conversation_result()

        await self._async_run_chat_loop(chat_log)
        return conversation.async_get_result_from_chat_log(user_input, chat_log)

    async def _async_run_chat_loop(self, chat_log: conversation.ChatLog) -> None:
        """Run chat-completion calls until the model stops requesting tools."""
        client: openai.AsyncOpenAI = self.entry.runtime_data
        options = self.entry.options
        agent_id = self.entity_id

        tools: list[ChatCompletionToolParam] | None = None
        if chat_log.llm_api:
            tools = [
                _format_tool(t, chat_log.llm_api.custom_serializer)
                for t in chat_log.llm_api.tools
            ]

        for _ in range(MAX_TOOL_ITERATIONS):
            messages = _content_to_messages(chat_log.content)

            try:
                result = await client.chat.completions.create(
                    model=options.get(CONF_CHAT_MODEL, RECOMMENDED_CHAT_MODEL),
                    messages=messages,
                    tools=tools or NOT_GIVEN,
                    max_tokens=int(
                        options.get(CONF_MAX_TOKENS, RECOMMENDED_MAX_TOKENS)
                    ),
                    top_p=float(options.get(CONF_TOP_P, RECOMMENDED_TOP_P)),
                    temperature=float(
                        options.get(CONF_TEMPERATURE, RECOMMENDED_TEMPERATURE)
                    ),
                    user=chat_log.conversation_id,
                )
            except openai.OpenAIError as err:
                LOGGER.error("Error talking to DeepSeek: %s", err)
                raise HomeAssistantError(f"DeepSeek API error: {err}") from err

            response = result.choices[0].message
            tool_inputs: list[llm.ToolInput] = []
            if response.tool_calls:
                for call in response.tool_calls:
                    try:
                        args = json.loads(call.function.arguments or "{}")
                    except json.JSONDecodeError:
                        args = {}
                    tool_inputs.append(
                        llm.ToolInput(
                            id=call.id,
                            tool_name=call.function.name,
                            tool_args=args,
                        )
                    )

            assistant_content = conversation.AssistantContent(
                agent_id=agent_id,
                content=response.content or None,
                tool_calls=tool_inputs or None,
            )

            if not tool_inputs:
                chat_log.async_add_assistant_content_without_tools(assistant_content)
                return

            # `async_add_assistant_content` is an async generator that
            # executes the requested tool calls and yields each result.
            async for _ in chat_log.async_add_assistant_content(assistant_content):
                pass

            if not chat_log.unresponded_tool_results:
                return
