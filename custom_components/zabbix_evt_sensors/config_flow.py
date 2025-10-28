"""Config flow for zabbix_evt_sensors integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_API_TOKEN,
    CONF_HOST,
    CONF_PATH,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_SSL,
    CONF_STOP,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from requests.exceptions import ConnectionError
from zabbix_utils.exceptions import APIRequestError

from .const import (DEFAULT_NAME,
                    DOMAIN,
                    ZBX_HOST_KEY,
                    ZBX_SENSOR_PREFIX,
                    ZBX_PROBLEMS_KEY,
                    ZBX_SERVICES_KEY,
                    ZBX_TAG_VALUE_LIST)
from .zabbix import Zbx

_LOGGER = logging.getLogger(__name__)

STEP_SENSOR_TAGGED_PROBLEM_DATA_SCHEMA = vol.Schema(
    {
        vol.Optional("tag", default=""): str,
        vol.Optional("value", default=""): str,
        vol.Required(CONF_STOP, default=False): bool
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> None:
    """Validate the user input allows us to connect."""

    zbx = await hass.async_add_executor_job(
        Zbx, data[CONF_HOST], data[CONF_API_TOKEN], data[CONF_PATH], data[CONF_PORT], data[CONF_SSL]
    )
    await hass.async_add_executor_job(zbx.services)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for zabbix_evt_sensors."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        super().__init__()

        self.cfg_data: dict[str, Any] = {ZBX_HOST_KEY: {},
                                         ZBX_SENSOR_PREFIX: "zabbix",
                                         ZBX_PROBLEMS_KEY: False,
                                         ZBX_TAG_VALUE_LIST: [],
                                         ZBX_SERVICES_KEY: True}
        self._is_reconfigure: bool = False
        self._reconfigure_entry: ConfigEntry | None = None

    def _build_user_schema(self) -> vol.Schema:
        host_cfg = self.cfg_data.get(ZBX_HOST_KEY, {})
        default_host = host_cfg.get(CONF_HOST, "zabbix")
        default_path = host_cfg.get(CONF_PATH, "")
        default_port = host_cfg.get(CONF_PORT, 443)
        default_token = host_cfg.get(CONF_API_TOKEN, "")
        default_ssl = host_cfg.get(CONF_SSL, True)
        default_scan = host_cfg.get(CONF_SCAN_INTERVAL, 3)
        return vol.Schema(
            {
                vol.Required(CONF_HOST, default=default_host): str,
                vol.Optional(CONF_PATH, default=default_path): str,
                vol.Required(CONF_PORT, default=default_port): int,
                vol.Required(CONF_API_TOKEN, default=default_token): str,
                vol.Required(CONF_SSL, default=default_ssl): bool,
                vol.Optional(CONF_SCAN_INTERVAL, default=default_scan): int
            }
        )

    def _build_sensor_schema(self) -> vol.Schema:
        default_prefix = self.cfg_data.get(ZBX_SENSOR_PREFIX, "zabbix")
        default_services = self.cfg_data.get(ZBX_SERVICES_KEY, True)
        default_problems = self.cfg_data.get(ZBX_PROBLEMS_KEY, False)
        return vol.Schema(
            {
                vol.Optional(ZBX_SENSOR_PREFIX, default=default_prefix): str,
                vol.Required(ZBX_SERVICES_KEY, default=default_services): bool,
                vol.Required(ZBX_PROBLEMS_KEY, default=default_problems): bool            }
        )

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Start reconfiguration for an existing entry."""

        entry_id = self.context.get("entry_id")
        if not entry_id:
            return self.async_abort(reason="not_found")

        entry = self.hass.config_entries.async_get_entry(entry_id)
        if entry is None:
            return self.async_abort(reason="not_found")

        self._is_reconfigure = True
        self._reconfigure_entry = entry

        # Seed cfg_data from existing entry data
        existing: dict[str, Any] = entry.data
        host_cfg = existing.get(ZBX_HOST_KEY, {})
        self.cfg_data = {
            ZBX_HOST_KEY: {
                CONF_HOST: host_cfg.get(CONF_HOST),
                CONF_PATH: host_cfg.get(CONF_PATH),
                CONF_PORT: host_cfg.get(CONF_PORT),
                CONF_API_TOKEN: host_cfg.get(CONF_API_TOKEN),
                CONF_SSL: host_cfg.get(CONF_SSL),
                CONF_SCAN_INTERVAL: host_cfg.get(CONF_SCAN_INTERVAL)
            },
            ZBX_SENSOR_PREFIX: existing.get(ZBX_SENSOR_PREFIX),
            ZBX_SERVICES_KEY: existing.get(ZBX_SERVICES_KEY),
            ZBX_PROBLEMS_KEY: existing.get(ZBX_PROBLEMS_KEY)
        }

        # Continue with the normal user step, but with defaults prefilled
        return await self.async_step_user()

    async def async_step_user(
            self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            host_norm = user_input[CONF_HOST].strip().lower()
            if not self._is_reconfigure:
                await self.async_set_unique_id(host_norm)
                self._abort_if_unique_id_configured()
            user_input[CONF_HOST] = host_norm
            try:
                await validate_input(self.hass, user_input)
            except APIRequestError:
                errors["base"] = "invalid_auth"
            except ConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                self.cfg_data[ZBX_HOST_KEY] = user_input
                return await self.async_step_sensors()

        # Show form (with dynamic defaults if reconfiguring)
        return self.async_show_form(
            step_id="user", data_schema=self._build_user_schema(), errors=errors
        )

    async def async_step_sensors(
            self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the sensors services step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            self.cfg_data[ZBX_SENSOR_PREFIX] = user_input[ZBX_SENSOR_PREFIX]
            self.cfg_data[ZBX_SERVICES_KEY] = user_input[ZBX_SERVICES_KEY]
            self.cfg_data[ZBX_PROBLEMS_KEY] = user_input[ZBX_PROBLEMS_KEY]
            if self.cfg_data[ZBX_PROBLEMS_KEY]:
                return await self.async_step_sensors_tagged_problems()
            return await self.async_end_flow()

        return self.async_show_form(
                step_id="sensors", data_schema=self._build_sensor_schema(), errors=errors
        )

    async def async_step_sensors_tagged_problems(
            self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the sensors services step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            if not self.cfg_data.get(ZBX_TAG_VALUE_LIST):
                self.cfg_data[ZBX_TAG_VALUE_LIST] = []
            tag = (user_input.get("tag") or "").strip()
            value = (user_input.get("value") or "").strip()
            stop = user_input.get(CONF_STOP, False)

            if tag:
                self.cfg_data[ZBX_TAG_VALUE_LIST].append(f"{tag}:{value}")
                if stop:
                    return await self.async_end_flow()
                return await self.async_step_sensors_tagged_problems()

            # No tag provided: only proceed if user chose to stop
            if stop:
                return await self.async_end_flow()
            errors["base"] = "tag_required_or_stop"

        return self.async_show_form(
            step_id="sensors_tagged_problems", data_schema=STEP_SENSOR_TAGGED_PROBLEM_DATA_SCHEMA, errors=errors
        )

    async def async_end_flow(self):
        """End the flow."""
        if self._is_reconfigure and self._reconfigure_entry is not None:
            # Persist new data into the existing entry and reload
            self.hass.config_entries.async_update_entry(self._reconfigure_entry, data=self.cfg_data)
            await self.hass.config_entries.async_reload(self._reconfigure_entry.entry_id)
            # Abort with a success-like reason to avoid creating a new entry with empty data
            return self.async_abort(reason="reconfigured")
        # Fresh setup
        return self.async_create_entry(title=DEFAULT_NAME, data=self.cfg_data)
