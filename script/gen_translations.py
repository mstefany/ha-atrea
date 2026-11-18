"""Write custom_components/atrea/translations/*.json.

English is the source and lives in this file. Every other language is a flat
file script/i18n/<language>.json: one key per text, for example
"entity.sensor.outdoor_air.name". The lists that several entities share
(modes, power levels, seasons, forced states) appear once, as "mode.off",
"power.circulation_min", "season.heating", "forced.none".

The script stops when a language file misses a key, has a key that English
does not have, or changes a placeholder such as {error}.

Run: python script/gen_translations.py
     python script/gen_translations.py --check   (compare, write nothing)
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
import sys
from typing import Any

ROOT = Path(__file__).parent.parent
OUT = ROOT / "custom_components" / "atrea" / "translations"
I18N = Path(__file__).parent / "i18n"


@dataclass(frozen=True)
class Group:
    """A list of state names that several entities share."""

    name: str
    texts: dict[str, str]

    def subset(self, *keys: str) -> Group:
        return Group(self.name, {key: self.texts[key] for key in keys})


MODES = Group(
    "mode",
    {
        "off": "Off",
        "automatic": "Automatic",
        "ventilation": "Ventilation",
        "circulation_with_ventilation": "Circulation with ventilation",
        "circulation": "Circulation",
        "night_precooling": "Night precooling",
        "unbalanced": "Unbalanced ventilation",
        "overpressure": "Overpressure ventilation",
    },
)
LEVELS = {"min": "Min", "norm": "Norm", "max": "Max"}
POWER = Group(
    "power",
    {
        **{f"ventilation_{k}": f"Ventilation {v}" for k, v in LEVELS.items()},
        **{f"circulation_{k}": f"Circulation {v}" for k, v in LEVELS.items()},
        **{
            f"{c}_{v}": f"Circulation {LEVELS[c]} / ventilation {LEVELS[v]}"
            for c in LEVELS
            for v in LEVELS
        },
    },
)
SEASONS = Group(
    "season",
    {
        "heating": "Heating season",
        "non_heating": "Non-heating season",
        "t_oda": "Automatic by outdoor temperature",
        "t_oda_plus": "Automatic by outdoor temperature and heat gain",
    },
)
FORCED = Group(
    "forced",
    {
        "none": "None",
        "starting": "Starting",
        "stopping": "Stopping",
        **{f"input_d{n}": f"Input D{n}" for n in range(1, 5)},
        **{f"input_in{n}": f"Input IN{n}" for n in range(1, 3)},
        **{
            f"input_k{k}_in{n}": f"Input INk{n} of module {k}"
            for k in (1, 2)
            for n in range(1, 5)
        },
        **{
            f"input_k{k}_tr{n}": f"Input TRk{n} of module {k}"
            for k in (1, 2)
            for n in range(1, 6)
        },
        "heat_pump_defrosting": "Heat pump defrosting",
        "preheating": "Preheating",
        "learning": "Learning",
        "heat_pump_defrosting_2": "Heat pump defrosting",
        "filter_test": "Filter test",
        "periodic_ventilation": "Periodic ventilation",
    },
)
GROUPS = (MODES, POWER, SEASONS, FORCED)


def name(text: str, **extra: Any) -> dict[str, Any]:
    return {"name": text, **extra}


TREE: dict[str, Any] = {
    "config": {
        "step": {
            "user": {
                "description": "Enable Modbus TCP on the unit first: service parameter 3.15.1.",
                "data": {"host": "Host", "port": "Port"},
                "data_description": {
                    "host": "The hostname or IP address of the unit.",
                    "port": "The Modbus TCP port of the unit.",
                },
            }
        },
        "error": {
            "cannot_connect": "Failed to connect: {error}",
            "not_rd5": "The device answers, but not like an Atrea unit with RD5 control.",
        },
        "abort": {"already_configured": "Device is already configured"},
    },
    "options": {
        "step": {
            "init": {
                "description": "The unit can take the room and the outdoor temperature from Home Assistant. This needs the matching service setting on the unit (temperature source BMS).",
                "data": {
                    "indoor_temperature_entity": "Room temperature sensor",
                    "outdoor_temperature_entity": "Outdoor temperature sensor",
                    "climate_sets_season": "Climate entity can change the season",
                },
                "data_description": {
                    "climate_sets_season": "Off: the climate entity switches the unit on and off only; change the season with the season select. On: heat, cool and heat/cool set the heating season, the non-heating season and T-ODA, also when a voice assistant or an automation asks.",
                },
            }
        }
    },
    "exceptions": {
        "season_locked": {
            "message": "The climate entity does not change the season. Use the season select, or allow it in the integration options."
        },
        "write_failed": {"message": "The unit did not accept the change: {error}"},
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
            "operating_mode": name("Operating mode", state=MODES),
            "power_level": name("Power level", state=POWER),
            "season_mode": name("Season", state=SEASONS),
        },
        "sensor": {
            "outdoor_air": name("Outdoor air temperature"),
            "supply_air": name("Supply air temperature"),
            "extract_air": name("Extract air temperature"),
            "exhaust_air": name("Exhaust air temperature"),
            "indoor_air": name("Room temperature"),
            "outdoor_air_average": name("Average outdoor air temperature"),
            "supply_flow": name("Supply air flow"),
            "extract_flow": name("Extract air flow"),
            "outdoor_flow": name("Outdoor air flow"),
            "supply_flow_requested": name("Requested supply air flow"),
            "extract_flow_requested": name("Requested extract air flow"),
            "outdoor_flow_requested": name("Requested outdoor air flow"),
            "current_mode": name("Current operating mode", state=MODES),
            "season": name(
                "Current season", state=SEASONS.subset("heating", "non_heating")
            ),
            "forced_state": name("Forced state", state=FORCED),
            "fan_m1_voltage": name("Fan M1 control voltage"),
            "fan_m2_voltage": name("Fan M2 control voltage"),
            "heat_pump_demand": name("Heat pump demand"),
            "heat_storage_top": name("Heat storage top temperature"),
            "heat_storage_middle": name("Heat storage middle temperature"),
        },
        "binary_sensor": {
            "fault": name("Fault"),
            "filter_change_due": name("Filter change"),
            "filter_clogged": name("Filter clogged"),
            "recuperator_frozen": name("Heat exchanger frozen"),
            "recuperator_defrosting": name("Heat exchanger defrosting"),
            "heat_pump_heating": name("Heat pump heating"),
            "heat_pump_cooling": name("Heat pump cooling"),
            "heat_pump_defrosting": name("Heat pump defrosting"),
        },
        "switch": {
            "weekly_program": name("Weekly program"),
            "electric_heater_1": name("Heat storage electric heater 1"),
            "electric_heater_2": name("Heat storage electric heater 2"),
        },
        "number": {
            "heat_storage_target_top": name("Heat storage top target temperature"),
            "heat_storage_target_middle": name(
                "Heat storage middle target temperature"
            ),
            "season_temperature": name("Season changeover temperature"),
            "power": name("Power"),
            "power_step": name("Power level"),
        },
        "button": {
            "reset_filter_interval": name("Reset filter change interval"),
            "reset_alarms": name("Reset alarms"),
        },
    },
}


def english() -> dict[str, str]:
    """Every English text by its flat key."""
    texts: dict[str, str] = {}
    for group in GROUPS:
        texts.update({f"{group.name}.{key}": text for key, text in group.texts.items()})

    def walk(node: Any, path: str) -> None:
        if isinstance(node, str):
            texts[path] = node
        elif isinstance(node, dict):
            for key, value in node.items():
                walk(value, f"{path}.{key}" if path else key)

    walk(TREE, "")
    return texts


def render(node: Any, texts: dict[str, str], path: str = "") -> Any:
    if isinstance(node, Group):
        return {key: texts[f"{node.name}.{key}"] for key in node.texts}
    if isinstance(node, str):
        return texts[path]
    return {
        key: render(value, texts, f"{path}.{key}" if path else key)
        for key, value in node.items()
    }


PLACEHOLDER = re.compile(r"\{[a-z_]+\}")


def problems(language: str, texts: dict[str, str], source: dict[str, str]) -> list[str]:
    found = [f"{language}: missing {key}" for key in source if key not in texts]
    found += [f"{language}: unknown {key}" for key in texts if key not in source]
    for key, text in texts.items():
        if key not in source:
            continue
        if sorted(PLACEHOLDER.findall(text)) != sorted(
            PLACEHOLDER.findall(source[key])
        ):
            found.append(f"{language}: placeholders differ in {key}")
        if not text.strip() or text != text.strip():
            found.append(f"{language}: empty text or spaces at the ends in {key}")
    return found


def main() -> int:
    check = "--check" in sys.argv
    source = english()
    outputs = {"en": render(TREE, source)}
    errors: list[str] = []
    for path in sorted(I18N.glob("*.json")):
        texts = json.loads(path.read_text(encoding="utf-8"))
        errors += problems(path.stem, texts, source)
        if not errors:
            outputs[path.stem] = render(TREE, texts)
    if errors:
        print("\n".join(errors))
        return 1
    stale = []
    for language, tree in outputs.items():
        target = OUT / f"{language}.json"
        content = json.dumps(tree, indent=2, ensure_ascii=False) + "\n"
        if check:
            if not target.exists() or target.read_text(encoding="utf-8") != content:
                stale.append(target.name)
            continue
        OUT.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8", newline="\n")
    if stale:
        print("Out of date, run python script/gen_translations.py:", ", ".join(stale))
        return 1
    print(f"{len(outputs)} languages, {len(source)} texts each")
    return 0


if __name__ == "__main__":
    sys.exit(main())
