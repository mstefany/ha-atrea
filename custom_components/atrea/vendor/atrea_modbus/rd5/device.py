"""The top-level object: one Atrea DUPLEX unit with RD5 control."""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

from modbus_connection.model import Device, Raw, UpdateReport, read_optional

from .alarms import Alarms
from .control import Control
from .enums import FanRegulation, OperatingMode, R5Power, Season
from .identity import Firmware, Identity
from .outputs import DigitalInputs, Outputs
from .sensors import RG_BOARD_INPUTS, TZ_BOARD_INPUTS, BoardInputs, Sensors
from .settings import (
    RESET_ALARMS_COIL,
    RESET_FILTER_INTERVAL_COIL,
    BmsTemperatures,
    Configuration,
    HeatStorage,
    Settings,
)

if TYPE_CHECKING:
    from modbus_connection import ModbusUnit

# Attribute names of the sub-systems each update method reads.
READINGS = (
    "control",
    "sensors",
    "outputs",
    "digital_inputs",
    "alarms",
    "rg_inputs",
    "tz_inputs",
)
SETTINGS = ("settings", "heat_storage")
# The identity is left out of a raw dump: it holds the production number.
ALL = ("firmware", "configuration", *READINGS, *SETTINGS)

_VENTILATION = (
    R5Power.VENTILATION_MIN,
    R5Power.VENTILATION_NORM,
    R5Power.VENTILATION_MAX,
)
_CIRCULATION = (
    R5Power.CIRCULATION_MIN,
    R5Power.CIRCULATION_NORM,
    R5Power.CIRCULATION_MAX,
)
_COMBINED = tuple(level for level in R5Power if level >= R5Power.MIN_MIN)

# The power levels an R_5 unit takes in each mode. Measured on a DUPLEX RB5:
# given a level of another family, the unit does not refuse it but runs the
# matching level of the family below (see ``r5_power_for_mode``). Automatic and
# night precooling did not run during the measurement, so their rows are an
# assumption.
R5_POWER_LEVELS: dict[OperatingMode, tuple[R5Power, ...]] = {
    OperatingMode.OFF: (),
    OperatingMode.AUTOMATIC: _COMBINED,
    OperatingMode.VENTILATION: _VENTILATION,
    OperatingMode.CIRCULATION_WITH_VENTILATION: _COMBINED,
    OperatingMode.CIRCULATION: _CIRCULATION,
    OperatingMode.NIGHT_PRECOOLING: _VENTILATION,
    OperatingMode.UNBALANCED: _VENTILATION,
    OperatingMode.OVERPRESSURE: _VENTILATION,
}


def r5_power_for_mode(power: R5Power, mode: OperatingMode) -> R5Power | None:
    """The level of the family a mode takes that matches a level of another.

    This is the translation the unit does itself: the ventilation part and the
    circulation part of a level carry over, and a part the level does not have
    becomes Min. ``None`` for a mode that takes no power (off).
    """
    levels = R5_POWER_LEVELS[mode]
    if not levels or power in levels:
        return power if levels else None
    code = int(power)
    # Min, Norm, Max as 0, 1, 2; None where the level has no such part.
    ventilation = code - 10 if code < 20 else (code - 30) % 3 if code >= 30 else None
    circulation = (
        code - 20 if 20 <= code < 30 else (code - 30) // 3 if code >= 30 else None
    )
    if levels is _VENTILATION:
        return R5Power(10 + (ventilation or 0))
    if levels is _CIRCULATION:
        return R5Power(20 + (circulation or 0))
    return R5Power(30 + 3 * (circulation or 0) + (ventilation or 0))


class AtreaRD5(Device):
    """An Atrea DUPLEX ventilation unit reached through a ``ModbusUnit``."""

    def __init__(self, unit: ModbusUnit) -> None:
        super().__init__(unit)
        # The source document asks for unhurried communication.
        unit.require_timeout(5.0)

        self.configuration = Configuration(unit)
        self.control = Control(unit)
        self.sensors = Sensors(unit)
        self.outputs = Outputs(unit)
        self.digital_inputs = DigitalInputs(unit)
        self.alarms = Alarms(unit)
        self.settings = Settings(unit)
        self.bms_temperatures = BmsTemperatures(unit)

        # Optional: filled in by setup if the unit serves them.
        self.identity: Identity | None = None
        self.firmware: Firmware | None = None
        self.rg_inputs: BoardInputs | None = None
        self.tz_inputs: BoardInputs | None = None
        self.heat_storage: HeatStorage | None = None

    async def _async_setup(self) -> None:
        """Read what never changes, and settle which sub-systems this unit has."""
        unit = self.modbus_unit
        self.identity = await read_optional(Identity(unit))
        self.firmware = await read_optional(Firmware(unit))
        await self.configuration.async_update()
        await self.digital_inputs.async_update()
        if self.digital_inputs.rg_board:
            self.rg_inputs = BoardInputs(unit, base_offset=RG_BOARD_INPUTS)
        if self.digital_inputs.tz_board:
            self.tz_inputs = BoardInputs(unit, base_offset=TZ_BOARD_INPUTS)
        # The heat storage tank is wired to one of the extension boards.
        if self.rg_inputs or self.tz_inputs:
            self.heat_storage = HeatStorage(unit)

    async def async_update_readings(self) -> UpdateReport:
        """Refresh what the unit measures and does."""
        return await self.async_poll(READINGS)

    async def async_update_settings(self) -> UpdateReport:
        """Refresh what the unit has been set to."""
        return await self.async_poll(SETTINGS)

    async def async_update(self) -> UpdateReport:
        """Refresh every sub-system."""
        report = await self.async_poll(READINGS)
        return await self.async_poll(SETTINGS, report)

    async def async_read_raw(self, names: Iterable[str] = ALL) -> Raw:
        """Every register this device reads, undecoded, for diagnostics."""
        return await super().async_read_raw(names)

    @property
    def is_r5(self) -> bool:
        """Whether this is an R_5 unit, with circulation and levelled power."""
        return self.configuration.fan_regulation is FanRegulation.R5_CONSTANT_FLOW

    @property
    def model(self) -> str:
        """The most this register map tells about the unit type."""
        return "DUPLEX R_5" if self.is_r5 else "DUPLEX"

    @property
    def serial_number(self) -> str | None:
        """The production number, where the unit serves it."""
        return self.identity.serial_number if self.identity else None

    @property
    def firmware_version(self) -> str | None:
        """The control software version, where the unit serves it."""
        return self.firmware.version if self.firmware else None

    @property
    def storage_inputs(self) -> BoardInputs | None:
        """The board whose T1 and T2 measure the heat storage tank."""
        return self.tz_inputs or self.rg_inputs

    @property
    def available_modes(self) -> tuple[OperatingMode, ...]:
        """The operating modes this unit accepts now (table 3)."""
        config = self.configuration
        if config.vav_box_mode:
            return (OperatingMode.OFF, OperatingMode.VENTILATION)
        modes = [OperatingMode.OFF, OperatingMode.AUTOMATIC, OperatingMode.VENTILATION]
        if config.circulation_with_ventilation:
            modes.append(OperatingMode.CIRCULATION_WITH_VENTILATION)
        if config.circulation_damper:
            modes.append(OperatingMode.CIRCULATION)
        if self.sensors.season is Season.NON_HEATING:
            modes.append(OperatingMode.NIGHT_PRECOOLING)
        modes += [OperatingMode.UNBALANCED, OperatingMode.OVERPRESSURE]
        return tuple(modes)

    @property
    def r5_power(self) -> R5Power | None:
        """The power level requested now, on an R_5 unit."""
        power = self.control.requested_power
        if not self.is_r5 or power is None:
            return None
        try:
            return R5Power(power)
        except ValueError:
            return None

    async def async_set_mode(self, mode: OperatingMode) -> None:
        """Request an operating mode the unit accepts now."""
        mode = OperatingMode(mode)
        if mode not in self.available_modes:
            raise ValueError(f"the unit does not accept {mode.name.lower()} now")
        await self.control.async_set_mode(mode)
        # Keep the requested power in the family the new mode takes, so the
        # request says what the unit will do.
        current = self.r5_power
        if current is not None and (level := r5_power_for_mode(current, mode)):
            if level is not current:
                await self.control.async_set_power(level)

    def _check_power(self, power: int) -> None:
        """Refuse a power value this type of fan regulation does not take."""
        regulation = self.configuration.fan_regulation
        if regulation is FanRegulation.R5_CONSTANT_FLOW:
            valid = power in tuple(R5Power)
        elif regulation is FanRegulation.CONSTANT_PRESSURE:
            valid = power in (1, 2)
        elif regulation is FanRegulation.CONSTANT_FLOW:
            valid = 1 <= power <= 100
        elif regulation in (FanRegulation.DIRECT, FanRegulation.ANALOG_INPUTS):
            valid = 12 <= power <= 100
        else:
            # Unknown regulation: the meaning of a value is unknown too.
            valid = False
        if not valid:
            raise ValueError(f"power {power} is not valid for this unit")

    async def async_set_power(self, power: int) -> None:
        """Request a power this unit takes; see ``FanRegulation``."""
        power = int(power)
        self._check_power(power)
        mode = self.control.requested_mode
        if self.is_r5 and mode is not None:
            power = r5_power_for_mode(R5Power(power), mode) or power
        await self.control.async_set_power(power)

    async def async_reset_alarms(self) -> None:
        """Clear the alarms that allow a reset."""
        await self.modbus_unit.write_coil(RESET_ALARMS_COIL, True)

    async def async_reset_filter_interval(self) -> None:
        """Start a new filter change interval, after the filters were changed."""
        await self.modbus_unit.write_coil(RESET_FILTER_INTERVAL_COIL, True)
