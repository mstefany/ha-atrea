"""What the unit drives: fans, valves, relays, and its digital inputs (table 12)."""

from __future__ import annotations

from modbus_connection.model import Component, coil, discrete_input, gauge, integer


class Outputs(Component):
    """Analog and relay outputs of the unit and its extension boards."""

    m1 = gauge(10200, 0.001, signed=False, unit="V")
    """Fan M1 control voltage; the fan runs above 1 V."""
    m2 = gauge(10201, 0.001, signed=False, unit="V")
    """Fan M2 control voltage; the fan runs above 1 V."""
    sa1 = gauge(10202, 0.001, signed=False, unit="V")
    sa2 = gauge(10203, 0.001, signed=False, unit="V")
    """Water or electric heating is active above 0 V."""
    sc = gauge(10204, 0.001, signed=False, unit="V")
    """Circulation damper."""
    sb_plus = integer(10205, signed=False, unit="ms")
    """Bypass opening pulse per regulation period; 65534 means held on."""
    sb_minus = integer(10206, signed=False, unit="ms")
    """Bypass closing pulse per regulation period; 65534 means held on."""
    da1 = gauge(10207, 0.001, signed=False, unit="V")
    """Heat pump demand; it runs above 0 V."""
    da2 = gauge(10208, 0.001, signed=False, unit="V")

    kk = coil(10200)
    """Heating water pump runs."""
    yv1 = coil(10201)
    """Heating water valve is open."""
    yv2 = coil(10202)
    sz1 = coil(10203)
    sz2 = coil(10204)
    sv = coil(10205)
    ext = coil(10206)
    sdb = coil(10207)
    sm = coil(10208)
    se = coil(10215)
    """Heat pump heats (RD4-IO board)."""
    sc_relay = coil(10216)
    """Heat pump cools (RD4-IO board)."""
    oc1 = coil(10217)

    rg_r1 = coil(10220)
    rg_r2 = coil(10221)
    rg_r3 = coil(10222)
    rg_r4 = coil(10223)
    rg_r5 = coil(10224)
    rg_r6 = coil(10225)
    rg_r7 = coil(10226)
    rg_r8 = coil(10227)
    rg_r9 = coil(10228)
    rg_ext = coil(10229)

    tz_r1 = coil(10230)
    tz_r2 = coil(10231)
    tz_r3 = coil(10232)
    tz_r4 = coil(10233)
    tz_r5 = coil(10234)
    tz_r6 = coil(10235)
    tz_r7 = coil(10236)
    tz_r8 = coil(10237)
    tz_ext = coil(10238)


class DigitalInputs(Component):
    """Digital inputs, and which extension boards answer."""

    d1 = discrete_input(10200)
    d2 = discrete_input(10201)
    d3 = discrete_input(10202)
    d4 = discrete_input(10203)
    stp = discrete_input(10204)
    tr = discrete_input(10205)
    io_board = discrete_input(10206)
    """The RD-IO board answers."""
    df = discrete_input(10207)
    k1_board = discrete_input(10208)
    """The RD5-K module at address 1 answers."""
    k2_board = discrete_input(10209)
    """The RD5-K module at address 2 answers."""
    rg_board = discrete_input(10210)
    """An RD5-RG board is fitted."""
    rg_d1 = discrete_input(10211)
    tz_board = discrete_input(10212)
    """An RD5-TZ board is fitted."""
    tz_d1 = discrete_input(10213)
