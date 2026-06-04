# Sunbank — Home Assistant integration

Pushes your Home Assistant sensor data up to your [Sunbank](https://github.com/DominionZA/sunbank)
account via the Sunbank API, and shows the link's health back in HA.

## Install (HACS)
1. HACS → ⋮ → **Custom repositories** → add `https://github.com/DominionZA/sunbank-ha`, type **Integration**.
2. Find **Sunbank** in HACS → **Download**.
3. Restart Home Assistant.
4. Settings → Devices & Services → **Add Integration** → **Sunbank**.
5. In Sunbank, create/open a **Home Assistant (push)** integration and copy that card's **Push key**. Enter your Sunbank **server URL** and that **Push key** in Home Assistant.

No secrets live in this repo — the API key is entered by each user at setup.

## How it shows up in HA

The integration is a **two-way bridge** over a single live WebSocket: it streams your sensor
readings up to Sunbank, and Sunbank streams its computed **states and warnings back** — in real
time, the instant they change. HA holds the raw sensors; Sunbank is the brain; the entities below
are what it tells you. The richer dashboards live in the [Sunbank app](https://github.com/DominionZA/sunbank).

You interact with it in two places:

**Its setup screen** — the only config UI it has.
`Settings → Devices & Services → Sunbank → Configure`. Here you set the server URL, API
Push key, and (v0.3.0+) pick which sensors are your **indoor/outdoor temperature & humidity**.
Only the sensors you pick are sent — nothing is published by default.

> If **Configure** doesn't show the four sensor pickers, you're on a pre-0.3.0 entry:
> delete it and **Add Integration → Sunbank** to get the new form.

**Its entities** — open the Sunbank device. Sunbank pushes these live (v0.4.0+):

| Entity | What it is |
|--------|------------|
| `Home energy state` | `surplus` / `charging` / `solar_deficit` / `on_battery` — the whole-home posture |
| `Battery` | usable battery % (inverter cutoff = 0%) |
| `Runtime remaining` | hours until the house switches off at the current draw |
| `Solar now` / `Load now` / `Battery flow` | live power in / used / into-or-out-of the battery |
| `Home health` | 0–100 score; `Status message` | plain-English summary |
| `Warning active` + one binary sensor per warning | `Power about to run out`, `Running low`, `Heavy load on a low battery`, `Battery low` |

The warning binary sensors flip on the moment Sunbank raises them — wire them to notifications or
automations ("if *Power about to run out* → notify me / switch off the geyser"). Sunbank also fires
a `sunbank_warning` event on the HA bus (`raised`/`cleared`) for event-style automations.

Diagnostic entities (link health): `Status` (`live` = real-time socket up, `online` = REST
fallback, `error` = not delivering), `Last upload`, `Readings sent`.
