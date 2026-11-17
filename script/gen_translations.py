"""Write translations/en.json and translations/cs.json from one table.

Keeping both languages side by side makes a missing translation obvious.
Run: python script/gen_translations.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

OUT = Path(__file__).parent.parent / "custom_components" / "atrea" / "translations"

# Each leaf is (English, Czech).
MODES = {
    "off": ("Off", "Vypnuto"),
    "automatic": ("Automatic", "Automat"),
    "ventilation": ("Ventilation", "Větrání"),
    "circulation_with_ventilation": (
        "Circulation with ventilation",
        "Cirkulace s větráním",
    ),
    "circulation": ("Circulation", "Cirkulace"),
    "night_precooling": ("Night precooling", "Noční předchlazení"),
    "unbalanced": ("Unbalanced ventilation", "Rozvážení"),
    "overpressure": ("Overpressure ventilation", "Přetlakové větrání"),
}
LEVELS = {"min": ("Min", "Min"), "norm": ("Norm", "Norm"), "max": ("Max", "Max")}
POWER = {
    **{
        f"ventilation_{k}": (f"Ventilation {en}", f"Větrání {cs}")
        for k, (en, cs) in LEVELS.items()
    },
    **{
        f"circulation_{k}": (f"Circulation {en}", f"Cirkulace {cs}")
        for k, (en, cs) in LEVELS.items()
    },
    **{
        f"{c}_{v}": (
            f"Circulation {LEVELS[c][0]} / ventilation {LEVELS[v][0]}",
            f"Cirkulace {LEVELS[c][1]} / větrání {LEVELS[v][1]}",
        )
        for c in LEVELS
        for v in LEVELS
    },
}
SEASON_MODES = {
    "heating": ("Heating season", "Topná sezóna"),
    "non_heating": ("Non-heating season", "Netopná sezóna"),
    "t_oda": ("Automatic by outdoor temperature", "Automaticky podle T-ODA"),
    "t_oda_plus": (
        "Automatic by outdoor temperature and heat gain",
        "Automaticky podle T-ODA+",
    ),
}
FORCED = {
    "none": ("None", "Žádný"),
    "starting": ("Starting", "Náběh"),
    "stopping": ("Stopping", "Doběh"),
    **{f"input_d{n}": (f"Input D{n}", f"Vstup D{n}") for n in range(1, 5)},
    **{f"input_in{n}": (f"Input IN{n}", f"Vstup IN{n}") for n in range(1, 3)},
    **{
        f"input_k{k}_in{n}": (f"Input INk{n} of module {k}", f"Vstup INk{n} modulu {k}")
        for k in (1, 2)
        for n in range(1, 5)
    },
    **{
        f"input_k{k}_tr{n}": (f"Input TRk{n} of module {k}", f"Vstup TRk{n} modulu {k}")
        for k in (1, 2)
        for n in range(1, 6)
    },
    "heat_pump_defrosting": ("Heat pump defrosting", "Odmrazování tepelného čerpadla"),
    "preheating": ("Preheating", "Předehřátí"),
    "learning": ("Learning", "Učící režim"),
    "heat_pump_defrosting_2": (
        "Heat pump defrosting",
        "Odmrazování tepelného čerpadla",
    ),
    "filter_test": ("Filter test", "Test filtru"),
    "periodic_ventilation": ("Periodic ventilation", "Periodické větrání"),
}


def name(en: str, cs: str, **extra: Any) -> dict[str, Any]:
    return {"name": (en, cs), **extra}


TREE: dict[str, Any] = {
    "config": {
        "step": {
            "user": {
                "description": (
                    "Enable Modbus TCP on the unit first: service parameter 3.15.1.",
                    "Nejprve na jednotce povolte Modbus TCP: servisní parametr 3.15.1.",
                ),
                "data": {"host": ("Host", "Adresa"), "port": ("Port", "Port")},
                "data_description": {
                    "host": (
                        "The hostname or IP address of the unit.",
                        "Název nebo IP adresa jednotky.",
                    ),
                    "port": (
                        "The Modbus TCP port of the unit.",
                        "Port Modbus TCP jednotky.",
                    ),
                },
            }
        },
        "error": {
            "cannot_connect": ("Failed to connect: {error}", "Nelze se připojit: {error}"),
            "not_rd5": (
                "The device answers, but not like an Atrea unit with RD5 control.",
                "Zařízení odpovídá, ale ne jako jednotka Atrea s regulací RD5.",
            ),
        },
        "abort": {
            "already_configured": (
                "Device is already configured",
                "Zařízení je již nastaveno",
            )
        },
    },
    "options": {
        "step": {
            "init": {
                "description": (
                    "The unit can take the room and the outdoor temperature from Home Assistant. This needs the matching service setting on the unit (temperature source BMS).",
                    "Jednotka může přebírat vnitřní a venkovní teplotu z Home Assistanta. Na jednotce musí být nastaven odpovídající zdroj teploty (BMS).",
                ),
                "data": {
                    "indoor_temperature_entity": (
                        "Room temperature sensor",
                        "Čidlo vnitřní teploty",
                    ),
                    "outdoor_temperature_entity": (
                        "Outdoor temperature sensor",
                        "Čidlo venkovní teploty",
                    ),
                },
            }
        }
    },
    "exceptions": {
        "write_failed": {
            "message": (
                "The unit did not accept the change: {error}",
                "Jednotka změnu nepřijala: {error}",
            )
        }
    },
    "entity": {
        "climate": {
            "unit": {
                "state_attributes": {
                    "preset_mode": {"state": MODES},
                    "fan_mode": {"state": POWER},
                }
            }
        },
        "select": {
            "operating_mode": name("Operating mode", "Režim", state=MODES),
            "power_level": name("Power level", "Výkon", state=POWER),
            "season_mode": name("Season", "Sezóna", state=SEASON_MODES),
        },
        "sensor": {
            "outdoor_air": name("Outdoor air temperature", "Teplota venkovního vzduchu"),
            "supply_air": name("Supply air temperature", "Teplota přiváděného vzduchu"),
            "extract_air": name("Extract air temperature", "Teplota odváděného vzduchu"),
            "exhaust_air": name("Exhaust air temperature", "Teplota odpadního vzduchu"),
            "indoor_air": name("Room temperature", "Teplota vnitřního vzduchu"),
            "outdoor_air_average": name(
                "Average outdoor air temperature", "Průměrná teplota venkovního vzduchu"
            ),
            "supply_flow": name("Supply air flow", "Průtok přiváděného vzduchu"),
            "extract_flow": name("Extract air flow", "Průtok odváděného vzduchu"),
            "outdoor_flow": name("Outdoor air flow", "Průtok venkovního vzduchu"),
            "supply_flow_requested": name(
                "Requested supply air flow", "Požadovaný průtok přiváděného vzduchu"
            ),
            "extract_flow_requested": name(
                "Requested extract air flow", "Požadovaný průtok odváděného vzduchu"
            ),
            "outdoor_flow_requested": name(
                "Requested outdoor air flow", "Požadovaný průtok venkovního vzduchu"
            ),
            "current_phase": name("Current phase", "Aktuální fáze", state=MODES),
            "season": name(
                "Current season",
                "Aktuální sezóna",
                state={
                    "heating": SEASON_MODES["heating"],
                    "non_heating": SEASON_MODES["non_heating"],
                },
            ),
            "forced_state": name("Forced state", "Vnucený stav", state=FORCED),
            "fan_m1_voltage": name("Fan M1 control voltage", "Řídicí napětí ventilátoru M1"),
            "fan_m2_voltage": name("Fan M2 control voltage", "Řídicí napětí ventilátoru M2"),
            "heat_pump_demand": name("Heat pump demand", "Požadavek na tepelné čerpadlo"),
            "heat_storage_top": name(
                "Heat storage top temperature", "Teplota v horní části zásobníku"
            ),
            "heat_storage_middle": name(
                "Heat storage middle temperature", "Teplota ve střední části zásobníku"
            ),
        },
        "binary_sensor": {
            "fault": name("Fault", "Porucha"),
            "filter_change_due": name("Filter change", "Výměna filtru"),
            "filter_clogged": name("Filter clogged", "Zanesený filtr"),
            "recuperator_frozen": name("Heat exchanger frozen", "Zámraz rekuperátoru"),
            "recuperator_defrosting": name(
                "Heat exchanger defrosting", "Odmrazování rekuperátoru"
            ),
            "heat_pump_heating": name("Heat pump heating", "Tepelné čerpadlo topí"),
            "heat_pump_cooling": name("Heat pump cooling", "Tepelné čerpadlo chladí"),
            "heat_pump_defrosting": name(
                "Heat pump defrosting", "Odmrazování tepelného čerpadla"
            ),
        },
        "switch": {
            "weekly_program": name("Weekly program", "Týdenní program"),
            "electric_heater_1": name(
                "Heat storage electric heater 1", "Elektrická patrona zásobníku 1"
            ),
            "electric_heater_2": name(
                "Heat storage electric heater 2", "Elektrická patrona zásobníku 2"
            ),
        },
        "number": {
            "heat_storage_target_top": name(
                "Heat storage top target temperature",
                "Požadovaná teplota v horní části zásobníku",
            ),
            "heat_storage_target_middle": name(
                "Heat storage middle target temperature",
                "Požadovaná teplota ve střední části zásobníku",
            ),
            "season_temperature": name(
                "Season changeover temperature", "Teplota přepnutí sezóny"
            ),
            "power": name("Power", "Výkon"),
            "power_step": name("Power level", "Stupeň výkonu"),
        },
        "button": {
            "reset_filter_interval": name(
                "Reset filter change interval", "Potvrdit výměnu filtru"
            ),
            "reset_alarms": name("Reset alarms", "Reset poruch"),
        },
    },
}


def pick(node: Any, index: int) -> Any:
    if isinstance(node, tuple):
        return node[index]
    return {key: pick(value, index) for key, value in node.items()}


for index, language in enumerate(("en", "cs")):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{language}.json").write_text(
        json.dumps(pick(TREE, index), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
