"""Diagnostics for an Atrea RD5 unit."""

from __future__ import annotations

from typing import Any

from modbus_connection import ModbusError

from homeassistant.core import HomeAssistant

from .coordinator import AtreaConfigEntry


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: AtreaConfigEntry
) -> dict[str, Any]:
    """Return the raw register map of the unit, without its production number."""
    runtime_data = entry.runtime_data
    device = runtime_data.device
    raw = read_error = None
    try:
        # The raw dump of the library leaves the production number out.
        raw = await device.async_read_raw()
    except ModbusError as err:
        read_error = str(err) or type(err).__name__
    reports = {
        "readings": runtime_data.readings.data,
        "settings": runtime_data.settings.data,
    }
    return {
        "model": device.model,
        "firmware": device.firmware_version,
        "available_modes": [mode.name.lower() for mode in device.available_modes],
        "updated": {
            name: sorted(report.updated) for name, report in reports.items() if report
        },
        "failed": {
            name: {part: str(err) for part, err in report.failed.items()}
            for name, report in reports.items()
            if report
        },
        "read_error": read_error,
        "registers": raw,
    }
