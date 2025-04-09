"""Support for Zabbix sensors."""

from __future__ import annotations

import datetime
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import CONFIG_KEY, DOMAIN, PROBLEMS_KEY, SERVICES_KEY

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
        hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the config entry for zabbix sensor."""
    _LOGGER.info("Instantiating DataUpdateCoordinator")
    zbx_config = hass.data[DOMAIN][entry.entry_id]
    scan_interval = entry.data[CONFIG_KEY][CONF_SCAN_INTERVAL]

    coordinator = ZabbixUpdateCoordinator(
        hass=hass,
        logger=_LOGGER,
        zbx=zbx_config,
        name="Zabbix Data Coordinator",
        update_interval=datetime.timedelta(seconds=scan_interval),
    )
    await coordinator.async_config_entry_first_refresh()

    prefix = entry.data.get("prefix", "Zabbix")

    sensors = []

    if entry.data.get(SERVICES_KEY):
        sensors.extend(
            ZabbixServiceSensor(coordinator, svc, prefix)
            for svc in coordinator.data[SERVICES_KEY]
        )

    if entry.data.get(PROBLEMS_KEY):
        sensors.extend(
            ZabbixProblemSensor(coordinator, prob, prefix)
            for prob in entry.data[PROBLEMS_KEY]
        )

    async_add_entities(sensors)


class ZabbixSensor(CoordinatorEntity, SensorEntity):
    """Zabbix Problem Sensor."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:alpha-z-box"
    _attr_name = None
    zabbix_sensor_type_name = None
    zabbix_sensor_type_key = None

    def __init__(self, coordinator, zbx_evt, prefix) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = zbx_evt
        self._attr_unique_id = f"zbx_{coordinator.zbx.host}_{self._attr_name}"
        self._attr_native_value = None
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f'{coordinator.zbx.host}_{self.zabbix_sensor_type_name}')},
            name=f'{prefix} {self.zabbix_sensor_type_name}',
            configuration_url=coordinator.zbx.url,
            manufacturer="Zabbix SIA",
            sw_version=coordinator.zbx.zapi.version.public,
        )
        self._attr_should_poll = True
        _LOGGER.debug("Created Zabbix %s sensor: %s", self.zabbix_sensor_type_name, self._attr_unique_id)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        _LOGGER.debug("Updating entity %s state", self.name)

        events = self.coordinator.data[self.zabbix_sensor_type_key].get(self._attr_name, [])
        self._attr_extra_state_attributes = {
            #"events": [f"{e.host}: {e.name} ({e.severity})" for e in events]
            "events": events
        }
        self._attr_native_value = max((e.severity for e in events), default=-1)
        self.async_write_ha_state()


class ZabbixServiceSensor(ZabbixSensor):
    """Zabbix Service Sensor."""

    zabbix_sensor_type_name = "Service"
    zabbix_sensor_type_key = SERVICES_KEY


class ZabbixProblemSensor(ZabbixSensor):
    """Zabbix Problem Sensor."""

    zabbix_sensor_type_name = "Problem"
    zabbix_sensor_type_key = PROBLEMS_KEY


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
        return {
            SERVICES_KEY: await self.hass.async_add_executor_job(self.zbx.services),
            PROBLEMS_KEY: await self.hass.async_add_executor_job(self.zbx.problems)
        }
