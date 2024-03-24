"""Config flow for zabbix_evt_sensors integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import (
    CONF_API_TOKEN, CONF_HOST, CONF_PATH,
    CONF_PORT, CONF_PREFIX, CONF_STOP, CONF_SSL
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from pyzabbix import ZabbixAPIException
from requests.exceptions import ConnectionError

from .const import DEFAULT_NAME, DOMAIN, CONFIG_KEY, PROBLEMS_KEY, SERVICES_KEY
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

STEP_SENSOR_DATA_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_PREFIX, default="Zabbix"): str,
        vol.Required(SERVICES_KEY, default=True): bool,
        vol.Required(PROBLEMS_KEY, default=False): bool,
    }
)

STEP_SENSOR_TAGGED_PROBLEM_DATA_SCHEMA = vol.Schema(
    {
        vol.Optional("tag", default=""): str,
        vol.Optional("value", default=""): str,
        vol.Required(CONF_STOP, default=False): bool
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

    def __init__(self):
        super().__init__()
        self.init_info: dict[str, Any] = {CONFIG_KEY: {}, "prefix": None, SERVICES_KEY: False, PROBLEMS_KEY: []}

    async def async_step_user(
            self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
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
                self.init_info[CONFIG_KEY] = user_input
                return await self.async_step_sensors()

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_sensors(
            self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the sensors services step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            self.init_info["prefix"] = user_input["prefix"]
            self.init_info[SERVICES_KEY] = user_input[SERVICES_KEY]
            if user_input[PROBLEMS_KEY]:
                return await self.async_step_sensors_tagged_problems()
            else:
                return await self.async_end_flow()

        return self.async_show_form(
            step_id="sensors", data_schema=STEP_SENSOR_DATA_SCHEMA, errors=errors
        )

    async def async_step_sensors_tagged_problems(
            self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the sensors services step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            if user_input['tag']:
                self.init_info[PROBLEMS_KEY].append(
                    f'{user_input["tag"]}:{user_input["value"]}'
                )
            if user_input[CONF_STOP]:
                return await self.async_end_flow()
            else:
                return await self.async_step_sensors_tagged_problems()

        return self.async_show_form(
            step_id="sensors_tagged_problems", data_schema=STEP_SENSOR_TAGGED_PROBLEM_DATA_SCHEMA, errors=errors
        )

    async def async_end_flow(self):
        return self.async_create_entry(title=DEFAULT_NAME, data=self.init_info)

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
