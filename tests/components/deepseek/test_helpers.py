"""Test request building for DeepSeek V4 models."""

from __future__ import annotations

from custom_components.deepseek.helpers import build_request_kwargs, resolve_model


def test_resolve_legacy_models() -> None:
    """Retired names map to V4, honouring an explicit effort."""
    assert resolve_model("deepseek-chat", None) == ("deepseek-v4-flash", "none")
    assert resolve_model("deepseek-reasoner", None) == ("deepseek-v4-flash", "high")
    assert resolve_model("deepseek-chat", "max") == ("deepseek-v4-flash", "max")
    assert resolve_model("deepseek-v4-pro", None) == ("deepseek-v4-pro", "none")
    assert resolve_model("custom-model", "high") == ("custom-model", "high")


def test_non_thinking_kwargs() -> None:
    """Thinking off: explicitly disabled, sampling params sent."""
    kwargs = build_request_kwargs("deepseek-v4-flash", "none", 512, 0.5, 0.9)
    assert kwargs == {
        "model": "deepseek-v4-flash",
        "max_tokens": 512,
        "extra_body": {"thinking": {"type": "disabled"}},
        "temperature": 0.5,
        "top_p": 0.9,
    }


def test_thinking_kwargs() -> None:
    """Thinking on: enabled with effort, sampling params omitted."""
    kwargs = build_request_kwargs("deepseek-reasoner", None, 512, 0.5, 0.9)
    assert kwargs == {
        "model": "deepseek-v4-flash",
        "max_tokens": 512,
        "extra_body": {"thinking": {"type": "enabled"}},
        "reasoning_effort": "high",
    }
