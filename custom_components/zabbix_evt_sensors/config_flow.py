"""Config flow for zabbix_evt_sensors integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import (
    CONF_API_TOKEN, CONF_ENABLED, CONF_HOST,
    CONF_PATH, CONF_PORT, CONF_PREFIX, CONF_STOP, CONF_SSL
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from pyzabbix import ZabbixAPIException
from requests.exceptions import ConnectionError

from .const import DEFAULT_NAME, DOMAIN
from .zabbix import Zbx

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST, default="zabbix.rexkramer.de"): str,
        vol.Optional(CONF_PATH, default=""): str,
        vol.Required(CONF_PORT, default=443): int,
        vol.Required(CONF_SSL, default=True): bool,
        vol.Required(CONF_API_TOKEN): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> None:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    zbx = await hass.async_add_executor_job(
        Zbx,
        data[CONF_HOST],
        data[CONF_API_TOKEN],
        data[CONF_PATH],
        data[CONF_PORT],
        data[CONF_SSL],
    )
    await hass.async_add_executor_job(zbx.services)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for zabbix_evt_sensors."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        self.init_info = {"conf": None, "services": None, "problems": []}
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_HOST])
            self._abort_if_unique_id_configured()
            try:
                await validate_input(self.hass, user_input)
            except ZabbixAPIException:
                errors["base"] = "invalid_auth"
            except ConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                self.init_info["conf"] = user_input
                return await self.async_step_sensors_services()

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


    async def async_step_sensors_services(
            self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the sensors services step."""
        errors: dict[str, str] = {}

        sensors_services = vol.Schema(
            {
                vol.Required(CONF_ENABLED, default=True): bool,
                vol.Optional(CONF_PREFIX, default=self.init_info["conf"][CONF_HOST]): str
            }
        )

        if user_input is not None:
            self.init_info["services"] = user_input
            return await self.async_step_sensors_tagged_problems()

        return self.async_show_form(
            step_id="sensors_services", data_schema=sensors_services, errors=errors
        )

    async def async_step_sensors_tagged_problems(
            self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the sensors services step."""
        errors: dict[str, str] = {}
        sensors_tagged_problems = vol.Schema(
            {
                vol.Optional("tag", default=""): str,
                vol.Optional("value", default=""): str,
                vol.Required(CONF_STOP, default=False): bool
            }
        )

        if user_input is not None:
            if user_input['tag']:
                self.init_info["problems"].append(
                    f'{user_input["tag"]}:{user_input["value"]}'
                )
            if user_input[CONF_STOP]:
                print(f"INPUT RECEIVED {self.init_info}")
                #return self.async_abort(reason="not_supported")
                return self.async_create_entry(title=DEFAULT_NAME, data=self.init_info)
            else:
                return await self.async_step_sensors_tagged_problems()

        return self.async_show_form(
            step_id="sensors_tagged_problems", data_schema=sensors_tagged_problems, errors=errors
        )

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            pass  # TODO: process user input

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema({vol.Required("input_parameter"): str}),
    )

class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
