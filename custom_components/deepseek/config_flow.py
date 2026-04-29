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
    SelectSelectorMode,
    TemplateSelector,
)
from homeassistant.helpers.typing import VolDictType

from .const import (
    CONF_BASE_URL,
    CONF_CHAT_MODEL,
    CONF_MAX_TOKENS,
    CONF_PROMPT,
    CONF_TEMPERATURE,
    CONF_TOP_P,
    DEFAULT_BASE_URL,
    DEFAULT_NAME,
    DOMAIN,
    LOGGER,
    MODELS,
    RECOMMENDED_CHAT_MODEL,
    RECOMMENDED_MAX_TOKENS,
    RECOMMENDED_TEMPERATURE,
    RECOMMENDED_TOP_P,
)


def _model_selector() -> SelectSelector:
    """Dropdown of supported models, with custom-value entry allowed."""
    return SelectSelector(
        SelectSelectorConfig(
            options=[SelectOptionDict(label=m, value=m) for m in MODELS],
            mode=SelectSelectorMode.DROPDOWN,
            custom_value=True,
        )
    )


STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_KEY): str,
        vol.Required(
            CONF_CHAT_MODEL, default=RECOMMENDED_CHAT_MODEL
        ): _model_selector(),
        vol.Optional(CONF_BASE_URL, default=DEFAULT_BASE_URL): str,
    }
)


async def _validate_api_key(hass: HomeAssistant, data: dict[str, Any]) -> None:
    """Probe the DeepSeek API; raise an openai error if the key is wrong."""
    client = openai.AsyncOpenAI(
        api_key=data[CONF_API_KEY],
        base_url=data.get(CONF_BASE_URL, DEFAULT_BASE_URL),
        http_client=get_async_client(hass),
    )
    # `/models` is the cheapest authenticated endpoint and is supported by
    # DeepSeek per https://api-docs.deepseek.com/api/list-models .
    await client.with_options(timeout=10.0).models.list()


class DeepSeekConfigFlow(ConfigFlow, domain=DOMAIN):
    """Initial config flow: ask for API key + model."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial setup step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=STEP_USER_DATA_SCHEMA,
                description_placeholders={
                    "api_keys_url": "https://platform.deepseek.com/api_keys"
                },
            )

        errors: dict[str, str] = {}
        try:
            await _validate_api_key(self.hass, user_input)
        except openai.AuthenticationError:
            errors["base"] = "invalid_auth"
        except (openai.APIConnectionError, openai.APITimeoutError):
            errors["base"] = "cannot_connect"
        except Exception:  # noqa: BLE001
            LOGGER.exception("Unexpected exception validating DeepSeek API key")
            errors["base"] = "unknown"
        else:
            chat_model = user_input.pop(CONF_CHAT_MODEL, RECOMMENDED_CHAT_MODEL)
            return self.async_create_entry(
                title=DEFAULT_NAME,
                data=user_input,
                options={
                    CONF_CHAT_MODEL: chat_model,
                    CONF_LLM_HASS_API: llm.LLM_API_ASSIST,
                    CONF_PROMPT: llm.DEFAULT_INSTRUCTIONS_PROMPT,
                    CONF_MAX_TOKENS: RECOMMENDED_MAX_TOKENS,
                    CONF_TEMPERATURE: RECOMMENDED_TEMPERATURE,
                    CONF_TOP_P: RECOMMENDED_TOP_P,
                },
            )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
            description_placeholders={
                "api_keys_url": "https://platform.deepseek.com/api_keys"
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Create the options flow."""
        return DeepSeekOptionsFlow()


class DeepSeekOptionsFlow(OptionsFlow):
    """Options flow: change model + tuning parameters at any time."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage options."""
        if user_input is not None:
            if user_input.get(CONF_LLM_HASS_API) == "none":
                user_input.pop(CONF_LLM_HASS_API, None)
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                _options_schema(self.hass, self.config_entry.options)
            ),
        )


def _options_schema(
    hass: HomeAssistant,
    options: dict[str, Any] | MappingProxyType[str, Any],
) -> VolDictType:
    """Build the options-flow schema, prefilled with current values."""
    hass_apis: list[SelectOptionDict] = [
        SelectOptionDict(label="No control", value="none")
    ]
    hass_apis.extend(
        SelectOptionDict(label=api.name, value=api.id)
        for api in llm.async_get_apis(hass)
    )

    return {
        vol.Required(
            CONF_CHAT_MODEL,
            default=options.get(CONF_CHAT_MODEL, RECOMMENDED_CHAT_MODEL),
        ): _model_selector(),
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
            description={"suggested_value": options.get(CONF_LLM_HASS_API, "none")},
            default="none",
        ): SelectSelector(SelectSelectorConfig(options=hass_apis)),
        vol.Optional(
            CONF_MAX_TOKENS,
            default=options.get(CONF_MAX_TOKENS, RECOMMENDED_MAX_TOKENS),
        ): NumberSelector(NumberSelectorConfig(min=64, max=8192, step=64, mode="box")),
        vol.Optional(
            CONF_TEMPERATURE,
            default=options.get(CONF_TEMPERATURE, RECOMMENDED_TEMPERATURE),
        ): NumberSelector(NumberSelectorConfig(min=0, max=2, step=0.05)),
        vol.Optional(
            CONF_TOP_P,
            default=options.get(CONF_TOP_P, RECOMMENDED_TOP_P),
        ): NumberSelector(NumberSelectorConfig(min=0, max=1, step=0.05)),
    }
