"""Switches of an Atrea RD5 unit."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import AtreaConfigEntry
from .entity import AtreaEntity, AtreaEntityDescription
from .vendor.atrea_modbus.rd5 import AtreaRD5

PARALLEL_UPDATES = 1


@dataclass(frozen=True, kw_only=True)
class AtreaSwitchEntityDescription(SwitchEntityDescription, AtreaEntityDescription):
    """Describe a switch."""

    value_fn: Callable[[AtreaRD5], bool | None]
    write_fn: Callable[[AtreaRD5, bool], Awaitable[None]]
    exists_fn: Callable[[AtreaRD5], bool] = lambda device: True


def _write_heater(device: AtreaRD5, field: str, value: bool) -> Awaitable[None]:
    assert device.heat_storage is not None
    return device.heat_storage.write(field, value)


SWITCHES: tuple[AtreaSwitchEntityDescription, ...] = (
    AtreaSwitchEntityDescription(
        key="weekly_program",
        translation_key="weekly_program",
        component="control",
        value_fn=lambda d: d.control.follows_schedule,
        write_fn=lambda d, value: d.control.async_follow_schedule(value),
    ),
    AtreaSwitchEntityDescription(
        key="electric_heater_1",
        translation_key="electric_heater_1",
        component="heat_storage",
        value_fn=lambda d: d.heat_storage.electric_heater_1 if d.heat_storage else None,
        write_fn=lambda d, value: _write_heater(d, "electric_heater_1", value),
        exists_fn=lambda d: d.heat_storage is not None,
    ),
    AtreaSwitchEntityDescription(
        key="electric_heater_2",
        translation_key="electric_heater_2",
        component="heat_storage",
        value_fn=lambda d: d.heat_storage.electric_heater_2 if d.heat_storage else None,
        write_fn=lambda d, value: _write_heater(d, "electric_heater_2", value),
        exists_fn=lambda d: d.heat_storage is not None,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AtreaConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the switches."""
    runtime_data = entry.runtime_data
    async_add_entities(
        AtreaSwitch(runtime_data, description)
        for description in SWITCHES
        if description.exists_fn(runtime_data.device)
    )


class AtreaSwitch(AtreaEntity, SwitchEntity):
    """A setting of the unit that is on or off."""

    entity_description: AtreaSwitchEntityDescription

    @property
    def is_on(self) -> bool | None:
        """Whether the setting is on."""
        return self.entity_description.value_fn(self.device)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Switch the setting on."""
        await self._async_write(self.entity_description.write_fn(self.device, True))

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Switch the setting off."""
        await self._async_write(self.entity_description.write_fn(self.device, False))
