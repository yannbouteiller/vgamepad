"""
Windows-only post-install hook: detect and install the ViGEmBus driver.

All project metadata lives in pyproject.toml. This file is only needed
because the ViGEmBus MSI must be run as a side-effect of source installs
(``pip install .`` / ``pip install -e .``). Wheel installs
from PyPI trigger the same logic on first ``import vgamepad``; see
``vgamepad.win.vigem_install``.

``setup.py`` loads ``vigem_install.py`` via importlib so importing the
``vgamepad`` package (and running import-time hooks twice) is avoided.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

from setuptools import setup

_root = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location(
    "_vgamepad_vigem_install",
    _root / "vgamepad" / "win" / "vigem_install.py",
)
if _spec is None or _spec.loader is None:
    raise RuntimeError("Could not load vgamepad/win/vigem_install.py")
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
_mod.ensure_vigembus_installed(_build_hook=True)

setup()
