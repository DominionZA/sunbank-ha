"""HA entity_id -> Sunbank catalog metric key, plus per-metric change-of-value tuning.

The Sunbank metric keys come from the published catalog (GET /v1/metrics); units are implied by
the key, so we only send the value. This will become user-configurable in the UI; hard-coded v0.
"""

ENTITY_METRICS: dict[str, str] = {
    "sensor.inverter_battery": "battery.soc",
    "sensor.inverter_battery_power": "battery.power",
    "sensor.inverter_pv_power": "solar.pv_power",
    "sensor.inverter_load_power": "load.power",
    # Grid / mains — power drawn from (or fed to) the grid, and a clean on/off state. Knowing the grid
    # is on changes everything downstream (solar stops being the only source), and the on/off history is
    # what lets us measure off-grid streaks. binary_sensor 'on'/'off' is sent as 1/0 (see _to_float).
    "sensor.inverter_grid_power": "grid.power",
    # BOOTSTRAP DEFAULT ONLY: this must become user-configurable in Sunbank's mapping UI. The product
    # contract is the Sunbank metric key (grid.connected), not this HA entity_id. This local helper is
    # Michael's current source of truth for grid supply; other homes may use a template, switch, helper,
    # Homey flow, direct inverter register, etc. The adapter maps that local truth into grid.connected.
    # The Solarman binary_sensor.inverter_grid reports inverter-side grid presence and can remain "on"
    # while the house is intentionally off-grid.
    "input_boolean.grid_supply": "grid.connected",
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
    "grid.power":     (40, 2),
    "grid.connected": (0.5, 0),   # any on↔off flip sends immediately — the transition is the event
    "environment.indoor_temperature":  (0.3, 60),
    "environment.indoor_humidity":     (1, 60),
    "environment.outdoor_temperature": (0.3, 60),
    "environment.outdoor_humidity":    (1, 60),
}

# Heartbeat: push the current value of every metric at least this often even when nothing changed,
# so a steady reading is distinguishable from a dead feed. Real-time changes flow via events; this
# is just the keep-alive. (The config entry's interval overrides this if set.)
HEARTBEAT_S = 300
