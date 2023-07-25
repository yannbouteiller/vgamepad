import os
from vgamepad.win.vigem_commons import VIGEM_TARGET_TYPE, XUSB_BUTTON, DS4_BUTTONS, DS4_SPECIAL_BUTTONS, DS4_DPAD_DIRECTIONS

if os.name == 'nt':
    from vgamepad.win.virtual_gamepad import VX360Gamepad, VDS4Gamepad
else:
    from vgamepad.linux.virtual_gamepad import VX360Gamepad, VDS4Gamepad
