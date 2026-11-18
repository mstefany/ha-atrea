"""Number entities of an Atrea RD5 unit."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import AtreaConfigEntry
from .entity import AtreaEntity, AtreaEntityDescription
from .vendor.atrea_modbus.rd5 import (
    MAX_STORAGE_TEMPERATURE,
    MIN_STORAGE_TEMPERATURE,
    AtreaRD5,
    FanRegulation,
)

PARALLEL_UPDATES = 1


@dataclass(frozen=True, kw_only=True)
class AtreaNumberEntityDescription(NumberEntityDescription, AtreaEntityDescription):
    """Describe a number entity."""

    value_fn: Callable[[AtreaRD5], float | None]
    write_fn: Callable[[AtreaRD5, float], Awaitable[None]]
    exists_fn: Callable[[AtreaRD5], bool] = lambda device: True


def _write_storage(device: AtreaRD5, field: str, value: float) -> Awaitable[None]:
    assert device.heat_storage is not None
    return device.heat_storage.write(field, value)


def _power(
    regulation: FanRegulation, low: int, high: int, unit: str | None
) -> AtreaNumberEntityDescription:
    """The power of a unit with this fan regulation."""
    return AtreaNumberEntityDescription(
        key="power",
        translation_key="power",
        component="control",
        native_unit_of_measurement=unit,
        native_min_value=low,
        native_max_value=high,
        native_step=1,
        value_fn=lambda d: d.control.requested_power,
        write_fn=lambda d, value: d.async_set_power(int(value)),
        exists_fn=lambda d: d.configuration.fan_regulation is regulation,
    )


def _storage_target(key: str, field: str) -> AtreaNumberEntityDescription:
    return AtreaNumberEntityDescription(
        key=key,
        translation_key=key,
        component="heat_storage",
        device_class=NumberDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        native_min_value=MIN_STORAGE_TEMPERATURE,
        native_max_value=MAX_STORAGE_TEMPERATURE,
        native_step=0.5,
        mode=NumberMode.BOX,
        value_fn=lambda d: getattr(d.heat_storage, field) if d.heat_storage else None,
        write_fn=lambda d, value: _write_storage(d, field, value),
        exists_fn=lambda d: d.heat_storage is not None,
    )


NUMBERS: tuple[AtreaNumberEntityDescription, ...] = (
    _storage_target("heat_storage_target_top", "target_top"),
    _storage_target("heat_storage_target_middle", "target_middle"),
    AtreaNumberEntityDescription(
        key="season_temperature",
        translation_key="season_temperature",
        component="settings",
        entity_category=EntityCategory.CONFIG,
        device_class=NumberDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        native_min_value=0,
        native_max_value=30,
        native_step=0.5,
        mode=NumberMode.BOX,
        value_fn=lambda d: d.settings.season_temperature,
        write_fn=lambda d, value: d.settings.write("season_temperature", value),
    ),
    # Units other than R_5 take the power as a number; its range depends on
    # the fan regulation.
    _power(FanRegulation.DIRECT, 12, 100, PERCENTAGE),
    _power(FanRegulation.ANALOG_INPUTS, 12, 100, PERCENTAGE),
    _power(FanRegulation.CONSTANT_FLOW, 1, 100, PERCENTAGE),
    # 1 is night, 2 is day.
    _power(FanRegulation.CONSTANT_PRESSURE, 1, 2, None),
    # An R_5 unit without two-zone operation takes levels 1 to 9 (Min/Min to
    # Max/Max) in the automatic mode and 1 to 3 (Min to Max) in the others.
    # Untested: the test unit has two-zone operation.
    AtreaNumberEntityDescription(
        key="power_step",
        translation_key="power_step",
        component="control",
        native_min_value=1,
        native_max_value=9,
        native_step=1,
        value_fn=lambda d: d.control.requested_power,
        write_fn=lambda d, value: d.async_set_power(int(value)),
        exists_fn=lambda d: d.is_r5 and not d.has_power_levels,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AtreaConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the number entities."""
    runtime_data = entry.runtime_data
    async_add_entities(
        AtreaNumber(runtime_data, description)
        for description in NUMBERS
        if description.exists_fn(runtime_data.device)
    )


class AtreaNumber(AtreaEntity, NumberEntity):
    """A numeric setting of the unit."""

    entity_description: AtreaNumberEntityDescription

    @property
    def native_value(self) -> float | None:
        """The value in effect."""
        return self.entity_description.value_fn(self.device)

    async def async_set_native_value(self, value: float) -> None:
        """Write the value to the unit."""
        await self._async_write(self.entity_description.write_fn(self.device, value))
