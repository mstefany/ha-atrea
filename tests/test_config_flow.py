"""Test the config flow."""

from __future__ import annotations

from modbus_connection import ModbusTimeoutError
from modbus_connection.mock import MockModbusUnit
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.atrea.const import (
    CONF_CLIMATE_SETS_SEASON,
    CONF_INDOOR_TEMPERATURE_ENTITY,
    DOMAIN,
)

from .conftest import SERIAL

USER_INPUT = {CONF_HOST: "192.0.2.10", CONF_PORT: 502}


async def test_user_flow_creates_an_entry(hass: HomeAssistant) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Atrea DUPLEX R_5"
    assert result["data"] == USER_INPUT
    assert result["result"].unique_id == SERIAL


async def test_silent_unit_shows_an_error_and_recovers(
    hass: HomeAssistant, unit: MockModbusUnit
) -> None:
    unit.fail_requests(ModbusTimeoutError())
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=USER_INPUT
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}

    unit.fail_requests(None)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_device_that_is_not_rd5_is_refused(
    hass: HomeAssistant, unit: MockModbusUnit
) -> None:
    unit.holding[10715] = 99  # not an operating mode
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=USER_INPUT
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "not_rd5"}


async def test_same_unit_is_not_added_twice(
    hass: HomeAssistant, entry: MockConfigEntry
) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_HOST: "192.0.2.99", CONF_PORT: 502},
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    # The unit moved to a new address: the entry follows it.
    assert entry.data[CONF_HOST] == "192.0.2.99"


async def test_options_flow_saves_the_choices(
    hass: HomeAssistant, loaded: MockConfigEntry
) -> None:
    result = await hass.config_entries.options.async_init(loaded.entry_id)
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_INDOOR_TEMPERATURE_ENTITY: "sensor.room",
            CONF_CLIMATE_SETS_SEASON: True,
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert loaded.options == {
        CONF_INDOOR_TEMPERATURE_ENTITY: "sensor.room",
        CONF_CLIMATE_SETS_SEASON: True,
    }
