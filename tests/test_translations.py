"""The translation files match script/i18n and cover every English text."""

from __future__ import annotations

from pathlib import Path
import runpy
import sys
from unittest.mock import patch

SCRIPT = Path(__file__).parent.parent / "script" / "gen_translations.py"


def test_translations_are_complete_and_up_to_date() -> None:
    generator = runpy.run_path(str(SCRIPT))
    with patch.object(sys, "argv", ["gen_translations.py", "--check"]):
        assert generator["main"]() == 0
