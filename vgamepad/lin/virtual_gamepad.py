"""
VGamepad API (Linux)

All API docstrings are defined in vgamepad.api
"""

from abc import ABC
import gc
import libevdev
import itertools
from inspect import signature

import vgamepad.api as api
from vgamepad.lin.force_feedback import ForceFeedback


_INDEX_COUNTER = itertools.count(1)
_VIGEMBUS_DEFAULT_REPORT = bytes([
    0x82, 0x7F, 0x7E, 0x80, 0x08, 0x00, 0x58,
    0x00, 0x00, 0xFD, 0x63, 0x06, 0x03, 0x00, 0xFE,
    0xFF, 0xFC, 0xFF, 0x79, 0xFD, 0x1B, 0x14, 0xD1,
    0xE9, 0x00, 0x00, 0x00, 0x00, 0x00, 0x1B, 0x00,
    0x00, 0x00, 0x00, 0x80, 0x00, 0x00, 0x00, 0x80,
    0x00, 0x00, 0x00, 0x00, 0x80, 0x00, 0x00, 0x00,
    0x80, 0x00, 0x00, 0x00, 0x00, 0x80, 0x00, 0x00,
    0x00, 0x80, 0x00, 0x00, 0x00, 0x00, 0x80, 0x00,
])


class NotificationCallback:

    def __init__(self, callback, light):
        self._callback = callback
        self._light = light

    def __call__(self, strong, weak):
        # Same arguments as the ViGEm callbacks: client, target, large motor, small motor, LED / lightbar, user data
        self._callback(None, None, strong >> 8, weak >> 8, self._light, None)


class VGamepad(ABC):

    def __init__(self, vid=None, pid=None, notification_light=None):
        self.device = libevdev.Device()
        self.device.name = 'Virtual Gamepad'
        self._vid = vid
        self._pid = pid
        self._index = next(_INDEX_COUNTER)
        self.uinput = None
        self._notifications_registered = False
        self._ff = None
        self._uinput_file = None
        self._notification_light = notification_light

    def __del__(self):
        self._release_devices()
        if gc is not None:
            gc.collect()

    def _release_devices(self):
        if self._ff is not None:
            self._ff.close()
            self._ff = None
        self.device = None
        self.uinput = None
        if self._uinput_file is not None:
            self._uinput_file.close()
            self._uinput_file = None

    def _create_uinput_device(self, device=None, uinput_fd=None):
        """
        Overrides the device VID and PID and returns its uinput.
        Must be called after self.device is fully configured.
        """
        device = self.device if device is None else device
        if self._vid is not None:
            device.id = {'vendor': self._vid}
        if self._pid is not None:
            device.id = {'product': self._pid}
        return device.create_uinput_device(uinput_fd)
    
    def _create_gamepad_uinput_device(self):
        """
        Creates the main uinput device, listening for notifications.
        """
        self.device.enable(libevdev.EV_FF.FF_RUMBLE)
        self._uinput_file = open('/dev/uinput', 'r+b', buffering=0)
        uinput = self._create_uinput_device(uinput_fd=self._uinput_file)
        self._ff = ForceFeedback(self._uinput_file)
        return uinput

    def get_vid(self):
        return self.uinput.id['vendor']

    def get_pid(self):
        return self.uinput.id['product']

    def get_index(self):
        return self._index
    
    def unregister_notification(self):
        self._ff.set_rumble_callback(None)


class VX360Gamepad(VGamepad, api.VX360Gamepad):
    """
    Virtual Xbox360 gamepad
    """

    def __init__(self, vid=None, pid=None):
        VGamepad.__init__(self, vid, pid, notification_light=0)

        self.device.name = 'Microsoft X-Box 360 pad'

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

        self.uinput = self._create_gamepad_uinput_device()
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
        self.uinput.send_events(events)
    
    def register_notification(self, callback_function):
        """
        Note: the callback must not call methods of the gamepad.
        """
        if self._notifications_registered:
            raise RuntimeError("Cannot register a callback more than once per gamepad.")
        if not api.check_callback_signature(callback_function):
            raise TypeError("Needed callback function signature: {}, but got: {}".format(signature(api.dummy_x360_callback), signature(callback_function)))
        self._ff.set_rumble_callback(NotificationCallback(callback_function, self._notification_light))
        self._notifications_registered = True


class VDS4Gamepad(VGamepad, api.VDS4Gamepad):
    """
    Virtual DualShock 4 gamepad
    """

    def __init__(self, vid=None, pid=None):
        VGamepad.__init__(self, vid, pid, notification_light=api.DS4_LIGHTBAR_COLOR(0, 0, 0))

        self.gyro_calibration = ((0, 1105920, 17676), (0, 1105920, 17771), (0, 1105920, 17786))
        self.accel_calibration = ((-297, 16384, 16209), (-42, 16384, 16148), (-512, 16384, 15988))

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
            # api.DS4_SPECIAL_BUTTONS.DS4_SPECIAL_BUTTON_TOUCHPAD: libevdev.EV_KEY.BTN_TOUCH,
        }

        # DS4 controllers create 3 evdev files on Linux:
        # 1: Sony Interactive Entertainment Wireless Controller
        # 2: Sony Interactive Entertainment Wireless Controller Motion Sensors
        # 3: Sony Interactive Entertainment Wireless Controller Touchpad

        # Gamepad:
        self.device.name = 'Sony Interactive Entertainment Wireless Controller'  # 'PS4 Controller'
        self.device.id = {
            'bustype': 0x0003,  # BUS_USB
            'vendor': 0x054C,   # Sony
            'product': 0x09CC,  # DualShock 4 v2
            'version': 0x8111, # FIXME: changed from 0x0100, double-check that this is correct (hid-playstation)
        }
        for key in (*self.DS4_BUTTON_TO_EV_KEY.values(), *self.DS4_SPECIAL_BUTTON_TO_EV_KEY.values()):
            self.device.enable(key)  # buttons
        for axis in (libevdev.EV_ABS.ABS_X, libevdev.EV_ABS.ABS_Y, libevdev.EV_ABS.ABS_RX, libevdev.EV_ABS.ABS_RY):
            self.device.enable(axis, libevdev.InputAbsInfo(minimum=0, maximum=255))  # axes
        for axis in (libevdev.EV_ABS.ABS_Z, libevdev.EV_ABS.ABS_RZ):
            self.device.enable(axis, libevdev.InputAbsInfo(minimum=0, maximum=255))  # triggers
        for axis in (libevdev.EV_ABS.ABS_HAT0X, libevdev.EV_ABS.ABS_HAT0Y):
            self.device.enable(axis, libevdev.InputAbsInfo(minimum=-1, maximum=1))  # hat
        self.uinput = self._create_gamepad_uinput_device()

        # Motion sensors
        self.sensors_device = libevdev.Device()
        self.sensors_device.name = 'Sony Interactive Entertainment Wireless Controller Motion Sensors'
        self.sensors_device.id = self.device.id
        self.sensors_device.enable(libevdev.INPUT_PROP_ACCELEROMETER)
        self.sensors_device.enable(libevdev.EV_MSC.MSC_TIMESTAMP)
        for axis in (libevdev.EV_ABS.ABS_X, libevdev.EV_ABS.ABS_Y, libevdev.EV_ABS.ABS_Z):
            self.sensors_device.enable(axis, libevdev.InputAbsInfo(minimum=-4 * 8192, maximum=4 * 8192, fuzz=16, resolution=8192))
        for axis in (libevdev.EV_ABS.ABS_RX, libevdev.EV_ABS.ABS_RY, libevdev.EV_ABS.ABS_RZ):
            self.sensors_device.enable(axis, libevdev.InputAbsInfo(minimum=-2048 * 1024, maximum=2048 * 1024, fuzz=16, resolution=1024))
        self.sensors_uinput = self._create_uinput_device(self.sensors_device)

        # Touchpad
        self.touchpad_device = libevdev.Device()
        self.touchpad_device.name = 'Sony Interactive Entertainment Wireless Controller Touchpad'
        self.touchpad_device.id = self.device.id
        self.touchpad_device.enable(libevdev.INPUT_PROP_POINTER)
        self.touchpad_device.enable(libevdev.INPUT_PROP_BUTTONPAD)
        for key in (libevdev.EV_KEY.BTN_LEFT, libevdev.EV_KEY.BTN_TOUCH, libevdev.EV_KEY.BTN_TOOL_FINGER, libevdev.EV_KEY.BTN_TOOL_DOUBLETAP):
            self.touchpad_device.enable(key)
        self.touchpad_device.enable(libevdev.EV_ABS.ABS_MT_SLOT, libevdev.InputAbsInfo(minimum=0, maximum=1))
        self.touchpad_device.enable(libevdev.EV_ABS.ABS_MT_TRACKING_ID, libevdev.InputAbsInfo(minimum=0, maximum=0xFFFF))
        for mt_axis, axis, size in ((libevdev.EV_ABS.ABS_MT_POSITION_X, libevdev.EV_ABS.ABS_X, 1920), (libevdev.EV_ABS.ABS_MT_POSITION_Y, libevdev.EV_ABS.ABS_Y, 942)):
            self.touchpad_device.enable(mt_axis, libevdev.InputAbsInfo(minimum=0, maximum=size - 1))
            self.touchpad_device.enable(axis, libevdev.InputAbsInfo(minimum=0, maximum=size - 1))
        self.touchpad_uinput = self._create_uinput_device(self.touchpad_device)

        self._sensor_timestamp_us = 0  # accumulated from wTimestamp
        self._prev_sensor_timestamp = None

        # Initial motion sensor state of a ViGEmBus virtual DualShock 4 (gravity reading):
        self._send_sensor_events(api.DS4_REPORT_EX.from_buffer_copy(_VIGEMBUS_DEFAULT_REPORT).Report)

        api.VDS4Gamepad.__init__(self)

    def _release_devices(self):
        VGamepad._release_devices(self)
        self.sensors_device = None
        self.sensors_uinput = None
        self.touchpad_device = None
        self.touchpad_uinput = None

    def get_type(self):
        return api.VIGEM_TARGET_TYPE.DualShock4Wired
    
    def _send_gamepad_events(self, report):
        hat_x, hat_y = self.dpad_mapping.get(report.wButtons & 0x0F, (0, 0))  # 8 to 15 = released
        self.uinput.send_events([
            *(libevdev.InputEvent(key, value=int(bool(report.wButtons & btn))) for btn, key in self.DS4_BUTTON_TO_EV_KEY.items()),
            *(libevdev.InputEvent(key, value=int(bool(report.bSpecial & btn))) for btn, key in self.DS4_SPECIAL_BUTTON_TO_EV_KEY.items()),
            libevdev.InputEvent(libevdev.EV_ABS.ABS_X, value=report.bThumbLX),
            libevdev.InputEvent(libevdev.EV_ABS.ABS_Y, value=report.bThumbLY),
            libevdev.InputEvent(libevdev.EV_ABS.ABS_RX, value=report.bThumbRX),
            libevdev.InputEvent(libevdev.EV_ABS.ABS_RY, value=report.bThumbRY),
            libevdev.InputEvent(libevdev.EV_ABS.ABS_Z, value=report.bTriggerL),
            libevdev.InputEvent(libevdev.EV_ABS.ABS_RZ, value=report.bTriggerR),
            libevdev.InputEvent(libevdev.EV_ABS.ABS_HAT0X, value=hat_x),
            libevdev.InputEvent(libevdev.EV_ABS.ABS_HAT0Y, value=hat_y),
            libevdev.InputEvent(libevdev.EV_SYN.SYN_REPORT, value=0),
        ])

    def _send_sensor_events(self, report):
        # calibrated gyro and accelerometer events:
        events = [
            libevdev.InputEvent(axis, value=int((raw - bias) * num / den)) for axis, raw, (bias, num, den) in zip(
            (libevdev.EV_ABS.ABS_RX, libevdev.EV_ABS.ABS_RY, libevdev.EV_ABS.ABS_RZ, libevdev.EV_ABS.ABS_X, libevdev.EV_ABS.ABS_Y, libevdev.EV_ABS.ABS_Z),
            (report.wGyroX, report.wGyroY, report.wGyroZ, report.wAccelX, report.wAccelY, report.wAccelZ), self.gyro_calibration + self.accel_calibration)
        ]
        # wTimestamp in units of 16/3 microseconds (wraps at 65536):
        if self._prev_sensor_timestamp is not None:
            delta = (report.wTimestamp - self._prev_sensor_timestamp) & 0xFFFF
            self._sensor_timestamp_us = (self._sensor_timestamp_us + (delta * 16 + 1) // 3) & 0xFFFFFFFF
        self._prev_sensor_timestamp = report.wTimestamp
        timestamp_us = self._sensor_timestamp_us
        events += [
            libevdev.InputEvent(
                libevdev.EV_MSC.MSC_TIMESTAMP,
                value=timestamp_us - (1 << 32) if timestamp_us >= (1 << 31) else timestamp_us
            ),
            libevdev.InputEvent(libevdev.EV_SYN.SYN_REPORT, value=0),
        ]
        self.sensors_uinput.send_events(events)

    def _send_touchpad_events(self, report, touches=()):
        events = []
        for touch in touches:
            positions = []
            for slot, (contact, data) in enumerate(
                ((touch.bIsUpTrackingNum1, touch.bTouchData1), (touch.bIsUpTrackingNum2, touch.bTouchData2))
            ):
                events.append(libevdev.InputEvent(libevdev.EV_ABS.ABS_MT_SLOT, value=slot))
                if contact & 0x80:  # finger not touching
                    events.append(libevdev.InputEvent(libevdev.EV_ABS.ABS_MT_TRACKING_ID, value=-1))
                else:
                    x = data[0] | (data[1] & 0x0F) << 8
                    y = data[1] >> 4 | data[2] << 4
                    positions.append((x, y))
                    events += [
                        libevdev.InputEvent(libevdev.EV_ABS.ABS_MT_TRACKING_ID, value=contact & 0x7F),
                        libevdev.InputEvent(libevdev.EV_ABS.ABS_MT_POSITION_X, value=x),
                        libevdev.InputEvent(libevdev.EV_ABS.ABS_MT_POSITION_Y, value=y),
                    ]
            events += [
                libevdev.InputEvent(libevdev.EV_KEY.BTN_TOUCH, value=int(len(positions) > 0)),
                libevdev.InputEvent(libevdev.EV_KEY.BTN_TOOL_FINGER, value=int(len(positions) == 1)),
                libevdev.InputEvent(libevdev.EV_KEY.BTN_TOOL_DOUBLETAP, value=int(len(positions) == 2)),
            ]
            if positions:
                events += [
                    libevdev.InputEvent(libevdev.EV_ABS.ABS_X, value=positions[0][0]),
                    libevdev.InputEvent(libevdev.EV_ABS.ABS_Y, value=positions[0][1]),
                ]
        touchpad_click = report.bSpecial & api.DS4_SPECIAL_BUTTONS.DS4_SPECIAL_BUTTON_TOUCHPAD
        events += [
            libevdev.InputEvent(libevdev.EV_KEY.BTN_LEFT, value=int(bool(touchpad_click))),
            libevdev.InputEvent(libevdev.EV_SYN.SYN_REPORT, value=0),
        ]
        self.touchpad_uinput.send_events(events)

    def update_from_report(self, report):
        self._send_gamepad_events(report)
        self._send_touchpad_events(report)

    def update_from_extended_report(self, extended_report):
        report = extended_report.Report
        self._send_gamepad_events(report)
        self._send_sensor_events(report)
        touches = (report.sCurrentTouch, *report.sPreviousTouch)[:min(report.bTouchPacketsN, 3)]
        self._send_touchpad_events(report, touches)

    def register_notification(self, callback_function):
        """
        Note: the callback must not call methods of the gamepad.
        """
        if self._notifications_registered:
            raise RuntimeError("Cannot register a callback more than once per gamepad.")
        if not api.check_callback_signature(callback_function):
            raise TypeError("Needed callback function signature: {}, but got: {}".format(signature(api.dummy_ds4_callback), signature(callback_function)))
        self._ff.set_rumble_callback(NotificationCallback(callback_function, self._notification_light))
        self._notifications_registered = True
