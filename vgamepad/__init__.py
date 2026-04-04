"""vgamepad - Virtual Xbox 360 and DualShock 4 gamepads in Python."""

from __future__ import annotations

import platform

from loguru import logger

from vgamepad.win.vigem_commons import (
    DS4_BUTTONS,
    DS4_DPAD_DIRECTIONS,
    DS4_REPORT,
    DS4_REPORT_EX,
    DS4_REPORT_INIT,
    DS4_SET_DPAD,
    DS4_SPECIAL_BUTTONS,
    VIGEM_TARGET_TYPE,
    XUSB_BUTTON,
    XUSB_REPORT,
)

__version__ = "0.1.3"

logger.disable("vgamepad")

if platform.system() == "Windows":
    from vgamepad.win.virtual_gamepad import VDS4Gamepad, VX360Gamepad
else:
    from vgamepad.lin.virtual_gamepad import VDS4Gamepad, VX360Gamepad

__all__ = [
    "DS4_BUTTONS",
    "DS4_DPAD_DIRECTIONS",
    "DS4_REPORT",
    "DS4_REPORT_EX",
    "DS4_REPORT_INIT",
    "DS4_SET_DPAD",
    "DS4_SPECIAL_BUTTONS",
    "VIGEM_TARGET_TYPE",
    "XUSB_BUTTON",
    "XUSB_REPORT",
    "VDS4Gamepad",
    "VX360Gamepad",
]
