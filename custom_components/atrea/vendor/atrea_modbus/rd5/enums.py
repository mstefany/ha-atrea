"""Value lists of the RD5 register map.

Names follow the Czech source document "Indexy protokolu Modbus TCP - RD5
regulace" (3 May 2021); the table numbers below refer to it.
"""

from __future__ import annotations

from enum import IntEnum


class ControlSource(IntEnum):
    """Who decides a requested value: H10700-H10703 (table 1)."""

    MANUAL = 0
    """The value stays until someone changes it."""
    SCHEDULE = 1
    """The weekly program sets the value."""
    TEMPORARY = 2
    """A manual change that holds until the next weekly-program interval."""


class OperatingMode(IntEnum):
    """Requested operating mode: H10705, H10709 (table 3)."""

    OFF = 0
    AUTOMATIC = 1
    VENTILATION = 2
    CIRCULATION_WITH_VENTILATION = 3
    CIRCULATION = 4
    NIGHT_PRECOOLING = 5
    UNBALANCED = 6
    """Supplies more air than it extracts ("Rozvážení"), for a fireplace."""
    OVERPRESSURE = 7


class R5Power(IntEnum):
    """Power levels of an R_5 unit, where H10510 = 4 (table 4).

    The combined levels name the circulation level first, then the
    ventilation level.
    """

    VENTILATION_MIN = 10
    VENTILATION_NORM = 11
    VENTILATION_MAX = 12
    CIRCULATION_MIN = 20
    CIRCULATION_NORM = 21
    CIRCULATION_MAX = 22
    MIN_MIN = 30
    MIN_NORM = 31
    MIN_MAX = 32
    NORM_MIN = 33
    NORM_NORM = 34
    NORM_MAX = 35
    MAX_MIN = 36
    MAX_NORM = 37
    MAX_MAX = 38


class Season(IntEnum):
    """The season the unit is in now: I11401."""

    HEATING = 0
    NON_HEATING = 1


class SeasonMode(IntEnum):
    """How the unit picks its season: H11401 (table 2)."""

    HEATING = 0
    NON_HEATING = 1
    T_ODA = 2
    """Switch by the averaged outdoor temperature."""
    T_ODA_PLUS = 3


class FanRegulation(IntEnum):
    """How the fans are regulated: H10510. It decides what a power value means."""

    DIRECT = 0
    """Power is 12-100 %."""
    CONSTANT_FLOW = 1
    """Power is 1-100, from the unit's minimum to its maximum flow."""
    CONSTANT_PRESSURE = 2
    """Power is 1 (night) or 2 (day)."""
    ANALOG_INPUTS = 3
    """Power is 12-100 %, by IN1 / IN2."""
    R5_CONSTANT_FLOW = 4
    """Power is an ``R5Power`` level."""


class PrimaryHeating(IntEnum):
    """Type of the primary heater: H10503."""

    NONE = 0
    WATER_CONTACT = 1
    WATER_ANALOG = 2
    ELECTRIC_PWM = 3
    ELECTRIC_CONTACT = 4
    HEAT_PUMP = 5


class Cooling(IntEnum):
    """Type of the cooler: H10507."""

    NONE = 0
    WATER = 1
    DIRECT = 2
    """Direct evaporator or heat pump."""


class IndoorTemperatureSource(IntEnum):
    """Where the unit takes the indoor temperature T-IDA from: H10514."""

    CONTROL_PANEL = 0
    EXTRACT_AIR = 1
    ROOM_SENSOR = 2
    BMS = 3
    """Written over Modbus to H10214, at least every 90 seconds."""


class ForcedState(IntEnum):
    """What overrides the requested mode right now: H10712 (tables 7 and 12).

    The values above 26 come from table 7, whose rows are hard to align.
    """

    NONE = 0
    STARTING = 1
    STOPPING = 2
    INPUT_D1 = 3
    INPUT_D2 = 4
    INPUT_D3 = 5
    INPUT_D4 = 6
    INPUT_IN1 = 7
    INPUT_IN2 = 8
    INPUT_K1_IN1 = 9
    INPUT_K1_IN2 = 10
    INPUT_K1_IN3 = 11
    INPUT_K1_IN4 = 12
    INPUT_K2_IN1 = 13
    INPUT_K2_IN2 = 14
    INPUT_K2_IN3 = 15
    INPUT_K2_IN4 = 16
    INPUT_K1_TR1 = 17
    INPUT_K1_TR2 = 18
    INPUT_K1_TR3 = 19
    INPUT_K1_TR4 = 20
    INPUT_K1_TR5 = 21
    INPUT_K2_TR1 = 22
    INPUT_K2_TR2 = 23
    INPUT_K2_TR3 = 24
    INPUT_K2_TR4 = 25
    INPUT_K2_TR5 = 26
    HEAT_PUMP_DEFROSTING = 27
    PREHEATING = 28
    LEARNING = 29
    HEAT_PUMP_DEFROSTING_2 = 30
    FILTER_TEST = 31
    PERIODIC_VENTILATION = 32
