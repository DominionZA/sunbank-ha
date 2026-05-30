"""The Sunbank integration — pushes Home Assistant data to a Sunbank account."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import (
    CONF_API_KEY, CONF_BASE_URL, CONF_INTERVAL, CONF_SITE, CONF_SOURCE,
    DEFAULT_INTERVAL, DEFAULT_SITE, DEFAULT_SOURCE, DOMAIN, ENV_ROLE_METRIC,
)
from .coordinator import SunbankCoordinator

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Sunbank from a config entry."""
    data = entry.data
    # the weather sensors the user authorised -> {entity_id: sunbank metric key}, published labelled
    extra = {data[c]: metric for c, metric in ENV_ROLE_METRIC.items() if data.get(c)}
    coordinator = SunbankCoordinator(
        hass,
        base_url=data[CONF_BASE_URL],
        api_key=data[CONF_API_KEY],
        site=data.get(CONF_SITE, DEFAULT_SITE),
        source=data.get(CONF_SOURCE, DEFAULT_SOURCE),
        interval=data.get(CONF_INTERVAL, DEFAULT_INTERVAL),
        extra=extra,
    )
    await coordinator.async_config_entry_first_refresh()
    coordinator.async_start()  # subscribe to state changes for near-real-time pushes

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        coordinator = hass.data[DOMAIN].pop(entry.entry_id, None)
        if coordinator:
            coordinator.async_stop()
    return unloaded
