"""Test DeepSeek chat-log <-> chat-completions translation."""

from __future__ import annotations

import dataclasses
from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.components import conversation
from homeassistant.core import Context, HomeAssistant
from homeassistant.helpers import llm

# The Python 3.12 CI job resolves an HA core older than this integration
# supports (no chat log / thinking content); nothing here can run there.
if not hasattr(conversation, "AssistantContent") or "thinking_content" not in {
    f.name for f in dataclasses.fields(conversation.AssistantContent)
}:
    pytest.skip("Home Assistant core too old", allow_module_level=True)

from custom_components.deepseek.conversation import _content_to_messages


def test_external_tool_calls_are_kept() -> None:
    """Locally handled (external) tool calls stay paired with their results.

    Dropping them used to send `tool_calls: []`, which DeepSeek rejects
    with a 400 (issue #2).
    """
    messages = _content_to_messages(
        [
            conversation.UserContent(content="turn on the light"),
            conversation.AssistantContent(
                agent_id="conversation.deepseek",
                tool_calls=[
                    llm.ToolInput(
                        id="call_1",
                        tool_name="HassTurnOn",
                        tool_args={"name": "light"},
                        external=True,
                    )
                ],
            ),
            conversation.ToolResultContent(
                agent_id="conversation.deepseek",
                tool_call_id="call_1",
                tool_name="HassTurnOn",
                tool_result={"success": True},
            ),
        ]
    )

    assistant = messages[1]
    assert assistant["role"] == "assistant"
    assert [tc["id"] for tc in assistant["tool_calls"]] == ["call_1"]
    assert messages[2]["tool_call_id"] == "call_1"


def test_no_tool_calls_key_without_calls() -> None:
    """Plain replies never carry a tool_calls key."""
    messages = _content_to_messages(
        [conversation.AssistantContent(agent_id="a", content="hi")]
    )
    assert "tool_calls" not in messages[0]


def test_reasoning_is_passed_back() -> None:
    """Stored thinking content is sent back as reasoning_content."""
    messages = _content_to_messages(
        [
            conversation.AssistantContent(
                agent_id="a", content="done", thinking_content="let me think"
            )
        ]
    )
    assert messages[0]["reasoning_content"] == "let me think"


async def test_conversation_round_trips_reasoning(
    hass: HomeAssistant,
    mock_openai_client: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """A thinking-mode reply's reasoning is re-sent on the next turn."""
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry,
        options={**mock_config_entry.options, "reasoning_effort": "high"},
    )
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    message = MagicMock(content="Hello!", tool_calls=None, reasoning_content="hmm")
    mock_openai_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=message)]
    )

    agent_id = "conversation.deepseek"
    first = await conversation.async_converse(
        hass, "hi", None, Context(), agent_id=agent_id
    )
    await conversation.async_converse(
        hass, "again", first.conversation_id, Context(), agent_id=agent_id
    )

    call = mock_openai_client.chat.completions.create.call_args_list[-1].kwargs
    assert call["model"] == "deepseek-v4-flash"
    assert call["reasoning_effort"] == "high"
    assert call["extra_body"] == {"thinking": {"type": "enabled"}}
    assert "temperature" not in call
    assistant = [m for m in call["messages"] if m["role"] == "assistant"]
    assert assistant[0]["reasoning_content"] == "hmm"
