"""Config flow for an Atrea RD5 unit."""

from __future__ import annotations

from typing import Any

from modbus_connection import ModbusError, ModbusTcpParams
import voluptuous as vol

from homeassistant.components.modbus import async_get_temporary_unit
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    TextSelector,
)

from .const import (
    CONF_INDOOR_TEMPERATURE_ENTITY,
    CONF_OUTDOOR_TEMPERATURE_ENTITY,
    DEFAULT_PORT,
    DOMAIN,
    UNIT_ID,
)
from .vendor.atrea_modbus.rd5 import AtreaRD5

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): TextSelector(),
        vol.Required(CONF_PORT, default=DEFAULT_PORT): vol.All(
            NumberSelector(
                NumberSelectorConfig(mode=NumberSelectorMode.BOX, min=1, max=65535)
            ),
            vol.Coerce(int),
        ),
    }
)

TEMPERATURE_SENSOR = EntitySelector(
    EntitySelectorConfig(domain="sensor", device_class="temperature")
)
OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_INDOOR_TEMPERATURE_ENTITY): TEMPERATURE_SENSOR,
        vol.Optional(CONF_OUTDOOR_TEMPERATURE_ENTITY): TEMPERATURE_SENSOR,
    }
)


class AtreaConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for an Atrea RD5 unit."""

    VERSION = 1

    async def _async_probe(self, data: dict[str, Any]) -> AtreaRD5:
        """Read the unit behind the given address once, or raise."""
        params = ModbusTcpParams(host=data[CONF_HOST], port=data[CONF_PORT])
        async with async_get_temporary_unit(self.hass, params, UNIT_ID) as unit:
            device = AtreaRD5(unit)
            await device.async_update()
        return device

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for the address of the unit, then read the unit behind it."""
        errors: dict[str, str] = {}
        placeholders: dict[str, str] = {"error": ""}
        if user_input is not None:
            try:
                device = await self._async_probe(user_input)
            except (ModbusError, HomeAssistantError) as err:
                errors["base"] = "cannot_connect"
                placeholders["error"] = str(err) or type(err).__name__
            else:
                if device.control.requested_mode is None:
                    # Something answers, but not with the register map of RD5.
                    errors["base"] = "not_rd5"
                else:
                    # A unit that does not tell its production number is
                    # known by its address.
                    await self.async_set_unique_id(
                        device.serial_number or user_input[CONF_HOST]
                    )
                    self._abort_if_unique_id_configured(updates=user_input)
                    return self.async_create_entry(
                        title=f"Atrea {device.model}", data=user_input
                    )
        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(
                STEP_USER_DATA_SCHEMA, user_input
            ),
            errors=errors,
            description_placeholders=placeholders,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> AtreaOptionsFlow:
        """Create the options flow."""
        return AtreaOptionsFlow()


class AtreaOptionsFlow(OptionsFlow):
    """Choose the sensors whose temperature is sent to the unit."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                OPTIONS_SCHEMA, self.config_entry.options
            ),
        )
