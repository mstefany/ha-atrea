"""Which unit this is. The source document does not list these registers.

They are the indexes the web interface of the unit uses, and a DUPLEX RB5
with firmware 2.03.41 answers them over Modbus as well.
"""

from __future__ import annotations

from modbus_connection.model import Component, integer

SERIAL_REGISTER = 12300
SERIAL_LENGTH = 10


class Identity(Component):
    """The production number and the type codes of the unit."""

    _serial_0 = integer(12300, signed=False)
    _serial_1 = integer(12301, signed=False)
    _serial_2 = integer(12302, signed=False)
    _serial_3 = integer(12303, signed=False)
    _serial_4 = integer(12304, signed=False)
    _serial_5 = integer(12305, signed=False)
    _serial_6 = integer(12306, signed=False)
    _serial_7 = integer(12307, signed=False)
    _serial_8 = integer(12308, signed=False)
    _serial_9 = integer(12309, signed=False)

    type_code_1 = integer(10520, signed=False)
    type_code_2 = integer(10521, signed=False)
    type_code_3 = integer(10522, signed=False)

    @property
    def serial_number(self) -> str | None:
        """The production number: one ASCII character per register."""
        codes = [getattr(self, f"_serial_{i}") for i in range(SERIAL_LENGTH)]
        text = "".join(chr(code) for code in codes if code and 32 <= code < 127)
        return text or None


class Firmware(Component):
    """The version of the control software."""

    register_space = "input"

    major = integer(20, signed=False)
    minor = integer(21, signed=False)
    patch = integer(22, signed=False)

    @property
    def version(self) -> str | None:
        """The version as the unit shows it, for example ``2.03.41``."""
        if self.major is None or self.minor is None or self.patch is None:
            return None
        return f"{self.major}.{self.minor:02d}.{self.patch:02d}"
