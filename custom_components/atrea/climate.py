"""The climate entity of an Atrea RD5 unit.

The unit maps onto a climate entity like this:

- The HVAC mode is the season: heat is the heating season, cool is the
  non-heating season, and heat/cool lets the unit pick by outdoor temperature.
  Off switches the unit off.
- The preset is the operating mode (automatic, ventilation, circulation ...).
- The fan mode is the power level, on R_5 units, whose levels depend on the
  operating mode.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.climate import (
    ATTR_HVAC_MODE,
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import CONF_CLIMATE_SETS_SEASON, DOMAIN
from .coordinator import AtreaConfigEntry, AtreaRuntimeData
from .entity import AtreaEntity, AtreaEntityDescription, option_slug
from .vendor.atrea_modbus.rd5 import (
    MAX_TEMPERATURE,
    MIN_TEMPERATURE,
    R5_POWER_LEVELS,
    OperatingMode,
    R5Power,
    SeasonMode,
)

PARALLEL_UPDATES = 1

_NATIVE_NAMES = hasattr(ClimateEntity, "native_temperature_unit")

SEASON_TO_HVAC = {
    SeasonMode.HEATING: HVACMode.HEAT,
    SeasonMode.NON_HEATING: HVACMode.COOL,
    SeasonMode.T_ODA: HVACMode.HEAT_COOL,
    SeasonMode.T_ODA_PLUS: HVACMode.HEAT_COOL,
}
HVAC_TO_SEASON = {
    HVACMode.HEAT: SeasonMode.HEATING,
    HVACMode.COOL: SeasonMode.NON_HEATING,
    HVACMode.HEAT_COOL: SeasonMode.T_ODA,
}

DESCRIPTION = AtreaEntityDescription(key="climate", component="control", name=None)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AtreaConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the climate entity."""
    async_add_entities([AtreaClimate(entry.runtime_data)])


class AtreaClimate(AtreaEntity, ClimateEntity):
    """The unit as a climate entity."""

    _attr_translation_key = "unit"
    _attr_min_temp = MIN_TEMPERATURE
    _attr_max_temp = MAX_TEMPERATURE
    _attr_target_temperature_step = 0.5

    def __init__(self, runtime_data: AtreaRuntimeData) -> None:
        """Initialize the climate entity."""
        super().__init__(runtime_data, DESCRIPTION)
        features = (
            ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.PRESET_MODE
            | ClimateEntityFeature.TURN_ON
            | ClimateEntityFeature.TURN_OFF
        )
        if self.device.has_power_levels:
            features |= ClimateEntityFeature.FAN_MODE
        self._attr_supported_features = features
        # The mode to return to when the unit is switched on again.
        self._last_mode = OperatingMode.AUTOMATIC

    async def async_added_to_hass(self) -> None:
        """Follow the settings as well: the season is one of them."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self.runtime_data.settings.async_add_listener(
                self._handle_coordinator_update
            )
        )

    @property
    def _mode(self) -> OperatingMode | None:
        mode = self.device.control.requested_mode
        if mode not in (None, OperatingMode.OFF):
            self._last_mode = mode
        return mode

    @property
    def _resume_mode(self) -> OperatingMode:
        """The mode to switch on in: the last one, if the unit still accepts it."""
        if self._last_mode in self.device.available_modes:
            return self._last_mode
        return OperatingMode.VENTILATION

    def _current_temperature(self) -> float | None:
        """The room temperature the unit regulates to."""
        return self.device.sensors.indoor_air

    def _target_temperature(self) -> float | None:
        """The requested temperature."""
        return self.device.control.requested_temperature

    # Home Assistant 2026.11 renamed these three; it warns about the old names
    # and earlier releases do not know the new ones.
    if _NATIVE_NAMES:
        _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
        native_current_temperature = property(_current_temperature)
        native_target_temperature = property(_target_temperature)
    else:
        _attr_temperature_unit = UnitOfTemperature.CELSIUS
        current_temperature = property(_current_temperature)
        target_temperature = property(_target_temperature)

    @property
    def hvac_mode(self) -> HVACMode | None:
        """Off, or the season the unit is set to."""
        if (mode := self._mode) is None:
            return None
        if mode is OperatingMode.OFF:
            return HVACMode.OFF
        season = self.device.settings.season_mode
        return SEASON_TO_HVAC.get(season) if season is not None else None

    @property
    def _sets_season(self) -> bool:
        """Whether the HVAC mode may change the season (an option)."""
        options = self.coordinator.config_entry.options
        return bool(options.get(CONF_CLIMATE_SETS_SEASON, False))

    @property
    def hvac_modes(self) -> list[HVACMode]:
        """Off and the seasons; by default only the season the unit is set to.

        The season decides whether the unit heats at all, and it changes about
        twice a year. By default a generic command, such as a voice assistant
        asking for cooling, cannot change it; the season select can.
        """
        if self._sets_season:
            return [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL, HVACMode.HEAT_COOL]
        season = self.device.settings.season_mode
        current = SEASON_TO_HVAC.get(season) if season is not None else None
        return [HVACMode.OFF] if current is None else [HVACMode.OFF, current]

    @property
    def hvac_action(self) -> HVACAction | None:
        """What the unit does right now."""
        outputs = self.device.outputs
        if self._mode is OperatingMode.OFF and not (outputs.m1 or outputs.m2):
            return HVACAction.OFF
        if outputs.sc_relay:
            return HVACAction.COOLING
        # The outputs that light the heating sign of the unit's own web
        # interface. SE and OC1 heat only on some installations.
        config = self.device.configuration
        if (
            outputs.yv2
            or (outputs.sa2 or 0) > 0
            or (outputs.se and config.ground_heat_exchanger == 0)
            or (outputs.oc1 and config.heat_exchanger_type == 0)
        ):
            return HVACAction.HEATING
        if (outputs.m1 or 0) > 1 or (outputs.m2 or 0) > 1:
            return HVACAction.FAN
        return HVACAction.IDLE

    @property
    def preset_modes(self) -> list[str]:
        """The operating modes the unit accepts now."""
        modes = [
            mode
            for mode in self.device.available_modes
            if mode is not OperatingMode.OFF
        ]
        # The panel or the weekly program may run a mode Home Assistant would
        # not offer now; it must still be a valid preset.
        if (current := self._mode) not in (None, OperatingMode.OFF, *modes):
            modes.append(current)
        return [option_slug(mode) for mode in modes]

    @property
    def preset_mode(self) -> str | None:
        """The requested operating mode."""
        mode = self._mode
        if mode is None or mode is OperatingMode.OFF:
            return None
        return option_slug(mode)

    @property
    def fan_modes(self) -> list[str] | None:
        """The power levels of the requested operating mode."""
        if not self.device.has_power_levels or (mode := self._mode) is None:
            return None
        return [option_slug(level) for level in R5_POWER_LEVELS[mode]]

    @property
    def fan_mode(self) -> str | None:
        """The requested power level."""
        level = self.device.r5_power
        return option_slug(level) if level is not None else None

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Request a temperature."""
        if (hvac_mode := kwargs.get(ATTR_HVAC_MODE)) is not None:
            await self.async_set_hvac_mode(hvac_mode)
        if (temperature := kwargs.get(ATTR_TEMPERATURE)) is not None:
            await self._async_write(
                self.device.control.async_set_temperature(temperature)
            )

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Switch the unit off, or set the season and switch it on."""
        if hvac_mode is HVACMode.OFF:
            await self._async_write(self.device.async_set_mode(OperatingMode.OFF))
            return
        season = HVAC_TO_SEASON[hvac_mode]
        current = self.device.settings.season_mode
        # Both automatic season modes show as heat/cool; keep the one in use.
        if current is None or SEASON_TO_HVAC.get(current) is not hvac_mode:
            if not self._sets_season:
                raise ServiceValidationError(
                    translation_domain=DOMAIN,
                    translation_key="season_locked",
                )
            await self._async_write(self.device.settings.write("season_mode", season))
        if self._mode is OperatingMode.OFF:
            await self._async_write(self.device.async_set_mode(self._resume_mode))

    async def async_turn_on(self) -> None:
        """Switch the unit on, in the mode it had before."""
        if self._mode is OperatingMode.OFF:
            await self._async_write(self.device.async_set_mode(self._resume_mode))

    async def async_turn_off(self) -> None:
        """Switch the unit off."""
        await self.async_set_hvac_mode(HVACMode.OFF)

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Request an operating mode."""
        await self._async_write(
            self.device.async_set_mode(OperatingMode[preset_mode.upper()])
        )

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Request a power level."""
        await self._async_write(self.device.async_set_power(R5Power[fan_mode.upper()]))
