"""Sunbank push coordinator: read mapped HA states, push to the Sunbank ingest API."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN
from .mapping import ENTITY_METRICS

_LOGGER = logging.getLogger(__name__)


class SunbankCoordinator(DataUpdateCoordinator):
    """Polls mapped entities on an interval and pushes them to Sunbank /v1/ingest."""

    def __init__(self, hass: HomeAssistant, *, base_url, api_key, site, source, interval):
        super().__init__(
            hass, _LOGGER, name=DOMAIN, update_interval=timedelta(seconds=interval)
        )
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._site = site
        self._source = source

    def _collect_readings(self) -> list[dict]:
        """Snapshot the mapped HA entities into Sunbank readings."""
        now = datetime.now(timezone.utc).isoformat()
        readings: list[dict] = []
        for entity_id, metric in ENTITY_METRICS.items():
            state = self.hass.states.get(entity_id)
            if state is None or state.state in (None, "", "unknown", "unavailable"):
                continue
            try:
                value = float(state.state)
            except (ValueError, TypeError):
                continue  # text metrics handled later; v0 is numeric
            readings.append({
                "metric": metric,
                "entity_id": entity_id,
                "ts": now,
                "resolution": "instant",
                "agg": "last",
                "value": value,
                "observation_type": "actual",
            })
        return readings

    async def _async_update_data(self) -> dict:
        """One push cycle. Returns status dict consumed by the sensors."""
        readings = self._collect_readings()
        if not readings:
            return {"ok": True, "sent": 0, "last_upload": None, "detail": "no mapped entities available"}

        session = async_get_clientsession(self.hass)
        # 'agent' tells Sunbank this is the integration source (vs the live WebSocket), so the
        # server can enforce a single active data source.
        payload = {"site": self._site, "source": self._source, "agent": "integration", "readings": readings}
        try:
            async with session.post(
                f"{self._base_url}/v1/ingest",
                json=payload,
                headers={"Authorization": f"Bearer {self._api_key}"},
            ) as resp:
                body = await resp.json(content_type=None)
                if resp.status != 200:
                    raise UpdateFailed(f"ingest HTTP {resp.status}: {body}")
        except UpdateFailed:
            raise
        except Exception as err:  # network etc. — surfaced as a failed update
            raise UpdateFailed(f"push failed: {err}") from err

        return {
            "ok": True,
            "sent": body.get("upserted", len(readings)),
            "rejected": body.get("rejected", 0),
            "last_upload": datetime.now(timezone.utc).isoformat(),
            "detail": "ok",
        }
