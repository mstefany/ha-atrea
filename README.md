# Atrea for Home Assistant

A Home Assistant integration for Atrea DUPLEX ventilation units with **RD5**
control, over Modbus TCP. It is set up from the user interface.

It uses the Modbus support that Home Assistant 2026.11 introduced: the
integration asks the built-in `modbus` integration for a shared connection, and
the register map lives in the [atrea-modbus](../atrea-modbus) library.

## How it differs from other Atrea integrations

- `atrea` (JurajNyiri/HomeAssistant-Atrea) uses the web interface of the unit
  (HTTP/XML, with the web password). Atrea has deprecated that interface.
- `atrea_rd5_modbus` (thozza) uses Modbus TCP, but does not control the mode,
  the power, or the temperature.
- Units with **aMotion** control are not supported: their register map differs.

This integration uses the domain `atrea`, the same as the first one. Remove
that one before you install this one.

## Status

Alpha. Tested on one DUPLEX RB5 with a heat pump and an integrated heat storage
tank, firmware 2.03.41.

## Install

1. On the unit, enable service parameter **3.15.1 Modbus TCP**.
2. Copy `custom_components/atrea` into the `custom_components` folder of
   your Home Assistant configuration, or add this repository to HACS as a
   custom repository.
3. Restart Home Assistant.
4. Go to **Settings > Devices & services > Add integration**, choose
   **Atrea**, and enter the address of the unit.

Home Assistant 2026.11 or newer is required.

## Entities

| Entity | What it does |
| --- | --- |
| Climate | Target and room temperature. HVAC mode is the season (heat = heating season, cool = non-heating season, heat/cool = automatic) or off. Preset is the operating mode. Fan mode is the power level (R_5 units). |
| Select: operating mode, power level, season | The same settings as single entities, for automations |
| Switch: weekly program | Hands control to the weekly program of the unit, or takes it back |
| Switch: heat storage electric heater 1 and 2 | For example to use photovoltaic surplus |
| Number: heat storage targets, season changeover temperature | |
| Sensors | Air temperatures, air flows, heat storage temperatures, current phase, season, forced state |
| Binary sensors | Fault (with the list of faults as an attribute), filter change, filter clogged, heat pump heating / cooling / defrosting, heat exchanger frozen / defrosting |
| Buttons | Reset the filter change interval, reset alarms |

Entities for parts that the unit does not have are not created.

### Changes under the weekly program

When the weekly program is on, a change of mode, power or temperature is
temporary. It holds until the next interval of the weekly program. This is how
the unit works, and its own control panel behaves the same way.

## Send temperatures to the unit

The unit can take the room temperature or the outdoor temperature from
Home Assistant. This needs the matching service setting on the unit
(temperature source "BMS"). Choose the sensors under **Configure** on the
integration. The integration then sends their values with every poll, every
30 seconds. If a sensor has no value, nothing is sent, and the unit raises its
own sensor fault after 90 seconds.

## Develop

The device library is copied into `custom_components/atrea/vendor`. Do not
edit the copy. Change the library and run:

```bash
python script/vendor.py            # copy ../atrea-modbus into the integration
python script/gen_translations.py  # write translations/en.json and cs.json
```

A separate Home Assistant for development, which shares nothing with your real
one:

```bash
podman run -d --name atrea-ha-dev -p 127.0.0.1:8124:8123 \
  -v ./dev-config:/config \
  -v ./custom_components:/config/custom_components:ro \
  ghcr.io/home-assistant/home-assistant:stable
```

Then open http://localhost:8124. After a code change: `podman restart atrea-ha-dev`.
