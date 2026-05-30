"""Config flow for Sunbank — asks for the server URL and the account API key."""
from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_API_KEY, CONF_BASE_URL, CONF_INTERVAL, CONF_SITE, CONF_SOURCE,
    DEFAULT_BASE_URL, DEFAULT_INTERVAL, DEFAULT_SITE, DEFAULT_SOURCE, DOMAIN,
)


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

        schema = vol.Schema({
            vol.Required(CONF_BASE_URL, default=DEFAULT_BASE_URL): str,
            vol.Required(CONF_API_KEY): str,
            vol.Optional(CONF_SITE, default=DEFAULT_SITE): str,
            vol.Optional(CONF_SOURCE, default=DEFAULT_SOURCE): str,
            vol.Optional(CONF_INTERVAL, default=DEFAULT_INTERVAL): int,
        })
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
