"""
VGamepad API (Windows)
"""

import vgamepad.win.vigem_commons as vcom
import vgamepad.win.vigem_client as vcli
import ctypes
import time
from ctypes import WINFUNCTYPE, c_void_p, c_ubyte  # Note: replaced CFUNCTYPE with WINFUNCTYPE for x86 compatibility (Windows only)
from abc import ABC, abstractmethod
from inspect import signature  # Check if user defined callback function is legal


def check_err(err):
    if err != vcom.VIGEM_ERRORS.VIGEM_ERROR_NONE:
        raise RuntimeError(f"Error: {vcom.VIGEM_ERRORS(err).name}")


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


class VBus:
    """
    Virtual USB bus (ViGEmBus)
    """
    def __init__(self):
        self._busp = vcli.vigem_alloc()
        check_err(vcli.vigem_connect(self._busp))

    def get_busp(self):
        return self._busp

    def __del__(self):
        vcli.vigem_disconnect(self._busp)
        vcli.vigem_free(self._busp)


# We instantiate a single global VBus for all controllers
VBUS = VBus()


class VGamepad(ABC):
    def __init__(self, vid=None, pid=None):
        self.cmp_func = None
        self.vbus = VBUS
        self._busp = self.vbus.get_busp()
        self._devicep = self.target_alloc()
        if vid is not None:
            vcli.vigem_target_set_vid(self._devicep, vid)
        if pid is not None:
            vcli.vigem_target_set_pid(self._devicep, pid)
        check_err(vcli.vigem_target_add(self._busp, self._devicep))
        if not vcli.vigem_target_is_attached(self._devicep):
            raise RuntimeError("The virtual device could not connect to ViGEmBus.")

    def __del__(self):
        if self.cmp_func is not None:
            self.unregister_notification()
        vcli.vigem_target_remove(self._busp, self._devicep)
        vcli.vigem_target_free(self._devicep)

    def get_vid(self):
        """
        :return: the vendor ID of the virtual device
        """
        return vcli.vigem_target_get_vid(self._devicep)

    def get_pid(self):
        """
        :return: the product ID of the virtual device
        """
        return vcli.vigem_target_get_pid(self._devicep)

    def get_index(self):
        """
        :return: the internally used index of the target device
        """
        return vcli.vigem_target_get_index(self._devicep)

    def get_type(self):
        """
        :return: the type of the object (e.g. VIGEM_TARGET_TYPE.Xbox360Wired)
        """
        return vcli.vigem_target_get_type(self._devicep)

    @abstractmethod
    def target_alloc(self):
        """
        :return: the pointer to an allocated ViGEm device (e.g. vcli.vigem_target_x360_alloc())
        """
        pass


class VX360Gamepad(VGamepad):
    """
    Virtual XBox360 gamepad
    """
    def __init__(self, vid=None, pid=None):
        super().__init__(vid=vid, pid=pid)
        self.CMPFUNC = WINFUNCTYPE(None, c_void_p, c_void_p, c_ubyte, c_ubyte, c_ubyte, c_void_p)
        self.report = self.get_default_report()
        self.update()

    def get_default_report(self):
        return vcom.XUSB_REPORT(
            wButtons=0,
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
        self.left_joystick(round(x_value_float * 32767), round(y_value_float * 32767))

    def right_joystick_float(self, x_value_float, y_value_float):
        """
        Sets the values of the X and Y axis for the right joystick

        :param: float between -1.0 and 1.0 (0 = neutral position)
        """
        self.right_joystick(round(x_value_float * 32767), round(y_value_float * 32767))

    def update(self):
        """
        Sends the current report (i.e. commands) to the virtual device
        """
        check_err(vcli.vigem_target_x360_update(self._busp, self._devicep, self.report))

    def register_notification(self, callback_function):
        """
        Registers a callback function that can handle force feedback, leds, etc.
        Can only succeed once per gamepad, all subsequent calls will throw an exception.

        :param: a function of the form: my_func(client, target, large_motor, small_motor, led_number, user_data)
        """
        if self.cmp_func is not None:
            raise RuntimeError("Cannot register a callback more than once per gamepad.")
        if not check_callback_signature(callback_function):
            raise TypeError("Needed callback function signature: {}, but got: {}".format(signature(dummy_x360_callback), signature(callback_function)))
        cmp_func = self.CMPFUNC(callback_function)  # keep its reference, otherwise the program will crash when a callback is made.
        check_err(vcli.vigem_target_x360_register_notification(self._busp, self._devicep, cmp_func, None))
        self.cmp_func = cmp_func

    def unregister_notification(self):
        """
        Unregisters a previously registered callback function.
        """
        vcli.vigem_target_x360_unregister_notification(self._devicep)

    def target_alloc(self):
        return vcli.vigem_target_x360_alloc()


class VDS4Gamepad(VGamepad):
    """
    Virtual DualShock 4 gamepad
    """

    def __init__(self, vid=None, pid=None):
        super().__init__(vid=vid, pid=pid)
        self.CMPFUNC = WINFUNCTYPE(None, c_void_p, c_void_p, c_ubyte, c_ubyte, vcom.DS4_LIGHTBAR_COLOR, c_void_p)
        self.report = self.get_default_report()
        self.extended_report = self.get_default_extended_report()
        self._use_extended_report = False
        self._touch_tracking_num = 0  # incremented for each new finger contact on the touchpad
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

    def get_default_extended_report(self):
        """
        :return: a DS4_REPORT_EX in a neutral state (default ViGEmBus DS4 report)
        """
        rep = vcom.DS4_REPORT_EX()
        vcom.DS4_REPORT_INIT(rep.Report)
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

    def reset(self):
        """
        Resets the report to the default state
        """
        self.report = self.get_default_report()
        self.extended_report = self.get_default_extended_report()
        self._use_extended_report = False

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
        self.left_joystick(128 + round(x_value_float * 127), 128 + round(y_value_float * 127))

    def right_joystick_float(self, x_value_float, y_value_float):
        """
        Sets the values of the X and Y axis for the right joystick

        :param: float between -1.0 and 1.0 (0 = neutral position)
        """
        self.right_joystick(128 + round(x_value_float * 127), 128 + round(y_value_float * 127))

    def directional_pad(self, direction):
        """
        Sets the direction of the directional pad (hat)
        All possible directions are in DS4_DPAD_DIRECTIONS

        :param: a DS4_DPAD_DIRECTIONS field, e.g. DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NORTHWEST
        """
        vcom.DS4_SET_DPAD(self.report, direction)

    def gyroscope(self, x_value, y_value, z_value):
        """
        Sets the 3D gyroscope reading.

        :param: integer between -32768 and 32767 (0 = no acceleration)
        """
        self.extended_report.Report.wGyroX = x_value
        self.extended_report.Report.wGyroY = y_value
        self.extended_report.Report.wGyroZ = z_value
        self._use_extended_report = True
    
    def accelerometer(self, x_value, y_value, z_value):
        """
        Sets the 3D accelerometer reading.

        :param: integer between -32768 and 32767 (0 = no acceleration)
        """
        self.extended_report.Report.wAccelX = x_value
        self.extended_report.Report.wAccelY = y_value
        self.extended_report.Report.wAccelZ = z_value
        self._use_extended_report = True
    
    def usb(self, connected):
        """
        Sets whether the USB cable is connected (default: True).

        :param: bool
        """
        if connected:
            self.extended_report.Report.bBatteryLvlSpecial |= 0x10
        else:
            self.extended_report.Report.bBatteryLvlSpecial &= ~0x10
        self._use_extended_report = True

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
        report = self.extended_report.Report
        report.bBatteryLvlSpecial = (report.bBatteryLvlSpecial & ~0x0F) | (battery_code & 0x0F)
        self._use_extended_report = True

    def touchpad(self, finger1, finger2):
        """
        Sets the touchpad reading.
        The touchpad can read up to two fingers.

        :param: None (finger not touching) or (x, y) tuple of integers (finger coordinates).
            x between 0 and 1919 (0 = left), y between 0 and 941 (0 = top)
        """
        report = self.extended_report.Report
        touch = report.sCurrentTouch
        for finger, attr_up, attr_data in ((finger1, "bIsUpTrackingNum1", "bTouchData1"),
                                           (finger2, "bIsUpTrackingNum2", "bTouchData2")):
            is_up = getattr(touch, attr_up)
            if finger is None:
                setattr(touch, attr_up, is_up | 0x80)  # lifted, keeps its last tracking number
            else:
                if is_up & 0x80:  # new contact
                    setattr(touch, attr_up, self._touch_tracking_num)
                    self._touch_tracking_num = (self._touch_tracking_num + 1) & 0x7F
                x, y = finger
                data = getattr(touch, attr_data)
                data[0] = x & 0xFF
                data[1] = ((x >> 8) & 0x0F) | ((y & 0x0F) << 4)
                data[2] = (y >> 4) & 0xFF
        touch.bPacketCounter = (touch.bPacketCounter + 1) & 0xFF
        report.bTouchPacketsN = 1
        self._use_extended_report = True

    def _sync_extended_report(self):
        for field in (
                "bThumbLX", "bThumbLY", "bThumbRX", "bThumbRY",
                "wButtons", "bSpecial", "bTriggerL", "bTriggerR"):
            setattr(self.extended_report.Report, field, getattr(self.report, field))
        self.extended_report.Report.wTimestamp = int(time.monotonic() * 187500) & 0xFFFF

    def update(self):
        """
        Sends the current report (i.e. commands) to the virtual device
        """
        if self._use_extended_report:
            self._sync_extended_report()
            self.update_extended_report(self.extended_report)
        else:
            check_err(vcli.vigem_target_ds4_update(self._busp, self._devicep, self.report))

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
        check_err(vcli.vigem_target_ds4_update_ex_ptr(self._busp, self._devicep, ctypes.byref(extended_report)))

    def register_notification(self, callback_function):
        """
        Registers a callback function that can handle force feedback, leds, etc.
        Can only succeed once per gamepad, all subsequent calls will throw an exception.

        :param: a function of the form: my_func(client, target, large_motor, small_motor, lightbar_color, user_data)
        """
        if self.cmp_func is not None:
            raise RuntimeError("Cannot register a callback more than once per gamepad.")
        if not check_callback_signature(callback_function):
            raise TypeError("Needed callback function signature: {}, but got: {}".format(signature(dummy_ds4_callback), signature(callback_function)))
        cmp_func = self.CMPFUNC(callback_function)
        check_err(vcli.vigem_target_ds4_register_notification(self._busp, self._devicep, cmp_func, None))
        self.cmp_func = cmp_func

    def unregister_notification(self):
        """
        Unregisters a previously registered callback function.
        """
        vcli.vigem_target_ds4_unregister_notification(self._devicep)

    def target_alloc(self):
        return vcli.vigem_target_ds4_alloc()
