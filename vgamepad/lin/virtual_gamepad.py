"""
VGamepad API (Linux)

All API docstrings are defined in vgamepad.api
"""

from abc import ABC, abstractmethod
import libevdev
import itertools

import vgamepad.api as api


_INDEX_COUNTER = itertools.count(1)


class VGamepad(ABC):

    def __init__(self, vid=None, pid=None):
        self.device = libevdev.Device()
        self.device.name = 'Virtual Gamepad'
        self._vid = vid
        self._pid = pid
        self._index = next(_INDEX_COUNTER)
        self.uinput = None
    
    def _create_uinput_device(self):
        """
        Must be called after self.device is fully configured
        """
        if self._vid is not None:
            self.device.id = {'vendor': self._vid}
        if self._pid is not None:
            self.device.id = {'product': self._pid}
        self.uinput = self.device.create_uinput_device()

    def get_vid(self):
        return self.uinput.id['vendor']

    def get_pid(self):
        return self.uinput.id['product']

    def get_index(self):
        return self._index


class VX360Gamepad(VGamepad, api.VX360Gamepad):
    """
    Virtual Xbox360 gamepad
    """

    def __init__(self, vid=None, pid=None):
        VGamepad.__init__(self, vid, pid)

        self.device.name = 'Microsoft X-Box 360 pad'

        # Spoof input_id so SDL2 generates the known GUID (030000005e0400008e02000014010000)
        # and uses SDL_GameControllerDB instead of heuristic button ordering.
        # This fixes BTN_MODE messing up button indices.
        self.device.id = {
            'bustype': 0x0003,  # BUS_USB
            'vendor': 0x045E,   # Microsoft
            'product': 0x028E,  # Xbox 360 Controller
            'version': 0x0114,
        }

        self.XUSB_BUTTON_TO_EV_KEY = {
            api.XUSB_BUTTON.XUSB_GAMEPAD_START: libevdev.EV_KEY.BTN_START,
            api.XUSB_BUTTON.XUSB_GAMEPAD_BACK: libevdev.EV_KEY.BTN_SELECT,
            api.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB: libevdev.EV_KEY.BTN_THUMBL,
            api.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB: libevdev.EV_KEY.BTN_THUMBR,
            api.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER: libevdev.EV_KEY.BTN_TL,
            api.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER: libevdev.EV_KEY.BTN_TR,
            api.XUSB_BUTTON.XUSB_GAMEPAD_GUIDE: libevdev.EV_KEY.BTN_MODE,
            api.XUSB_BUTTON.XUSB_GAMEPAD_A: libevdev.EV_KEY.BTN_SOUTH,
            api.XUSB_BUTTON.XUSB_GAMEPAD_B: libevdev.EV_KEY.BTN_EAST,
            api.XUSB_BUTTON.XUSB_GAMEPAD_X: libevdev.EV_KEY.BTN_NORTH,
            api.XUSB_BUTTON.XUSB_GAMEPAD_Y: libevdev.EV_KEY.BTN_WEST,
        }

        for key in self.XUSB_BUTTON_TO_EV_KEY.values():
            self.device.enable(key)

        # Enable joysticks
        axis_config = libevdev.InputAbsInfo(minimum=-32768, maximum=32767, fuzz=16, flat=128)
        for axis in (libevdev.EV_ABS.ABS_X, libevdev.EV_ABS.ABS_Y, libevdev.EV_ABS.ABS_RX, libevdev.EV_ABS.ABS_RY):
            self.device.enable(axis, axis_config)

        # Enable triggers
        self.device.enable(libevdev.EV_ABS.ABS_Z, libevdev.InputAbsInfo(minimum=0, maximum=255))
        self.device.enable(libevdev.EV_ABS.ABS_RZ, libevdev.InputAbsInfo(minimum=0, maximum=255))

        # Enable D-Pad
        self.device.enable(libevdev.EV_ABS.ABS_HAT0X, libevdev.InputAbsInfo(minimum=-1, maximum=1))
        self.device.enable(libevdev.EV_ABS.ABS_HAT0Y, libevdev.InputAbsInfo(minimum=-1, maximum=1))

        self._create_uinput_device()
        api.VX360Gamepad.__init__(self)
    
    def get_type(self):
        return api.VIGEM_TARGET_TYPE.Xbox360Wired

    def update_from_report(self, report):
        buttons = report.wButtons
        events = [libevdev.InputEvent(key, value=(int(bool(buttons & btn)))) for btn, key in self.XUSB_BUTTON_TO_EV_KEY.items()]
        events += [
            libevdev.InputEvent(libevdev.EV_ABS.ABS_X, value=report.sThumbLX),
            libevdev.InputEvent(libevdev.EV_ABS.ABS_Y, value=~report.sThumbLY),  # inverted in Linux xpad driver
            libevdev.InputEvent(libevdev.EV_ABS.ABS_RX, value=report.sThumbRX),
            libevdev.InputEvent(libevdev.EV_ABS.ABS_RY, value=~report.sThumbRY),  # inverted in Linux xpad driver
            libevdev.InputEvent(libevdev.EV_ABS.ABS_Z, value=report.bLeftTrigger),
            libevdev.InputEvent(libevdev.EV_ABS.ABS_RZ, value=report.bRightTrigger),
            libevdev.InputEvent(
                libevdev.EV_ABS.ABS_HAT0X,
                value=bool(buttons & api.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT) - bool(buttons & api.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT)),
            libevdev.InputEvent(
                libevdev.EV_ABS.ABS_HAT0Y,
                value=bool(buttons & api.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN) - bool(buttons & api.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP)),
            libevdev.InputEvent(libevdev.EV_SYN.SYN_REPORT, value=0),
        ]
        self.uinput.send_events([libevdev.InputEvent(libevdev.EV_SYN.SYN_REPORT, value=0)])
    
    def register_notification(self, callback):
        raise NotImplementedError
    
    def unregister_notification(self):
        raise NotImplementedError


class VDS4Gamepad(VGamepad):
    """
    Virtual DualShock 4 gamepad
    """

    def __init__(self, vid=None, pid=None):
        VGamepad.__init__(self, vid, pid)

        # Spoof input_id so SDL2 recognizes DS4 via SDL_GameControllerDB
        self.device.id = {
            'bustype': 0x0003,  # BUS_USB
            'vendor': 0x054C,   # Sony
            'product': 0x09CC,  # DualShock 4 v2
            'version': 0x0100,
        }

        self.dpad_direction = api.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NONE

        self.dpad_mapping = {
            api.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NONE: (0, 0),
            api.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_EAST: (1, 0),
            api.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_SOUTHEAST: (1, 1),
            api.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_SOUTH: (0, 1),
            api.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_SOUTHWEST: (-1, 1),
            api.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_WEST: (-1, 0),
            api.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NORTHWEST: (-1, -1),
            api.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NORTH: (0, -1),
            api.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NORTHEAST: (1, -1)
        }

        self.DS4_BUTTON_TO_EV_KEY = {
            api.DS4_BUTTONS.DS4_BUTTON_THUMB_RIGHT: libevdev.EV_KEY.BTN_THUMBR,
            api.DS4_BUTTONS.DS4_BUTTON_THUMB_LEFT: libevdev.EV_KEY.BTN_THUMBL,
            api.DS4_BUTTONS.DS4_BUTTON_OPTIONS: libevdev.EV_KEY.BTN_START,
            api.DS4_BUTTONS.DS4_BUTTON_SHARE: libevdev.EV_KEY.BTN_SELECT,
            api.DS4_BUTTONS.DS4_BUTTON_TRIGGER_RIGHT: libevdev.EV_KEY.BTN_TR2,
            api.DS4_BUTTONS.DS4_BUTTON_TRIGGER_LEFT: libevdev.EV_KEY.BTN_TL2,
            api.DS4_BUTTONS.DS4_BUTTON_SHOULDER_RIGHT: libevdev.EV_KEY.BTN_TR,
            api.DS4_BUTTONS.DS4_BUTTON_SHOULDER_LEFT: libevdev.EV_KEY.BTN_TL,
            api.DS4_BUTTONS.DS4_BUTTON_TRIANGLE: libevdev.EV_KEY.BTN_NORTH,
            api.DS4_BUTTONS.DS4_BUTTON_CIRCLE: libevdev.EV_KEY.BTN_EAST,
            api.DS4_BUTTONS.DS4_BUTTON_CROSS: libevdev.EV_KEY.BTN_SOUTH,
            api.DS4_BUTTONS.DS4_BUTTON_SQUARE: libevdev.EV_KEY.BTN_WEST,
        }

        self.DS4_SPECIAL_BUTTON_TO_EV_KEY = {
            api.DS4_SPECIAL_BUTTONS.DS4_SPECIAL_BUTTON_PS: libevdev.EV_KEY.BTN_MODE,
            api.DS4_SPECIAL_BUTTONS.DS4_SPECIAL_BUTTON_TOUCHPAD: libevdev.EV_KEY.BTN_TOUCH,
        }

        # Note: physical DS4 controllers create 3 evdev files on Linux:
        # 1: Sony Interactive Entertainment Wireless Controller
        # 2: Sony Interactive Entertainment Wireless Controller Motion Sensors
        # 3: Sony Interactive Entertainment Wireless Controller Touchpad
        # TODO: emulate the motion sensors and touchpad on Linux

        self.device.name = 'Sony Interactive Entertainment Wireless Controller'  # 'PS4 Controller'

        # Enable buttons
        self.device.enable(libevdev.EV_KEY.BTN_SOUTH)
        self.device.enable(libevdev.EV_KEY.BTN_EAST)
        self.device.enable(libevdev.EV_KEY.BTN_NORTH)
        self.device.enable(libevdev.EV_KEY.BTN_WEST)
        self.device.enable(libevdev.EV_KEY.BTN_TL)
        self.device.enable(libevdev.EV_KEY.BTN_TR)
        self.device.enable(libevdev.EV_KEY.BTN_TL2)
        self.device.enable(libevdev.EV_KEY.BTN_TR2)
        self.device.enable(libevdev.EV_KEY.BTN_SELECT)
        self.device.enable(libevdev.EV_KEY.BTN_START)
        self.device.enable(libevdev.EV_KEY.BTN_MODE)
        self.device.enable(libevdev.EV_KEY.BTN_THUMBL)
        self.device.enable(libevdev.EV_KEY.BTN_THUMBR)
        self.device.enable(libevdev.EV_KEY.BTN_TOUCH)

        # Enable axes
        self.device.enable(libevdev.EV_ABS.ABS_X, libevdev.InputAbsInfo(minimum=0, maximum=255, value=128))
        self.device.enable(libevdev.EV_ABS.ABS_Y, libevdev.InputAbsInfo(minimum=0, maximum=255, value=128))
        self.device.enable(libevdev.EV_ABS.ABS_RX, libevdev.InputAbsInfo(minimum=0, maximum=255, value=128))
        self.device.enable(libevdev.EV_ABS.ABS_RY, libevdev.InputAbsInfo(minimum=0, maximum=255, value=128))
        self.device.enable(libevdev.EV_ABS.ABS_HAT0X, libevdev.InputAbsInfo(minimum=-1, maximum=1, value=0))
        self.device.enable(libevdev.EV_ABS.ABS_HAT0Y, libevdev.InputAbsInfo(minimum=-1, maximum=1, value=0))

        # Enable triggers
        self.device.enable(libevdev.EV_ABS.ABS_Z, libevdev.InputAbsInfo(minimum=0, maximum=255))
        self.device.enable(libevdev.EV_ABS.ABS_RZ, libevdev.InputAbsInfo(minimum=0, maximum=255))

        self.uinput = self.device.create_uinput_device()

        self.report = self.get_default_report()
        self.update()

    def get_default_report(self):
        rep = api.DS4_REPORT(
            bThumbLX=0,
            bThumbLY=0,
            bThumbRX=0,
            bThumbRY=0,
            wButtons=0,
            bSpecial=0,
            bTriggerL=0,
            bTriggerR=0)
        api.DS4_REPORT_INIT(rep)
        return rep

    def reset(self):
        """
        Resets the report to the default state
        """
        self.report = self.get_default_report()
        self.dpad_direction = api.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NONE

    def press_button(self, button):
        """
        Presses a button (no effect if already pressed)
        All possible buttons are in DS4_BUTTONS

        :param: a DS4_BUTTONS field, e.g. DS4_BUTTONS.DS4_BUTTON_TRIANGLE
        """
        self.report.wButtons = self.report.wButtons | button

    def release_button(self, button):
        """
        Releases a button (no effect if already released)
        All possible buttons are in DS4_BUTTONS

        :param: a DS4_BUTTONS field, e.g. DS4_BUTTONS.DS4_BUTTON_TRIANGLE
        """
        self.report.wButtons = self.report.wButtons & ~button

    def press_special_button(self, special_button):
        """
        Presses a special button (no effect if already pressed)
        All possible buttons are in DS4_SPECIAL_BUTTONS

        :param: a DS4_SPECIAL_BUTTONS field, e.g. DS4_SPECIAL_BUTTONS.DS4_SPECIAL_BUTTON_TOUCHPAD
        """
        self.report.bSpecial = self.report.bSpecial | special_button

    def release_special_button(self, special_button):
        """
        Releases a special button (no effect if already released)
        All possible buttons are in DS4_SPECIAL_BUTTONS

        :param: a DS4_SPECIAL_BUTTONS field, e.g. DS4_SPECIAL_BUTTONS.DS4_SPECIAL_BUTTON_TOUCHPAD
        """
        self.report.bSpecial = self.report.bSpecial & ~special_button

    def left_trigger(self, value):
        """
        Sets the value of the left trigger

        :param: integer between 0 and 255 (0 = trigger released)
        """
        self.report.bTriggerL = value

    def right_trigger(self, value):
        """
        Sets the value of the right trigger

        :param: integer between 0 and 255 (0 = trigger released)
        """
        self.report.bTriggerR = value

    def left_trigger_float(self, value_float):
        """
        Sets the value of the left trigger

        :param: float between 0.0 and 1.0 (0.0 = trigger released)
        """
        self.left_trigger(round(value_float * 255))

    def right_trigger_float(self, value_float):
        """
        Sets the value of the right trigger

        :param: float between 0.0 and 1.0 (0.0 = trigger released)
        """
        self.right_trigger(round(value_float * 255))

    def left_joystick(self, x_value, y_value):
        """
        Sets the values of the X and Y axis for the left joystick

        :param: integer between 0 and 255 (128 = neutral position)
        """
        self.report.bThumbLX = x_value
        self.report.bThumbLY = y_value

    def right_joystick(self, x_value, y_value):
        """
        Sets the values of the X and Y axis for the right joystick

        :param: integer between 0 and 255 (128 = neutral position)
        """
        self.report.bThumbRX = x_value
        self.report.bThumbRY = y_value

    def left_joystick_float(self, x_value_float, y_value_float):
        """
        Sets the values of the X and Y axis for the left joystick

        :param: float between -1.0 and 1.0 (0 = neutral position)
        """
        self.left_joystick(128 + round(x_value_float * 127),
                           128 + round(y_value_float * 127))

    def right_joystick_float(self, x_value_float, y_value_float):
        """
        Sets the values of the X and Y axis for the right joystick

        :param: float between -1.0 and 1.0 (0 = neutral position)
        """
        self.right_joystick(128 + round(x_value_float * 127),
                            128 + round(y_value_float * 127))

    def directional_pad(self, direction):
        """
        Sets the direction of the directional pad (hat)
        All possible directions are in DS4_DPAD_DIRECTIONS

        :param: a DS4_DPAD_DIRECTIONS field, e.g. DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NORTHWEST
        """
        api.DS4_SET_DPAD(self.report, direction)
        self.dpad_direction = direction

    def update(self):
        """
        Sends the current report (i.e. commands) to the virtual device
        """
        for btn, key in self.DS4_BUTTON_TO_EV_KEY.items():
            self.uinput.send_events([
                libevdev.InputEvent(key, value=(int(bool(self.report.wButtons & btn)))),
            ])

        for btn, key in self.DS4_SPECIAL_BUTTON_TO_EV_KEY.items():
            self.uinput.send_events([
                libevdev.InputEvent(key, value=(int(bool(self.report.bSpecial & btn)))),
            ])

        # Update axes
        self.uinput.send_events([
            # Left joystick
            libevdev.InputEvent(libevdev.EV_ABS.ABS_X, value=self.report.bThumbLX),
            libevdev.InputEvent(libevdev.EV_ABS.ABS_Y, value=self.report.bThumbLY),
            # Right joystick
            libevdev.InputEvent(libevdev.EV_ABS.ABS_RX, value=self.report.bThumbRX),
            libevdev.InputEvent(libevdev.EV_ABS.ABS_RY, value=self.report.bThumbRY),
            # Triggers
            libevdev.InputEvent(libevdev.EV_ABS.ABS_Z, value=self.report.bTriggerL),
            libevdev.InputEvent(libevdev.EV_ABS.ABS_RZ, value=self.report.bTriggerR)
        ])

        hat0x_value, hat0y_value = self.dpad_mapping[self.dpad_direction]

        self.uinput.send_events([
            libevdev.InputEvent(libevdev.EV_ABS.ABS_HAT0X, value=hat0x_value),
            libevdev.InputEvent(libevdev.EV_ABS.ABS_HAT0Y, value=hat0y_value)
        ])

        self.uinput.send_events([libevdev.InputEvent(libevdev.EV_SYN.SYN_REPORT, value=0)])
