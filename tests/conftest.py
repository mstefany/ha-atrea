"""Fixtures: the integration over the in-memory mock unit of modbus-connection."""

from __future__ import annotations

from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager
import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

from modbus_connection.mock import MockModbusConnection, MockModbusUnit, WriteEvent
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant

from custom_components.atrea.const import DOMAIN

FIXTURES = Path(__file__).parent / "fixtures"
SERIAL = "0A1234567"

Writes = list[tuple[str, int, list[int] | list[bool]]]


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Let Home Assistant load the integration under test."""


@pytest.fixture(autouse=True)
def no_settle_delay() -> Generator[None]:
    """The mock unit applies a write at once."""
    with patch("custom_components.atrea.entity.WRITE_SETTLE_SECONDS", 0):
        yield


@pytest.fixture
def unit() -> MockModbusUnit:
    """A DUPLEX RB5 with a heat pump and an integrated heat storage tank."""
    unit = MockModbusConnection().for_unit(1)
    unit.load_raw(json.loads((FIXTURES / "rb5_heat_pump_izt.json").read_text()))
    return unit


@pytest.fixture
def writes(unit: MockModbusUnit) -> Writes:
    """Every write the unit received, and a unit that applies requested values."""
    log: Writes = []

    def record(event: WriteEvent) -> None:
        log.append((event.register_type, event.address, list(event.values)))
        # The unit copies a value set by hand into the requested value and
        # into the value in effect.
        if event.register_type == "holding" and 10708 <= event.address <= 10711:
            unit.holding[event.address - 4] = int(event.values[0])
            unit.holding[event.address + 6] = int(event.values[0])

    unit.on_write(record)
    return log


@pytest.fixture(autouse=True)
def modbus(unit: MockModbusUnit) -> Generator[None]:
    """Hand the mock unit to the integration in place of a real connection."""

    @asynccontextmanager
    async def temporary_unit(*args: Any) -> AsyncGenerator[MockModbusUnit]:
        yield unit

    with (
        patch("custom_components.atrea.async_get_unit", return_value=unit),
        patch(
            "custom_components.atrea.config_flow.async_get_temporary_unit",
            temporary_unit,
        ),
    ):
        yield


@pytest.fixture
def entry(hass: HomeAssistant) -> MockConfigEntry:
    """A config entry for the unit, not set up yet."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Atrea DUPLEX R_5",
        unique_id=SERIAL,
        data={CONF_HOST: "192.0.2.10", CONF_PORT: 502},
    )
    entry.add_to_hass(hass)
    return entry


@pytest.fixture
async def loaded(hass: HomeAssistant, entry: MockConfigEntry) -> MockConfigEntry:
    """The config entry, set up."""
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry
