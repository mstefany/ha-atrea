"""What the unit measures: the input registers (tables 7 and 12)."""

from __future__ import annotations

from modbus_connection.model import Component, enum, gauge, integer

from .enums import Season

# A temperature input with no sensor connected reads 126.0 °C.
NOT_CONNECTED = 1260
# The same for the T7s inputs, which range higher.
NOT_CONNECTED_T7S = 3260


class Sensors(Component):
    """Temperatures, air flows and the current season."""

    register_space = "input"

    tu1 = gauge(10200, 0.1, unit="°C", nan=NOT_CONNECTED)
    """Input TU1 of the unit."""
    tu2 = gauge(10201, 0.1, unit="°C", nan=NOT_CONNECTED)
    """Input TU2 of the unit."""
    tea = gauge(10202, 0.1, unit="°C", nan=NOT_CONNECTED)
    """Input TEa."""
    teb = gauge(10203, 0.1, unit="°C", nan=NOT_CONNECTED)
    """Input TEb."""
    ta2 = gauge(10204, 0.1, unit="°C", nan=NOT_CONNECTED)
    """Input TA2."""
    in1 = gauge(10205, 0.001, signed=False, unit="V")
    """Analog input IN1."""
    in2 = gauge(10206, 0.001, signed=False, unit="V")
    """Analog input IN2."""
    control_panel_temperature = gauge(10207, 0.1, unit="°C", nan=NOT_CONNECTED)
    """Temperature sensor of the control panel."""

    outdoor_air = gauge(10211, 0.1, unit="°C", nan=NOT_CONNECTED)
    """T-ODA, the air taken from outside."""
    supply_air = gauge(10212, 0.1, unit="°C", nan=NOT_CONNECTED)
    """T-SUP, the air supplied to the rooms."""
    extract_air = gauge(10213, 0.1, unit="°C", nan=NOT_CONNECTED)
    """T-ETA, the air extracted from the rooms."""
    exhaust_air = gauge(10214, 0.1, unit="°C", nan=NOT_CONNECTED)
    """T-EHA, the air blown outside."""
    indoor_air = gauge(10215, 0.1, unit="°C", nan=NOT_CONNECTED)
    """T-IDA, the room temperature the unit regulates to."""

    season = enum(11401, Season)
    """The season the unit is in now."""
    outdoor_air_average = gauge(11420, 0.1, unit="°C", nan=NOT_CONNECTED)
    """Averaged T-ODA, which the T-ODA season modes switch by."""

    supply_flow_requested = integer(11600, signed=False, unit="m³/h")
    extract_flow_requested = integer(11601, signed=False, unit="m³/h")
    supply_flow = integer(11602, signed=False, unit="m³/h")
    extract_flow = integer(11603, signed=False, unit="m³/h")
    outdoor_flow_requested = integer(11604, signed=False, unit="m³/h")
    """Requested outdoor air flow; R_5 units only."""
    outdoor_flow = integer(11605, signed=False, unit="m³/h")
    """Outdoor air flow; R_5 units only."""


class BoardInputs(Component):
    """Inputs of an extension board: RD5-RG at I10236, RD5-TZ at I10245."""

    register_space = "input"

    in1 = gauge(0, 0.001, signed=False, unit="V")
    in2 = gauge(1, 0.001, signed=False, unit="V")
    t1 = gauge(2, 0.1, unit="°C", nan=NOT_CONNECTED)
    """Top of the integrated heat storage tank, where the unit has one."""
    t2 = gauge(3, 0.1, unit="°C", nan=NOT_CONNECTED)
    """Middle of the integrated heat storage tank, where the unit has one."""
    t3 = gauge(4, 0.1, unit="°C", nan=NOT_CONNECTED)
    t4 = gauge(5, 0.1, unit="°C", nan=NOT_CONNECTED)
    t5 = gauge(6, 0.1, unit="°C", nan=NOT_CONNECTED)
    t6 = gauge(7, 0.1, unit="°C", nan=NOT_CONNECTED)
    t7s = gauge(8, 0.1, unit="°C", nan=NOT_CONNECTED_T7S)


RG_BOARD_INPUTS = 10236
TZ_BOARD_INPUTS = 10245


class ModeLimits(Component):
    """Which operating modes the unit lets a user request now.

    The source document does not list this register; the web interface of the
    unit takes its list of modes from it.
    """

    register_space = "input"

    writable_modes = integer(12004, signed=False)
    """Bit mask: bit N is set when the operating mode N can be requested."""
