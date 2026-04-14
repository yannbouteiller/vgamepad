"""VGamepad API (Linux) - uinput backend via libevdev."""

from __future__ import annotations

import contextlib
import ctypes
import fcntl
import select
import struct
import sys
import threading
import os
from abc import ABC, abstractmethod
from collections.abc import Callable
from inspect import signature
from typing import Any, ClassVar

import libevdev
from loguru import logger  # Logging is off by default. It can be enabled in __init__.py

import vgamepad.win.vigem_commons as vcom


def _ioc(direction: int, ioc_type: int, nr: int, size: int) -> int:
    return (direction << 30) | (ioc_type << 8) | (nr << 0) | (size << 16)


def _iowr(ioc_type: int, nr: int, size: int) -> int:
    return _ioc(3, ioc_type, nr, size)


def _iow(ioc_type: int, nr: int, size: int) -> int:
    return _ioc(1, ioc_type, nr, size)


_UINPUT_IOCTL_BASE = ord("U")

_PTR_SIZE = ctypes.sizeof(ctypes.c_void_p)
_FF_EFFECT_SIZE = 44 if _PTR_SIZE == 4 else 48
_FF_UPLOAD_SIZE = 4 + 4 + _FF_EFFECT_SIZE + _FF_EFFECT_SIZE
_FF_ERASE_SIZE = 12

UI_BEGIN_FF_UPLOAD = _iowr(_UINPUT_IOCTL_BASE, 200, _FF_UPLOAD_SIZE)
UI_END_FF_UPLOAD = _iow(_UINPUT_IOCTL_BASE, 201, _FF_UPLOAD_SIZE)
UI_BEGIN_FF_ERASE = _iowr(_UINPUT_IOCTL_BASE, 202, _FF_ERASE_SIZE)
UI_END_FF_ERASE = _iow(_UINPUT_IOCTL_BASE, 203, _FF_ERASE_SIZE)

_EV_FF = 0x15
_EV_UINPUT = 0x0101
_FF_RUMBLE = 0x50

_UI_FF_UPLOAD = 1
_UI_FF_ERASE = 2

_RUMBLE_STRONG_OFFSET = 14 if _PTR_SIZE == 4 else 16
_RUMBLE_WEAK_OFFSET = _RUMBLE_STRONG_OFFSET + 2
_EFFECT_ID_OFFSET = 2


class _FFUpload(ctypes.Structure):
    """Mirrors struct uinput_ff_upload."""

    _fields_ = [
        ("request_id", ctypes.c_uint32),
        ("retval", ctypes.c_int32),
        ("effect", ctypes.c_ubyte * _FF_EFFECT_SIZE),
        ("old", ctypes.c_ubyte * _FF_EFFECT_SIZE),
    ]


class _FFErase(ctypes.Structure):
    """Mirrors struct uinput_ff_erase."""

    _fields_ = [
        ("request_id", ctypes.c_uint32),
        ("retval", ctypes.c_int32),
        ("effect_id", ctypes.c_uint32),
    ]


def _dummy_callback(
        client,
        target,
        large_motor,
        small_motor,
        led_number,
        user_data,
):
    pass


def _parse_ff_rumble(raw_bytes: bytes) -> tuple[int | None, int | None]:
    """Extract rumble magnitudes from an ff_effect struct.

    Returns ``(strong, weak)`` as 0-65535 values, or ``(None, None)``
    if the effect is not ``FF_RUMBLE``.
    """
    if len(raw_bytes) < _RUMBLE_WEAK_OFFSET + 2:
        return None, None
    effect_type = struct.unpack_from("<H", raw_bytes, 0)[0]
    if effect_type != _FF_RUMBLE:
        return None, None
    strong, weak = struct.unpack_from("<HH", raw_bytes, _RUMBLE_STRONG_OFFSET)
    return strong, weak


class VGamepad(ABC):

    def __init__(self) -> None:
        self.device = libevdev.Device()
        self.device.name = "Virtual Gamepad"
        self._ff_thread: threading.Thread | None = None
        self._ff_stop = threading.Event()
        self._ff_callback: Callable[..., Any] | None = None
        self._ff_effects: dict[int, tuple[int, int]] = {}

    def get_vid(self) -> int:
        """Return the vendor ID of the virtual device."""
        return self.device.id.vendor

    def get_pid(self) -> int:
        """Return the product ID of the virtual device."""
        return self.device.id.product

    def set_vid(self, vid: int) -> None:
        """Set the vendor ID of the virtual device."""
        self.device.id = {"vendor": vid}

    def set_pid(self, pid: int) -> None:
        """Set the product ID of the virtual device."""
        self.device.id = {"product": pid}

    def get_index(self) -> int:
        """Return the internally used index of the target device."""
        return 0

    def get_type(self) -> int:
        """Return the type of the object (bus type)."""
        return self.device.id.bustype

    def _handle_ff_upload(self, fd: int, request_id: int) -> None:
        """Handle a UI_FF_UPLOAD request from the kernel."""
        upload = _FFUpload()
        upload.request_id = request_id
        try:
            fcntl.ioctl(fd, UI_BEGIN_FF_UPLOAD, upload)
        except OSError:
            return
        effect_bytes = bytes(upload.effect)
        strong, weak = _parse_ff_rumble(effect_bytes)
        effect_id = struct.unpack_from("<h", effect_bytes, _EFFECT_ID_OFFSET)[0]
        if effect_id < 0:
            effect_id = len(self._ff_effects)
            struct.pack_into("<h", upload.effect, _EFFECT_ID_OFFSET, effect_id)
        if strong is not None:
            self._ff_effects[effect_id] = (strong, weak)  # type: ignore[arg-type]
        upload.retval = 0
        with contextlib.suppress(OSError):
            fcntl.ioctl(fd, UI_END_FF_UPLOAD, upload)

    def _handle_ff_erase(self, fd: int, request_id: int) -> None:
        """Handle a UI_FF_ERASE request from the kernel."""
        erase = _FFErase()
        erase.request_id = request_id
        try:
            fcntl.ioctl(fd, UI_BEGIN_FF_ERASE, erase)
        except OSError:
            return
        self._ff_effects.pop(erase.effect_id, None)
        erase.retval = 0
        with contextlib.suppress(OSError):
            fcntl.ioctl(fd, UI_END_FF_ERASE, erase)

    def get_raw_uinput_fd(self) -> int:
        """Retrieves fd from /dev/uinput, bypassing libevdev."""
        for fd in os.listdir("/proc/self/fd"):
            try:
                if os.readlink(f"/proc/self/fd/{fd}") == "/dev/uinput":
                    return int(fd)
            except OSError:
                continue
        raise RuntimeError("No dev/input open")

    def register_notification(self, callback_function: Callable[..., Any]) -> None:
        """Register a callback for force-feedback notifications.

        On Linux force feedback is implemented by reading ``FF_RUMBLE``
        events from the uinput device.  The callback receives the same
        signature as Windows:

            ``callback(client, target, large_motor, small_motor, led_number, user_data)``

        ``large_motor`` and ``small_motor`` are scaled to 0-255 from the
        kernel's 0-65535 range.
        """
        if signature(callback_function) != signature(_dummy_callback):
            raise TypeError(
                f"Expected callback signature: {signature(_dummy_callback)}, "
                f"got: {signature(callback_function)}"
            )

        self._ff_callback = callback_function

        if self._ff_thread is not None:
            return
        uinput_fd = self.get_raw_uinput_fd()
        if uinput_fd is None:
            return

        self._ff_stop.clear()
        self._ff_thread = threading.Thread(
            target=self._ff_reader_loop,
            args=(uinput_fd,),
            daemon=True,
        )
        self._ff_thread.start()

    def _ff_reader_loop(self, fd: int) -> None:
        """Background thread: reads EV_FF / EV_UINPUT events and dispatches rumble callbacks."""
        os.set_blocking(fd, False)
        while not self._ff_stop.is_set():
            ready, _, _ = select.select([fd], [], [], 0.1)
            if not ready:
                continue
            try:
                data = os.read(fd, 24)
            except OSError:
                continue
            if len(data) < 24:
                continue
            _sec, _usec, ev_type, ev_code, ev_value = struct.unpack("llHHi", data)
            if ev_type == _EV_FF and ev_code in self._ff_effects:
                strong, weak = self._ff_effects[ev_code]
                large_motor = (strong * 255) // 65535 if strong else 0
                small_motor = (weak * 255) // 65535 if weak else 0
                if self._ff_callback:
                    try:
                        self._ff_callback(None, None, large_motor, small_motor, 0, None)
                    except Exception:
                        logger.opt(exception=True).debug("FF callback raised")
            elif ev_type == _EV_UINPUT:
                if ev_code == _UI_FF_UPLOAD:
                    self._handle_ff_upload(fd, ev_value)
                elif ev_code == _UI_FF_ERASE:
                    self._handle_ff_erase(fd, ev_value)


def unregister_notification(self) -> None:
    """Unregister a previously registered callback function."""
    self._ff_callback = None
    self._ff_stop.set()
    if self._ff_thread is not None:
        self._ff_thread.join(timeout=2.0)
        self._ff_thread = None
    self._ff_effects.clear()


def __del__(self) -> None:
    self._ff_stop.set()
    if self._ff_thread is not None:
        self._ff_thread.join(timeout=1.0)


@abstractmethod
def target_alloc(self) -> Any:
    """Return the pointer to an allocated evdev device."""
    ...


class VX360Gamepad(VGamepad):
    """Virtual Xbox 360 gamepad (Linux / uinput)."""

    XUSB_BUTTON_TO_EV_KEY: ClassVar[dict[vcom.XUSB_BUTTON, Any]] = {
        vcom.XUSB_BUTTON.XUSB_GAMEPAD_START: libevdev.EV_KEY.BTN_START,
        vcom.XUSB_BUTTON.XUSB_GAMEPAD_BACK: libevdev.EV_KEY.BTN_SELECT,
        vcom.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB: libevdev.EV_KEY.BTN_THUMBL,
        vcom.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB: libevdev.EV_KEY.BTN_THUMBR,
        vcom.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER: libevdev.EV_KEY.BTN_TL,
        vcom.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER: libevdev.EV_KEY.BTN_TR,
        vcom.XUSB_BUTTON.XUSB_GAMEPAD_GUIDE: libevdev.EV_KEY.BTN_MODE,
        vcom.XUSB_BUTTON.XUSB_GAMEPAD_A: libevdev.EV_KEY.BTN_SOUTH,
        vcom.XUSB_BUTTON.XUSB_GAMEPAD_B: libevdev.EV_KEY.BTN_EAST,
        vcom.XUSB_BUTTON.XUSB_GAMEPAD_X: libevdev.EV_KEY.BTN_NORTH,
        vcom.XUSB_BUTTON.XUSB_GAMEPAD_Y: libevdev.EV_KEY.BTN_WEST,
    }

    def __init__(self) -> None:
        super().__init__()
        self.device.name = "Xbox 360 Controller"

        self.device.enable(libevdev.EV_KEY.BTN_SOUTH)
        self.device.enable(libevdev.EV_KEY.BTN_EAST)
        self.device.enable(libevdev.EV_KEY.BTN_NORTH)
        self.device.enable(libevdev.EV_KEY.BTN_WEST)

        self.device.enable(libevdev.EV_KEY.BTN_TL)
        self.device.enable(libevdev.EV_KEY.BTN_TR)

        self.device.enable(libevdev.EV_KEY.BTN_SELECT)
        self.device.enable(libevdev.EV_KEY.BTN_START)

        self.device.enable(libevdev.EV_KEY.BTN_MODE)

        self.device.enable(libevdev.EV_KEY.BTN_THUMBL)
        self.device.enable(libevdev.EV_KEY.BTN_THUMBR)

        self.device.enable(
            libevdev.EV_ABS.ABS_X,
            libevdev.InputAbsInfo(minimum=-32768, maximum=32767, fuzz=16, flat=128),
        )
        self.device.enable(
            libevdev.EV_ABS.ABS_Y,
            libevdev.InputAbsInfo(minimum=-32768, maximum=32767, fuzz=16, flat=128),
        )
        self.device.enable(
            libevdev.EV_ABS.ABS_RX,
            libevdev.InputAbsInfo(minimum=-32768, maximum=32767, fuzz=16, flat=128),
        )
        self.device.enable(
            libevdev.EV_ABS.ABS_RY,
            libevdev.InputAbsInfo(minimum=-32768, maximum=32767, fuzz=16, flat=128),
        )
        self.device.enable(libevdev.EV_ABS.ABS_Z, libevdev.InputAbsInfo(minimum=0, maximum=1023))
        self.device.enable(libevdev.EV_ABS.ABS_RZ, libevdev.InputAbsInfo(minimum=0, maximum=1023))

        self.device.enable(libevdev.EV_ABS.ABS_HAT0X, libevdev.InputAbsInfo(minimum=-1, maximum=1))
        self.device.enable(libevdev.EV_ABS.ABS_HAT0Y, libevdev.InputAbsInfo(minimum=-1, maximum=1))

        self.device.enable(libevdev.EV_FF.FF_RUMBLE)
        self.device.enable(libevdev.EV_FF.FF_PERIODIC)
        self.device.enable(libevdev.EV_FF.FF_SQUARE)
        self.device.enable(libevdev.EV_FF.FF_TRIANGLE)
        self.device.enable(libevdev.EV_FF.FF_SINE)
        self.device.enable(libevdev.EV_FF.FF_GAIN)

        self.uinput = self.device.create_uinput_device()

        self.report = self.get_default_report()
        self.update()
        logger.debug("VX360Gamepad created on {}", self.uinput.devnode)

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
        for btn, key in self.XUSB_BUTTON_TO_EV_KEY.items():
            self.uinput.send_events([
                libevdev.InputEvent(key, value=int(bool(self.report.wButtons & btn))),
            ])

        self.uinput.send_events([
            libevdev.InputEvent(libevdev.EV_ABS.ABS_X, value=self.report.sThumbLX),
            libevdev.InputEvent(libevdev.EV_ABS.ABS_Y, value=self.report.sThumbLY),
            libevdev.InputEvent(libevdev.EV_ABS.ABS_RX, value=self.report.sThumbRX),
            libevdev.InputEvent(libevdev.EV_ABS.ABS_RY, value=self.report.sThumbRY),
            libevdev.InputEvent(libevdev.EV_ABS.ABS_Z, value=self.report.bLeftTrigger * 4),
            libevdev.InputEvent(libevdev.EV_ABS.ABS_RZ, value=self.report.bRightTrigger * 4),
        ])

        hat0x_value = int(bool(self.report.wButtons & vcom.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT)) - int(
            bool(self.report.wButtons & vcom.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT)
        )
        hat0y_value = int(bool(self.report.wButtons & vcom.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN)) - int(
            bool(self.report.wButtons & vcom.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP)
        )
        self.uinput.send_events([
            libevdev.InputEvent(libevdev.EV_ABS.ABS_HAT0X, value=hat0x_value),
            libevdev.InputEvent(libevdev.EV_ABS.ABS_HAT0Y, value=hat0y_value),
        ])

        self.uinput.send_events([libevdev.InputEvent(libevdev.EV_SYN.SYN_REPORT, value=0)])

    def target_alloc(self) -> Any:
        return self.uinput


class VDS4Gamepad(VGamepad):
    """Virtual DualShock 4 gamepad (Linux / uinput)."""

    DS4_BUTTON_TO_EV_KEY: ClassVar[dict[vcom.DS4_BUTTONS, Any]] = {
        vcom.DS4_BUTTONS.DS4_BUTTON_THUMB_RIGHT: libevdev.EV_KEY.BTN_THUMBR,
        vcom.DS4_BUTTONS.DS4_BUTTON_THUMB_LEFT: libevdev.EV_KEY.BTN_THUMBL,
        vcom.DS4_BUTTONS.DS4_BUTTON_OPTIONS: libevdev.EV_KEY.BTN_SELECT,
        vcom.DS4_BUTTONS.DS4_BUTTON_SHARE: libevdev.EV_KEY.BTN_START,
        vcom.DS4_BUTTONS.DS4_BUTTON_TRIGGER_RIGHT: libevdev.EV_KEY.BTN_TR2,
        vcom.DS4_BUTTONS.DS4_BUTTON_TRIGGER_LEFT: libevdev.EV_KEY.BTN_TL2,
        vcom.DS4_BUTTONS.DS4_BUTTON_SHOULDER_RIGHT: libevdev.EV_KEY.BTN_TR,
        vcom.DS4_BUTTONS.DS4_BUTTON_SHOULDER_LEFT: libevdev.EV_KEY.BTN_TL,
        vcom.DS4_BUTTONS.DS4_BUTTON_TRIANGLE: libevdev.EV_KEY.BTN_NORTH,
        vcom.DS4_BUTTONS.DS4_BUTTON_CIRCLE: libevdev.EV_KEY.BTN_EAST,
        vcom.DS4_BUTTONS.DS4_BUTTON_CROSS: libevdev.EV_KEY.BTN_SOUTH,
        vcom.DS4_BUTTONS.DS4_BUTTON_SQUARE: libevdev.EV_KEY.BTN_WEST,
    }

    DS4_SPECIAL_BUTTON_TO_EV_KEY: ClassVar[dict[vcom.DS4_SPECIAL_BUTTONS, Any]] = {
        vcom.DS4_SPECIAL_BUTTONS.DS4_SPECIAL_BUTTON_PS: libevdev.EV_KEY.BTN_MODE,
        vcom.DS4_SPECIAL_BUTTONS.DS4_SPECIAL_BUTTON_TOUCHPAD: libevdev.EV_KEY.BTN_TOUCH,
    }

    DPAD_MAPPING: ClassVar[dict[vcom.DS4_DPAD_DIRECTIONS, tuple[int, int]]] = {
        vcom.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NONE: (0, 0),
        vcom.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_EAST: (1, 0),
        vcom.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_SOUTHEAST: (1, 1),
        vcom.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_SOUTH: (0, 1),
        vcom.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_SOUTHWEST: (-1, 1),
        vcom.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_WEST: (-1, 0),
        vcom.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NORTHWEST: (-1, -1),
        vcom.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NORTH: (0, -1),
        vcom.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NORTHEAST: (1, -1),
    }

    def __init__(self) -> None:
        super().__init__()

        self.dpad_direction = vcom.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NONE

        self.device.name = "Sony Interactive Entertainment Wireless Controller"

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

        self.device.enable(libevdev.EV_ABS.ABS_X, libevdev.InputAbsInfo(minimum=0, maximum=255, value=127))
        self.device.enable(libevdev.EV_ABS.ABS_Y, libevdev.InputAbsInfo(minimum=0, maximum=255, value=127))
        self.device.enable(libevdev.EV_ABS.ABS_RX, libevdev.InputAbsInfo(minimum=0, maximum=255, value=127))
        self.device.enable(libevdev.EV_ABS.ABS_RY, libevdev.InputAbsInfo(minimum=0, maximum=255, value=127))
        self.device.enable(libevdev.EV_ABS.ABS_HAT0X, libevdev.InputAbsInfo(minimum=-1, maximum=1, value=0))
        self.device.enable(libevdev.EV_ABS.ABS_HAT0Y, libevdev.InputAbsInfo(minimum=-1, maximum=1, value=0))

        self.device.enable(libevdev.EV_ABS.ABS_Z, libevdev.InputAbsInfo(minimum=0, maximum=255))
        self.device.enable(libevdev.EV_ABS.ABS_RZ, libevdev.InputAbsInfo(minimum=0, maximum=255))

        self.device.enable(libevdev.EV_FF.FF_RUMBLE)
        self.device.enable(libevdev.EV_FF.FF_PERIODIC)
        self.device.enable(libevdev.EV_FF.FF_SQUARE)
        self.device.enable(libevdev.EV_FF.FF_TRIANGLE)
        self.device.enable(libevdev.EV_FF.FF_SINE)
        self.device.enable(libevdev.EV_FF.FF_GAIN)

        self.uinput = self.device.create_uinput_device()

        self.report = self.get_default_report()
        self.update()
        logger.debug("VDS4Gamepad created on {}", self.uinput.devnode)

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
        self.dpad_direction = direction

    def update(self) -> None:
        """Send the current report to the virtual device."""
        for btn, key in self.DS4_BUTTON_TO_EV_KEY.items():
            self.uinput.send_events([
                libevdev.InputEvent(key, value=int(bool(self.report.wButtons & btn))),
            ])

        for btn, key in self.DS4_SPECIAL_BUTTON_TO_EV_KEY.items():
            self.uinput.send_events([
                libevdev.InputEvent(key, value=int(bool(self.report.bSpecial & btn))),
            ])

        self.uinput.send_events([
            libevdev.InputEvent(libevdev.EV_ABS.ABS_X, value=self.report.bThumbLX),
            libevdev.InputEvent(libevdev.EV_ABS.ABS_Y, value=self.report.bThumbLY),
            libevdev.InputEvent(libevdev.EV_ABS.ABS_RX, value=self.report.bThumbRX),
            libevdev.InputEvent(libevdev.EV_ABS.ABS_RY, value=self.report.bThumbRY),
            libevdev.InputEvent(libevdev.EV_ABS.ABS_Z, value=self.report.bTriggerL),
            libevdev.InputEvent(libevdev.EV_ABS.ABS_RZ, value=self.report.bTriggerR),
        ])

        hat0x_value, hat0y_value = self.DPAD_MAPPING[self.dpad_direction]

        self.uinput.send_events([
            libevdev.InputEvent(libevdev.EV_ABS.ABS_HAT0X, value=hat0x_value),
            libevdev.InputEvent(libevdev.EV_ABS.ABS_HAT0Y, value=hat0y_value),
        ])

        self.uinput.send_events([libevdev.InputEvent(libevdev.EV_SYN.SYN_REPORT, value=0)])

    def update_extended_report(self, extended_report: vcom.DS4_REPORT_EX) -> None:
        """Send a DS4_REPORT_EX to the virtual device.

        On Linux the standard gamepad fields are extracted and sent via
        the normal update path.  Gyro, accelerometer, and touchpad
        coordinate data are not emitted as evdev events.
        """
        sub = extended_report.Report

        self.report.bThumbLX = sub.bThumbLX
        self.report.bThumbLY = sub.bThumbLY
        self.report.bThumbRX = sub.bThumbRX
        self.report.bThumbRY = sub.bThumbRY
        self.report.wButtons = sub.wButtons
        self.report.bSpecial = sub.bSpecial
        self.report.bTriggerL = sub.bTriggerL
        self.report.bTriggerR = sub.bTriggerR

        self.dpad_direction = vcom.DS4_DPAD_DIRECTIONS(sub.wButtons & 0xF)

        self.update()

    def target_alloc(self) -> Any:
        return self.uinput
