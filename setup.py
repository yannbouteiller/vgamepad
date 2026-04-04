"""
Windows-only post-install hook: detect and install the ViGEmBus driver.

All project metadata lives in pyproject.toml.  This file is only needed
because the ViGEmBus MSI must be run as a side-effect of `pip install`.
On Linux this file is a no-op.
"""

from __future__ import annotations

import os
import platform
import subprocess
import sys
import warnings
from pathlib import Path

from setuptools import setup

VIGEMBUS_VERSION = "1.17.333.0"

_is_windows = platform.system() == "Windows"


def _detect_arch() -> str:
    machine = platform.machine()
    if machine.endswith("64"):
        return "x64"
    if machine.endswith("86"):
        return "x86"
    arch = "x64" if platform.architecture()[0] == "64bit" else "x86"
    warnings.warn(
        f"Could not determine system architecture from '{machine}'; "
        f"defaulting to {arch}.  If this is wrong, cancel the upcoming "
        f"ViGEmBus installation and install it manually from "
        f"https://github.com/ViGEm/ViGEmBus/releases/tag/setup-v{VIGEMBUS_VERSION}",
        stacklevel=2,
    )
    return arch


def _install_vigembus() -> None:
    if not _is_windows:
        return
    if os.environ.get("VGAMEPAD_SKIP_VIGEMBUS_INSTALL", "").lower() == "true":
        return
    if len(sys.argv) > 1 and sys.argv[1] in {"egg_info", "sdist"}:
        return

    try:
        reg_output = subprocess.check_output(
            ["reg", "query", r"HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall", "/s"],
            text=True,
        ).lower()
        marker = "nefarius virtual gamepad emulation bus driver"
        idx = reg_output.find(marker)
        if idx > 0:
            ver_idx = reg_output[:idx].rfind("displayversion")
            if ver_idx != -1:
                found_ver = reg_output[ver_idx:idx].split()[2]
                if found_ver != VIGEMBUS_VERSION:
                    warnings.warn(
                        f"Found ViGEmBus {found_ver}; expected {VIGEMBUS_VERSION}.",
                        stacklevel=2,
                    )
            return  # already installed
    except Exception as exc:
        warnings.warn(f"ViGEmBus detection failed: {exc}", stacklevel=2)

    arch = _detect_arch()
    msi = Path(__file__).parent / "vgamepad" / "win" / "vigem" / "install" / arch / f"ViGEmBusSetup_{arch}.msi"
    subprocess.call(["msiexec", "/i", str(msi)], shell=True)


_install_vigembus()

setup()
