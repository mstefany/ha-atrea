"""Sensors of an Atrea RD5 unit."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    EntityCategory,
    UnitOfElectricPotential,
    UnitOfTemperature,
    UnitOfVolumeFlowRate,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import AtreaConfigEntry
from .entity import AtreaEntity, AtreaEntityDescription, enum_options, option_slug
from .vendor.atrea_modbus.rd5 import AtreaRD5, ForcedState, OperatingMode, Season

# The coordinators fetch the data; the entities only read it.
PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class AtreaSensorEntityDescription(SensorEntityDescription, AtreaEntityDescription):
    """Describe a sensor."""

    value_fn: Callable[[AtreaRD5], float | str | None]
    exists_fn: Callable[[AtreaRD5], bool] = lambda device: True


def _temperature(
    key: str, component: str, value_fn: Callable[[AtreaRD5], float | None], **kwargs
) -> AtreaSensorEntityDescription:
    return AtreaSensorEntityDescription(
        key=key,
        translation_key=key,
        component=component,
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=value_fn,
        **kwargs,
    )


def _flow(
    key: str, value_fn: Callable[[AtreaRD5], float | None], **kwargs
) -> AtreaSensorEntityDescription:
    return AtreaSensorEntityDescription(
        key=key,
        translation_key=key,
        component="sensors",
        device_class=SensorDeviceClass.VOLUME_FLOW_RATE,
        native_unit_of_measurement=UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=value_fn,
        **kwargs,
    )


def _voltage(
    key: str, value_fn: Callable[[AtreaRD5], float | None]
) -> AtreaSensorEntityDescription:
    return AtreaSensorEntityDescription(
        key=key,
        translation_key=key,
        component="outputs",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=value_fn,
    )


def _enum_slug(value: object) -> str | None:
    return option_slug(value) if value is not None else None  # type: ignore[arg-type]


def _forced_state(device: AtreaRD5) -> str | None:
    state = device.control.forced_state
    if state is None:
        return None
    try:
        return option_slug(ForcedState(state))
    except ValueError:
        return None


SENSORS: tuple[AtreaSensorEntityDescription, ...] = (
    _temperature("outdoor_air", "sensors", lambda d: d.sensors.outdoor_air),
    _temperature("supply_air", "sensors", lambda d: d.sensors.supply_air),
    _temperature("extract_air", "sensors", lambda d: d.sensors.extract_air),
    _temperature("exhaust_air", "sensors", lambda d: d.sensors.exhaust_air),
    _temperature("indoor_air", "sensors", lambda d: d.sensors.indoor_air),
    _temperature(
        "outdoor_air_average",
        "sensors",
        lambda d: d.sensors.outdoor_air_average,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    _flow("supply_flow", lambda d: d.sensors.supply_flow),
    _flow("extract_flow", lambda d: d.sensors.extract_flow),
    _flow(
        "outdoor_flow", lambda d: d.sensors.outdoor_flow, exists_fn=lambda d: d.is_r5
    ),
    _flow(
        "supply_flow_requested",
        lambda d: d.sensors.supply_flow_requested,
        entity_registry_enabled_default=False,
    ),
    _flow(
        "extract_flow_requested",
        lambda d: d.sensors.extract_flow_requested,
        entity_registry_enabled_default=False,
    ),
    _flow(
        "outdoor_flow_requested",
        lambda d: d.sensors.outdoor_flow_requested,
        entity_registry_enabled_default=False,
        exists_fn=lambda d: d.is_r5,
    ),
    AtreaSensorEntityDescription(
        key="current_mode",
        translation_key="current_mode",
        component="control",
        device_class=SensorDeviceClass.ENUM,
        options=enum_options(OperatingMode),
        value_fn=lambda d: _enum_slug(d.control.mode),
    ),
    AtreaSensorEntityDescription(
        key="season",
        translation_key="season",
        component="sensors",
        device_class=SensorDeviceClass.ENUM,
        options=enum_options(Season),
        value_fn=lambda d: _enum_slug(d.sensors.season),
    ),
    AtreaSensorEntityDescription(
        key="forced_state",
        translation_key="forced_state",
        component="control",
        device_class=SensorDeviceClass.ENUM,
        options=enum_options(ForcedState),
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_forced_state,
    ),
    _voltage("fan_m1_voltage", lambda d: d.outputs.m1),
    _voltage("fan_m2_voltage", lambda d: d.outputs.m2),
    _voltage("heat_pump_demand", lambda d: d.outputs.da1),
)

# The heat storage tank is measured by whichever extension board is fitted.
STORAGE_SENSORS: tuple[AtreaSensorEntityDescription, ...] = (
    _temperature(
        "heat_storage_top",
        "tz_inputs",
        lambda d: d.storage_inputs.t1 if d.storage_inputs else None,
    ),
    _temperature(
        "heat_storage_middle",
        "tz_inputs",
        lambda d: d.storage_inputs.t2 if d.storage_inputs else None,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AtreaConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the sensors."""
    runtime_data = entry.runtime_data
    device = runtime_data.device
    descriptions = [d for d in SENSORS if d.exists_fn(device)]
    if device.storage_inputs is not None:
        component = "tz_inputs" if device.tz_inputs is not None else "rg_inputs"
        descriptions += [replace(d, component=component) for d in STORAGE_SENSORS]
    async_add_entities(AtreaSensor(runtime_data, d) for d in descriptions)


class AtreaSensor(AtreaEntity, SensorEntity):
    """A value the unit measures or reports."""

    entity_description: AtreaSensorEntityDescription

    @property
    def native_value(self) -> float | str | None:
        """The value."""
        return self.entity_description.value_fn(self.device)
