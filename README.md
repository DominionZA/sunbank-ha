# Sunbank — Home Assistant integration

Pushes your Home Assistant sensor data up to your [Sunbank](https://github.com/DominionZA/sunbank)
account via the Sunbank API, and shows the link's health back in HA.

## Install (HACS)
1. HACS → ⋮ → **Custom repositories** → add `https://github.com/DominionZA/sunbank-ha`, type **Integration**.
2. Find **Sunbank** in HACS → **Download**.
3. Restart Home Assistant.
4. Settings → Devices & Services → **Add Integration** → **Sunbank**.
5. Enter your Sunbank **server URL** and **API key** (from the Sunbank dashboard → Settings → Account).

No secrets live in this repo — the API key is entered by each user at setup.

## How it shows up in HA

There's no dashboard card or panel — that's deliberate. This is a **background uploader**:
HA holds the sensors, the integration is the pipe, and the [Sunbank app](https://github.com/DominionZA/sunbank)
is where you actually look. Once it's set up there's nothing to drive on the HA side.

You interact with it in two places:

**Its setup screen** — the only config UI it has.
`Settings → Devices & Services → Sunbank → Configure`. Here you set the server URL, API
key, and (v0.3.0+) pick which sensors are your **indoor/outdoor temperature & humidity**.
Only the sensors you pick are sent — nothing is published by default.

> If **Configure** doesn't show the four sensor pickers, you're on a pre-0.3.0 entry:
> delete it and **Add Integration → Sunbank** to get the new form.

**Its health sensors** — open the Sunbank device to see three diagnostic entities:

| Sensor | What it tells you |
|--------|-------------------|
| `Status` | `online` when the link is healthy, `error` if pushes are failing |
| `Last upload` | timestamp of the most recent successful push |
| `Readings sent` | running count of readings delivered |

If `Status` is `online` and `Last upload` keeps ticking, it's working. Drop these onto a
dashboard if you want an at-a-glance health check.
