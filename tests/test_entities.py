"""Test the entities against a captured unit."""

from __future__ import annotations

from modbus_connection import IllegalDataAddressError, ModbusTimeoutError
from modbus_connection.mock import MockModbusUnit
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr

from custom_components.atrea.const import DOMAIN

from .conftest import SERIAL, Writes

P = "atrea_duplex_r_5"
CLIMATE = f"climate.{P}"


def state(hass: HomeAssistant, entity_id: str) -> str:
    found = hass.states.get(entity_id)
    assert found is not None, entity_id
    return found.state


async def call(
    hass: HomeAssistant, domain: str, service: str, entity_id: str, **data: object
) -> None:
    await hass.services.async_call(
        domain, service, {"entity_id": entity_id, **data}, blocking=True
    )


async def test_device_and_states(hass: HomeAssistant, loaded: MockConfigEntry) -> None:
    devices = dr.async_entries_for_config_entry(dr.async_get(hass), loaded.entry_id)
    assert len(devices) == 1
    device = devices[0]
    assert device.identifiers == {(DOMAIN, SERIAL)}
    assert device.manufacturer == "Atrea"
    assert device.model == "DUPLEX R_5"
    assert device.sw_version == "2.03.41"

    climate = hass.states.get(CLIMATE)
    assert climate is not None
    assert climate.state == "heat"
    assert climate.attributes["current_temperature"] == 22.5
    assert climate.attributes["temperature"] == 22.5
    assert climate.attributes["preset_mode"] == "circulation_with_ventilation"
    assert climate.attributes["fan_mode"] == "norm_max"
    assert "night_precooling" not in climate.attributes["preset_modes"]

    assert state(hass, f"sensor.{P}_outdoor_air_temperature") == "6.9"
    assert state(hass, f"sensor.{P}_supply_air_flow") == "422"
    assert state(hass, f"sensor.{P}_heat_storage_top_temperature") == "47.1"
    assert state(hass, f"sensor.{P}_current_season") == "heating"
    assert state(hass, f"binary_sensor.{P}_filter_change") == "on"
    assert state(hass, f"binary_sensor.{P}_fault") == "off"
    assert state(hass, f"select.{P}_operating_mode") == "circulation_with_ventilation"
    assert state(hass, f"select.{P}_power_level") == "norm_max"
    assert state(hass, f"select.{P}_season") == "heating"
    assert state(hass, f"switch.{P}_weekly_program") == "off"
    assert state(hass, f"switch.{P}_heat_storage_electric_heater_2") == "on"
    assert state(hass, f"number.{P}_heat_storage_top_target_temperature") == "48.0"


async def test_unit_without_heat_storage_has_no_storage_entities(
    hass: HomeAssistant, unit: MockModbusUnit, entry: MockConfigEntry
) -> None:
    unit.discrete[10212] = False
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get(f"sensor.{P}_heat_storage_top_temperature") is None
    assert hass.states.get(f"switch.{P}_heat_storage_electric_heater_1") is None
    assert hass.states.get(CLIMATE) is not None


async def test_setup_retries_when_the_unit_is_silent(
    hass: HomeAssistant, unit: MockModbusUnit, entry: MockConfigEntry
) -> None:
    unit.fail_requests(ModbusTimeoutError())
    assert not await hass.config_entries.async_setup(entry.entry_id)
    assert entry.state.name == "SETUP_RETRY"


async def test_climate_writes(
    hass: HomeAssistant, loaded: MockConfigEntry, writes: Writes
) -> None:
    await call(hass, "climate", "set_temperature", CLIMATE, temperature=21.5)
    assert writes == [("holding", 10710, [215])]
    assert hass.states.get(CLIMATE).attributes["temperature"] == 21.5

    writes.clear()
    await call(hass, "climate", "set_preset_mode", CLIMATE, preset_mode="ventilation")
    # The power follows the mode: Norm/Max becomes ventilation Max.
    assert writes == [("holding", 10709, [2]), ("holding", 10708, [12])]
    assert hass.states.get(CLIMATE).attributes["preset_mode"] == "ventilation"
    assert hass.states.get(CLIMATE).attributes["fan_mode"] == "ventilation_max"

    writes.clear()
    await call(hass, "climate", "set_hvac_mode", CLIMATE, hvac_mode="off")
    assert writes == [("holding", 10709, [0])]
    assert state(hass, CLIMATE) == "off"

    # Switching on returns to the mode the unit had before.
    writes.clear()
    await call(hass, "climate", "turn_on", CLIMATE)
    assert writes == [("holding", 10709, [2])]
    assert state(hass, CLIMATE) == "heat"

    # Cool is the non-heating season.
    writes.clear()
    await call(hass, "climate", "set_hvac_mode", CLIMATE, hvac_mode="cool")
    assert writes == [("holding", 11401, [1])]
    assert state(hass, CLIMATE) == "cool"
    assert state(hass, f"select.{P}_season") == "non_heating"


async def test_weekly_program_makes_a_change_temporary(
    hass: HomeAssistant, unit: MockModbusUnit, entry: MockConfigEntry, writes: Writes
) -> None:
    for address in range(10700, 10704):
        unit.holding[address] = 1
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert state(hass, f"switch.{P}_weekly_program") == "on"

    await call(hass, "climate", "set_temperature", CLIMATE, temperature=20)
    assert writes == [("holding", 10710, [200]), ("holding", 10702, [2])]


async def test_mode_the_unit_does_not_accept_is_refused(
    hass: HomeAssistant, loaded: MockConfigEntry, writes: Writes
) -> None:
    with pytest.raises(HomeAssistantError):
        await call(
            hass,
            "select",
            "select_option",
            f"select.{P}_operating_mode",
            option="night_precooling",
        )
    assert writes == []


async def test_other_writes(
    hass: HomeAssistant, loaded: MockConfigEntry, writes: Writes
) -> None:
    await call(
        hass, "select", "select_option", f"select.{P}_season", option="t_oda_plus"
    )
    await call(
        hass, "switch", "turn_off", f"switch.{P}_heat_storage_electric_heater_2"
    )
    await call(
        hass,
        "number",
        "set_value",
        f"number.{P}_heat_storage_top_target_temperature",
        value=50,
    )
    await call(hass, "button", "press", f"button.{P}_reset_filter_change_interval")
    await call(hass, "switch", "turn_on", f"switch.{P}_weekly_program")
    assert writes == [
        ("holding", 11401, [3]),
        ("holding", 12915, [0]),
        ("holding", 12925, [500]),
        ("coil", 10007, [True]),
        ("holding", 10700, [1, 1, 1, 1]),
    ]
    assert state(hass, CLIMATE) == "heat_cool"
    assert state(hass, f"switch.{P}_weekly_program") == "on"


async def test_failing_part_makes_only_its_entities_unavailable(
    hass: HomeAssistant, loaded: MockConfigEntry, unit: MockModbusUnit
) -> None:
    unit.fail_read(11100, IllegalDataAddressError(), register_type="discrete")
    await loaded.runtime_data.readings.async_refresh()
    await hass.async_block_till_done()
    assert state(hass, f"binary_sensor.{P}_fault") == "unavailable"
    assert state(hass, CLIMATE) == "heat"


async def test_room_temperature_is_sent_to_the_unit(
    hass: HomeAssistant, entry: MockConfigEntry, writes: Writes
) -> None:
    hass.states.async_set(
        "sensor.room", "21.36", {"unit_of_measurement": "°C", "device_class": "temperature"}
    )
    hass.config_entries.async_update_entry(
        entry, options={"indoor_temperature_entity": "sensor.room"}
    )
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert ("holding", 10214, [214]) in writes

    # A sensor without a value is not sent, so the unit raises its own fault.
    writes.clear()
    hass.states.async_set("sensor.room", "unavailable")
    await entry.runtime_data.readings.async_refresh()
    assert writes == []


async def test_diagnostics_leave_the_production_number_out(
    hass: HomeAssistant, loaded: MockConfigEntry
) -> None:
    from custom_components.atrea.diagnostics import async_get_config_entry_diagnostics

    result = await async_get_config_entry_diagnostics(hass, loaded)
    assert result["firmware"] == "2.03.41"
    assert 12300 not in result["registers"]["holding"]
    assert result["registers"]["holding"][10715] == 3
    assert SERIAL not in str(result)
