"""Config flow for DeepSeek integration."""

from __future__ import annotations

import logging
from typing import Any

from openai import AsyncOpenAI, AuthenticationError
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry, OptionsFlow
from homeassistant.const import CONF_API_KEY, CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import selector

from .const import (
    CONF_BASE_URL,
    CONF_MAX_TOKENS,
    CONF_MODEL,
    CONF_TEMPERATURE,
    CONF_REASONING,
    DEFAULT_BASE_URL,
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    DEFAULT_REASONING,
    DOMAIN,
    MODELS,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_KEY): str,
        vol.Optional(CONF_NAME, default="DeepSeek"): str,
    }
)

STEP_OPTIONS_DATA_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_MODEL, default=DEFAULT_MODEL): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=MODELS,
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        ),
        vol.Optional(CONF_BASE_URL, default=DEFAULT_BASE_URL): str,
        vol.Optional(
            CONF_MAX_TOKENS, default=DEFAULT_MAX_TOKENS
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=1,
                max=128000,
                step=1,
                mode=selector.NumberSelectorMode.BOX,
            )
        ),
        vol.Optional(
            CONF_TEMPERATURE, default=DEFAULT_TEMPERATURE
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=0.0,
                max=2.0,
                step=0.1,
                mode=selector.NumberSelectorMode.SLIDER,
            )
        ),
        vol.Optional(CONF_REASONING, default=DEFAULT_REASONING): bool,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """

    api_key = data[CONF_API_KEY]
    base_url = data.get(CONF_BASE_URL, DEFAULT_BASE_URL)

    # Test the API key by making a simple request
    client = AsyncOpenAI(
        api_key=api_key,
        base_url=base_url,
    )

    try:
        # Test authentication with a simple models list request
        # DeepSeek API is OpenAI-compatible, so we can use the models endpoint
        response = await client.models.list()

        # Check if DeepSeek models are available
        deepseek_models = [
            model.id for model in response.data if "deepseek" in model.id.lower()
        ]

        if not deepseek_models:
            raise CannotConnect(
                "No DeepSeek models found. Please check your API key and base URL."
            )

        _LOGGER.debug(
            "Successfully connected to DeepSeek API. Available models: %s",
            deepseek_models,
        )

        # Return info to be stored in the config entry
        return {"title": data.get(CONF_NAME, "DeepSeek"), "models": deepseek_models}

    except AuthenticationError as err:
        _LOGGER.error("Authentication error: %s", err)
        raise InvalidAuth from err
    except Exception as err:
        _LOGGER.error("Cannot connect to DeepSeek API: %s", err)
        raise CannotConnect from err


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for DeepSeek."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow for this handler."""
        return OptionsFlowHandler()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Store the validated data
                self._user_input = user_input

                # Show options step
                return await self.async_step_options()

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
            description_placeholders={
                "docs_url": "https://platform.deepseek.com/api-keys"
            },
        )

    async def async_step_options(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the options step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Combine user input from both steps
            full_data = {**self._user_input, **user_input}

            # Create the config entry
            return self.async_create_entry(
                title=full_data.get(CONF_NAME, "DeepSeek"),
                data=full_data,
            )

        # Show options form with defaults
        return self.async_show_form(
            step_id="options",
            data_schema=STEP_OPTIONS_DATA_SCHEMA,
            errors=errors,
            description_placeholders={
                "model_docs": "https://platform.deepseek.com/api-docs"
            },
        )


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for DeepSeek."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate the input
            try:
                # Test the API key if it was changed
                if CONF_API_KEY in user_input:
                    test_data = {
                        CONF_API_KEY: user_input[CONF_API_KEY],
                        CONF_BASE_URL: user_input.get(CONF_BASE_URL, DEFAULT_BASE_URL),
                    }
                    await validate_input(self.hass, test_data)

                # Update options
                return self.async_create_entry(title="", data=user_input)

            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        # Get current options
        current_options = self.config_entry.options
        current_data = self.config_entry.data

        # Build schema with current values
        options_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_API_KEY, default=current_data.get(CONF_API_KEY, "")
                ): str,
                vol.Optional(
                    CONF_MODEL, default=current_options.get(CONF_MODEL, DEFAULT_MODEL)
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=MODELS,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional(
                    CONF_BASE_URL,
                    default=current_options.get(CONF_BASE_URL, DEFAULT_BASE_URL),
                ): str,
                vol.Optional(
                    CONF_MAX_TOKENS,
                    default=current_options.get(CONF_MAX_TOKENS, DEFAULT_MAX_TOKENS),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1,
                        max=128000,
                        step=1,
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Optional(
                    CONF_TEMPERATURE,
                    default=current_options.get(CONF_TEMPERATURE, DEFAULT_TEMPERATURE),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0.0,
                        max=2.0,
                        step=0.1,
                        mode=selector.NumberSelectorMode.SLIDER,
                    )
                ),
                vol.Optional(
                    CONF_REASONING,
                    default=current_options.get(CONF_REASONING, DEFAULT_REASONING),
                ): bool,
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=options_schema,
            errors=errors,
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
