"""Copy the atrea-modbus library into the integration.

A custom integration may carry its device library inside itself. Until
atrea-modbus is on PyPI, this keeps the integration installable from HACS.
Run: python script/vendor.py [path to the atrea-modbus repository]
"""

from __future__ import annotations

from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).parent.parent
SOURCE = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT.parent / "atrea-modbus"
TARGET = ROOT / "custom_components" / "atrea" / "vendor"

package = SOURCE / "src" / "atrea_modbus"
if not package.is_dir():
    raise SystemExit(f"{package} is not the atrea_modbus package")

if TARGET.exists():
    shutil.rmtree(TARGET)
shutil.copytree(
    package, TARGET / "atrea_modbus", ignore=shutil.ignore_patterns("__pycache__")
)
(TARGET / "__init__.py").write_text(
    '"""Libraries carried inside the integration. Do not edit: see script/vendor.py."""\n',
    encoding="utf-8",
    newline="\n",
)
print(f"Copied {package} to {TARGET / 'atrea_modbus'}")
