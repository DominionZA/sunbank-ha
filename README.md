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
