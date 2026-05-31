"""Sunbank coordinator — duplex live link, with a REST fallback and heartbeat safety net.

Runs inside Home Assistant. It bridges two ways:
  • UP   — subscribes to state-change events for the mapped entities and streams readings to
           Sunbank over the live WebSocket (falling back to REST /v1/ingest if the socket is down).
  • DOWN — receives Sunbank's evaluated home state + warnings on the same socket the instant they
           change, stores them for the live sensors, and fires `sunbank_warning` events on HA's bus.

A slow heartbeat re-sends current values even when nothing changes, so a steady reading is
distinguishable from a dead feed. There is no poll interval to tune for responsiveness.
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
from .ws_client import SunbankWSClient

_LOGGER = logging.getLogger(__name__)
FLUSH_DELAY = 2.0  # seconds — micro-batch window after a change, so simultaneous changes go in one push


def _to_float(state: str | None):
    try:
        return float(state)
    except (TypeError, ValueError):
        return None


class SunbankCoordinator(DataUpdateCoordinator):
    """Streams mapped HA entities to Sunbank and receives live home state + warnings back."""

    def __init__(self, hass: HomeAssistant, *, base_url, api_key, site, source, interval, extra=None):
        # The coordinator's polling IS the heartbeat (safety net); real-time comes from events + the socket.
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=timedelta(seconds=interval))
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

        self.device_info = None                # set by __init__ so all entities group under one device

        # downstream live state from Sunbank
        self.home: dict | None = None          # latest evaluated home state + warnings
        self.live_connected = False            # is the WebSocket up?
        self._active_warn: set[str] = set()
        self._ws = SunbankWSClient(
            hass, base_url, api_key,
            on_home=self._on_home, on_connect=self._on_ws_connect, on_status=self._on_ws_status,
        )

    # ---- lifecycle ----------------------------------------------------------
    @callback
    def async_start(self) -> None:
        """Subscribe to state changes (near real-time) and open the live socket."""
        self._listen_cancel = async_track_state_change_event(
            self.hass, list(self._map.keys()), self._on_state_event)
        self._ws.start()

    async def async_close(self) -> None:
        if self._listen_cancel:
            self._listen_cancel()
            self._listen_cancel = None
        if self._flush_cancel:
            self._flush_cancel()
            self._flush_cancel = None
        await self._ws.stop()

    # ---- downstream: live state + warnings from Sunbank ---------------------
    @callback
    def _on_home(self, home: dict) -> None:
        self.home = home
        active = {w["id"] for w in home.get("warnings", [])}
        raised = set(home.get("raised") or (active - self._active_warn))
        cleared = set(home.get("cleared") or (self._active_warn - active))
        for w in home.get("warnings", []):
            if w["id"] in raised:
                self.hass.bus.async_fire(f"{DOMAIN}_warning", {
                    "state": "raised", "id": w["id"], "severity": w.get("severity"),
                    "title": w.get("title"), "message": w.get("message"),
                })
        for wid in cleared:
            self.hass.bus.async_fire(f"{DOMAIN}_warning", {"state": "cleared", "id": wid})
        self._active_warn = active
        self.async_update_listeners()      # refresh the live sensors/binary_sensors

    @callback
    def _on_ws_status(self, connected: bool) -> None:
        self.live_connected = connected
        self.async_update_listeners()

    async def _on_ws_connect(self) -> None:
        """On (re)connect, push a full snapshot so Sunbank has current values immediately."""
        readings = self._snapshot()
        if readings:
            await self._ws.send({
                "type": "readings", "site": self._site, "source": self._source,
                "agent": "integration", "readings": readings,
            })

    @property
    def active_warnings(self) -> list[dict]:
        return (self.home or {}).get("warnings", []) if self.home else []

    # ---- upstream: real-time path -------------------------------------------
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
        status = await self._deliver(batch)
        self.async_set_updated_data(status)

    # ---- heartbeat path (coordinator's interval poll) -----------------------
    async def _async_update_data(self) -> dict:
        """Heartbeat: snapshot + push every mapped metric, so 'steady' != 'dead' and a fresh
        install sends immediately. Returns the status the diagnostic sensors render."""
        readings = self._snapshot()
        if not readings:
            return self._status("no mapped entities available", ok=True)
        return await self._deliver(readings)

    def _snapshot(self) -> list[dict]:
        """Current value of every mapped entity (skipping unknowns), as readings."""
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
        return readings

    # ---- shared delivery: live socket first, REST fallback ------------------
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

    async def _deliver(self, readings: list[dict]) -> dict:
        """Send over the live socket if it's up; otherwise fall back to REST so nothing is lost."""
        sent_live = await self._ws.send({
            "type": "readings", "site": self._site, "source": self._source,
            "agent": "integration", "readings": readings,
        })
        if sent_live:
            self._total_sent += len(readings)
            self._last_upload = datetime.now(timezone.utc).isoformat()
            return self._status("ok (live)", ok=True)
        return await self._post(readings)

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
                return self._status("ok (rest)", ok=True)
        except Exception as err:  # noqa: BLE001 — any failure surfaces on the Status sensor
            _LOGGER.warning("Sunbank push failed: %s", err)
            return self._status(f"push failed: {err}", ok=False)

    def _status(self, detail: str, *, ok: bool) -> dict:
        return {
            "ok": ok, "sent": self._total_sent, "last_upload": self._last_upload,
            "detail": detail, "live": self.live_connected,
        }
