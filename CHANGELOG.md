# Changelog

All notable changes to the Sunbank Home Assistant integration. These notes also
appear as the update descriptions in HACS (they're published as GitHub Releases).

## v0.4.1 — Sunbank looks like a real device now

Before, Sunbank's bits were scattered around Home Assistant. Now they live together as one Sunbank device. Open it (Settings → Devices & Services → Sunbank) and you'll see what it is, which version you're on, and a link straight to your Sunbank dashboard — everything in one place.

There's also a "Download diagnostics" button for when something's not right. It hands you a tidy summary — with your key hidden — that you can read or send on, instead of digging through logs.

## v0.4.0 — Sunbank talks back now, in real time

Until now this just sent your data up to Sunbank. Now Sunbank sends its answers straight back, the moment things change — no waiting, no refreshing.

- **Your home's status, live in Home Assistant** — battery level, how long it'll last, solar coming in, power being used, and a plain summary of how things are going. All kept current the instant anything changes.
- **A heads-up before it's too late** — Sunbank tells you when power's about to run out, when you're getting low, or when something big is draining a low battery. Hook any of these up to a phone notification, and if someone switches on the kettle when the battery's nearly flat, you'll hear about it *now* — not once the lights are already off.
- **A connection that looks after itself** — faster than before, and if it ever drops it quietly reconnects and catches up, so nothing slips through.

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
