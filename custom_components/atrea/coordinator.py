"""Data update coordinators for an Atrea RD5 unit."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import timedelta
import logging

from modbus_connection import ModbusError
from modbus_connection.model import UpdateReport

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN, UnitOfTemperature
from homeassistant.core import (
    CALLBACK_TYPE,
    Event,
    EventStateChangedData,
    HomeAssistant,
    callback,
)
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util.unit_conversion import TemperatureConverter

from .const import (
    CONF_INDOOR_TEMPERATURE_ENTITY,
    CONF_OUTDOOR_TEMPERATURE_ENTITY,
    DOMAIN,
    MANUFACTURER,
)
from .vendor.atrea_modbus.rd5 import READINGS, AtreaRD5, IndoorTemperatureSource

_LOGGER = logging.getLogger(__name__)

NO_VALUE = (STATE_UNAVAILABLE, STATE_UNKNOWN)


class AtreaCoordinator(DataUpdateCoordinator[UpdateReport]):
    """Run one of the update methods of the unit on its own interval."""

    config_entry: AtreaConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: AtreaConfigEntry,
        name: str,
        device: AtreaRD5,
        poll: Callable[[], Awaitable[UpdateReport]],
        interval: timedelta,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass, _LOGGER, config_entry=entry, name=name, update_interval=interval
        )
        self.device = device
        self._poll = poll
        self._failing: set[str] = set()

    async def _async_update_data(self) -> UpdateReport:
        try:
            report = await self._poll()
        except ModbusError as err:
            raise UpdateFailed(
                f"The unit did not answer: {str(err) or type(err).__name__}"
            ) from err
        if not report.updated:
            errors = list(report.failed.values())
            raise UpdateFailed(
                f"No part of the unit answered: {errors[0] if errors else 'no data'}"
            )
        for name, cause in report.failed.items():
            if name not in self._failing:
                self._failing.add(name)
                _LOGGER.warning(
                    "%s: %s failed to refresh, its entities are unavailable: %s",
                    self.name,
                    name,
                    str(cause) or type(cause).__name__,
                )
        for name in report.updated & self._failing:
            self._failing.discard(name)
            _LOGGER.info("%s: %s is available again", self.name, name)
        return report


class AtreaReadingsCoordinator(AtreaCoordinator):
    """Poll the readings, and send the temperatures the unit takes from outside."""

    _unwatch: CALLBACK_TYPE | None = None

    @callback
    def async_watch_sources(self) -> None:
        """Send at once when a chosen sensor gets a value again.

        The unit raises a sensor fault 90 seconds after the last value. After a
        restart of Home Assistant, or after the sensor was unavailable, the
        value goes out without waiting for the next poll. Other changes wait
        for the poll, which keeps the Modbus traffic low.
        """
        self.async_stop_watching()
        options = self.config_entry.options
        entities = [
            entity_id
            for option in (
                CONF_INDOOR_TEMPERATURE_ENTITY,
                CONF_OUTDOOR_TEMPERATURE_ENTITY,
            )
            if (entity_id := options.get(option))
        ]
        if entities:
            self._unwatch = async_track_state_change_event(
                self.hass, entities, self._async_source_changed
            )

    @callback
    def async_stop_watching(self) -> None:
        """Stop following the chosen sensors."""
        if self._unwatch is not None:
            self._unwatch()
            self._unwatch = None

    async def _async_source_changed(self, event: Event[EventStateChangedData]) -> None:
        old, new = event.data["old_state"], event.data["new_state"]
        if new is None or new.state in NO_VALUE:
            return
        if old is None or old.state in NO_VALUE:
            await self._async_send_temperatures()

    async def _async_update_data(self) -> UpdateReport:
        report = await super()._async_update_data()
        await self._async_send_temperatures()
        return report

    def _temperature(self, option: str) -> float | None:
        """The temperature of the sensor an option names, in °C."""
        entity_id = self.config_entry.options.get(option)
        if not entity_id or (state := self.hass.states.get(entity_id)) is None:
            return None
        if state.state in NO_VALUE:
            return None
        unit = state.attributes.get("unit_of_measurement", UnitOfTemperature.CELSIUS)
        try:
            value = TemperatureConverter.convert(
                float(state.state), unit, UnitOfTemperature.CELSIUS
            )
        except (ValueError, HomeAssistantError):
            return None
        # The range of the unit; also drops NaN and infinity.
        return value if -50.0 <= value <= 130.0 else None

    async def _async_send_temperatures(self) -> None:
        """Send the configured temperatures; the unit wants them every 90 seconds.

        A value that is missing is not sent, so the unit raises its own sensor
        fault instead of regulating to a stale temperature.
        """
        config = self.device.configuration
        bms = self.device.bms_temperatures
        try:
            if (
                config.indoor_temperature_source is IndoorTemperatureSource.BMS
                and (indoor := self._temperature(CONF_INDOOR_TEMPERATURE_ENTITY))
                is not None
            ):
                await bms.write("indoor_air", round(indoor, 1))
            if (
                config.outdoor_temperature_from_bms
                and (outdoor := self._temperature(CONF_OUTDOOR_TEMPERATURE_ENTITY))
                is not None
            ):
                await bms.write("outdoor_air", round(outdoor, 1))
        except (ModbusError, ValueError, OverflowError) as err:
            _LOGGER.warning(
                "%s: could not send a temperature to the unit: %s",
                self.name,
                str(err) or type(err).__name__,
            )


@dataclass
class AtreaRuntimeData:
    """What a loaded config entry holds."""

    device: AtreaRD5
    readings: AtreaReadingsCoordinator
    settings: AtreaCoordinator
    unique_id: str

    def coordinator_for(self, component: str) -> AtreaCoordinator:
        """Which coordinator polls a given sub-system of the unit."""
        return self.readings if component in READINGS else self.settings

    @property
    def device_info(self) -> dr.DeviceInfo:
        """Describe the unit to the device registry."""
        return dr.DeviceInfo(
            identifiers={(DOMAIN, self.unique_id)},
            manufacturer=MANUFACTURER,
            model=self.device.model,
            serial_number=self.device.serial_number,
            sw_version=self.device.firmware_version,
        )

    async def async_refresh_all(self) -> None:
        """Poll everything again, after a write that touches both groups."""
        # Not the debounced request: the caller waits for the fresh state.
        await self.settings.async_refresh()
        await self.readings.async_refresh()


type AtreaConfigEntry = ConfigEntry[AtreaRuntimeData]
