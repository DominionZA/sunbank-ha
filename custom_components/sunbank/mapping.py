"""HA entity_id -> Sunbank catalog metric key.

Starter set (the recovery-question core). The Sunbank metric keys come from the published
catalog (GET /v1/metrics); units are implied by the key, so we only send the value.
This will become user-configurable in the UI; hard-coded for v0.
"""

ENTITY_METRICS: dict[str, str] = {
    "sensor.inverter_battery": "battery.soc",
    "sensor.inverter_battery_power": "battery.power",
    "sensor.inverter_pv_power": "solar.pv_power",
    "sensor.inverter_load_power": "load.power",
}
