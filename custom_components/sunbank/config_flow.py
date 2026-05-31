"""Config flow for Sunbank — asks for the server URL and the account API key."""
from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_API_KEY, CONF_BASE_URL, CONF_SITE, CONF_SOURCE,
    CONF_INDOOR_TEMP, CONF_INDOOR_HUM, CONF_OUTDOOR_TEMP, CONF_OUTDOOR_HUM,
    DEFAULT_BASE_URL, DEFAULT_SITE, DEFAULT_SOURCE, DOMAIN,
)

def _sensor(device_class):
    return selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor", device_class=device_class))


async def _validate(hass, base_url: str, api_key: str) -> str | None:
    """Return an error key, or None if the server + key check out."""
    session = async_get_clientsession(hass)
    url = base_url.rstrip("/") + "/v1/account"
    try:
        async with session.get(url, headers={"Authorization": f"Bearer {api_key}"}) as resp:
            if resp.status == 401:
                return "invalid_auth"
            if resp.status != 200:
                return "cannot_connect"
    except Exception:  # noqa: BLE001 — any network failure is "cannot connect"
        return "cannot_connect"
    return None


class SunbankConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the Sunbank setup dialog."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors: dict[str, str] = {}
        if user_input is not None:
            err = await _validate(self.hass, user_input[CONF_BASE_URL], user_input[CONF_API_KEY])
            if err:
                errors["base"] = err
            else:
                return self.async_create_entry(title="Sunbank", data=user_input)

        # No push-interval field: data flows in real time via state-change events, so there's
        # nothing to tune. (A slow heartbeat keep-alive is handled internally.)
        schema = vol.Schema({
            vol.Required(CONF_BASE_URL, default=DEFAULT_BASE_URL): str,
            vol.Required(CONF_API_KEY): str,
            vol.Optional(CONF_SITE, default=DEFAULT_SITE): str,
            vol.Optional(CONF_SOURCE, default=DEFAULT_SOURCE): str,
            # You tell us which sensors are which; we publish them already labelled.
            vol.Optional(CONF_INDOOR_TEMP): _sensor("temperature"),
            vol.Optional(CONF_INDOOR_HUM): _sensor("humidity"),
            vol.Optional(CONF_OUTDOOR_TEMP): _sensor("temperature"),
            vol.Optional(CONF_OUTDOOR_HUM): _sensor("humidity"),
        })
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    # ---- reauth: HA calls this when the integration reports the key was rejected --------------
    async def async_step_reauth(self, entry_data):
        """Triggered by ConfigEntryAuthFailed — HA shows a 'needs attention' prompt."""
        self._reauth_entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None):
        """Ask for a fresh API key and, if it checks out, swap it in and reload — no re-adding."""
        errors: dict[str, str] = {}
        entry = self._reauth_entry
        if user_input is not None:
            err = await _validate(self.hass, entry.data[CONF_BASE_URL], user_input[CONF_API_KEY])
            if err:
                errors["base"] = err
            else:
                self.hass.config_entries.async_update_entry(
                    entry, data={**entry.data, CONF_API_KEY: user_input[CONF_API_KEY]})
                await self.hass.config_entries.async_reload(entry.entry_id)
                return self.async_abort(reason="reauth_successful")
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_API_KEY): str}),
            errors=errors,
            description_placeholders={"server": entry.data[CONF_BASE_URL]},
        )
