"""Constants for the DeepSeek integration."""

from __future__ import annotations

import logging
from typing import Final

DOMAIN: Final = "deepseek"
LOGGER: Final = logging.getLogger(__package__)

# Legacy config keys (kept for smoke test + config flow inputs).
CONF_API_KEY: Final = "api_key"
CONF_MODEL: Final = "model"
CONF_BASE_URL: Final = "base_url"
CONF_MAX_TOKENS: Final = "max_tokens"
CONF_TEMPERATURE: Final = "temperature"
CONF_REASONING: Final = "show_reasoning"

# New (HA core-style) option keys.
CONF_CHAT_MODEL: Final = "chat_model"
CONF_TOP_P: Final = "top_p"
CONF_PROMPT: Final = "prompt"
CONF_RECOMMENDED: Final = "recommended"

DEFAULT_NAME: Final = "DeepSeek"
DEFAULT_MODEL: Final = "deepseek-chat"
DEFAULT_BASE_URL: Final = "https://api.deepseek.com"
DEFAULT_MAX_TOKENS: Final = 2048
DEFAULT_TEMPERATURE: Final = 0.7
DEFAULT_REASONING: Final = False

RECOMMENDED_CHAT_MODEL: Final = "deepseek-chat"
RECOMMENDED_MAX_TOKENS: Final = 2048
RECOMMENDED_TEMPERATURE: Final = 0.7
RECOMMENDED_TOP_P: Final = 1.0

MODELS: Final = [
    "deepseek-chat",
    "deepseek-reasoner",
    "deepseek-coder",
]
