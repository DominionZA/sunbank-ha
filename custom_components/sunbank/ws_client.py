"""Duplex WebSocket client to Sunbank.

One persistent connection carries both directions:
  • UP   — live readings (same shape as the REST /v1/ingest body).
  • DOWN — the evaluated home state + warnings, the instant Sunbank computes them.

It reconnects on its own with backoff, and on every (re)connect asks the coordinator to send a
full snapshot so Sunbank has current values immediately. If the socket is down, the caller falls
back to REST — so a blip never loses data.
"""
from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Awaitable, Callable

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)
_MAX_BACKOFF = 30


def _ws_url(base_url: str) -> str:
    u = base_url.rstrip("/")
    if u.startswith("https://"):
        u = "wss://" + u[len("https://"):]
    elif u.startswith("http://"):
        u = "ws://" + u[len("http://"):]
    return u + "/v1/stream"


class SunbankWSClient:
    """Manages the live socket: connect loop, send, and inbound dispatch."""

    def __init__(
        self,
        hass: HomeAssistant,
        base_url: str,
        api_key: str,
        *,
        on_home: Callable[[dict], None] | None = None,
        on_policy: Callable[[], Awaitable[None]] | None = None,
        on_connect: Callable[[], Awaitable[None]] | None = None,
        on_status: Callable[[bool], None] | None = None,
    ) -> None:
        self.hass = hass
        self._url = _ws_url(base_url)
        self._api_key = api_key
        self._on_home = on_home
        self._on_policy = on_policy
        self._on_connect = on_connect
        self._on_status = on_status
        self._ws: aiohttp.ClientWebSocketResponse | None = None
        self._task: asyncio.Task | None = None
        self._closing = False
        self.connected = False

    # ---- lifecycle ----------------------------------------------------------
    def start(self) -> None:
        self._closing = False
        self._task = self.hass.async_create_background_task(self._run(), "sunbank_ws")

    async def stop(self) -> None:
        self._closing = True
        if self._ws is not None and not self._ws.closed:
            await self._ws.close()
        if self._task is not None:
            self._task.cancel()
            self._task = None

    # ---- send (up) ----------------------------------------------------------
    async def send(self, payload: dict) -> bool:
        """Send a JSON frame. Returns False if the socket isn't up (caller falls back to REST)."""
        ws = self._ws
        if ws is None or ws.closed:
            return False
        try:
            await ws.send_json(payload)
            return True
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug("Sunbank WS send failed: %s", err)
            return False

    # ---- connect loop -------------------------------------------------------
    async def _run(self) -> None:
        backoff = 1
        session = async_get_clientsession(self.hass)
        while not self._closing:
            try:
                async with session.ws_connect(
                    self._url,
                    headers={"Authorization": f"Bearer {self._api_key}"},
                    heartbeat=30,        # aiohttp ping/pong keep-alive
                ) as ws:
                    self._ws = ws
                    self.connected = True
                    backoff = 1
                    _LOGGER.info("Sunbank live socket connected: %s", self._url)
                    if self._on_status:
                        self._on_status(True)
                    if self._on_connect:
                        await self._on_connect()         # push a fresh snapshot on (re)connect
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            self._dispatch(msg.data)
                        elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                            break
            except asyncio.CancelledError:
                raise
            except Exception as err:  # noqa: BLE001 — any failure → reconnect
                _LOGGER.debug("Sunbank WS connection error: %s", err)
            finally:
                self._ws = None
                if self.connected and self._on_status:
                    self._on_status(False)
                self.connected = False
            if self._closing:
                break
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, _MAX_BACKOFF)

    def _dispatch(self, raw: str) -> None:
        try:
            msg = json.loads(raw)
        except ValueError:
            return
        if msg.get("type") == "home" and self._on_home:
            self._on_home(msg)
        elif msg.get("type") == "policy_updated" and self._on_policy:
            self.hass.async_create_background_task(self._on_policy(), "sunbank_policy_sync")
