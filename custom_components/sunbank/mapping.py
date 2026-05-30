"""HA entity_id -> Sunbank catalog metric key, plus per-metric change-of-value tuning.

The Sunbank metric keys come from the published catalog (GET /v1/metrics); units are implied by
the key, so we only send the value. This will become user-configurable in the UI; hard-coded v0.
"""

ENTITY_METRICS: dict[str, str] = {
    "sensor.inverter_battery": "battery.soc",
    "sensor.inverter_battery_power": "battery.power",
    "sensor.inverter_pv_power": "solar.pv_power",
    "sensor.inverter_load_power": "load.power",
}

# Change-of-value tuning per metric: (deadband, throttle_seconds).
#   deadband         — minimum change (in the metric's units) worth sending; kills sensor noise.
#   throttle_seconds — minimum gap between sends for that metric; a hard anti-spam ceiling.
# We push within ~2s of any change that clears these — near real-time, but not chatty.
COV: dict[str, tuple[float, float]] = {
    "battery.soc":    (0.5, 10),
    "battery.power":  (40, 2),
    "solar.pv_power": (40, 2),
    "load.power":     (40, 2),
}

# Heartbeat: push the current value of every metric at least this often even when nothing changed,
# so a steady reading is distinguishable from a dead feed. Real-time changes flow via events; this
# is just the keep-alive. (The config entry's interval overrides this if set.)
HEARTBEAT_S = 300
