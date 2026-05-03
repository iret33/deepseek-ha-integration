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
# picker shows on a fresh install. `deepseek-chat` and `deepseek-reasoner`
# are pinned to *non-thinking* mode and work cleanly with the plain
# chat-completions API this integration uses. The newer `deepseek-v4-*`
# models default to *thinking* mode, which streams a `reasoning_content`
# field that has to be re-fed on follow-up turns; this integration does
# not yet round-trip that field, so picking a v4 model produces a
# 400 ("reasoning_content in the thinking mode must be passed back") on
# multi-turn conversations. Until reasoning_content support lands, the
# v4 names are kept in the dropdown for users who want to opt in but
# the default points at `deepseek-chat`.
MODELS: Final = [
    "deepseek-chat",
    "deepseek-reasoner",
    "deepseek-v4-flash",
    "deepseek-v4-pro",
]

RECOMMENDED_CHAT_MODEL: Final = "deepseek-chat"
RECOMMENDED_MAX_TOKENS: Final = 2048
RECOMMENDED_TEMPERATURE: Final = 0.7
RECOMMENDED_TOP_P: Final = 1.0
