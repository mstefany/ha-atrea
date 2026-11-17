"""Alarms and notices: discrete inputs D11100-D11184 (table 9).

The text layer of the source PDF loses the row alignment from D11156 on. The
names from there are paired with the addresses by their order in the table.
"""

from __future__ import annotations

from modbus_connection.model import Component, discrete_input

# States the unit reports as a notice, not as a fault.
NOTICES = frozenset(
    {
        "recuperator_defrosting",
        "high_tariff",
        "heat_pump_defrosting",
        "update_in_progress",
        "evaporation_active",
        "boost_on_fire_lighting",
        "filter_change_due",
    }
)


class Alarms(Component):
    """Every alarm and notice flag of the unit."""

    unit_overheated = discrete_input(11100)
    orientation_not_set = discrete_input(11101)
    heater_type_not_set = discrete_input(11102)
    frost_protection_2 = discrete_input(11103)
    stp_contact_active = discrete_input(11104)
    dp1_fault = discrete_input(11105)
    dp2_fault = discrete_input(11106)
    tu1_fault = discrete_input(11107)
    tu2_fault = discrete_input(11108)
    tea_fault = discrete_input(11109)
    teb_fault = discrete_input(11110)
    ta2_fault = discrete_input(11111)
    io_board_fault = discrete_input(11112)
    unbalanced_flow = discrete_input(11114)
    frost_protection_1 = discrete_input(11115)
    indoor_sensor_fault = discrete_input(11116)
    recuperator_frozen = discrete_input(11117)
    recuperator_defrosting = discrete_input(11118)
    high_tariff = discrete_input(11119)
    insufficient_flow = discrete_input(11120)
    insufficient_primary_heating = discrete_input(11121)
    filter_clogged = discrete_input(11122)
    in1_fault = discrete_input(11123)
    in2_fault = discrete_input(11124)
    k1_in1_fault = discrete_input(11125)
    k1_in2_fault = discrete_input(11126)
    k1_in3_fault = discrete_input(11127)
    k1_in4_fault = discrete_input(11128)
    k2_in1_fault = discrete_input(11129)
    k2_in2_fault = discrete_input(11130)
    k2_in3_fault = discrete_input(11131)
    k2_in4_fault = discrete_input(11132)
    not_commissioned = discrete_input(11140)
    configuration_file_missing = discrete_input(11141)
    insufficient_preheating = discrete_input(11143)
    invalid_heater_combination = discrete_input(11144)
    dp3_fault = discrete_input(11145)
    external_pressure_sensor_fault = discrete_input(11146)
    k1_board_fault = discrete_input(11147)
    k2_board_fault = discrete_input(11148)
    heat_pump_defrosting = discrete_input(11149)
    k1_tr1_fault = discrete_input(11150)
    k1_tr2_fault = discrete_input(11151)
    k1_tr3_fault = discrete_input(11152)
    k1_tr4_fault = discrete_input(11153)
    k1_tr5_fault = discrete_input(11154)
    k2_tr1_fault = discrete_input(11155)
    k2_tr2_fault = discrete_input(11156)
    k2_tr3_fault = discrete_input(11157)
    k2_tr4_fault = discrete_input(11158)
    k2_tr5_fault = discrete_input(11159)
    update_in_progress = discrete_input(11160)
    invalid_cooling_configuration = discrete_input(11162)
    emergency_mode_active = discrete_input(11165)
    capillary_frost_protection = discrete_input(11166)
    frost_protection_configuration = discrete_input(11167)
    learning_incomplete = discrete_input(11168)
    outdoor_sensor_fault = discrete_input(11169)
    extract_sensor_fault = discrete_input(11170)
    cooling_unavailable = discrete_input(11171)
    heating_unavailable = discrete_input(11172)
    evaporation_active = discrete_input(11173)
    boost_on_fire_lighting = discrete_input(11174)
    invalid_flow_settings = discrete_input(11175)
    filter_change_due = discrete_input(11183)
    """The filter change interval has run out."""
    filter_test_configuration = discrete_input(11184)

    @property
    def active(self) -> frozenset[str]:
        """Names of every flag that is set, alarms and notices alike."""
        return frozenset(name for name in self.declared_fields if getattr(self, name))

    @property
    def faults(self) -> frozenset[str]:
        """Names of the set flags that are faults."""
        return self.active - NOTICES
