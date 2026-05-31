# Changelog

All notable changes to the Sunbank Home Assistant integration. These notes also
appear as the update descriptions in HACS (they're published as GitHub Releases).

## v0.4.1 — A proper device page

Sunbank now shows up as a real Home Assistant **device**, not a loose pile of entities.

- **One Sunbank device** — every entity (live values + warnings + diagnostics) groups under it, with the **integration version**, manufacturer, and a **link to your Sunbank dashboard** right on the device page. Settings → Devices & Services → Sunbank → the device.
- **Download diagnostics** — ⋮ → *Download diagnostics* gives a redacted snapshot: is the live socket connected, the last state Sunbank pushed, active warnings, and which HA sensors are mapped — so problems are easy to see and share.

## v0.4.0 — Real-time states & warnings, both ways

Sunbank now talks back. One live connection carries your readings up *and* brings Sunbank's computed states and warnings back down — instantly, the moment they change.

- **New live entities** — `Home energy state`, `Battery`, `Runtime remaining`, `Solar now`, `Load now`, `Battery flow`, `Home health`, and a `Status message`. These are computed by Sunbank and pushed to HA, ready for dashboards and automations.
- **Real-time warnings** — a binary sensor per alert (`Power about to run out`, `Running low`, `Heavy load on a low battery`, `Battery low`) plus a `Warning active` summary. They flip on the instant Sunbank raises them — wire them to a notification and you'll know *before* a heavy appliance drains the battery, not after.
- **`sunbank_warning` events** — Sunbank fires an event on HA's bus when a warning is raised or cleared, for event-style automations.
- **Faster, tougher link** — readings now stream over a live WebSocket (with automatic REST fallback if it drops, so nothing is lost). The `Status` sensor shows `live` when the real-time socket is up.

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
