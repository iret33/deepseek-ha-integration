"""Request-building helpers shared by the conversation, AI Task and service code."""

from __future__ import annotations

from typing import Any

from .const import LEGACY_MODELS, RECOMMENDED_REASONING_EFFORT


def resolve_model(model: str, reasoning_effort: str | None) -> tuple[str, str]:
    """Map a retired model name onto its V4 equivalent.

    An explicit reasoning effort wins over the one implied by the legacy
    name, so `deepseek-chat` + `high` still thinks.
    """
    if model in LEGACY_MODELS:
        model, implied_effort = LEGACY_MODELS[model]
        return model, reasoning_effort or implied_effort
    return model, reasoning_effort or RECOMMENDED_REASONING_EFFORT


def build_request_kwargs(
    model: str,
    reasoning_effort: str | None,
    max_tokens: int,
    temperature: float,
    top_p: float,
) -> dict[str, Any]:
    """Build chat.completions.create kwargs for a model + thinking setting.

    V4 models think by default, so thinking is always set explicitly.
    Sampling parameters have no effect in thinking mode and are omitted.
    """
    model, effort = resolve_model(model, reasoning_effort)
    kwargs: dict[str, Any] = {"model": model, "max_tokens": max_tokens}
    if effort == "none":
        kwargs["extra_body"] = {"thinking": {"type": "disabled"}}
        kwargs["temperature"] = temperature
        kwargs["top_p"] = top_p
    else:
        kwargs["extra_body"] = {"thinking": {"type": "enabled"}}
        kwargs["reasoning_effort"] = effort
    return kwargs
