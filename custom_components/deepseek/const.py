"""Constants for the DeepSeek integration."""

from typing import Final

DOMAIN: Final = "deepseek"
DEFAULT_NAME: Final = "DeepSeek"

# Configuration keys
CONF_API_KEY: Final = "api_key"
CONF_MODEL: Final = "model"
CONF_BASE_URL: Final = "base_url"
CONF_MAX_TOKENS: Final = "max_tokens"
CONF_TEMPERATURE: Final = "temperature"
CONF_REASONING: Final = "show_reasoning"

# Default values
DEFAULT_MODEL: Final = "deepseek-chat"
DEFAULT_BASE_URL: Final = "https://api.deepseek.com"
DEFAULT_MAX_TOKENS: Final = 2048
DEFAULT_TEMPERATURE: Final = 0.7
DEFAULT_REASONING: Final = False

# Available DeepSeek models
MODELS: Final = [
    "deepseek-chat",
    "deepseek-reasoner",
    "deepseek-coder",
]

# Services
SERVICE_CHAT: Final = "chat"
SERVICE_SUMMARIZE: Final = "summarize"
SERVICE_TRANSLATE: Final = "translate"

# Attributes
ATTR_RESPONSE: Final = "response"
ATTR_CONVERSATION_ID: Final = "conversation_id"
ATTR_TOKENS_USED: Final = "tokens_used"
ATTR_REASONING: Final = "reasoning"

# Platform
PLATFORM = "conversation"