"""Buttons of an Atrea RD5 unit."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import AtreaConfigEntry
from .entity import AtreaEntity, AtreaEntityDescription
from .vendor.atrea_modbus.rd5 import AtreaRD5

PARALLEL_UPDATES = 1


@dataclass(frozen=True, kw_only=True)
class AtreaButtonEntityDescription(ButtonEntityDescription, AtreaEntityDescription):
    """Describe a button."""

    press_fn: Callable[[AtreaRD5], Awaitable[None]]


BUTTONS: tuple[AtreaButtonEntityDescription, ...] = (
    AtreaButtonEntityDescription(
        key="reset_filter_interval",
        translation_key="reset_filter_interval",
        component="alarms",
        entity_category=EntityCategory.CONFIG,
        press_fn=lambda d: d.async_reset_filter_interval(),
    ),
    AtreaButtonEntityDescription(
        key="reset_alarms",
        translation_key="reset_alarms",
        component="alarms",
        entity_category=EntityCategory.CONFIG,
        press_fn=lambda d: d.async_reset_alarms(),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AtreaConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the buttons."""
    async_add_entities(
        AtreaButton(entry.runtime_data, description) for description in BUTTONS
    )


class AtreaButton(AtreaEntity, ButtonEntity):
    """A command to the unit."""

    entity_description: AtreaButtonEntityDescription

    async def async_press(self) -> None:
        """Send the command."""
        await self._async_write(self.entity_description.press_fn(self.device))
