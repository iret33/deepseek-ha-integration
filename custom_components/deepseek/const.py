"""Constants for the DeepSeek integration."""

from __future__ import annotations

import logging
from typing import Final

DOMAIN: Final = "deepseek"
LOGGER: Final = logging.getLogger(__package__)

# Config-entry data keys (stored in entry.data; require reconfiguration to change).
CONF_API_KEY: Final = "api_key"
CONF_BASE_URL: Final = "base_url"

# Options-flow keys (stored in entry.options; user-tunable any time).
CONF_CHAT_MODEL: Final = "chat_model"
CONF_MAX_TOKENS: Final = "max_tokens"
CONF_TEMPERATURE: Final = "temperature"
CONF_TOP_P: Final = "top_p"
CONF_PROMPT: Final = "prompt"

# Endpoint defaults.
DEFAULT_NAME: Final = "DeepSeek"
DEFAULT_BASE_URL: Final = "https://api.deepseek.com"

# Model catalogue. Order matters — the first entry is the default the
# picker shows on a fresh install. DeepSeek retired the legacy
# `deepseek-chat` / `deepseek-reasoner` names on 2026-07-24; they were
# only aliases for the non-thinking / thinking modes of
# `deepseek-v4-flash`. Thinking is now a request option on the V4 models,
# selected with CONF_REASONING_EFFORT below.
MODELS: Final = [
    "deepseek-v4-flash",
    "deepseek-v4-pro",
]

# Legacy model names -> (current model, reasoning effort). Used to migrate
# stored options and to translate names still passed to the service.
LEGACY_MODELS: Final[dict[str, tuple[str, str]]] = {
    "deepseek-chat": ("deepseek-v4-flash", "none"),
    "deepseek-reasoner": ("deepseek-v4-flash", "high"),
    "deepseek-coder": ("deepseek-v4-flash", "none"),
}

# Thinking mode. "none" disables thinking (fast, cheap, honours
# temperature / top_p); "high" and "max" enable it with that effort.
CONF_REASONING_EFFORT: Final = "reasoning_effort"
REASONING_EFFORTS: Final = ["none", "high", "max"]

RECOMMENDED_CHAT_MODEL: Final = "deepseek-v4-flash"
RECOMMENDED_REASONING_EFFORT: Final = "none"
RECOMMENDED_MAX_TOKENS: Final = 2048
RECOMMENDED_TEMPERATURE: Final = 0.7
RECOMMENDED_TOP_P: Final = 1.0
