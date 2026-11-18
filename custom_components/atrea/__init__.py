"""Integrate Atrea DUPLEX ventilation units with RD5 control into Home Assistant."""

from __future__ import annotations

from modbus_connection import ModbusTcpParams

from homeassistant.components.modbus import async_get_unit
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant

from .const import SCAN_INTERVAL, SETTINGS_SCAN_INTERVAL, UNIT_ID
from .coordinator import (
    AtreaConfigEntry,
    AtreaCoordinator,
    AtreaReadingsCoordinator,
    AtreaRuntimeData,
)
from .vendor.atrea_modbus.rd5 import AtreaRD5

PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.CLIMATE,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]


async def async_setup_entry(hass: HomeAssistant, entry: AtreaConfigEntry) -> bool:
    """Set up a unit from a config entry."""
    # The connection belongs to the modbus integration, which shares it with
    # every other integration that asks for the same host and port.
    unit = async_get_unit(
        hass,
        entry,
        ModbusTcpParams(host=entry.data[CONF_HOST], port=entry.data[CONF_PORT]),
        UNIT_ID,
    )
    device = AtreaRD5(unit)
    readings = AtreaReadingsCoordinator(
        hass,
        entry,
        f"{entry.title} readings",
        device,
        device.async_update_readings,
        SCAN_INTERVAL,
    )
    settings = AtreaCoordinator(
        hass,
        entry,
        f"{entry.title} settings",
        device,
        device.async_update_settings,
        SETTINGS_SCAN_INTERVAL,
    )
    # The first read opens the link; a unit that is off makes setup retry.
    await readings.async_config_entry_first_refresh()
    await settings.async_config_entry_first_refresh()

    entry.runtime_data = AtreaRuntimeData(
        device=device,
        readings=readings,
        settings=settings,
        unique_id=entry.unique_id or entry.entry_id,
    )
    readings.async_watch_sources()
    entry.async_on_unload(readings.async_stop_watching)
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _async_options_updated(hass: HomeAssistant, entry: AtreaConfigEntry) -> None:
    """Send the newly chosen temperatures without waiting for the next poll."""
    entry.runtime_data.readings.async_watch_sources()
    await entry.runtime_data.readings.async_request_refresh()


async def async_unload_entry(hass: HomeAssistant, entry: AtreaConfigEntry) -> bool:
    """Unload a config entry. The modbus integration closes the connection."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
