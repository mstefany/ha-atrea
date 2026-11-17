"""Base entity for an Atrea RD5 unit."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from enum import IntEnum

from modbus_connection import ModbusError

from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AtreaCoordinator, AtreaRuntimeData


WRITE_SETTLE_SECONDS = 2.0


def option_slug(member: IntEnum) -> str:
    """The option slug of a device enum member."""
    return member.name.lower()


def enum_options(enum_type: type[IntEnum]) -> list[str]:
    """The option slugs of a device enum."""
    return [option_slug(member) for member in enum_type]


@dataclass(frozen=True, kw_only=True)
class AtreaEntityDescription(EntityDescription):
    """Describe an entity by the sub-system of the unit it reads."""

    component: str  # attribute name on AtreaRD5, as an update report names it


class AtreaEntity(CoordinatorEntity[AtreaCoordinator]):
    """An entity that reads one sub-system of the unit."""

    _attr_has_entity_name = True
    entity_description: AtreaEntityDescription

    def __init__(
        self, runtime_data: AtreaRuntimeData, description: AtreaEntityDescription
    ) -> None:
        """Initialize the entity."""
        super().__init__(runtime_data.coordinator_for(description.component))
        self.runtime_data = runtime_data
        self.device = runtime_data.device
        self.entity_description = description
        self._attr_unique_id = f"{runtime_data.unique_id}_{description.key}"
        self._attr_device_info = runtime_data.device_info

    @property
    def available(self) -> bool:
        """Whether the sub-system of this entity answered the last poll."""
        return (
            super().available
            and self.coordinator.data is not None
            and self.entity_description.component in self.coordinator.data.updated
        )

    async def _async_write(self, write: object) -> None:
        """Run a write to the unit, and poll again to show its effect."""
        try:
            await write  # type: ignore[misc]
        except (ModbusError, ValueError) as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="write_failed",
                translation_placeholders={"error": str(err) or type(err).__name__},
            ) from err
        # The unit takes a moment to apply a change; a poll right after the
        # write still reads the old state.
        await asyncio.sleep(WRITE_SETTLE_SECONDS)
        await self.runtime_data.async_refresh_all()
