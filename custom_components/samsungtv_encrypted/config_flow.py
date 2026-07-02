"""Config flow for SamsungTV Encrypted."""
import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_MAC, CONF_NAME, CONF_PORT

from . import DOMAIN
from .PySmartCrypto.pysmartcrypto import PySmartCrypto

_LOGGER = logging.getLogger(__name__)

CONF_PIN = "pin"
CONF_TOKEN = "token"
CONF_SESSIONID = "sessionid"
CONF_KEY_POWER_OFF = "key_power_off"
DEFAULT_KEY_POWER_OFF = "KEY_POWEROFF"
DEFAULT_NAME = "Samsung TV Remote"
DEFAULT_PORT = 8080


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
            self._name = user_input.get(CONF_NAME, DEFAULT_NAME)
            self._mac = user_input.get(CONF_MAC)
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
                    vol.Optional(CONF_NAME, default=self._name): str,
                    vol.Optional(CONF_MAC): str,
                    vol.Optional(
                        CONF_KEY_POWER_OFF, default=self._key_power_off
                    ): str,
                }
            ),
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
            except Exception:
                _LOGGER.exception("Could not finish Samsung TV pairing")
                errors["base"] = "cannot_connect"
            else:
                if not pairing_data:
                    errors["base"] = "invalid_pin"
                else:
                    self._pairing.close()
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
