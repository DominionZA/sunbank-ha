"""Constants for the Sunbank integration."""

DOMAIN = "sunbank"

CONF_BASE_URL = "base_url"
CONF_API_KEY = "api_key"
CONF_SITE = "site"
CONF_SOURCE = "source"
CONF_INTERVAL = "interval"

# Weather sensors the user authorises here in the integration (the integration owns identification;
# the app just receives them already labelled). Each maps to a Sunbank environment.* metric.
CONF_INDOOR_TEMP = "indoor_temp"
CONF_INDOOR_HUM = "indoor_humidity"
CONF_OUTDOOR_TEMP = "outdoor_temp"
CONF_OUTDOOR_HUM = "outdoor_humidity"
ENV_ROLE_METRIC = {
    CONF_INDOOR_TEMP: "environment.indoor_temperature",
    CONF_INDOOR_HUM: "environment.indoor_humidity",
    CONF_OUTDOOR_TEMP: "environment.outdoor_temperature",
    CONF_OUTDOOR_HUM: "environment.outdoor_humidity",
}

DEFAULT_BASE_URL = "http://localhost:8137"
DEFAULT_SITE = "home"
DEFAULT_SOURCE = "home_assistant"
# Real-time changes flow via HA state-change events; this is the heartbeat keep-alive interval
# (also what the liveness indicator is sized against, so keep it modest).
DEFAULT_INTERVAL = 60
