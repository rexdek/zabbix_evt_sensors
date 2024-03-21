"""Support for Zabbix sensors."""

from __future__ import annotations

import datetime
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry, ConfigEntryNotReady
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
from pyzabbix import ZabbixAPIException

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the config entry for zabbix sensor."""
    _LOGGER.info("Instantiating DataUpdateCoordinator")
    coordinator = ZabbixUpdateCoordinator(
        hass,
        _LOGGER,
        hass.data[DOMAIN][entry.entry_id],
        name="Zabbix Data Coordinator",
        update_interval=datetime.timedelta(seconds=3),
    )
    await coordinator.async_config_entry_first_refresh()
    for zbx_svc in coordinator.data:
        async_add_entities([ZabbixProblemSensor(coordinator, zbx_svc)])


class ZabbixProblemSensor(CoordinatorEntity, SensorEntity):
    """Zabbix Problem Sensor."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:alpha-z-box"
    _attr_name = None

    def __init__(self, coordinator, zbx_svc) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = zbx_svc
        self._attr_native_value = None
        self._attr_unique_id = f"zbx_{coordinator.zbx.host}_{self._attr_name}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.zbx.host)},
            name=coordinator.zbx.host,
            configuration_url=coordinator.zbx.url,
            manufacturer="Zabbix SIA",
            sw_version=coordinator.zbx.zapi.version.public,
        )
        self._attr_should_poll = True
        _LOGGER.info("Created Zabbix sensor entity zbx_%s", self._attr_name)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        _LOGGER.info("Updating entity %s state", self.name)
        slavalues = [
            f"{e.host}: {e.name} ({e.severity})"
            for e in self.coordinator.data[self._attr_name]
        ]
        self._attr_extra_state_attributes = {"events": slavalues}
        states = [e.severity for e in self.coordinator.data[self._attr_name]]
        state = max(states) if states else -1
        self._attr_native_value = state
        self.async_write_ha_state()


class ZabbixUpdateCoordinator(DataUpdateCoordinator):
    """Zabbix DataUpdateCoordinator used to retrieve data for all sensors at once."""

    def __init__(
        self,
        hass: HomeAssistant,
        logger: logging.Logger,
        zbx,
        name: str = DOMAIN,
        update_interval: datetime.timedelta = datetime.timedelta(30),
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(hass, logger, name=name, update_interval=update_interval)
        self.zbx = zbx

    async def _async_update_data(self):
        return await self.hass.async_add_executor_job(self.zbx.services)
