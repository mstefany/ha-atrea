"""Select entities of an Atrea RD5 unit."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import IntEnum

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import AtreaConfigEntry
from .entity import AtreaEntity, AtreaEntityDescription, enum_options, option_slug
from .vendor.atrea_modbus.rd5 import AtreaRD5, OperatingMode, R5Power, SeasonMode

PARALLEL_UPDATES = 1


@dataclass(frozen=True, kw_only=True)
class AtreaSelectEntityDescription(SelectEntityDescription, AtreaEntityDescription):
    """Describe a select entity."""

    value_fn: Callable[[AtreaRD5], IntEnum | None]
    write_fn: Callable[[AtreaRD5, str], Awaitable[None]]
    exists_fn: Callable[[AtreaRD5], bool] = lambda device: True


SELECTS: tuple[AtreaSelectEntityDescription, ...] = (
    AtreaSelectEntityDescription(
        key="operating_mode",
        translation_key="operating_mode",
        component="control",
        options=enum_options(OperatingMode),
        value_fn=lambda device: device.control.requested_mode,
        write_fn=lambda device, option: device.async_set_mode(
            OperatingMode[option.upper()]
        ),
    ),
    AtreaSelectEntityDescription(
        key="power_level",
        translation_key="power_level",
        component="control",
        options=enum_options(R5Power),
        value_fn=lambda device: device.r5_power,
        write_fn=lambda device, option: device.async_set_power(R5Power[option.upper()]),
        exists_fn=lambda device: device.is_r5,
    ),
    AtreaSelectEntityDescription(
        key="season_mode",
        translation_key="season_mode",
        component="settings",
        entity_category=EntityCategory.CONFIG,
        options=enum_options(SeasonMode),
        value_fn=lambda device: device.settings.season_mode,
        write_fn=lambda device, option: device.settings.write(
            "season_mode", SeasonMode[option.upper()]
        ),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AtreaConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the select entities."""
    runtime_data = entry.runtime_data
    async_add_entities(
        AtreaSelect(runtime_data, description)
        for description in SELECTS
        if description.exists_fn(runtime_data.device)
    )


class AtreaSelect(AtreaEntity, SelectEntity):
    """A setting of the unit with a fixed list of values."""

    entity_description: AtreaSelectEntityDescription

    @property
    def current_option(self) -> str | None:
        """The value in effect."""
        value = self.entity_description.value_fn(self.device)
        return option_slug(value) if value is not None else None

    async def async_select_option(self, option: str) -> None:
        """Write the chosen value to the unit."""
        await self._async_write(self.entity_description.write_fn(self.device, option))
