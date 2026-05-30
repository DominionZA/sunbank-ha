# Sunbank — Home Assistant Integration

A custom integration that pushes your Home Assistant sensor data into your Sunbank account, and
shows the link's health back in HA. It's the first consumer of the Sunbank API — it authenticates
with your account **API key** and pushes readings mapped to the published metric catalog.

## What it does (v0)
- On an interval (default 60s), reads a set of HA sensors, maps them to Sunbank metric keys, and
  `POST`s them to `/v1/ingest` with `Authorization: Bearer <api_key>`.
- Exposes diagnostic sensors: `sensor.sunbank_status` (online/error), `sensor.sunbank_last_upload`,
  `sensor.sunbank_readings_sent`.

Mapped entities (v0, hard-coded in `mapping.py` — will become UI-configurable):

| HA entity | Sunbank metric |
|---|---|
| `sensor.inverter_battery` | `battery.soc` |
| `sensor.inverter_battery_power` | `battery.power` |
| `sensor.inverter_pv_power` | `solar.pv_power` |
| `sensor.inverter_load_power` | `load.power` |

## Install
1. Copy `custom_components/sunbank/` into your HA config dir → `…/config/custom_components/sunbank/`.
2. Restart Home Assistant.
3. **Settings → Devices & Services → Add Integration → "Sunbank"**.
4. Enter:
   - **Sunbank server URL** — where the Sunbank server runs (e.g. `http://<your-machine>:8137`; the
     HA box must be able to reach it).
   - **API key** — from the Sunbank dashboard → Settings → API key (Copy).
   - Site / Source / interval — defaults are fine.
5. The Sunbank diagnostic sensors appear; data starts flowing into your Sunbank dashboard.

## Notes
- Outbound only — HA pushes to Sunbank; nothing is exposed inbound.
- The mapping + catalog will move into the config UI; this v0 proves the contract end-to-end.
