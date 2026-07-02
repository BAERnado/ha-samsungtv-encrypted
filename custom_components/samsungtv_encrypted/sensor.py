"""Diagnostic sensors for SamsungTV Encrypted."""
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import CONF_HOST, CONF_MAC, CONF_NAME, CONF_PORT

DEFAULT_NAME = "Samsung TV Remote"
DEFAULT_PORT = 8080

SENSOR_DESCRIPTIONS = (
    ("host", "Host", CONF_HOST),
    ("port", "Port", CONF_PORT),
    ("mac", "MAC address", CONF_MAC),
)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up SamsungTV Encrypted diagnostic sensors."""
    async_add_entities(
        SamsungTVEncryptedDiagnosticSensor(entry, key, sensor_name, config_key)
        for key, sensor_name, config_key in SENSOR_DESCRIPTIONS
    )


class SamsungTVEncryptedDiagnosticSensor(SensorEntity):
    """Read-only SamsungTV Encrypted diagnostic sensor."""

    def __init__(self, entry, key, sensor_name, config_key):
        """Initialize the diagnostic sensor."""
        self._entry = entry
        self._key = key
        self._sensor_name = sensor_name
        self._config_key = config_key

    @property
    def name(self):
        """Return the sensor name."""
        data = {**self._entry.data, **self._entry.options}
        return f"{data.get(CONF_NAME, DEFAULT_NAME)} {self._sensor_name}"

    @property
    def native_value(self):
        """Return the configured value."""
        data = {**self._entry.data, **self._entry.options}
        value = data.get(self._config_key)
        if self._config_key == CONF_PORT:
            return value or DEFAULT_PORT
        return value or "unknown"

    @property
    def unique_id(self):
        """Return a unique ID for the sensor."""
        return f"{self._entry.entry_id}_{self._key}"
