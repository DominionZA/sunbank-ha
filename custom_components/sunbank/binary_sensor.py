"""Sunbank warning binary sensors.

One per warning Sunbank can raise, plus an aggregate "Warning active". Each turns on the instant
Sunbank pushes the warning down the live socket — so HA automations ("notify me", "switch off the
geyser") fire in real time. The warning's message/severity/since ride along as attributes, and the
coordinator also fires a `sunbank_warning` event on raised/cleared for event-style automations.
"""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

# (warning id, friendly name, device_class) — must match the server's WARNING_RULES / OUTPUTS.
WARNINGS = [
    ("runtime_critical", "Power about to run out", BinarySensorDeviceClass.SAFETY),
    ("runtime_low", "Running low", BinarySensorDeviceClass.PROBLEM),
    ("heavy_draw", "Heavy load on a low battery", BinarySensorDeviceClass.PROBLEM),
    ("battery_low", "Battery low", BinarySensorDeviceClass.PROBLEM),
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [SunbankWarningSensor(coordinator, entry, wid, name, dc) for wid, name, dc in WARNINGS]
    entities.append(SunbankAnyWarningSensor(coordinator, entry))
    async_add_entities(entities)


class _Base(CoordinatorEntity, BinarySensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, key, name):
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_name = name

    @property
    def available(self) -> bool:
        return self.coordinator.home is not None


class SunbankWarningSensor(_Base):
    def __init__(self, coordinator, entry, warning_id, name, device_class):
        super().__init__(coordinator, entry, f"warn_{warning_id}", name)
        self._warning_id = warning_id
        self._attr_device_class = device_class

    def _warning(self) -> dict | None:
        for w in self.coordinator.active_warnings:
            if w.get("id") == self._warning_id:
                return w
        return None

    @property
    def is_on(self) -> bool:
        return self._warning() is not None

    @property
    def extra_state_attributes(self):
        w = self._warning()
        if not w:
            return {"severity": None, "message": None, "since": None}
        return {"severity": w.get("severity"), "message": w.get("message"), "since": w.get("since")}


class SunbankAnyWarningSensor(_Base):
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_icon = "mdi:alert"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "warn_any", "Warning active")

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.active_warnings)

    @property
    def extra_state_attributes(self):
        ws = self.coordinator.active_warnings
        return {
            "count": len(ws),
            "warnings": [{"id": w.get("id"), "severity": w.get("severity"), "message": w.get("message")} for w in ws],
            "highest": "critical" if any(w.get("severity") == "critical" for w in ws) else ("warning" if ws else None),
        }
