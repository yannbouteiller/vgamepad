import platform
from vgamepad.api import VIGEM_TARGET_TYPE, XUSB_BUTTON, DS4_BUTTONS, DS4_SPECIAL_BUTTONS, DS4_DPAD_DIRECTIONS, DS4_LIGHTBAR_COLOR

if platform.system() == 'Windows':
    from vgamepad.win.virtual_gamepad import VX360Gamepad, VDS4Gamepad
else:  # Linux
    from vgamepad.lin.virtual_gamepad import VX360Gamepad, VDS4Gamepad
