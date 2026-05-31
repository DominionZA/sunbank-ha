"""Diagnostics for Sunbank — Settings → Devices & Services → Sunbank → ⋮ → Download diagnostics.

Gives a redacted snapshot of how the link is set up and what it's currently seeing: connection
state, the last evaluated home state Sunbank pushed, active warnings, and which HA entities are
mapped to which Sunbank metrics. The API key is redacted.
"""
from __future__ import annotations

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_API_KEY, DOMAIN

TO_REDACT = {CONF_API_KEY}


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: ConfigEntry) -> dict:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    return {
        "config": async_redact_data(dict(entry.data), TO_REDACT),
        "connection": {
            "live_socket_connected": coordinator.live_connected,
            "last_status": coordinator.data,           # ok / detail / sent / last_upload / live
        },
        "home_state": coordinator.home,                 # latest evaluated state Sunbank pushed
        "active_warnings": coordinator.active_warnings,
        "mapped_entities": coordinator._map,            # {entity_id: sunbank metric}
    }
