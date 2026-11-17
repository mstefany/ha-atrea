"""What the unit is asked to do: mode, power, temperature and zone (tables 1-6).

Each of the four values has four registers: who decides it (H10700-H10703),
what the unit does now (H10704-H10707), the last value set by hand
(H10708-H10711), which is the one to write, and the value requested now
(H10714-H10717). The source document names the last group only in passing.
"""

from __future__ import annotations

from modbus_connection.model import Component, enum, gauge, integer

from .enums import ControlSource, OperatingMode

MIN_TEMPERATURE = 10.0
MAX_TEMPERATURE = 40.0


def _temperature(value: float) -> float:
    if not MIN_TEMPERATURE <= value <= MAX_TEMPERATURE:
        raise ValueError(
            f"temperature {value} is outside {MIN_TEMPERATURE}-{MAX_TEMPERATURE} °C"
        )
    return value


def _power(value: int) -> int:
    if not 0 <= value <= 100:
        raise ValueError(f"power {value} is outside 0-100")
    return value


def _zone(value: int) -> int:
    if not 0 <= value <= 2:
        raise ValueError(f"zone {value} is outside 0-2")
    return value


class Control(Component):
    """The requested operation of the unit."""

    power_source = enum(10700, ControlSource, writable=True)
    """Who decides the power."""
    mode_source = enum(10701, ControlSource, writable=True)
    """Who decides the operating mode."""
    temperature_source = enum(10702, ControlSource, writable=True)
    """Who decides the temperature."""
    zone_source = enum(10703, ControlSource, writable=True)
    """Who decides the zone."""

    power = integer(10704, signed=False)
    """Power of the current phase; see ``Configuration.fan_regulation``."""
    mode = enum(10705, OperatingMode)
    """Mode of the current phase. Automatic alternates between other modes."""
    temperature = gauge(10706, 0.1, unit="°C")
    """Temperature in effect."""
    zone = integer(10707, signed=False)
    """Zone in effect: 0 is zone 1, 1 is zone 2, 2 is both."""

    manual_power = integer(10708, signed=False, writable=_power)
    """Power last set by hand."""
    manual_mode = enum(10709, OperatingMode, writable=True)
    """Operating mode last set by hand."""
    manual_temperature = gauge(10710, 0.1, unit="°C", writable=_temperature)
    """Temperature last set by hand."""
    manual_zone = integer(10711, signed=False, writable=_zone)
    """Zone last set by hand."""

    forced_state = integer(10712, signed=False)
    """What overrides the request right now; see ``ForcedState``."""

    requested_power = integer(10714, signed=False)
    """Power requested now, by hand or by the weekly program."""
    requested_mode = enum(10715, OperatingMode)
    """Operating mode requested now, by hand or by the weekly program."""
    requested_temperature = gauge(10716, 0.1, unit="°C")
    """Temperature requested now, by hand or by the weekly program."""
    requested_zone = integer(10717, signed=False)
    """Zone requested now: 0 is zone 1, 1 is zone 2, 2 is both."""

    @property
    def follows_schedule(self) -> bool | None:
        """Whether the weekly program decides any of the four values."""
        sources = (
            self.power_source,
            self.mode_source,
            self.temperature_source,
            self.zone_source,
        )
        if any(source is None for source in sources):
            return None
        return any(source is not ControlSource.MANUAL for source in sources)

    async def _async_request(self, field: str, source: str, value: object) -> None:
        """Write a requested value the way table 11 prescribes.

        Under the weekly program the unit takes a new value only after its
        source register says "temporary". The source is read fresh, since the
        program or the control panel may have changed it since the last poll.
        """
        await self.write(field, value)
        source_address = self.resolved_fields[source].address
        (current,) = await self._unit.read_holding_registers(source_address, 1)
        if current != ControlSource.MANUAL:
            await self.write(source, ControlSource.TEMPORARY)
        await self.async_update()

    async def async_set_mode(self, mode: OperatingMode) -> None:
        """Request an operating mode."""
        await self._async_request("manual_mode", "mode_source", OperatingMode(mode))

    async def async_set_power(self, power: int) -> None:
        """Request a power, in the terms of ``Configuration.fan_regulation``."""
        await self._async_request("manual_power", "power_source", int(power))

    async def async_set_temperature(self, temperature: float) -> None:
        """Request a temperature, 10-40 °C."""
        await self._async_request(
            "manual_temperature", "temperature_source", temperature
        )

    async def async_set_zone(self, zone: int) -> None:
        """Request a zone."""
        await self._async_request("manual_zone", "zone_source", int(zone))

    async def async_follow_schedule(self, follow: bool) -> None:
        """Hand all four values to the weekly program, or take them back."""
        source = ControlSource.SCHEDULE if follow else ControlSource.MANUAL
        await self._unit.write_registers(
            self.resolved_fields["power_source"].address, [int(source)] * 4
        )
        await self.async_update()
