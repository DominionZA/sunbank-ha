"""Constants for the Sunbank integration."""

DOMAIN = "sunbank"

CONF_BASE_URL = "base_url"
CONF_API_KEY = "api_key"
CONF_SITE = "site"
CONF_SOURCE = "source"
CONF_INTERVAL = "interval"

DEFAULT_BASE_URL = "http://localhost:8137"
DEFAULT_SITE = "home"
DEFAULT_SOURCE = "home_assistant"
# Real-time changes flow via HA state-change events; this is the heartbeat keep-alive interval
# (also what the liveness indicator is sized against, so keep it modest).
DEFAULT_INTERVAL = 60
