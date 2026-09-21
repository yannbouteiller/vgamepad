import platform
from vgamepad.win.vigem_commons import VIGEM_TARGET_TYPE, XUSB_BUTTON, DS4_BUTTONS, DS4_SPECIAL_BUTTONS, DS4_DPAD_DIRECTIONS

if platform.system() == 'Windows':
    from vgamepad.win.virtual_gamepad import VX360Gamepad, VDS4Gamepad
else:  # Linux
    from vgamepad.lin.virtual_gamepad import VX360Gamepad, VDS4Gamepad
