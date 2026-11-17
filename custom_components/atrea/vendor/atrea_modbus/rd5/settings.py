"""How the unit is set up, and the few settings a user changes (tables 2, 8, 10, 12)."""

from __future__ import annotations

from modbus_connection.model import Component, boolean, coil, enum, gauge, integer

from .enums import (
    Cooling,
    FanRegulation,
    IndoorTemperatureSource,
    PrimaryHeating,
    SeasonMode,
)

MIN_STORAGE_TEMPERATURE = 20.0
MAX_STORAGE_TEMPERATURE = 70.0


def _storage_temperature(value: float) -> float:
    if not MIN_STORAGE_TEMPERATURE <= value <= MAX_STORAGE_TEMPERATURE:
        raise ValueError(
            f"temperature {value} is outside "
            f"{MIN_STORAGE_TEMPERATURE}-{MAX_STORAGE_TEMPERATURE} °C"
        )
    return value


def _season_temperature(value: float) -> float:
    if not 0.0 <= value <= 30.0:
        raise ValueError(f"temperature {value} is outside 0-30 °C")
    return value


class Configuration(Component):
    """Service settings that describe the installation. Read once at setup."""

    primary_heating = enum(10503, PrimaryHeating)
    cooling = enum(10507, Cooling)
    fan_regulation = enum(10510, FanRegulation)
    """Decides what a power value means."""
    zone_function = integer(10511, signed=False)
    """Function of the SZ1/SZ2 outputs; 1 means the unit ventilates by zone."""
    indoor_temperature_source = enum(10514, IndoorTemperatureSource)
    automatic_ventilation_interval = integer(10502, signed=False, unit="min")
    """Minutes per hour the unit ventilates in the automatic mode (3.2.13)."""
    supply_fan_correction = integer(10513, unit="%")
    """How much faster the supply fan runs than the extract fan (3.2.3).

    The "unbalanced" mode applies it; at 0 that mode equals ventilation.
    """
    night_cooling_test_interval = integer(11429, signed=False, unit="min")
    """Time between the test runs of night precooling (3.2.12), 10-600 min.

    Between the tests the unit stands still; a test runs the fans for five
    minutes to measure the real air temperatures.
    """
    ground_heat_exchanger = integer(10519, signed=False)
    """Ground heat exchanger type (3.10.1); 0 means none."""
    heat_exchanger_type = integer(11801, signed=False)
    """Heat exchanger type (3.3.1); 0 means a plate heat exchanger."""
    circulation_damper = boolean(11700)
    """The unit has a circulation damper."""

    vav_box_mode = coil(10508)
    """VAV box ventilation; when set, only Off and Ventilation are allowed."""
    circulation_with_ventilation = coil(10509)
    """Two-zone operation (3.1.51); "circulation with ventilation" needs it."""
    outdoor_temperature_from_bms = coil(10510)
    """T-ODA is written over Modbus to H10213, at least every 90 seconds."""


class R5Flows(Component):
    """Air flow of each power level of an R_5 unit (3.2.30 to 3.2.35).

    The source document does not list these registers; the web interface of
    the unit names them.
    """

    circulation_min = integer(11627, signed=False, unit="m³/h")
    circulation_norm = integer(11628, signed=False, unit="m³/h")
    circulation_max = integer(11629, signed=False, unit="m³/h")
    ventilation_min = integer(11630, signed=False, unit="m³/h")
    ventilation_norm = integer(11631, signed=False, unit="m³/h")
    ventilation_max = integer(11632, signed=False, unit="m³/h")


class Settings(Component):
    """Settings a user changes in normal use."""

    season_mode = enum(11401, SeasonMode, writable=True)
    """How the unit picks between the heating and the non-heating season."""
    season_temperature = gauge(11402, 0.1, unit="°C", writable=_season_temperature)
    """Outdoor temperature at which the T-ODA season modes switch."""


class HeatStorage(Component):
    """The integrated heat storage tank, "IZT" (table 8)."""

    electric_heater_1 = boolean(12914, writable=True)
    """Electric heating rod 1, for example to use photovoltaic surplus."""
    electric_heater_2 = boolean(12915, writable=True)
    """Electric heating rod 2."""
    target_top = gauge(12925, 0.1, unit="°C", writable=_storage_temperature)
    """Tp1: requested temperature at the top of the tank, by sensor T1."""
    target_middle = gauge(12928, 0.1, unit="°C", writable=_storage_temperature)
    """Tp2: requested temperature in the middle of the tank, by sensor T2."""


class BmsTemperatures(Component):
    """Temperatures a building management system sends to the unit (table 10).

    The unit reports a sensor fault when a value it expects is older than
    90 seconds.
    """

    outdoor_air = gauge(10213, 0.1, unit="°C", writable=True)
    indoor_air = gauge(10214, 0.1, unit="°C", writable=True)


# Write-only coils (table 10).
RESET_ALARMS_COIL = 10005
RESET_FILTER_INTERVAL_COIL = 10007
