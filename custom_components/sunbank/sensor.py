"""Sunbank sensors.

Two groups:
  • Live sensors — the values Sunbank computes and pushes back (home energy state, battery, runtime,
    solar, load, health, status message). These are the product: usable in dashboards + automations.
  • Diagnostic sensors — link health (status / last upload / readings sent).
"""
from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfPower, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN

HOME_ENERGY_STATES = ["surplus", "charging", "solar_deficit", "on_battery"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        # live (the product)
        SunbankHomeEnergyStateSensor(coordinator, entry),
        SunbankLiveSensor(coordinator, entry, "battery_usable", "Battery", lambda h: h.get("battery", {}).get("usable_pct"),
                          unit=PERCENTAGE, device_class=SensorDeviceClass.BATTERY, state_class=SensorStateClass.MEASUREMENT),
        SunbankLiveSensor(coordinator, entry, "runtime", "Runtime remaining", lambda h: h.get("runtime_h"),
                          unit=UnitOfTime.HOURS, device_class=SensorDeviceClass.DURATION, state_class=SensorStateClass.MEASUREMENT, icon="mdi:timer-sand"),
        SunbankLiveSensor(coordinator, entry, "solar", "Solar now", lambda h: h.get("solar_w"),
                          unit=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
        SunbankLiveSensor(coordinator, entry, "load", "Load now", lambda h: h.get("load_w"),
                          unit=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
        SunbankLiveSensor(coordinator, entry, "battery_flow", "Battery flow", lambda h: h.get("battery_w"),
                          unit=UnitOfPower.WATT, device_class=SensorDeviceClass.POWER, state_class=SensorStateClass.MEASUREMENT),
        SunbankLiveSensor(coordinator, entry, "health", "Home health", lambda h: h.get("health"),
                          state_class=SensorStateClass.MEASUREMENT, icon="mdi:heart-pulse"),
        SunbankLiveSensor(coordinator, entry, "message", "Status message", lambda h: h.get("message"), icon="mdi:message-text"),
        # diagnostics (link health)
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
        self._attr_device_info = coordinator.device_info


# ---- live sensors -----------------------------------------------------------
class _LiveBase(_Base):
    """Reads from coordinator.home (the pushed state). Unavailable until the first push."""

    @property
    def available(self) -> bool:
        return self.coordinator.home is not None


class SunbankHomeEnergyStateSensor(_LiveBase):
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = HOME_ENERGY_STATES
    _attr_icon = "mdi:home-lightning-bolt"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "home_energy_state", "Home energy state")

    @property
    def native_value(self):
        return (self.coordinator.home or {}).get("home_energy_state")

    @property
    def extra_state_attributes(self):
        h = self.coordinator.home or {}
        return {"label": h.get("label"), "message": h.get("message"), "health": h.get("health")}


class SunbankLiveSensor(_LiveBase):
    """Generic live measure/text sensor driven by a getter over coordinator.home."""

    def __init__(self, coordinator, entry, key, name, getter, *, unit=None,
                 device_class=None, state_class=None, icon=None):
        super().__init__(coordinator, entry, key, name)
        self._getter = getter
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        if icon:
            self._attr_icon = icon

    @property
    def native_value(self):
        return self._getter(self.coordinator.home or {})


# ---- diagnostics ------------------------------------------------------------
class _Diag(_Base):
    def __init__(self, coordinator, entry, key, name):
        super().__init__(coordinator, entry, key, name)
        self._attr_entity_category = EntityCategory.DIAGNOSTIC


class SunbankStatusSensor(_Diag):
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["live", "online", "error"]
    _attr_icon = "mdi:lan-connect"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "status", "Status")

    @property
    def native_value(self):
        if self.coordinator.live_connected:
            return "live"   # the WebSocket is up — real-time both ways
        if self.coordinator.last_update_success and (self.coordinator.data or {}).get("ok"):
            return "online"  # delivering over REST fallback
        return "error"


class SunbankLastUploadSensor(_Diag):
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "last_upload", "Last upload")

    @property
    def native_value(self):
        ts = (self.coordinator.data or {}).get("last_upload")
        return dt_util.parse_datetime(ts) if ts else None


class SunbankSentSensor(_Diag):
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "sent", "Readings sent")

    @property
    def native_value(self):
        return (self.coordinator.data or {}).get("sent")
