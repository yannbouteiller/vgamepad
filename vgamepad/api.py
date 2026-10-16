"""
VGamepad API.

This file defines the abstract interfaces implemented in VGamepad.
"""

from abc import ABC, abstractmethod
from inspect import signature
from enum import IntFlag, IntEnum
from ctypes import Structure, Union, c_short, c_ushort, c_ubyte, sizeof

c_byte = c_ubyte  # because BYTE is actually unsigned char


# ========== VGamepad structures (adapted from ViGEmBus) ==========


class VIGEM_TARGET_TYPE(IntFlag):
    """
    Represents the desired target type for the emulated device.
    NOTE: 1 skipped on purpose to maintain compatibility
    """
    Xbox360Wired = 0  # Microsoft Xbox 360 Controller (wired)
    DualShock4Wired = 2  # Sony DualShock 4 (wired)


class XUSB_BUTTON(IntFlag):
    """
    Possible XUSB report buttons.
    """
    XUSB_GAMEPAD_DPAD_UP = 0x0001
    XUSB_GAMEPAD_DPAD_DOWN = 0x0002
    XUSB_GAMEPAD_DPAD_LEFT = 0x0004
    XUSB_GAMEPAD_DPAD_RIGHT = 0x0008
    XUSB_GAMEPAD_START = 0x0010
    XUSB_GAMEPAD_BACK = 0x0020
    XUSB_GAMEPAD_LEFT_THUMB = 0x0040
    XUSB_GAMEPAD_RIGHT_THUMB = 0x0080
    XUSB_GAMEPAD_LEFT_SHOULDER = 0x0100
    XUSB_GAMEPAD_RIGHT_SHOULDER = 0x0200
    XUSB_GAMEPAD_GUIDE = 0x0400
    XUSB_GAMEPAD_A = 0x1000
    XUSB_GAMEPAD_B = 0x2000
    XUSB_GAMEPAD_X = 0x4000
    XUSB_GAMEPAD_Y = 0x8000


class XUSB_REPORT(Structure):
    """
    Represents an XINPUT_GAMEPAD-compatible report structure.
    """
    _fields_ = [("wButtons", c_ushort),
                ("bLeftTrigger", c_byte),
                ("bRightTrigger", c_byte),
                ("sThumbLX", c_short),
                ("sThumbLY", c_short),
                ("sThumbRX", c_short),
                ("sThumbRY", c_short)]


class DS4_LIGHTBAR_COLOR(Structure):
    """
    The color value (RGB) of a DualShock 4 Lightbar
    """
    _fields_ = [("Red", c_ubyte),  # Red part of the Lightbar (0-255).
                ("Green", c_ubyte),  # Green part of the Lightbar (0-255).
                ("Blue", c_ubyte)]  # Blue part of the Lightbar (0-255).


class DS4_BUTTONS(IntFlag):
    """
    DualShock 4 digital buttons
    """
    DS4_BUTTON_THUMB_RIGHT = 1 << 15
    DS4_BUTTON_THUMB_LEFT = 1 << 14
    DS4_BUTTON_OPTIONS = 1 << 13
    DS4_BUTTON_SHARE = 1 << 12
    DS4_BUTTON_TRIGGER_RIGHT = 1 << 11
    DS4_BUTTON_TRIGGER_LEFT = 1 << 10
    DS4_BUTTON_SHOULDER_RIGHT = 1 << 9
    DS4_BUTTON_SHOULDER_LEFT = 1 << 8
    DS4_BUTTON_TRIANGLE = 1 << 7
    DS4_BUTTON_CIRCLE = 1 << 6
    DS4_BUTTON_CROSS = 1 << 5
    DS4_BUTTON_SQUARE = 1 << 4


class DS4_SPECIAL_BUTTONS(IntFlag):
    """
    DualShock 4 special buttons
    """
    DS4_SPECIAL_BUTTON_PS = 1 << 0
    DS4_SPECIAL_BUTTON_TOUCHPAD = 1 << 1


class DS4_DPAD_DIRECTIONS(IntEnum):
    """
    DualShock 4 directional pad (HAT) values
    """
    DS4_BUTTON_DPAD_NONE = 0x8
    DS4_BUTTON_DPAD_NORTHWEST = 0x7
    DS4_BUTTON_DPAD_WEST = 0x6
    DS4_BUTTON_DPAD_SOUTHWEST = 0x5
    DS4_BUTTON_DPAD_SOUTH = 0x4
    DS4_BUTTON_DPAD_SOUTHEAST = 0x3
    DS4_BUTTON_DPAD_EAST = 0x2
    DS4_BUTTON_DPAD_NORTHEAST = 0x1
    DS4_BUTTON_DPAD_NORTH = 0x0


class DS4_REPORT(Structure):
    """
    DualShock 4 HID Input report
    """
    _fields_ = [("bThumbLX", c_byte),
                ("bThumbLY", c_byte),
                ("bThumbRX", c_byte),
                ("bThumbRY", c_byte),
                ("wButtons", c_ushort),
                ("bSpecial", c_byte),
                ("bTriggerL", c_byte),
                ("bTriggerR", c_byte)]


def DS4_SET_DPAD(report, dpad):
    report.wButtons &= ~0xF
    report.wButtons |= dpad  # TODO cast USHORT?


def DS4_REPORT_INIT(report):
    report.bThumbLX = 0x80
    report.bThumbLY = 0x80
    report.bThumbRX = 0x80
    report.bThumbRY = 0x80
    DS4_SET_DPAD(report, DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NONE)


class DS4_TOUCH(Structure):
    """
    DualShock 4 HID Touchpad structure
    """
    _layout_ = "ms"
    _pack_ = 1
    _fields_ = [("bPacketCounter", c_byte),  # timestamp / packet counter associated with touch event
                ("bIsUpTrackingNum1", c_byte),  # 0 means down; active low
                # unique to each finger down, so for a lift and repress the value is incremented
                ("bTouchData1", c_byte * 3),  # Two 12 bits values (for X and Y)
                # middle byte holds last 4 bits of X and the starting
                ("bIsUpTrackingNum2", c_byte),  # second touch data immediately follows data of first
                ("bTouchData2", c_byte * 3)]  # resolution is 1920x943


class DS4_SUB_REPORT_EX(Structure):
    _layout_ = "ms"
    _pack_ = 1
    _fields_ = [("bThumbLX", c_byte),
                ("bThumbLY", c_byte),
                ("bThumbRX", c_byte),
                ("bThumbRY", c_byte),
                ("wButtons", c_ushort),
                ("bSpecial", c_byte),
                ("bTriggerL", c_byte),
                ("bTriggerR", c_byte),
                ("wTimestamp", c_ushort),
                ("bBatteryLvl", c_byte),
                ("wGyroX", c_short),
                ("wGyroY", c_short),
                ("wGyroZ", c_short),
                ("wAccelX", c_short),
                ("wAccelY", c_short),
                ("wAccelZ", c_short),
                ("_bUnknown1", c_byte * 5),
                ("bBatteryLvlSpecial", c_byte),
                # really should have a enum to show everything that this can represent (USB charging, battery level; EXT, headset, microphone connected)
                ("_bUnknown2", c_byte * 2),
                ("bTouchPacketsN", c_byte),  # 0x00 to 0x03 (USB max)
                ("sCurrentTouch", DS4_TOUCH),
                ("sPreviousTouch", DS4_TOUCH * 2)]


class DS4_REPORT_EX(Union):
    """
    DualShock 4 v1 complete HID Input report
    """
    _layout_ = "ms"
    _pack_ = 1
    _fields_ = [("Report", DS4_SUB_REPORT_EX),
                ("ReportBuffer", c_ubyte * 63)]


class VIGEM_ERRORS(IntEnum):
    """
    Values that represent ViGEm errors
    """
    VIGEM_ERROR_NONE = 0x20000000
    VIGEM_ERROR_BUS_NOT_FOUND = 0xE0000001
    VIGEM_ERROR_NO_FREE_SLOT = 0xE0000002
    VIGEM_ERROR_INVALID_TARGET = 0xE0000003
    VIGEM_ERROR_REMOVAL_FAILED = 0xE0000004
    VIGEM_ERROR_ALREADY_CONNECTED = 0xE0000005
    VIGEM_ERROR_TARGET_UNINITIALIZED = 0xE0000006
    VIGEM_ERROR_TARGET_NOT_PLUGGED_IN = 0xE0000007
    VIGEM_ERROR_BUS_VERSION_MISMATCH = 0xE0000008
    VIGEM_ERROR_BUS_ACCESS_FAILED = 0xE0000009
    VIGEM_ERROR_CALLBACK_ALREADY_REGISTERED = 0xE0000010
    VIGEM_ERROR_CALLBACK_NOT_FOUND = 0xE0000011
    VIGEM_ERROR_BUS_ALREADY_CONNECTED = 0xE0000012
    VIGEM_ERROR_BUS_INVALID_HANDLE = 0xE0000013
    VIGEM_ERROR_XUSB_USERINDEX_OUT_OF_RANGE = 0xE0000014
    VIGEM_ERROR_INVALID_PARAMETER = 0xE0000015
    VIGEM_ERROR_NOT_SUPPORTED = 0xE0000016


# Double-check that the DS4 packed structures have the correct shape:
assert sizeof(DS4_SUB_REPORT_EX) == 60
assert sizeof(DS4_REPORT_EX) == 63


# ========== VGamepad classes ==========


def dummy_x360_callback(client, target, large_motor, small_motor, led_number, user_data):
    """
    Pattern for callback functions to be registered as notifications for VX360Gamepad

    :param client: vigem bus ID
    :param target: vigem device ID
    :param large_motor: integer in [0, 255] representing the state of the large motor
    :param small_motor: integer in [0, 255] representing the state of the small motor
    :param led_number: integer in [0, 255] representing the state of the LED ring
    :param user_data: placeholder, do not use
    """
    pass


def dummy_ds4_callback(client, target, large_motor, small_motor, lightbar_color, user_data):
    """
    Pattern for callback functions to be registered as notifications for VDS4Gamepad

    :param client: vigem bus ID
    :param target: vigem device ID
    :param large_motor: integer in [0, 255] representing the state of the large motor
    :param small_motor: integer in [0, 255] representing the state of the small motor
    :param lightbar_color: DS4_LIGHTBAR_COLOR representing the state of the lightbar
    :param user_data: placeholder, do not use
    """
    pass


def check_callback_signature(callback):
    """
    Checks whether a callback is valid
    """
    try:
        signature(callback).bind(*range(6))
    except (TypeError, ValueError):
        return False
    return True


class VX360Gamepad(ABC):
    """
    Virtual XBox360 gamepad
    """

    def get_default_report(self):
        return XUSB_REPORT(
            wButtons=0,
            bLeftTrigger=0,
            bRightTrigger=0,
            sThumbLX=0,
            sThumbLY=0,
            sThumbRX=0,
            sThumbRY=0)

    @abstractmethod
    def get_vid(self):
        """
        :return: the vendor ID of the virtual device
        """
        raise NotImplementedError
    
    @abstractmethod
    def get_pid(self):
        """
        :return: the product ID of the virtual device
        """
        raise NotImplementedError

    @abstractmethod
    def get_index(self):
        """
        :return: the internally used index of the target device
        """
        raise NotImplementedError

    @abstractmethod
    def get_type(self):
        """
        :return: the type of the object (e.g. VIGEM_TARGET_TYPE.Xbox360Wired)
        """
        raise NotImplementedError
    
    @abstractmethod
    def reset(self):
        """
        Resets the report to the default state
        """
        raise NotImplementedError
    
    @abstractmethod
    def press_button(self, button):
        """
        Presses a button (no effect if already pressed)
        All possible buttons are in XUSB_BUTTON

        :param: a XUSB_BUTTON field, e.g. XUSB_BUTTON.XUSB_GAMEPAD_X
        """
        raise NotImplementedError

    @abstractmethod
    def release_button(self, button):
        """
        Releases a button (no effect if already released)
        All possible buttons are in XUSB_BUTTON

        :param: a XUSB_BUTTON field, e.g. XUSB_BUTTON.XUSB_GAMEPAD_X
        """
        raise NotImplementedError

    @abstractmethod
    def left_trigger(self, value):
        """
        Sets the value of the left trigger

        :param: integer between 0 and 255 (0 = trigger released)
        """
        raise NotImplementedError

    @abstractmethod
    def right_trigger(self, value):
        """
        Sets the value of the right trigger

        :param: integer between 0 and 255 (0 = trigger released)
        """
        raise NotImplementedError

    @abstractmethod
    def left_trigger_float(self, value_float):
        """
        Sets the value of the left trigger

        :param: float between 0.0 and 1.0 (0.0 = trigger released)
        """
        raise NotImplementedError

    @abstractmethod
    def right_trigger_float(self, value_float):
        """
        Sets the value of the right trigger

        :param: float between 0.0 and 1.0 (0.0 = trigger released)
        """
        raise NotImplementedError

    @abstractmethod
    def left_joystick(self, x_value, y_value):
        """
        Sets the values of the X and Y axis for the left joystick

        :param: integer between -32768 and 32767 (0 = neutral position)
        """
        raise NotImplementedError

    @abstractmethod
    def right_joystick(self, x_value, y_value):
        """
        Sets the values of the X and Y axis for the right joystick

        :param: integer between -32768 and 32767 (0 = neutral position)
        """
        raise NotImplementedError

    @abstractmethod
    def left_joystick_float(self, x_value_float, y_value_float):
        """
        Sets the values of the X and Y axis for the left joystick

        :param: float between -1.0 and 1.0 (0 = neutral position)
        """
        raise NotImplementedError

    @abstractmethod
    def right_joystick_float(self, x_value_float, y_value_float):
        """
        Sets the values of the X and Y axis for the right joystick

        :param: float between -1.0 and 1.0 (0 = neutral position)
        """
        raise NotImplementedError

    @abstractmethod
    def update(self):
        """
        Sends the current report (i.e. commands) to the virtual device
        """
        raise NotImplementedError

    @abstractmethod
    def register_notification(self, callback_function):
        """
        Registers a callback function that can handle force feedback, leds, etc.
        Can only succeed once per gamepad, all subsequent calls will throw an exception.

        :param: a function of the form: my_func(client, target, large_motor, small_motor, led_number, user_data)
        """
        raise NotImplementedError

    @abstractmethod
    def unregister_notification(self):
        """
        Unregisters a previously registered callback function.
        """
        raise NotImplementedError


class VDS4Gamepad(ABC):
    """
    Virtual DualShock 4 gamepad
    """

    def get_default_report(self):
        rep = DS4_REPORT(
            bThumbLX=0,
            bThumbLY=0,
            bThumbRX=0,
            bThumbRY=0,
            wButtons=0,
            bSpecial=0,
            bTriggerL=0,
            bTriggerR=0)
        DS4_REPORT_INIT(rep)
        return rep

    def get_default_extended_report(self):
        """
        :return: a DS4_REPORT_EX in a neutral state (default ViGEmBus DS4 report)
        """
        rep = DS4_REPORT_EX()
        DS4_REPORT_INIT(rep.Report)
        rep.Report.bBatteryLvlSpecial = 0x1B  # USB cable connected, battery full
        # Gravity (raw values of the ViGEmBus default report):
        rep.Report.wAccelX = -647
        rep.Report.wAccelY = 5147
        rep.Report.wAccelZ = -5679
        # No finger on the touchpad:
        for touch in (rep.Report.sCurrentTouch, *rep.Report.sPreviousTouch):
            touch.bIsUpTrackingNum1 = 0x80
            touch.bIsUpTrackingNum2 = 0x80
        return rep

    @abstractmethod
    def get_vid(self):
        """
        :return: the vendor ID of the virtual device
        """
        raise NotImplementedError

    @abstractmethod
    def get_pid(self):
        """
        :return: the product ID of the virtual device
        """
        raise NotImplementedError

    @abstractmethod
    def get_index(self):
        """
        :return: the internally used index of the target device
        """
        raise NotImplementedError

    @abstractmethod
    def get_type(self):
        """
        :return: the type of the object (e.g. VIGEM_TARGET_TYPE.Xbox360Wired)
        """
        raise NotImplementedError

    @abstractmethod
    def reset(self):
        """
        Resets the report to the default state
        """
        raise NotImplementedError

    @abstractmethod
    def press_button(self, button):
        """
        Presses a button (no effect if already pressed)
        All possible buttons are in DS4_BUTTONS

        :param: a DS4_BUTTONS field, e.g. DS4_BUTTONS.DS4_BUTTON_TRIANGLE
        """
        raise NotImplementedError

    @abstractmethod
    def release_button(self, button):
        """
        Releases a button (no effect if already released)
        All possible buttons are in DS4_BUTTONS

        :param: a DS4_BUTTONS field, e.g. DS4_BUTTONS.DS4_BUTTON_TRIANGLE
        """
        raise NotImplementedError

    @abstractmethod
    def press_special_button(self, special_button):
        """
        Presses a special button (no effect if already pressed)
        All possible buttons are in DS4_SPECIAL_BUTTONS

        :param: a DS4_SPECIAL_BUTTONS field, e.g. DS4_SPECIAL_BUTTONS.DS4_SPECIAL_BUTTON_TOUCHPAD
        """
        raise NotImplementedError

    @abstractmethod
    def release_special_button(self, special_button):
        """
        Releases a special button (no effect if already released)
        All possible buttons are in DS4_SPECIAL_BUTTONS

        :param: a DS4_SPECIAL_BUTTONS field, e.g. DS4_SPECIAL_BUTTONS.DS4_SPECIAL_BUTTON_TOUCHPAD
        """
        raise NotImplementedError

    @abstractmethod
    def left_trigger(self, value):
        """
        Sets the value of the left trigger

        :param: integer between 0 and 255 (0 = trigger released)
        """
        raise NotImplementedError

    @abstractmethod
    def right_trigger(self, value):
        """
        Sets the value of the right trigger

        :param: integer between 0 and 255 (0 = trigger released)
        """
        raise NotImplementedError

    @abstractmethod
    def left_trigger_float(self, value_float):
        """
        Sets the value of the left trigger

        :param: float between 0.0 and 1.0 (0.0 = trigger released)
        """
        raise NotImplementedError

    @abstractmethod
    def right_trigger_float(self, value_float):
        """
        Sets the value of the right trigger

        :param: float between 0.0 and 1.0 (0.0 = trigger released)
        """
        raise NotImplementedError

    @abstractmethod
    def left_joystick(self, x_value, y_value):
        """
        Sets the values of the X and Y axis for the left joystick

        :param: integer between 0 and 255 (128 = neutral position)
        """
        raise NotImplementedError

    @abstractmethod
    def right_joystick(self, x_value, y_value):
        """
        Sets the values of the X and Y axis for the right joystick

        :param: integer between 0 and 255 (128 = neutral position)
        """
        raise NotImplementedError

    @abstractmethod
    def left_joystick_float(self, x_value_float, y_value_float):
        """
        Sets the values of the X and Y axis for the left joystick

        :param: float between -1.0 and 1.0 (0 = neutral position)
        """
        raise NotImplementedError

    @abstractmethod
    def right_joystick_float(self, x_value_float, y_value_float):
        """
        Sets the values of the X and Y axis for the right joystick

        :param: float between -1.0 and 1.0 (0 = neutral position)
        """
        raise NotImplementedError

    @abstractmethod
    def directional_pad(self, direction):
        """
        Sets the direction of the directional pad (hat)
        All possible directions are in DS4_DPAD_DIRECTIONS

        :param: a DS4_DPAD_DIRECTIONS field, e.g. DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NORTHWEST
        """
        raise NotImplementedError

    @abstractmethod
    def gyroscope(self, x_value, y_value, z_value):
        """
        Sets the 3D gyroscope reading.

        :param: integer between -32768 and 32767 (0 = no torque)
        """
        raise NotImplementedError
    
    @abstractmethod
    def accelerometer(self, x_value, y_value, z_value):
        """
        Sets the 3D accelerometer reading.

        :param: integer between -32768 and 32767 (0 = no acceleration)
        """
        raise NotImplementedError
    
    @abstractmethod
    def usb(self, connected):
        """
        Sets whether the USB cable is connected (default: True).

        :param: bool
        """
        raise NotImplementedError

    @abstractmethod
    def battery(self, battery_code):
        """
        Sets the battery status code (default: 11).

        Codes meaning:
            usb unplugged:
                0 to 9 = 0-9%, 10-19%, ..., 90-99%
                10 to 15 = 100%
            usb connected:
                0 to 9 = same as unplugged, charging
                10 = 100%, charging
                11 = full
                14 = not charging (voltage or temperature error)
                15 = charging error

        :param: integer between 0 and 15
        """
        raise NotImplementedError

    @abstractmethod
    def touchpad(self, finger1, finger2):
        """
        Sets the touchpad reading.
        The touchpad can read up to two fingers.

        :param: None (finger not touching) or (x, y) tuple of integers (finger coordinates).
            x between 0 and 1919 (0 = left), y between 0 and 941 (0 = top)
        """
        raise NotImplementedError

    @abstractmethod
    def update(self):
        """
        Sends the current report (i.e. commands) to the virtual device
        """
        raise NotImplementedError

    @abstractmethod
    def update_extended_report(self, extended_report):
        """
        Enables using a DS4_REPORT_EX directly (advanced users only).
        This method can be used instead of the vgamepad high-level API for DS4.

        Description of each byte's role in DS4_REPORT_EX.Report:

        Sources:
        https://github.com/torvalds/linux/blob/master/drivers/hid/hid-playstation.c
        https://chromium.googlesource.com/chromium/src/+/ef290da170d481d1ef1c9ca4e11d156cfaf09afe/device/gamepad/dualshock4_controller.cc


        Sticks, buttons and triggers (identical to DS4_REPORT):
            bThumbLX, bThumbLY (0, 1): left stick X/Y, 0 to 255 (128 = centered, X: 0 = left, Y: 0 = up)
            bThumbRX, bThumbRY (2, 3): right stick X/Y, 0 to 255 (128 = centered, X: 0 = left, Y: 0 = up)
            wButtons (4-5):
                bits 0-3: D-pad (hat) direction, see DS4_DPAD_DIRECTIONS (8 = released)
                bits 4-15: digital buttons, see DS4_BUTTONS
            bSpecial (6):
                bits 0-1: PS and touchpad-click buttons, see DS4_SPECIAL_BUTTONS
                bits 2-7: 6-bit report counter (unknown effect: not used by the Linux and Chromium drivers)
            bTriggerL, bTriggerR (7, 8): analog L2/R2, 0 (released) to 255 (fully pressed);
                independent from the digital DS4_BUTTON_TRIGGER_LEFT/RIGHT bits

        IMU:
            wTimestamp (9-10): sensor timestamp in units of 5.33 microseconds, wrapping around at 65535;
                used to date gyroscope/accelerometer samples
            bBatteryLvl (11): named "sensor temperature" by the Linux and Chromium drivers (despite its ViGEm name);
            wGyroX, wGyroY, wGyroZ (12-17): raw signed angular velocity (pitch, yaw, roll);
                host drivers scale it with the calibration data of the virtual DualShock 4 (feature report 0x02)
            wAccelX, wAccelY, wAccelZ (18-23): raw signed acceleration on the X, Y, Z axes;
                host drivers scale it and remove its bias with the same calibration data
            _bUnknown1 (24-28): unknown effect

        Status:
            bBatteryLvlSpecial (29):
                bits 0-3: battery level, interpreted according to bit 4:
                    cable unplugged: 0-9 = 0-9%, 10-19%, ... 90-99%; 10 = 100% (discharging)
                    cable plugged: 0-9 = same as above; 10 = 100% (charging); 11 = full; 14-15 = charging error
                bit 4: USB cable connected (1) or not (0)
                bits 5-6: unknown effect
                bit 7: named "extension detection" by the Chromium driver; unknown effect
            _bUnknown2[0] (30):
                bit 2: Sony wireless adapter connected (0) or disconnected (1)
                other bits: unknown effect
            _bUnknown2[1] (31): unknown effect

        Touchpad:
            bTouchPacketsN (32): number of valid touch packets, 0 to 3 (sCurrentTouch, then sPreviousTouch[0], [1])
            sCurrentTouch (33-41), sPreviousTouch[0] (42-50), sPreviousTouch[1] (51-59): DS4_TOUCH packets, each with:
                bPacketCounter: touch packet timestamp/counter (unknown effect: not used by the Linux driver)
                bIsUpTrackingNum1:
                    bit 7: first finger NOT touching (1) or touching (0)
                    bits 0-6: tracking number, unique to each finger contact
                bTouchData1: position of the first finger, two 12-bit values:
                    x = bTouchData1[0] | (bTouchData1[1] & 0x0F) << 8  (0 to 1919)
                    y = bTouchData1[1] >> 4 | bTouchData1[2] << 4  (0 to 941)
                bIsUpTrackingNum2, bTouchData2: same for the second finger

        Remaining bytes:
            ReportBuffer[60:63]: unknown effect

        :param: a DS4_REPORT_EX
        """
        raise NotImplementedError

    @abstractmethod
    def register_notification(self, callback_function):
        """
        Registers a callback function that can handle force feedback, leds, etc.
        Can only succeed once per gamepad, all subsequent calls will throw an exception.

        :param: a function of the form: my_func(client, target, large_motor, small_motor, lightbar_color, user_data)
        """
        raise NotImplementedError

    @abstractmethod
    def unregister_notification(self):
        """
        Unregisters a previously registered callback function.
        """
        raise NotImplementedError
