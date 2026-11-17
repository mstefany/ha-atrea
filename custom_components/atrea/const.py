"""Constants for the Atrea integration."""

from datetime import timedelta

DOMAIN = "atrea"
MANUFACTURER = "Atrea"

DEFAULT_PORT = 502
# The unit answers every unit id from 1 to 255.
UNIT_ID = 1

SCAN_INTERVAL = timedelta(seconds=30)
SETTINGS_SCAN_INTERVAL = timedelta(minutes=5)

# Options: sensors whose temperature is sent to the unit.
CONF_INDOOR_TEMPERATURE_ENTITY = "indoor_temperature_entity"
CONF_OUTDOOR_TEMPERATURE_ENTITY = "outdoor_temperature_entity"
