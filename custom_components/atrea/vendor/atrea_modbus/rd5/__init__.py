"""Read and control Atrea DUPLEX units with RD5 control over Modbus."""

from .alarms import NOTICES, Alarms
from .control import MAX_TEMPERATURE, MIN_TEMPERATURE, Control
from .device import (
    ALL,
    R5_POWER_LEVELS,
    READINGS,
    SETTINGS,
    AtreaRD5,
    r5_power_for_mode,
)
from .enums import (
    ControlSource,
    Cooling,
    FanRegulation,
    ForcedState,
    IndoorTemperatureSource,
    OperatingMode,
    PrimaryHeating,
    R5Power,
    Season,
    SeasonMode,
)
from .identity import SERIAL_LENGTH, SERIAL_REGISTER, Firmware, Identity
from .outputs import DigitalInputs, Outputs
from .sensors import BoardInputs, ModeLimits, Sensors
from .settings import (
    MAX_STORAGE_TEMPERATURE,
    MIN_STORAGE_TEMPERATURE,
    BmsTemperatures,
    Configuration,
    HeatStorage,
    R5Flows,
    Settings,
)

__all__ = [
    "ALL",
    "MAX_STORAGE_TEMPERATURE",
    "MAX_TEMPERATURE",
    "MIN_STORAGE_TEMPERATURE",
    "MIN_TEMPERATURE",
    "NOTICES",
    "R5_POWER_LEVELS",
    "READINGS",
    "SERIAL_LENGTH",
    "SERIAL_REGISTER",
    "SETTINGS",
    "Alarms",
    "AtreaRD5",
    "BmsTemperatures",
    "BoardInputs",
    "Configuration",
    "Control",
    "ControlSource",
    "Cooling",
    "DigitalInputs",
    "FanRegulation",
    "Firmware",
    "ForcedState",
    "HeatStorage",
    "Identity",
    "IndoorTemperatureSource",
    "ModeLimits",
    "OperatingMode",
    "Outputs",
    "PrimaryHeating",
    "R5Flows",
    "R5Power",
    "Season",
    "Sensors",
    "Settings",
    "SeasonMode",
    "r5_power_for_mode",
]
