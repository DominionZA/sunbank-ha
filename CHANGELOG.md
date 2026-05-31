# Changelog

All notable changes to the Sunbank Home Assistant integration. These notes also
appear as the update descriptions in HACS (they're published as GitHub Releases).

## v0.3.0 — Tell Sunbank about your indoor & outdoor sensors

You can now point Sunbank at your own temperature and humidity sensors — and nothing extra is shared unless you choose it.

- **Pick your sensors in setup** — four optional choosers: indoor temperature, indoor humidity, outdoor temperature, outdoor humidity. Sunbank shows "Inside 22°" on the Forecast weather line once you've picked them.
- **You're in control** — the integration only sends the sensors you select. Nothing is published by default.
- **To enable:** update here, restart Home Assistant, then remove and re-add the Sunbank integration to see the new sensor pickers.

## v0.2.0 — Real-time updates

Sunbank now updates the instant your sensors change — no more waiting on a timer.

- **Live, event-driven** — values are sent the moment Home Assistant sees a change, so your dashboard keeps pace with HA instead of lagging behind.
- **Nothing to tune** — the old polling interval is gone; there's no refresh setting to get wrong.
- **Steady heartbeat** — a quiet check-in every 60s keeps your connection showing healthy even when readings are calm.

## v0.1.0 — First release

First Sunbank integration. Connects Home Assistant to your Sunbank app and sends your solar, battery, load, grid and weather readings up to it.

- Pushes your mapped HA sensors to Sunbank so the dashboard and forecast have live data.
- Set it up once with your Sunbank server address and API key.
