"""
VGamepad API (Linux)
"""
from abc import ABC, abstractmethod
import libevdev
import vgamepad.win.vigem_commons as vcom

import contextlib
import ctypes
import fcntl
import os
import select
import struct
import threading
import warnings
from inspect import signature


def _open_uinput_host_file():
    for path in ("/dev/uinput", "/dev/input/uinput"):
        try:
            return open(path, "rb+", buffering=0)
        except OSError:
            continue
    return None


def _uinput_kernel_fd(uinput):
    """Kernel fd for FF ioctls (Device._uinput.fd), not a second event devnode open."""
    inner = getattr(uinput, "_uinput", None)
    if inner is not None:
        fo = getattr(inner, "fd", None)
        if fo is not None:
            fn = getattr(fo, "fileno", None)
            if callable(fn):
                with contextlib.suppress(Exception):
                    n = int(fn())
                    if n >= 0:
                        return n
    for name in ("fd", "_fd", "_uinput_fd", "input_fd", "device_fd"):
        with contextlib.suppress(Exception):
            c = getattr(uinput, name, None)
            if isinstance(c, int) and c >= 0:
                return c
            if c is not None:
                fn = getattr(c, "fileno", None)
                if callable(fn):
                    with contextlib.suppress(Exception):
                        n = int(fn())
                        if n >= 0:
                            return n
    fileno = getattr(uinput, "fileno", None)
    if callable(fileno):
        with contextlib.suppress(Exception):
            n = int(fileno())
            if n >= 0:
                return n
    return None


def _ioc(direction, ioc_type, nr, size):
    return (direction << 30) | (ioc_type << 8) | (nr << 0) | (size << 16)


def _iowr(ioc_type, nr, size):
    return _ioc(3, ioc_type, nr, size)


def _iow(ioc_type, nr, size):
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
_INPUT_EVENT_FORMAT = "llHHi"
_INPUT_EVENT_SIZE = struct.calcsize(_INPUT_EVENT_FORMAT)


class _FFUpload(ctypes.Structure):
    _fields_ = [
        ("request_id", ctypes.c_uint32),
        ("retval", ctypes.c_int32),
        ("effect", ctypes.c_ubyte * _FF_EFFECT_SIZE),
        ("old", ctypes.c_ubyte * _FF_EFFECT_SIZE),
    ]


class _FFErase(ctypes.Structure):
    _fields_ = [
        ("request_id", ctypes.c_uint32),
        ("retval", ctypes.c_int32),
        ("effect_id", ctypes.c_uint32),
    ]


def _parse_ff_rumble(raw_bytes):
    if len(raw_bytes) < _RUMBLE_WEAK_OFFSET + 2:
        return None, None
    effect_type = struct.unpack_from("<H", raw_bytes, 0)[0]
    if effect_type != _FF_RUMBLE:
        return None, None
    strong, weak = struct.unpack_from("<HH", raw_bytes, _RUMBLE_STRONG_OFFSET)
    return strong, weak


def _create_uinput(device, host_file):
    if host_file is not None:
        return device.create_uinput_device(uinput_fd=host_file)
    warnings.warn(
        "Could not open /dev/uinput (permissions?). Using libevdev managed mode; "
        "force-feedback notifications will not work.",
        stacklevel=2,
    )
    return device.create_uinput_device()


class VGamepad(ABC):

    def __init__(self):
        self.device = libevdev.Device()
        self.device.name = 'Virtual Gamepad'

        self._uinput_host = None
        self._ff_thread = None
        self._ff_stop = threading.Event()
        self._ff_callback = None
        self._ff_effects = {}

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


    def register_notification(self, callback_function):
        """
        Register a callback for force-feedback (rumble) on Linux.
        Uses the same uinput kernel fd as libevdev (do not re-open the event devnode).
        """
        if not vcom.notification_callback_matches(callback_function):
            raise TypeError(
                "Needed callback with six parameters "
                "(client, target, large_motor, small_motor, led_number, user_data); "
                "got: {}".format(signature(callback_function))
            )
        self._ff_callback = callback_function
        if self._ff_thread is not None:
            return
        fd = _uinput_kernel_fd(self.uinput)
        if fd is None:
            warnings.warn(
                "Force-feedback notifications unavailable (no uinput kernel fd).",
                stacklevel=2,
            )
            return
        self._ff_stop.clear()
        self._ff_thread = threading.Thread(
            target=self._ff_reader_loop, args=(fd, False), daemon=True
        )
        self._ff_thread.start()

    def _ff_reader_loop(self, fd, own_fd):
        try:
            while not self._ff_stop.is_set():
                ready, _, _ = select.select([fd], [], [], 0.1)
                if not ready:
                    continue
                try:
                    data = os.read(fd, _INPUT_EVENT_SIZE)
                except OSError:
                    continue
                if len(data) < _INPUT_EVENT_SIZE:
                    continue
                _sec, _usec, ev_type, ev_code, ev_value = struct.unpack(
                    _INPUT_EVENT_FORMAT, data
                )
                if ev_type == _EV_FF and ev_code in self._ff_effects:
                    strong, weak = self._ff_effects[ev_code]
                    large_motor = (strong * 255) // 65535 if strong else 0
                    small_motor = (weak * 255) // 65535 if weak else 0
                    if self._ff_callback:
                        try:
                            self._ff_callback(None, None, large_motor, small_motor, 0, None)
                        except Exception:
                            pass
                elif ev_type == _EV_UINPUT:
                    if ev_code == _UI_FF_UPLOAD:
                        self._handle_ff_upload(fd, ev_value)
                    elif ev_code == _UI_FF_ERASE:
                        self._handle_ff_erase(fd, ev_value)
        finally:
            if own_fd:
                with contextlib.suppress(OSError):
                    os.close(fd)

    def _handle_ff_upload(self, fd, request_id):
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
            self._ff_effects[effect_id] = (strong, weak)
        upload.retval = 0
        with contextlib.suppress(OSError):
            fcntl.ioctl(fd, UI_END_FF_UPLOAD, upload)

    def _handle_ff_erase(self, fd, request_id):
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

    def unregister_notification(self):
        self._ff_callback = None
        self._ff_stop.set()
        if self._ff_thread is not None:
            self._ff_thread.join(timeout=2.0)
            self._ff_thread = None
        self._ff_effects.clear()

    def __del__(self):
        self._ff_stop.set()
        if self._ff_thread is not None:
            self._ff_thread.join(timeout=1.0)
        with contextlib.suppress(Exception):
            self.uinput = None
        uih = getattr(self, "_uinput_host", None)
        if uih is not None:
            with contextlib.suppress(Exception):
                uih.close()
            with contextlib.suppress(Exception):
                self._uinput_host = None

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


        self.device.enable(libevdev.EV_FF.FF_RUMBLE)
        self.device.enable(libevdev.EV_FF.FF_PERIODIC)
        self.device.enable(libevdev.EV_FF.FF_SQUARE)
        self.device.enable(libevdev.EV_FF.FF_TRIANGLE)
        self.device.enable(libevdev.EV_FF.FF_SINE)
        self.device.enable(libevdev.EV_FF.FF_GAIN)

        self._uinput_host = _open_uinput_host_file()
        self.uinput = _create_uinput(self.device, self._uinput_host)

        self.report = self.get_default_report()
        self.update()

    XUSB_BUTTON_TO_EV_KEY = {
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

        # Spoof input_id so SDL2 recognizes DS4 via SDL_GameControllerDB
        self.device.id = {
            'bustype': 0x0003,  # BUS_USB
            'vendor': 0x054C,   # Sony
            'product': 0x09CC,  # DualShock 4 v2
            'version': 0x0100,
        }

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
            vcom.DS4_BUTTONS.DS4_BUTTON_TRIGGER_RIGHT: libevdev.EV_KEY.BTN_TR2,
            vcom.DS4_BUTTONS.DS4_BUTTON_TRIGGER_LEFT: libevdev.EV_KEY.BTN_TL2,
            vcom.DS4_BUTTONS.DS4_BUTTON_SHOULDER_RIGHT: libevdev.EV_KEY.BTN_TR,
            vcom.DS4_BUTTONS.DS4_BUTTON_SHOULDER_LEFT: libevdev.EV_KEY.BTN_TL,
            vcom.DS4_BUTTONS.DS4_BUTTON_TRIANGLE: libevdev.EV_KEY.BTN_NORTH,
            vcom.DS4_BUTTONS.DS4_BUTTON_CIRCLE: libevdev.EV_KEY.BTN_EAST,
            vcom.DS4_BUTTONS.DS4_BUTTON_CROSS: libevdev.EV_KEY.BTN_SOUTH,
            vcom.DS4_BUTTONS.DS4_BUTTON_SQUARE: libevdev.EV_KEY.BTN_WEST,
        }

        self.DS4_SPECIAL_BUTTON_TO_EV_KEY = {
            vcom.DS4_SPECIAL_BUTTONS.DS4_SPECIAL_BUTTON_PS: libevdev.EV_KEY.BTN_MODE,
            vcom.DS4_SPECIAL_BUTTONS.DS4_SPECIAL_BUTTON_TOUCHPAD: libevdev.EV_KEY.BTN_TOUCH,
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
        self.device.enable(libevdev.EV_ABS.ABS_X, libevdev.InputAbsInfo(minimum=0, maximum=255, value=127))
        self.device.enable(libevdev.EV_ABS.ABS_Y, libevdev.InputAbsInfo(minimum=0, maximum=255, value=127))
        self.device.enable(libevdev.EV_ABS.ABS_RX, libevdev.InputAbsInfo(minimum=0, maximum=255, value=127))
        self.device.enable(libevdev.EV_ABS.ABS_RY, libevdev.InputAbsInfo(minimum=0, maximum=255, value=127))
        self.device.enable(libevdev.EV_ABS.ABS_HAT0X, libevdev.InputAbsInfo(minimum=-1, maximum=1, value=0))
        self.device.enable(libevdev.EV_ABS.ABS_HAT0Y, libevdev.InputAbsInfo(minimum=-1, maximum=1, value=0))

        # Enable triggers
        self.device.enable(libevdev.EV_ABS.ABS_Z, libevdev.InputAbsInfo(minimum=0, maximum=255))
        self.device.enable(libevdev.EV_ABS.ABS_RZ, libevdev.InputAbsInfo(minimum=0, maximum=255))


        self.device.enable(libevdev.EV_FF.FF_RUMBLE)
        self.device.enable(libevdev.EV_FF.FF_PERIODIC)
        self.device.enable(libevdev.EV_FF.FF_SQUARE)
        self.device.enable(libevdev.EV_FF.FF_TRIANGLE)
        self.device.enable(libevdev.EV_FF.FF_SINE)
        self.device.enable(libevdev.EV_FF.FF_GAIN)

        self._uinput_host = _open_uinput_host_file()
        self.uinput = _create_uinput(self.device, self._uinput_host)

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

    def update_extended_report(self, extended_report):
        """
        Send DS4_REPORT_EX fields supported on Linux (no gyro/touchpad evdev events).
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

    def target_alloc(self):
        return self.uinput
