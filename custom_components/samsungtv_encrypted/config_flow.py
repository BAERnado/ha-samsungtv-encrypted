"""Config flow for SamsungTV Encrypted."""
import logging
from urllib.parse import urlparse

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_MAC, CONF_NAME, CONF_PORT

from . import DOMAIN
from .network import get_arp_mac
from .PySmartCrypto.pysmartcrypto import PairingError, PySmartCrypto

_LOGGER = logging.getLogger(__name__)

CONF_PIN = "pin"
CONF_TOKEN = "token"
CONF_SESSIONID = "sessionid"
CONF_KEY_POWER_OFF = "key_power_off"
DEFAULT_KEY_POWER_OFF = "KEY_POWEROFF"
DEFAULT_NAME = "Samsung TV Remote"
DEFAULT_PORT = 8080

SSDP_UPNP_UDN = ("udn", "UDN")
SSDP_UPNP_FRIENDLY_NAME = ("friendlyName", "friendly_name", "name")
SSDP_UPNP_MODEL_NAME = ("modelName", "model_name")


def _strip_uuid(value):
    """Strip SSDP uuid prefix."""
    return value.removeprefix("uuid:")


def _discovery_attr(discovery_info, name, default=None):
    """Read discovery data from modern service info objects or dicts."""
    if isinstance(discovery_info, dict):
        return discovery_info.get(name, default)
    return getattr(discovery_info, name, default)


def _upnp_value(upnp, keys, default=None):
    """Read the first matching UPnP value."""
    if not upnp:
        return default
    for key in keys:
        if key in upnp:
            return upnp[key]
    return default


class SamsungTVEncryptedConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a SamsungTV Encrypted config flow."""

    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        self._host = None
        self._port = DEFAULT_PORT
        self._name = DEFAULT_NAME
        self._mac = None
        self._key_power_off = DEFAULT_KEY_POWER_OFF
        self._pairing = None

    async def async_step_user(self, user_input=None):
        """Start pairing with the TV."""
        errors = {}

        if user_input is not None:
            self._host = user_input[CONF_HOST]
            self._port = user_input.get(CONF_PORT, DEFAULT_PORT)
            self._key_power_off = user_input.get(
                CONF_KEY_POWER_OFF, DEFAULT_KEY_POWER_OFF
            )

            await self.async_set_unique_id(self._host)
            self._abort_if_unique_id_configured()

            try:
                self._pairing = await self.hass.async_add_executor_job(
                    PySmartCrypto.start_pairing, self._host, self._port
                )
            except Exception:
                _LOGGER.exception("Could not start Samsung TV pairing")
                errors["base"] = "cannot_connect"
            else:
                return await self.async_step_pin()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Optional(CONF_PORT, default=self._port): int,
                    vol.Optional(
                        CONF_KEY_POWER_OFF, default=self._key_power_off
                    ): str,
                }
            ),
            errors=errors,
        )

    async def async_step_ssdp(self, discovery_info):
        """Handle a flow initialized by SSDP discovery."""
        _LOGGER.debug("Samsung TV found via SSDP: %s", discovery_info)
        location = _discovery_attr(discovery_info, "ssdp_location")
        host = urlparse(location or "").hostname
        if not host:
            return self.async_abort(reason="cannot_connect")

        upnp = _discovery_attr(discovery_info, "upnp", {}) or {}
        name = _upnp_value(upnp, SSDP_UPNP_FRIENDLY_NAME)
        model = _upnp_value(upnp, SSDP_UPNP_MODEL_NAME)
        udn = _upnp_value(upnp, SSDP_UPNP_UDN)

        self._host = host
        self._port = DEFAULT_PORT
        self._name = (name or model or DEFAULT_NAME).replace("[TV] ", "")
        self._mac = await self.hass.async_add_executor_job(get_arp_mac, self._host)
        self._key_power_off = DEFAULT_KEY_POWER_OFF

        unique_id = _strip_uuid(udn) if udn else self._host
        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured()

        return await self.async_step_confirm()

    async def async_step_confirm(self, user_input=None):
        """Confirm a discovered Samsung TV before pairing."""
        errors = {}

        if user_input is not None:
            try:
                self._pairing = await self.hass.async_add_executor_job(
                    PySmartCrypto.start_pairing, self._host, self._port
                )
            except Exception:
                _LOGGER.exception("Could not start Samsung TV pairing")
                errors["base"] = "cannot_connect"
            else:
                return await self.async_step_pin()

        self.context["title_placeholders"] = {"name": self._name}
        return self.async_show_form(
            step_id="confirm",
            description_placeholders={
                "name": self._name,
                "host": self._host,
            },
            errors=errors,
        )

    async def async_step_pin(self, user_input=None):
        """Finish pairing with the PIN displayed on the TV."""
        errors = {}

        if user_input is not None:
            try:
                pairing_data = await self.hass.async_add_executor_job(
                    self._pairing.finish_pairing, user_input[CONF_PIN]
                )
            except PairingError as err:
                _LOGGER.warning("Samsung TV pairing failed: %s", err)
                errors["base"] = "pairing_failed"
            except Exception:
                _LOGGER.exception("Could not finish Samsung TV pairing")
                errors["base"] = "cannot_connect"
            else:
                if not pairing_data:
                    errors["base"] = "invalid_pin"
                else:
                    self._pairing.close()
                    if not self._mac:
                        self._mac = await self.hass.async_add_executor_job(
                            get_arp_mac, self._host
                        )
                        if self._mac:
                            _LOGGER.info(
                                "Detected Samsung TV MAC address from ARP cache"
                            )
                    return self.async_create_entry(
                        title=self._name,
                        data={
                            CONF_HOST: self._host,
                            CONF_PORT: self._port,
                            CONF_NAME: self._name,
                            CONF_MAC: self._mac,
                            CONF_KEY_POWER_OFF: self._key_power_off,
                            CONF_TOKEN: pairing_data[CONF_TOKEN],
                            CONF_SESSIONID: pairing_data[CONF_SESSIONID],
                        },
                    )

        return self.async_show_form(
            step_id="pin",
            data_schema=vol.Schema({vol.Required(CONF_PIN): str}),
            errors=errors,
        )
