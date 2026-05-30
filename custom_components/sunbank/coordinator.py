"""Sunbank push coordinator — event-driven (near real-time) with a heartbeat safety net.

The integration runs inside Home Assistant, so it subscribes directly to state-change events for
the mapped entities and pushes within ~2s of a change (change-of-value filtered, so it isn't
chatty). A slow heartbeat re-sends current values even when nothing changes, so a steady reading
is distinguishable from a dead feed. This is the real-time design — there is no poll interval to
tune for responsiveness.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_call_later, async_track_state_change_event
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN
from .mapping import COV, ENTITY_METRICS

_LOGGER = logging.getLogger(__name__)
FLUSH_DELAY = 2.0  # seconds — micro-batch window after a change, so simultaneous changes go in one push


def _to_float(state: str | None):
    try:
        return float(state)
    except (TypeError, ValueError):
        return None


class SunbankCoordinator(DataUpdateCoordinator):
    """Pushes mapped HA entities to Sunbank /v1/ingest: on change (real-time) + on a heartbeat."""

    def __init__(self, hass: HomeAssistant, *, base_url, api_key, site, source, interval, extra=None):
        # The coordinator's polling IS the heartbeat (safety net); real-time comes from events.
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=timedelta(seconds=interval))
        # hard-coded inverter metrics + the weather sensors the user authorised (entity_id -> metric)
        self._map = {**ENTITY_METRICS, **(extra or {})}
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._site = site
        self._source = source
        self._sent: dict[str, tuple[float, float]] = {}  # metric -> (last_value, last_sent_monotonic)
        self._outbox: list[dict] = []
        self._flush_cancel = None
        self._listen_cancel = None
        self._total_sent = 0
        self._last_upload: str | None = None

    # ---- lifecycle ----------------------------------------------------------
    @callback
    def async_start(self) -> None:
        """Subscribe to state changes for the mapped entities (near real-time)."""
        self._listen_cancel = async_track_state_change_event(
            self.hass, list(self._map.keys()), self._on_state_event)

    @callback
    def async_stop(self) -> None:
        if self._listen_cancel:
            self._listen_cancel()
            self._listen_cancel = None
        if self._flush_cancel:
            self._flush_cancel()
            self._flush_cancel = None

    # ---- real-time path -----------------------------------------------------
    @callback
    def _on_state_event(self, event: Event) -> None:
        entity_id = event.data.get("entity_id")
        new_state = event.data.get("new_state")
        metric = self._map.get(entity_id)
        if metric is None or new_state is None:
            return
        value = _to_float(new_state.state)
        if value is None:
            return
        if self._should_send(metric, value):
            self._enqueue(metric, entity_id, value)
            self._schedule_flush()

    def _should_send(self, metric: str, value: float) -> bool:
        deadband, throttle_s = COV.get(metric, (0.0, 0.0))
        prev = self._sent.get(metric)
        if prev is None:
            return True  # first sample for this metric always goes
        last_value, last_ts = prev
        if (self.hass.loop.time() - last_ts) < throttle_s:
            return False  # throttle ceiling
        return abs(value - last_value) >= deadband  # deadband

    @callback
    def _schedule_flush(self) -> None:
        if self._flush_cancel is not None:
            return  # a flush is already pending; this change rides along
        self._flush_cancel = async_call_later(self.hass, FLUSH_DELAY, self._flush)

    async def _flush(self, _now=None) -> None:
        self._flush_cancel = None
        batch, self._outbox = self._outbox, []
        if not batch:
            return
        status = await self._post(batch)
        self.async_set_updated_data(status)

    # ---- heartbeat path (coordinator's interval poll) -----------------------
    async def _async_update_data(self) -> dict:
        """Heartbeat: snapshot + push every mapped metric, so 'steady' != 'dead' and a fresh
        install sends immediately. Returns the status the diagnostic sensors render."""
        readings = []
        for entity_id, metric in self._map.items():
            st = self.hass.states.get(entity_id)
            if st is None or st.state in (None, "", "unknown", "unavailable"):
                continue
            value = _to_float(st.state)
            if value is None:
                continue
            readings.append(self._reading(metric, entity_id, value))
            self._sent[metric] = (value, self.hass.loop.time())
        if not readings:
            return self._status("no mapped entities available", ok=True)
        return await self._post(readings)

    # ---- shared push --------------------------------------------------------
    def _enqueue(self, metric: str, entity_id: str, value: float) -> None:
        self._outbox.append(self._reading(metric, entity_id, value))
        self._sent[metric] = (value, self.hass.loop.time())

    def _reading(self, metric: str, entity_id: str, value: float) -> dict:
        return {
            "metric": metric,
            "entity_id": entity_id,
            "ts": datetime.now(timezone.utc).isoformat(),
            "resolution": "instant",
            "agg": "last",
            "value": value,
            "observation_type": "actual",
        }

    async def _post(self, readings: list[dict]) -> dict:
        session = async_get_clientsession(self.hass)
        # 'agent' marks this as the integration source so Sunbank can enforce a single active source.
        payload = {"site": self._site, "source": self._source, "agent": "integration", "readings": readings}
        try:
            async with session.post(
                f"{self._base_url}/v1/ingest",
                json=payload,
                headers={"Authorization": f"Bearer {self._api_key}"},
            ) as resp:
                body = await resp.json(content_type=None)
                if resp.status != 200:
                    _LOGGER.warning("Sunbank ingest HTTP %s: %s", resp.status, body)
                    return self._status(f"ingest HTTP {resp.status}", ok=False)
                self._total_sent += int(body.get("upserted", len(readings)))
                self._last_upload = datetime.now(timezone.utc).isoformat()
                return self._status("ok", ok=True)
        except Exception as err:  # noqa: BLE001 — any failure surfaces on the Status sensor
            _LOGGER.warning("Sunbank push failed: %s", err)
            return self._status(f"push failed: {err}", ok=False)

    def _status(self, detail: str, *, ok: bool) -> dict:
        return {"ok": ok, "sent": self._total_sent, "last_upload": self._last_upload, "detail": detail}
