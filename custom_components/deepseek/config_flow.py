"""Config flow for the DeepSeek integration."""

from __future__ import annotations

from types import MappingProxyType
from typing import Any

import openai
import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_API_KEY, CONF_LLM_HASS_API
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import llm
from homeassistant.helpers.httpx_client import get_async_client
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    TemplateSelector,
)
from homeassistant.helpers.typing import VolDictType

from .const import (
    CONF_BASE_URL,
    CONF_CHAT_MODEL,
    CONF_MAX_TOKENS,
    CONF_PROMPT,
    CONF_RECOMMENDED,
    CONF_TEMPERATURE,
    CONF_TOP_P,
    DEFAULT_BASE_URL,
    DEFAULT_NAME,
    DOMAIN,
    LOGGER,
    RECOMMENDED_CHAT_MODEL,
    RECOMMENDED_MAX_TOKENS,
    RECOMMENDED_TEMPERATURE,
    RECOMMENDED_TOP_P,
)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_KEY): str,
        vol.Optional(CONF_BASE_URL, default=DEFAULT_BASE_URL): str,
    }
)

RECOMMENDED_OPTIONS: dict[str, Any] = {
    CONF_RECOMMENDED: True,
    CONF_LLM_HASS_API: llm.LLM_API_ASSIST,
    CONF_PROMPT: llm.DEFAULT_INSTRUCTIONS_PROMPT,
}


async def _validate_api_key(hass: HomeAssistant, data: dict[str, Any]) -> None:
    """Raise an openai error if the API key or base URL are wrong."""
    client = openai.AsyncOpenAI(
        api_key=data[CONF_API_KEY],
        base_url=data.get(CONF_BASE_URL, DEFAULT_BASE_URL),
        http_client=get_async_client(hass),
    )
    await client.with_options(timeout=10.0).models.list()


class DeepSeekConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for DeepSeek."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors: dict[str, str] = {}
        try:
            await _validate_api_key(self.hass, user_input)
        except openai.AuthenticationError:
            errors["base"] = "invalid_auth"
        except openai.APIConnectionError:
            errors["base"] = "cannot_connect"
        except Exception:  # noqa: BLE001
            LOGGER.exception("Unexpected exception validating DeepSeek API key")
            errors["base"] = "unknown"
        else:
            return self.async_create_entry(
                title=DEFAULT_NAME,
                data=user_input,
                options=RECOMMENDED_OPTIONS,
            )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Create the options flow."""
        return DeepSeekOptionsFlow(config_entry)


class DeepSeekOptionsFlow(OptionsFlow):
    """DeepSeek options flow."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.last_rendered_recommended = config_entry.options.get(
            CONF_RECOMMENDED, False
        )

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage options."""
        options: dict[str, Any] | MappingProxyType[str, Any] = self.config_entry.options

        if user_input is not None:
            if user_input.get(CONF_RECOMMENDED) == self.last_rendered_recommended:
                if user_input.get(CONF_LLM_HASS_API) == "none":
                    user_input.pop(CONF_LLM_HASS_API, None)
                return self.async_create_entry(title="", data=user_input)

            self.last_rendered_recommended = bool(user_input.get(CONF_RECOMMENDED))
            options = {
                CONF_RECOMMENDED: user_input.get(CONF_RECOMMENDED, False),
                CONF_PROMPT: user_input.get(CONF_PROMPT),
                CONF_LLM_HASS_API: user_input.get(CONF_LLM_HASS_API),
            }

        schema = _options_schema(self.hass, options)
        return self.async_show_form(step_id="init", data_schema=vol.Schema(schema))


def _options_schema(
    hass: HomeAssistant,
    options: dict[str, Any] | MappingProxyType[str, Any],
) -> VolDictType:
    """Build the options schema."""
    hass_apis: list[SelectOptionDict] = [
        SelectOptionDict(label="No control", value="none")
    ]
    hass_apis.extend(
        SelectOptionDict(label=api.name, value=api.id) for api in llm.async_get_apis(hass)
    )

    schema: VolDictType = {
        vol.Optional(
            CONF_PROMPT,
            description={
                "suggested_value": options.get(
                    CONF_PROMPT, llm.DEFAULT_INSTRUCTIONS_PROMPT
                )
            },
        ): TemplateSelector(),
        vol.Optional(
            CONF_LLM_HASS_API,
            description={"suggested_value": options.get(CONF_LLM_HASS_API)},
            default="none",
        ): SelectSelector(SelectSelectorConfig(options=hass_apis)),
        vol.Required(
            CONF_RECOMMENDED, default=options.get(CONF_RECOMMENDED, False)
        ): bool,
    }

    if options.get(CONF_RECOMMENDED):
        return schema

    schema.update(
        {
            vol.Optional(
                CONF_CHAT_MODEL,
                description={"suggested_value": options.get(CONF_CHAT_MODEL)},
                default=RECOMMENDED_CHAT_MODEL,
            ): str,
            vol.Optional(
                CONF_MAX_TOKENS,
                description={"suggested_value": options.get(CONF_MAX_TOKENS)},
                default=RECOMMENDED_MAX_TOKENS,
            ): int,
            vol.Optional(
                CONF_TOP_P,
                description={"suggested_value": options.get(CONF_TOP_P)},
                default=RECOMMENDED_TOP_P,
            ): NumberSelector(NumberSelectorConfig(min=0, max=1, step=0.05)),
            vol.Optional(
                CONF_TEMPERATURE,
                description={"suggested_value": options.get(CONF_TEMPERATURE)},
                default=RECOMMENDED_TEMPERATURE,
            ): NumberSelector(NumberSelectorConfig(min=0, max=2, step=0.05)),
        }
    )
    return schema
