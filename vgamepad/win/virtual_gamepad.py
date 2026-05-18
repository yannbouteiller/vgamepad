"""VGamepad API (Windows) - ViGEm backend."""

from __future__ import annotations

import ctypes
from abc import ABC, abstractmethod
from collections.abc import Callable
from ctypes import CFUNCTYPE, byref, c_ubyte, c_ulong, c_void_p
from typing import Any

import vgamepad.win.vigem_client as vcli
import vgamepad.win.vigem_commons as vcom


def _check_err(err: int) -> None:
    if err != vcom.VIGEM_ERRORS.VIGEM_ERROR_NONE:
        raise Exception(vcom.VIGEM_ERRORS(err).name)


def _dummy_callback(
    client: Any,
    target: Any,
    large_motor: int,
    small_motor: int,
    led_number: int,
    user_data: Any,
) -> None:
    """Reference signature for notification callbacks."""


class VBus:
    """Virtual USB bus (ViGEmBus)."""

    def __init__(self) -> None:
        self._busp = vcli.vigem_alloc()
        _check_err(vcli.vigem_connect(self._busp))

    def get_busp(self) -> Any:
        return self._busp

    def __del__(self) -> None:
        vcli.vigem_disconnect(self._busp)
        vcli.vigem_free(self._busp)


VBUS = VBus()


class VGamepad(ABC):
    def __init__(self) -> None:
        self.vbus = VBUS
        self._busp = self.vbus.get_busp()
        self._devicep = self.target_alloc()
        self.CMPFUNC = CFUNCTYPE(None, c_void_p, c_void_p, c_ubyte, c_ubyte, c_ubyte, c_void_p)
        self.cmp_func: Any | None = None
        vcli.vigem_target_add(self._busp, self._devicep)
        if not vcli.vigem_target_is_attached(self._devicep):
            raise RuntimeError("The virtual device could not connect to ViGEmBus.")

    def __del__(self) -> None:
        vcli.vigem_target_remove(self._busp, self._devicep)
        vcli.vigem_target_free(self._devicep)

    def get_vid(self) -> int:
        """Return the vendor ID of the virtual device."""
        return vcli.vigem_target_get_vid(self._devicep)

    def get_pid(self) -> int:
        """Return the product ID of the virtual device."""
        return vcli.vigem_target_get_pid(self._devicep)

    def set_vid(self, vid: int) -> None:
        """Set the vendor ID of the virtual device."""
        vcli.vigem_target_set_vid(self._devicep, vid)

    def set_pid(self, pid: int) -> None:
        """Set the product ID of the virtual device."""
        vcli.vigem_target_set_pid(self._devicep, pid)

    def get_index(self) -> int:
        """Return the internally used index of the target device."""
        return vcli.vigem_target_get_index(self._devicep)

    def get_type(self) -> Any:
        """Return the type of the object (e.g. ``VIGEM_TARGET_TYPE.Xbox360Wired``)."""
        return vcli.vigem_target_get_type(self._devicep)

    @abstractmethod
    def target_alloc(self) -> Any:
        """Return the pointer to an allocated ViGEm device."""
        ...


class VX360Gamepad(VGamepad):
    """Virtual Xbox 360 gamepad (Windows / ViGEm)."""

    def __init__(self) -> None:
        super().__init__()
        self.report = self.get_default_report()
        self.update()

    def get_default_report(self) -> vcom.XUSB_REPORT:
        return vcom.XUSB_REPORT(
            wButtons=0,
            bLeftTrigger=0,
            bRightTrigger=0,
            sThumbLX=0,
            sThumbLY=0,
            sThumbRX=0,
            sThumbRY=0,
        )

    def reset(self) -> None:
        """Reset the report to the default state."""
        self.report = self.get_default_report()

    def press_button(self, button: vcom.XUSB_BUTTON) -> None:
        """Press a button (no effect if already pressed).

        :param button: an ``XUSB_BUTTON`` field, e.g. ``XUSB_BUTTON.XUSB_GAMEPAD_X``
        """
        self.report.wButtons = self.report.wButtons | button

    def release_button(self, button: vcom.XUSB_BUTTON) -> None:
        """Release a button (no effect if already released).

        :param button: an ``XUSB_BUTTON`` field, e.g. ``XUSB_BUTTON.XUSB_GAMEPAD_X``
        """
        self.report.wButtons = self.report.wButtons & ~button

    def left_trigger(self, value: int) -> None:
        """Set the left trigger value (0-255, 0 = released)."""
        self.report.bLeftTrigger = value

    def right_trigger(self, value: int) -> None:
        """Set the right trigger value (0-255, 0 = released)."""
        self.report.bRightTrigger = value

    def left_trigger_float(self, value_float: float) -> None:
        """Set the left trigger value (0.0-1.0, 0.0 = released)."""
        self.left_trigger(round(value_float * 255))

    def right_trigger_float(self, value_float: float) -> None:
        """Set the right trigger value (0.0-1.0, 0.0 = released)."""
        self.right_trigger(round(value_float * 255))

    def left_joystick(self, x_value: int, y_value: int) -> None:
        """Set the left joystick axes (-32768 to 32767, 0 = neutral)."""
        self.report.sThumbLX = x_value
        self.report.sThumbLY = y_value

    def right_joystick(self, x_value: int, y_value: int) -> None:
        """Set the right joystick axes (-32768 to 32767, 0 = neutral)."""
        self.report.sThumbRX = x_value
        self.report.sThumbRY = y_value

    def left_joystick_float(self, x_value_float: float, y_value_float: float) -> None:
        """Set the left joystick axes (-1.0 to 1.0, 0.0 = neutral)."""
        self.left_joystick(round(x_value_float * 32767), round(y_value_float * 32767))

    def right_joystick_float(self, x_value_float: float, y_value_float: float) -> None:
        """Set the right joystick axes (-1.0 to 1.0, 0.0 = neutral)."""
        self.right_joystick(round(x_value_float * 32767), round(y_value_float * 32767))

    def update(self) -> None:
        """Send the current report to the virtual device."""
        _check_err(vcli.vigem_target_x360_update(self._busp, self._devicep, self.report))

    def get_xinput_user_index(self) -> int | None:
        """Return the XInput user index (0--3) for this virtual device, or None if unavailable.

        This matches ``dwUserIndex`` for ``XInputGetState`` / ``XInputGetStateEx``. Prefer this
        over scanning the first connected controller when multiple gamepads are present.
        """
        idx = c_ulong()
        err = vcli.vigem_target_x360_get_user_index(self._busp, self._devicep, byref(idx))
        if err != vcom.VIGEM_ERRORS.VIGEM_ERROR_NONE:
            return None
        u = int(idx.value)
        if u > 3:
            return None
        return u

    def register_notification(self, callback_function: Callable[..., Any]) -> None:
        """Register a callback for force feedback, LEDs, etc.

        :param callback_function: ``f(client, target, large_motor, small_motor, led_number, user_data)``
        """
        if not vcom.notification_callback_matches(callback_function):
            raise TypeError(
                "Expected a callback with six parameters "
                "(client, target, large_motor, small_motor, led_number, user_data)"
            )
        self.cmp_func = self.CMPFUNC(callback_function)
        _check_err(vcli.vigem_target_x360_register_notification(self._busp, self._devicep, self.cmp_func, None))

    def unregister_notification(self) -> None:
        """Unregister a previously registered callback function."""
        vcli.vigem_target_x360_unregister_notification(self._devicep)

    def target_alloc(self) -> Any:
        return vcli.vigem_target_x360_alloc()


class VDS4Gamepad(VGamepad):
    """Virtual DualShock 4 gamepad (Windows / ViGEm)."""

    def __init__(self) -> None:
        super().__init__()
        self.report = self.get_default_report()
        self.update()

    def get_default_report(self) -> vcom.DS4_REPORT:
        rep = vcom.DS4_REPORT(
            bThumbLX=0,
            bThumbLY=0,
            bThumbRX=0,
            bThumbRY=0,
            wButtons=0,
            bSpecial=0,
            bTriggerL=0,
            bTriggerR=0,
        )
        vcom.DS4_REPORT_INIT(rep)
        return rep

    def reset(self) -> None:
        """Reset the report to the default state."""
        self.report = self.get_default_report()

    def press_button(self, button: vcom.DS4_BUTTONS) -> None:
        """Press a button (no effect if already pressed).

        :param button: a ``DS4_BUTTONS`` field, e.g. ``DS4_BUTTONS.DS4_BUTTON_TRIANGLE``
        """
        self.report.wButtons = self.report.wButtons | button

    def release_button(self, button: vcom.DS4_BUTTONS) -> None:
        """Release a button (no effect if already released).

        :param button: a ``DS4_BUTTONS`` field, e.g. ``DS4_BUTTONS.DS4_BUTTON_TRIANGLE``
        """
        self.report.wButtons = self.report.wButtons & ~button

    def press_special_button(self, special_button: vcom.DS4_SPECIAL_BUTTONS) -> None:
        """Press a special button (no effect if already pressed).

        :param special_button: a ``DS4_SPECIAL_BUTTONS`` field
        """
        self.report.bSpecial = self.report.bSpecial | special_button

    def release_special_button(self, special_button: vcom.DS4_SPECIAL_BUTTONS) -> None:
        """Release a special button (no effect if already released).

        :param special_button: a ``DS4_SPECIAL_BUTTONS`` field
        """
        self.report.bSpecial = self.report.bSpecial & ~special_button

    def left_trigger(self, value: int) -> None:
        """Set the left trigger value (0-255, 0 = released)."""
        self.report.bTriggerL = value

    def right_trigger(self, value: int) -> None:
        """Set the right trigger value (0-255, 0 = released)."""
        self.report.bTriggerR = value

    def left_trigger_float(self, value_float: float) -> None:
        """Set the left trigger value (0.0-1.0, 0.0 = released)."""
        self.left_trigger(round(value_float * 255))

    def right_trigger_float(self, value_float: float) -> None:
        """Set the right trigger value (0.0-1.0, 0.0 = released)."""
        self.right_trigger(round(value_float * 255))

    def left_joystick(self, x_value: int, y_value: int) -> None:
        """Set the left joystick axes (0-255, 128 = neutral)."""
        self.report.bThumbLX = x_value
        self.report.bThumbLY = y_value

    def right_joystick(self, x_value: int, y_value: int) -> None:
        """Set the right joystick axes (0-255, 128 = neutral)."""
        self.report.bThumbRX = x_value
        self.report.bThumbRY = y_value

    def left_joystick_float(self, x_value_float: float, y_value_float: float) -> None:
        """Set the left joystick axes (-1.0 to 1.0, 0.0 = neutral)."""
        self.left_joystick(128 + round(x_value_float * 127), 128 + round(y_value_float * 127))

    def right_joystick_float(self, x_value_float: float, y_value_float: float) -> None:
        """Set the right joystick axes (-1.0 to 1.0, 0.0 = neutral)."""
        self.right_joystick(128 + round(x_value_float * 127), 128 + round(y_value_float * 127))

    def directional_pad(self, direction: vcom.DS4_DPAD_DIRECTIONS) -> None:
        """Set the directional pad (hat) direction.

        :param direction: a ``DS4_DPAD_DIRECTIONS`` field
        """
        vcom.DS4_SET_DPAD(self.report, direction)

    def update(self) -> None:
        """Send the current report to the virtual device."""
        _check_err(vcli.vigem_target_ds4_update(self._busp, self._devicep, self.report))

    def update_extended_report(self, extended_report: vcom.DS4_REPORT_EX) -> None:
        """Send a DS4_REPORT_EX to the virtual device (advanced users only).

        :param extended_report: a ``DS4_REPORT_EX``
        """
        _check_err(vcli.vigem_target_ds4_update_ex_ptr(self._busp, self._devicep, ctypes.byref(extended_report)))

    def register_notification(self, callback_function: Callable[..., Any]) -> None:
        """Register a callback for force feedback, LEDs, etc.

        :param callback_function: ``f(client, target, large_motor, small_motor, led_number, user_data)``
        """
        if not vcom.notification_callback_matches(callback_function):
            raise TypeError(
                "Expected a callback with six parameters "
                "(client, target, large_motor, small_motor, led_number, user_data)"
            )
        self.cmp_func = self.CMPFUNC(callback_function)
        _check_err(vcli.vigem_target_ds4_register_notification(self._busp, self._devicep, self.cmp_func, None))

    def unregister_notification(self) -> None:
        """Unregister a previously registered callback function."""
        vcli.vigem_target_ds4_unregister_notification(self._devicep)

    def target_alloc(self) -> Any:
        return vcli.vigem_target_ds4_alloc()
