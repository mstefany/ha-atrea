"""Binary sensors of an Atrea RD5 unit."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import AtreaConfigEntry
from .entity import AtreaEntity, AtreaEntityDescription
from .vendor.atrea_modbus.rd5 import AtreaRD5, Cooling, PrimaryHeating


@dataclass(frozen=True, kw_only=True)
class AtreaBinarySensorEntityDescription(
    BinarySensorEntityDescription, AtreaEntityDescription
):
    """Describe a binary sensor."""

    value_fn: Callable[[AtreaRD5], bool | None]
    attributes_fn: Callable[[AtreaRD5], dict[str, Any]] | None = None
    exists_fn: Callable[[AtreaRD5], bool] = lambda device: True


def _has_heat_pump(device: AtreaRD5) -> bool:
    config = device.configuration
    return (
        config.primary_heating is PrimaryHeating.HEAT_PUMP
        or config.cooling is Cooling.DIRECT
    )


BINARY_SENSORS: tuple[AtreaBinarySensorEntityDescription, ...] = (
    AtreaBinarySensorEntityDescription(
        key="fault",
        translation_key="fault",
        component="alarms",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda d: bool(d.alarms.faults),
        attributes_fn=lambda d: {"faults": sorted(d.alarms.faults)},
    ),
    AtreaBinarySensorEntityDescription(
        key="filter_change_due",
        translation_key="filter_change_due",
        component="alarms",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda d: d.alarms.filter_change_due,
    ),
    AtreaBinarySensorEntityDescription(
        key="filter_clogged",
        translation_key="filter_clogged",
        component="alarms",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda d: d.alarms.filter_clogged,
    ),
    AtreaBinarySensorEntityDescription(
        key="recuperator_frozen",
        translation_key="recuperator_frozen",
        component="alarms",
        device_class=BinarySensorDeviceClass.COLD,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.alarms.recuperator_frozen,
    ),
    AtreaBinarySensorEntityDescription(
        key="recuperator_defrosting",
        translation_key="recuperator_defrosting",
        component="alarms",
        device_class=BinarySensorDeviceClass.RUNNING,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.alarms.recuperator_defrosting,
    ),
    AtreaBinarySensorEntityDescription(
        key="heat_pump_heating",
        translation_key="heat_pump_heating",
        component="outputs",
        device_class=BinarySensorDeviceClass.RUNNING,
        value_fn=lambda d: d.outputs.se,
        exists_fn=_has_heat_pump,
    ),
    AtreaBinarySensorEntityDescription(
        key="heat_pump_cooling",
        translation_key="heat_pump_cooling",
        component="outputs",
        device_class=BinarySensorDeviceClass.RUNNING,
        value_fn=lambda d: d.outputs.sc_relay,
        exists_fn=_has_heat_pump,
    ),
    AtreaBinarySensorEntityDescription(
        key="heat_pump_defrosting",
        translation_key="heat_pump_defrosting",
        component="alarms",
        device_class=BinarySensorDeviceClass.RUNNING,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.alarms.heat_pump_defrosting,
        exists_fn=_has_heat_pump,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AtreaConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the binary sensors."""
    runtime_data = entry.runtime_data
    async_add_entities(
        AtreaBinarySensor(runtime_data, description)
        for description in BINARY_SENSORS
        if description.exists_fn(runtime_data.device)
    )


class AtreaBinarySensor(AtreaEntity, BinarySensorEntity):
    """A state the unit reports as on or off."""

    entity_description: AtreaBinarySensorEntityDescription

    @property
    def is_on(self) -> bool | None:
        """The state."""
        return self.entity_description.value_fn(self.device)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """What stands behind the state."""
        if (attributes_fn := self.entity_description.attributes_fn) is None:
            return None
        return attributes_fn(self.device)
