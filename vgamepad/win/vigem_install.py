"""ViGEmBus driver installation (Windows).

``pip install`` from PyPI usually installs a wheel; wheels do not execute ``setup.py`` on the
end user's machine. Driver installation must therefore run when the package is first imported
on Windows (and may still run from ``setup.py`` during editable/sdist installs).
"""

from __future__ import annotations

import os
import platform
import subprocess
import sys
import warnings
from pathlib import Path

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
        f"defaulting to {arch}. If this is wrong, cancel the upcoming "
        f"ViGEmBus installation and install it manually from "
        f"https://github.com/ViGEm/ViGEmBus/releases/tag/setup-v{VIGEMBUS_VERSION}",
        stacklevel=2,
    )
    return arch


def _msi_path(arch: str) -> Path:
    return Path(__file__).resolve().parent / "vigem" / "install" / arch / f"ViGEmBusSetup_{arch}.msi"


def ensure_vigembus_installed(*, _build_hook: bool = False) -> None:
    """Detect ViGEmBus and run the bundled MSI if it is missing (Windows only)."""
    if not _is_windows:
        return
    if os.environ.get("VGAMEPAD_SKIP_VIGEMBUS_INSTALL", "").lower() == "true":
        return
    if _build_hook and len(sys.argv) > 1 and sys.argv[1] in {"egg_info", "sdist"}:
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
    msi = _msi_path(arch)
    if not msi.is_file():
        warnings.warn(
            f"ViGEmBus installer not found at {msi}. "
            "Install ViGEmBus manually from "
            f"https://github.com/ViGEm/ViGEmBus/releases/tag/setup-v{VIGEMBUS_VERSION}",
            stacklevel=2,
        )
        return

    subprocess.call(["msiexec", "/i", str(msi)], shell=True)
