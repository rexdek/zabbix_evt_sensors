"""The zabbix_evt_sensors integration."""
from __future__ import annotations

import logging

import urllib3

from zabbix_utils.exceptions import APIRequestError
from homeassistant.config_entries import ConfigEntry, ConfigEntryNotReady
from homeassistant.const import (
    CONF_API_TOKEN,
    CONF_HOST,
    CONF_PATH,
    CONF_PORT,
    CONF_SSL,
    Platform,
)
from homeassistant.core import HomeAssistant

from .const import ZBX_HOST_KEY, DOMAIN
from .zabbix import Zbx

PLATFORMS: list[Platform] = [Platform.SENSOR]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Zabbix Problems from config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Create Zabbix client in executor; wrap connection errors so HA retries startup
    cfg = entry.data.get(ZBX_HOST_KEY)
    if not cfg:
        _LOGGER.warning("Missing %s in entry %s; deferring setup", ZBX_HOST_KEY, entry.entry_id)
        raise ConfigEntryNotReady

    _LOGGER.debug("Creating Zabbix client for entry %s", entry.entry_id)
    try:
        zbx = await hass.async_add_executor_job(
            Zbx,
            cfg[CONF_HOST],
            cfg[CONF_API_TOKEN],
            cfg[CONF_PATH],
            cfg[CONF_PORT],
            cfg[CONF_SSL]
        )
    except APIRequestError as e:
        # Defer setup until the API becomes available
        raise ConfigEntryNotReady from e

    hass.data[DOMAIN][entry.entry_id] = zbx

    # Forward platform setups (let HA handle platform-specific exceptions)
    async def _options_updated(hass: HomeAssistant, updated_entry: ConfigEntry):
        await hass.config_entries.async_reload(updated_entry.entry_id)

    entry.async_on_unload(entry.add_update_listener(_options_updated))

    _LOGGER.debug("Forwarding platforms for entry %s", entry.entry_id)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
