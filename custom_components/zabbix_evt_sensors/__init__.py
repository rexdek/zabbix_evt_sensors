"""The zabbix_problems integration."""

from __future__ import annotations

import logging

import urllib3

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_TOKEN, CONF_HOST, CONF_PORT, CONF_SSL, Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .zabbix import Zbx

urllib3.disable_warnings()

PLATFORMS: list[Platform] = [Platform.SENSOR]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Zabbix Problems from config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = await hass.async_add_executor_job(
        Zbx,
        entry.data[CONF_HOST],
        entry.data[CONF_API_TOKEN],
        entry.data[CONF_PORT],
        entry.data[CONF_SSL],
    )
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
