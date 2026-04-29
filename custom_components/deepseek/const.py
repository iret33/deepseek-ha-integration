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

# Model catalogue. Order matters — the first entry is the default and the
# one shown selected when the user opens the picker. `deepseek-v4-flash`
# and `deepseek-v4-pro` are the current generation; `deepseek-chat` and
# `deepseek-reasoner` are deprecated (per DeepSeek API docs, 2026-07-24)
# but still functional and kept for users with existing config entries.
MODELS: Final = [
    "deepseek-v4-flash",
    "deepseek-v4-pro",
    "deepseek-chat",
    "deepseek-reasoner",
]

RECOMMENDED_CHAT_MODEL: Final = "deepseek-v4-flash"
RECOMMENDED_MAX_TOKENS: Final = 2048
RECOMMENDED_TEMPERATURE: Final = 0.7
RECOMMENDED_TOP_P: Final = 1.0
