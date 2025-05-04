"""Config flow for the groq_whisper integration."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import requests
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_API_KEY, CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST, default="https://api.groq.com"): str,
        vol.Required(CONF_API_KEY): str,
    }
)


class GroqWhisperHub:
    def __init__(self, host: str, api_key: str) -> None:
        """Initialize."""
        self.host = host
        self.api_key = api_key

    async def authenticate(self, host: str, api_key: str) -> bool:
        """Check if the API key is valid."""
        response = await asyncio.to_thread(
            requests.get,
            url=f"{host}/openai/v1/models",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )

        if response.status_code == 401:
            raise InvalidAPIKey

        if response.status_code == 403:
            raise UnauthorizedError

        if response.status_code != 200:
            _LOGGER.error(
                "Failed to connect to Groq Whisper API: %s", response.status_code
            )
            raise UnknownError

        return True


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """

    hub = GroqWhisperHub(data[CONF_HOST], data[CONF_API_KEY])

    if not await hub.authenticate(data[CONF_HOST], data[CONF_API_KEY]):
        raise InvalidAuth

    return {"title": "Groq Whisper"}


class GroqWhisperConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for groq_whisper."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except UnauthorizedError:
                errors["base"] = "unauthorized"
            except InvalidAPIKey:
                errors["base"] = "invalid_api_key"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""


class UnknownError(HomeAssistantError):
    """Unknown error."""


class UnauthorizedError(HomeAssistantError):
    """API key valid but not authorized to access the resource."""


class InvalidAPIKey(HomeAssistantError):
    """Invalid api_key error."""
