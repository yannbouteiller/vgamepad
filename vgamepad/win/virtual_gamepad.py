"""
VGamepad API (Windows)

All API docstrings are defined in vgamepad.api
"""

import ctypes
import time
from ctypes import WINFUNCTYPE, c_void_p, c_ubyte  # Note: replaced CFUNCTYPE with WINFUNCTYPE for x86 compatibility (Windows only)
from abc import ABC, abstractmethod
from inspect import signature

import vgamepad.api as api
import vgamepad.win.vigem_client as vcli


def check_err(err):
    if err != api.VIGEM_ERRORS.VIGEM_ERROR_NONE:
        raise RuntimeError(f"Error: {api.VIGEM_ERRORS(err).name}")


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
        return vcli.vigem_target_get_vid(self._devicep)

    def get_pid(self):
        return vcli.vigem_target_get_pid(self._devicep)

    def get_index(self):
        return vcli.vigem_target_get_index(self._devicep)

    def get_type(self):
        return vcli.vigem_target_get_type(self._devicep)

    @abstractmethod
    def target_alloc(self):
        pass


class VX360Gamepad(VGamepad, api.VX360Gamepad):
    """
    Virtual XBox360 gamepad
    """
    def __init__(self, vid=None, pid=None):
        super().__init__(vid=vid, pid=pid)
        self.CMPFUNC = WINFUNCTYPE(None, c_void_p, c_void_p, c_ubyte, c_ubyte, c_ubyte, c_void_p)
        self.report = self.get_default_report()
        self.update()

    def reset(self):
        self.report = self.get_default_report()

    def press_button(self, button):
        self.report.wButtons = self.report.wButtons | button

    def release_button(self, button):
        self.report.wButtons = self.report.wButtons & ~button

    def left_trigger(self, value):
        self.report.bLeftTrigger = value

    def right_trigger(self, value):
        self.report.bRightTrigger = value

    def left_trigger_float(self, value_float):
        self.left_trigger(round(value_float * 255))

    def right_trigger_float(self, value_float):
        self.right_trigger(round(value_float * 255))

    def left_joystick(self, x_value, y_value):
        self.report.sThumbLX = x_value
        self.report.sThumbLY = y_value

    def right_joystick(self, x_value, y_value):
        self.report.sThumbRX = x_value
        self.report.sThumbRY = y_value

    def left_joystick_float(self, x_value_float, y_value_float):
        self.left_joystick(round(x_value_float * 32767), round(y_value_float * 32767))

    def right_joystick_float(self, x_value_float, y_value_float):
        self.right_joystick(round(x_value_float * 32767), round(y_value_float * 32767))

    def update(self):
        check_err(vcli.vigem_target_x360_update(self._busp, self._devicep, self.report))

    def register_notification(self, callback_function):
        if self.cmp_func is not None:
            raise RuntimeError("Cannot register a callback more than once per gamepad.")
        if not api.check_callback_signature(callback_function):
            raise TypeError("Needed callback function signature: {}, but got: {}".format(signature(api.dummy_x360_callback), signature(callback_function)))
        cmp_func = self.CMPFUNC(callback_function)  # keep its reference, otherwise the program will crash when a callback is made.
        check_err(vcli.vigem_target_x360_register_notification(self._busp, self._devicep, cmp_func, None))
        self.cmp_func = cmp_func

    def unregister_notification(self):
        vcli.vigem_target_x360_unregister_notification(self._devicep)

    def target_alloc(self):
        return vcli.vigem_target_x360_alloc()


class VDS4Gamepad(VGamepad, api.VDS4Gamepad):
    """
    Virtual DualShock 4 gamepad
    """

    def __init__(self, vid=None, pid=None):
        super().__init__(vid=vid, pid=pid)
        self.CMPFUNC = WINFUNCTYPE(None, c_void_p, c_void_p, c_ubyte, c_ubyte, api.DS4_LIGHTBAR_COLOR, c_void_p)
        self.report = self.get_default_report()
        self.extended_report = self.get_default_extended_report()
        self._use_extended_report = False
        self._touch_tracking_num = 0  # incremented for each new finger contact on the touchpad
        self.update()

    def reset(self):
        self.report = self.get_default_report()
        self.extended_report = self.get_default_extended_report()
        self._use_extended_report = False

    def press_button(self, button):
        self.report.wButtons = self.report.wButtons | button

    def release_button(self, button):
        self.report.wButtons = self.report.wButtons & ~button

    def press_special_button(self, special_button):
        self.report.bSpecial = self.report.bSpecial | special_button

    def release_special_button(self, special_button):
        self.report.bSpecial = self.report.bSpecial & ~special_button

    def left_trigger(self, value):
        self.report.bTriggerL = value

    def right_trigger(self, value):
        self.report.bTriggerR = value

    def left_trigger_float(self, value_float):
        self.left_trigger(round(value_float * 255))

    def right_trigger_float(self, value_float):
        self.right_trigger(round(value_float * 255))

    def left_joystick(self, x_value, y_value):
        self.report.bThumbLX = x_value
        self.report.bThumbLY = y_value

    def right_joystick(self, x_value, y_value):
        self.report.bThumbRX = x_value
        self.report.bThumbRY = y_value

    def left_joystick_float(self, x_value_float, y_value_float):
        self.left_joystick(128 + round(x_value_float * 127), 128 + round(y_value_float * 127))

    def right_joystick_float(self, x_value_float, y_value_float):
        self.right_joystick(128 + round(x_value_float * 127), 128 + round(y_value_float * 127))

    def directional_pad(self, direction):
        api.DS4_SET_DPAD(self.report, direction)

    def gyroscope(self, x_value, y_value, z_value):
        self.extended_report.Report.wGyroX = x_value
        self.extended_report.Report.wGyroY = y_value
        self.extended_report.Report.wGyroZ = z_value
        self._use_extended_report = True
    
    def accelerometer(self, x_value, y_value, z_value):
        self.extended_report.Report.wAccelX = x_value
        self.extended_report.Report.wAccelY = y_value
        self.extended_report.Report.wAccelZ = z_value
        self._use_extended_report = True
    
    def usb(self, connected):
        if connected:
            self.extended_report.Report.bBatteryLvlSpecial |= 0x10
        else:
            self.extended_report.Report.bBatteryLvlSpecial &= ~0x10
        self._use_extended_report = True

    def battery(self, battery_code):
        report = self.extended_report.Report
        report.bBatteryLvlSpecial = (report.bBatteryLvlSpecial & ~0x0F) | (battery_code & 0x0F)
        self._use_extended_report = True

    def touchpad(self, finger1, finger2):
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
        if self._use_extended_report:
            self._sync_extended_report()
            self.update_extended_report(self.extended_report)
        else:
            check_err(vcli.vigem_target_ds4_update(self._busp, self._devicep, self.report))

    def update_extended_report(self, extended_report):
        check_err(vcli.vigem_target_ds4_update_ex_ptr(self._busp, self._devicep, ctypes.byref(extended_report)))

    def register_notification(self, callback_function):
        if self.cmp_func is not None:
            raise RuntimeError("Cannot register a callback more than once per gamepad.")
        if not api.check_callback_signature(callback_function):
            raise TypeError("Needed callback function signature: {}, but got: {}".format(signature(api.dummy_ds4_callback), signature(callback_function)))
        cmp_func = self.CMPFUNC(callback_function)
        check_err(vcli.vigem_target_ds4_register_notification(self._busp, self._devicep, cmp_func, None))
        self.cmp_func = cmp_func

    def unregister_notification(self):
        vcli.vigem_target_ds4_unregister_notification(self._devicep)

    def target_alloc(self):
        return vcli.vigem_target_ds4_alloc()
