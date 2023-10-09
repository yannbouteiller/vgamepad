"""
VGamepad API (Linux)
"""
from abc import ABC, abstractmethod
from time import sleep

import libevdev
import vgamepad.win.vigem_commons as vcom


class VGamepad(ABC):

    def __init__(self):
        self.device = libevdev.Device()
        self.device.name = 'Virtual Gamepad'

    def get_vid(self):
        """
        :return: the vendor ID of the virtual device
        """
        return self.device.id.vendor

    def get_pid(self):
        """
        :return: the product ID of the virtual device
        """
        return self.device.id.product

    def set_vid(self, vid):
        """
        :param: the new vendor ID of the virtual device
        """
        self.device.id = {'vendor': vid}  # setter only uses set keys

    def set_pid(self, pid):
        """
        :param: the new product ID of the virtual device
        """
        self.device.id = {'product': pid}  # setter only uses set keys

    def get_index(self):
        """
        :return: the internally used index of the target device
        """
        return 0

    def get_type(self):
        """
        :return: the type of the object (e.g. Xbox360Wired)
        """
        return self.device.id.bustype

    @abstractmethod
    def target_alloc(self):
        """
        :return: the pointer to an allocated evdev device (e.g. create_uinput_device())
        """
        pass


class VX360Gamepad(VGamepad):
    """
    Virtual Xbox360 gamepad
    """

    def __init__(self):
        super().__init__()
        self.device.name = 'Xbox 360 Controller'

        # Enable buttons
        self.device.enable(libevdev.EV_KEY.BTN_SOUTH)
        self.device.enable(libevdev.EV_KEY.BTN_EAST)
        self.device.enable(libevdev.EV_KEY.BTN_NORTH)
        self.device.enable(libevdev.EV_KEY.BTN_WEST)

        self.device.enable(libevdev.EV_KEY.BTN_TL)
        self.device.enable(libevdev.EV_KEY.BTN_TR)

        self.device.enable(libevdev.EV_KEY.BTN_SELECT)
        self.device.enable(libevdev.EV_KEY.BTN_START)

        # self.device.enable(libevdev.EV_KEY.BTN_MODE)  # FIXME: On Linux, this messes up the button order

        self.device.enable(libevdev.EV_KEY.BTN_THUMBL)
        self.device.enable(libevdev.EV_KEY.BTN_THUMBR)

        # Enable joysticks
        self.device.enable(
            libevdev.EV_ABS.ABS_X,
            libevdev.InputAbsInfo(minimum=-32768,
                                  maximum=32767,
                                  fuzz=16,
                                  flat=128))
        self.device.enable(
            libevdev.EV_ABS.ABS_Y,
            libevdev.InputAbsInfo(minimum=-32768,
                                  maximum=32767,
                                  fuzz=16,
                                  flat=128))
        self.device.enable(
            libevdev.EV_ABS.ABS_RX,
            libevdev.InputAbsInfo(minimum=-32768,
                                  maximum=32767,
                                  fuzz=16,
                                  flat=128))
        self.device.enable(
            libevdev.EV_ABS.ABS_RY,
            libevdev.InputAbsInfo(minimum=-32768,
                                  maximum=32767,
                                  fuzz=16,
                                  flat=128))
        # Enable triggers
        self.device.enable(libevdev.EV_ABS.ABS_Z, libevdev.InputAbsInfo(minimum=0, maximum=1023))
        self.device.enable(libevdev.EV_ABS.ABS_RZ, libevdev.InputAbsInfo(minimum=0, maximum=1023))

        # Enable D-Pad
        self.device.enable(libevdev.EV_ABS.ABS_HAT0X, libevdev.InputAbsInfo(minimum=-1, maximum=1))
        self.device.enable(libevdev.EV_ABS.ABS_HAT0Y, libevdev.InputAbsInfo(minimum=-1, maximum=1))

        self.uinput = self.device.create_uinput_device()

        self.report = self.get_default_report()
        self.update()

    XUSB_BUTTON_TO_EV_KEY = {
        vcom.XUSB_BUTTON.XUSB_GAMEPAD_START: libevdev.EV_KEY.BTN_START,
        vcom.XUSB_BUTTON.XUSB_GAMEPAD_BACK: libevdev.EV_KEY.BTN_SELECT,
        vcom.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB: libevdev.EV_KEY.BTN_THUMBL,
        vcom.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB: libevdev.EV_KEY.BTN_THUMBR,
        vcom.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER: libevdev.EV_KEY.BTN_TL,
        vcom.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER: libevdev.EV_KEY.BTN_TR,
        # vcom.XUSB_BUTTON.XUSB_GAMEPAD_GUIDE: libevdev.EV_KEY.BTN_MODE,  # FIXME: does not work properly on Linux
        vcom.XUSB_BUTTON.XUSB_GAMEPAD_A: libevdev.EV_KEY.BTN_SOUTH,
        vcom.XUSB_BUTTON.XUSB_GAMEPAD_B: libevdev.EV_KEY.BTN_EAST,
        vcom.XUSB_BUTTON.XUSB_GAMEPAD_X: libevdev.EV_KEY.BTN_NORTH,
        vcom.XUSB_BUTTON.XUSB_GAMEPAD_Y: libevdev.EV_KEY.BTN_WEST,
    }

    def get_default_report(self):
        return vcom.XUSB_REPORT(wButtons=0,
                                bLeftTrigger=0,
                                bRightTrigger=0,
                                sThumbLX=0,
                                sThumbLY=0,
                                sThumbRX=0,
                                sThumbRY=0)

    def reset(self):
        """
        Resets the report to the default state
        """
        self.report = self.get_default_report()

    def press_button(self, button):
        """
        Presses a button (no effect if already pressed)
        All possible buttons are in XUSB_BUTTON
        Note: The GUIDE button is not available on Linux

        :param: a XUSB_BUTTON field, e.g. XUSB_BUTTON.XUSB_GAMEPAD_X
        """
        self.report.wButtons = self.report.wButtons | button

    def release_button(self, button):
        """
        Releases a button (no effect if already released)
        All possible buttons are in XUSB_BUTTON

        :param: a XUSB_BUTTON field, e.g. XUSB_BUTTON.XUSB_GAMEPAD_X
        """
        self.report.wButtons = self.report.wButtons & ~button

    def left_trigger(self, value):
        """
        Sets the value of the left trigger

        :param: integer between 0 and 255 (0 = trigger released)
        """
        self.report.bLeftTrigger = value

    def right_trigger(self, value):
        """
        Sets the value of the right trigger

        :param: integer between 0 and 255 (0 = trigger released)
        """
        self.report.bRightTrigger = value

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

        :param: integer between -32768 and 32767 (0 = neutral position)
        """
        self.report.sThumbLX = x_value
        self.report.sThumbLY = y_value

    def right_joystick(self, x_value, y_value):
        """
        Sets the values of the X and Y axis for the right joystick

        :param: integer between -32768 and 32767 (0 = neutral position)
        """
        self.report.sThumbRX = x_value
        self.report.sThumbRY = y_value

    def left_joystick_float(self, x_value_float, y_value_float):
        """
        Sets the values of the X and Y axis for the left joystick

        :param: float between -1.0 and 1.0 (0 = neutral position)
        """
        self.left_joystick(round(x_value_float * 32767),
                           round(y_value_float * 32767))

    def right_joystick_float(self, x_value_float, y_value_float):
        """
        Sets the values of the X and Y axis for the right joystick

        :param: float between -1.0 and 1.0 (0 = neutral position)
        """
        self.right_joystick(round(x_value_float * 32767),
                            round(y_value_float * 32767))

    def update(self):
        """
        Sends the current report (i.e. commands) to the virtual device
        """
        # Update buttons
        for btn, key in self.XUSB_BUTTON_TO_EV_KEY.items():
            self.uinput.send_events([
                libevdev.InputEvent(key, value=(int(bool(self.report.wButtons & btn)))),
            ])

        # Update axes
        self.uinput.send_events([
            # Left joystick
            libevdev.InputEvent(libevdev.EV_ABS.ABS_X, value=self.report.sThumbLX),
            libevdev.InputEvent(libevdev.EV_ABS.ABS_Y, value=self.report.sThumbLY),
            # Right joystick
            libevdev.InputEvent(libevdev.EV_ABS.ABS_RX, value=self.report.sThumbRX),
            libevdev.InputEvent(libevdev.EV_ABS.ABS_RY, value=self.report.sThumbRY),
            # Triggers
            libevdev.InputEvent(libevdev.EV_ABS.ABS_Z, value=self.report.bLeftTrigger * 4),
            libevdev.InputEvent(libevdev.EV_ABS.ABS_RZ, value=self.report.bRightTrigger * 4)
        ])

        hat0x_value = bool(self.report.wButtons
                           & vcom.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT) - bool(
                               self.report.wButtons
                               & vcom.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT)
        hat0y_value = bool(self.report.wButtons
                           & vcom.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN) - bool(
                               self.report.wButtons
                               & vcom.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP)
        self.uinput.send_events([
            libevdev.InputEvent(libevdev.EV_ABS.ABS_HAT0X, value=hat0x_value),
            libevdev.InputEvent(libevdev.EV_ABS.ABS_HAT0Y, value=hat0y_value)
        ])

        self.uinput.send_events([libevdev.InputEvent(libevdev.EV_SYN.SYN_REPORT, value=0)])

    def target_alloc(self):
        return self.uinput


class VDS4Gamepad(VGamepad):
    """
    Virtual DuslaShock 4 gamepad
    """

    def __init__(self):
        super().__init__()

        self.dpad_direction = vcom.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NONE

        self.dpad_mapping = {
            vcom.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NONE: (0, 0),
            vcom.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_EAST: (1, 0),
            vcom.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_SOUTHEAST: (1, 1),
            vcom.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_SOUTH: (0, 1),
            vcom.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_SOUTHWEST: (-1, 1),
            vcom.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_WEST: (-1, 0),
            vcom.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NORTHWEST: (-1, -1),
            vcom.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NORTH: (0, -1),
            vcom.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NORTHEAST: (1, -1)
        }

        self.DS4_BUTTON_TO_EV_KEY = {
            vcom.DS4_BUTTONS.DS4_BUTTON_THUMB_RIGHT: libevdev.EV_KEY.BTN_THUMBR,
            vcom.DS4_BUTTONS.DS4_BUTTON_THUMB_LEFT: libevdev.EV_KEY.BTN_THUMBL,
            vcom.DS4_BUTTONS.DS4_BUTTON_OPTIONS: libevdev.EV_KEY.BTN_SELECT,
            vcom.DS4_BUTTONS.DS4_BUTTON_SHARE: libevdev.EV_KEY.BTN_START,
            vcom.DS4_BUTTONS.DS4_BUTTON_SHOULDER_RIGHT: libevdev.EV_KEY.BTN_TR,
            vcom.DS4_BUTTONS.DS4_BUTTON_SHOULDER_LEFT: libevdev.EV_KEY.BTN_TL,
            vcom.DS4_BUTTONS.DS4_BUTTON_TRIANGLE: libevdev.EV_KEY.BTN_NORTH,
            vcom.DS4_BUTTONS.DS4_BUTTON_CIRCLE: libevdev.EV_KEY.BTN_EAST,
            vcom.DS4_BUTTONS.DS4_BUTTON_CROSS: libevdev.EV_KEY.BTN_SOUTH,
            vcom.DS4_BUTTONS.DS4_BUTTON_SQUARE: libevdev.EV_KEY.BTN_WEST,
        }

        self.DS4_SPECIAL_BUTTON_TO_EV_KEY = {
            vcom.DS4_SPECIAL_BUTTONS.DS4_SPECIAL_BUTTON_PS: libevdev.EV_KEY.BTN_MODE,
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

        # Enable axes
        self.device.enable(libevdev.EV_ABS.ABS_X, libevdev.InputAbsInfo(minimum=0, maximum=255, value=127))
        self.device.enable(libevdev.EV_ABS.ABS_Y, libevdev.InputAbsInfo(minimum=0, maximum=255, value=127))
        self.device.enable(libevdev.EV_ABS.ABS_RX, libevdev.InputAbsInfo(minimum=0, maximum=255, value=127))
        self.device.enable(libevdev.EV_ABS.ABS_RY, libevdev.InputAbsInfo(minimum=0, maximum=255, value=127))
        self.device.enable(libevdev.EV_ABS.ABS_HAT0X, libevdev.InputAbsInfo(minimum=-1, maximum=1, value=0))
        self.device.enable(libevdev.EV_ABS.ABS_HAT0Y, libevdev.InputAbsInfo(minimum=-1, maximum=1, value=0))

        # Enable triggers
        self.device.enable(libevdev.EV_ABS.ABS_Z, libevdev.InputAbsInfo(minimum=0, maximum=255))
        self.device.enable(libevdev.EV_ABS.ABS_RZ, libevdev.InputAbsInfo(minimum=0, maximum=255))

        self.uinput = self.device.create_uinput_device()

        self.report = self.get_default_report()
        self.update()

    def get_default_report(self):
        rep = vcom.DS4_REPORT(
            bThumbLX=0,
            bThumbLY=0,
            bThumbRX=0,
            bThumbRY=0,
            wButtons=0,
            bSpecial=0,
            bTriggerL=0,
            bTriggerR=0)
        vcom.DS4_REPORT_INIT(rep)
        return rep

    def reset(self):
        """
        Resets the report to the default state
        """
        self.report = self.get_default_report()

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
        vcom.DS4_SET_DPAD(self.report, direction)
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

    def target_alloc(self):
        return self.uinput
