"""Sunbank status sensors — so HA shows whether the link is healthy and when it last uploaded."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        SunbankStatusSensor(coordinator, entry),
        SunbankLastUploadSensor(coordinator, entry),
        SunbankSentSensor(coordinator, entry),
    ])


class _Base(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, key, name):
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_name = name
        self._attr_entity_category = EntityCategory.DIAGNOSTIC


class SunbankStatusSensor(_Base):
    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "status", "Status")

    @property
    def native_value(self):
        if self.coordinator.last_update_success and (self.coordinator.data or {}).get("ok"):
            return "online"
        return "error"


class SunbankLastUploadSensor(_Base):
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "last_upload", "Last upload")

    @property
    def native_value(self):
        ts = (self.coordinator.data or {}).get("last_upload")
        return dt_util.parse_datetime(ts) if ts else None


class SunbankSentSensor(_Base):
    _attr_state_class = "measurement"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "sent", "Readings sent")

    @property
    def native_value(self):
        return (self.coordinator.data or {}).get("sent")
