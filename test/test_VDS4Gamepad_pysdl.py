import ctypes
import math
import time
import unittest
import platform

import vgamepad as vg

# This test file tests the full extended report capability.
# PySDL2 and an SDL2 binary must be installed to execute this file:
#   pip install pysdl2 pysdl2-dll
# Unlike pygame, SDL does not need a display to read joysticks.

import sdl2


# SDL reports the DS4 differently accross OS because it picks different backends.
# On Windows, ViGEmBus creates a real USB HID device, read by the HIDAPI PS4 driver.
# On Linux, vgamepad creates uinput (evdev) devices, read by the evdev backend.
# The GameController layer maps both to the same layout (on Linux, through the SDL mapping database).

WAIT_S = 0.1
SYSTEM = platform.system()
STANDARD_GRAVITY = 9.80665

DS4_JOYSTICK_NAME = "PS4 Controller" if SYSTEM == "Windows" else "Sony Interactive Entertainment Wireless Controller"
DS4_NB_BUTTONS = 16 if SYSTEM == "Windows" else 13
DS4_NB_HATS = 0 if SYSTEM == "Windows" else 1

DS4_LEFT_TRIGGER = 4 if SYSTEM == "Windows" else 2
DS4_RIGHT_TRIGGER = 5
DS4_LEFT_JOYSTICK = (0, 1)
DS4_RIGHT_JOYSTICK = (2, 3) if SYSTEM == "Windows" else (3, 4)
DS4_DIRECTIONAL_PAD = (11, 12, 13, 14) if SYSTEM == "Windows" else None

DS4_TEST_BUTTONS = [
    (vg.DS4_BUTTONS.DS4_BUTTON_CROSS, 0),
    (vg.DS4_BUTTONS.DS4_BUTTON_CIRCLE, 1),
    (vg.DS4_BUTTONS.DS4_BUTTON_SQUARE, 2),
    (vg.DS4_BUTTONS.DS4_BUTTON_TRIANGLE, 3),
    (vg.DS4_BUTTONS.DS4_BUTTON_SHARE, 4),
    (vg.DS4_BUTTONS.DS4_BUTTON_OPTIONS, 6),
    (vg.DS4_BUTTONS.DS4_BUTTON_THUMB_LEFT, 7),
    (vg.DS4_BUTTONS.DS4_BUTTON_THUMB_RIGHT, 8),
    (vg.DS4_BUTTONS.DS4_BUTTON_SHOULDER_LEFT, 9),
    (vg.DS4_BUTTONS.DS4_BUTTON_SHOULDER_RIGHT, 10),
    ] if SYSTEM == "Windows" else [
    (vg.DS4_BUTTONS.DS4_BUTTON_CROSS, 0),
    (vg.DS4_BUTTONS.DS4_BUTTON_CIRCLE, 1),
    (vg.DS4_BUTTONS.DS4_BUTTON_SQUARE, 3),
    (vg.DS4_BUTTONS.DS4_BUTTON_TRIANGLE, 2),
    (vg.DS4_BUTTONS.DS4_BUTTON_SHARE, 8),
    (vg.DS4_BUTTONS.DS4_BUTTON_OPTIONS, 9),
    (vg.DS4_BUTTONS.DS4_BUTTON_THUMB_LEFT, 11),
    (vg.DS4_BUTTONS.DS4_BUTTON_THUMB_RIGHT, 12),
    (vg.DS4_BUTTONS.DS4_BUTTON_SHOULDER_LEFT, 4),
    (vg.DS4_BUTTONS.DS4_BUTTON_SHOULDER_RIGHT, 5),
    ]

DS4_TEST_SPECIAL_BUTTONS = [
    (vg.DS4_SPECIAL_BUTTONS.DS4_SPECIAL_BUTTON_PS, 5),
    (vg.DS4_SPECIAL_BUTTONS.DS4_SPECIAL_BUTTON_TOUCHPAD, 15),
    ] if SYSTEM == "Windows" else [  # On Linux, the touchpad click is on the separate touchpad device
    (vg.DS4_SPECIAL_BUTTONS.DS4_SPECIAL_BUTTON_PS, 10),
    ]

DS4_TEST_DIRECTIONAL_PAD = [  # On Windows, SDL detects the directional pad as 4 buttons (up, down, left, right)
    (vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NONE, (0, 0, 0, 0)),
    (vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NORTHWEST, (1, 0, 1, 0)),
    (vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_WEST, (0, 0, 1, 0)),
    (vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_SOUTHWEST, (0, 1, 1, 0)),
    (vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_SOUTH, (0, 1, 0, 0)),
    (vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_SOUTHEAST, (0, 1, 0, 1)),
    (vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_EAST, (0, 0, 0, 1)),
    (vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NORTHEAST, (1, 0, 0, 1)),
    (vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NORTH, (1, 0, 0, 0)),
    ] if SYSTEM == "Windows" else [  # On Linux, the directional pad is a hat
    (vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NONE, sdl2.SDL_HAT_CENTERED),
    (vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NORTHWEST, sdl2.SDL_HAT_LEFTUP),
    (vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_WEST, sdl2.SDL_HAT_LEFT),
    (vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_SOUTHWEST, sdl2.SDL_HAT_LEFTDOWN),
    (vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_SOUTH, sdl2.SDL_HAT_DOWN),
    (vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_SOUTHEAST, sdl2.SDL_HAT_RIGHTDOWN),
    (vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_EAST, sdl2.SDL_HAT_RIGHT),
    (vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NORTHEAST, sdl2.SDL_HAT_RIGHTUP),
    (vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NORTH, sdl2.SDL_HAT_UP),
    ]

# Joystick axes are normalized to [-1.0, 1.0] (SDL value / 32768); triggers rest at -1.0

DS4_TEST_TRIGGER_INT = [
    (0, -1.0),
    (5, -0.96),
    (10, -0.92),
    (63, -0.5),
    (127, 0.0),
    (191, 0.5),
    (255, 1.0),
    ]

DS4_TEST_TRIGGER_FLOAT = [
    (0.0, -1.0),
    (0.5, 0.0),
    (1.0, 1.0),
    ]

DS4_TEST_JOYSTICK_INT = [
    ((0, 127), (-1.0, 0.0)),
    ((63, 63), (-0.5, -0.5)),
    ((127, 0), (0.0, -1.0)),
    ((191, 255), (0.5, 1.0)),
    ((255, 191), (1.0, 0.5)),
    ]

DS4_TEST_JOYSTICK_FLOAT = [
    ((-1.0, 0.0), (-1.0, 0.0)),
    ((-0.5, -0.5), (-0.5, -0.5)),
    ((0.0, -1.0), (0.0, -1.0)),
    ((0.5, 1.0), (0.5, 1.0)),
    ((1.0, 0.5), (1.0, 0.5)),
    ]

DS4_CONTROLLER_NAME = "PS4 Controller"

DS4_CONTROLLER_TEST_BUTTONS = [
    (vg.DS4_BUTTONS.DS4_BUTTON_CROSS, sdl2.SDL_CONTROLLER_BUTTON_A),
    (vg.DS4_BUTTONS.DS4_BUTTON_CIRCLE, sdl2.SDL_CONTROLLER_BUTTON_B),
    (vg.DS4_BUTTONS.DS4_BUTTON_SQUARE, sdl2.SDL_CONTROLLER_BUTTON_X),
    (vg.DS4_BUTTONS.DS4_BUTTON_TRIANGLE, sdl2.SDL_CONTROLLER_BUTTON_Y),
    (vg.DS4_BUTTONS.DS4_BUTTON_SHARE, sdl2.SDL_CONTROLLER_BUTTON_BACK),
    (vg.DS4_BUTTONS.DS4_BUTTON_OPTIONS, sdl2.SDL_CONTROLLER_BUTTON_START),
    (vg.DS4_BUTTONS.DS4_BUTTON_THUMB_LEFT, sdl2.SDL_CONTROLLER_BUTTON_LEFTSTICK),
    (vg.DS4_BUTTONS.DS4_BUTTON_THUMB_RIGHT, sdl2.SDL_CONTROLLER_BUTTON_RIGHTSTICK),
    (vg.DS4_BUTTONS.DS4_BUTTON_SHOULDER_LEFT, sdl2.SDL_CONTROLLER_BUTTON_LEFTSHOULDER),
    (vg.DS4_BUTTONS.DS4_BUTTON_SHOULDER_RIGHT, sdl2.SDL_CONTROLLER_BUTTON_RIGHTSHOULDER),
    ]

DS4_CONTROLLER_TEST_SPECIAL_BUTTONS = [
    (vg.DS4_SPECIAL_BUTTONS.DS4_SPECIAL_BUTTON_PS, sdl2.SDL_CONTROLLER_BUTTON_GUIDE),
    ] + ([
    (vg.DS4_SPECIAL_BUTTONS.DS4_SPECIAL_BUTTON_TOUCHPAD, sdl2.SDL_CONTROLLER_BUTTON_TOUCHPAD),
    ] if SYSTEM == "Windows" else [])  # On Linux, the touchpad click is on the separate touchpad device

DS4_CONTROLLER_DPAD_BUTTONS = (
    sdl2.SDL_CONTROLLER_BUTTON_DPAD_UP,
    sdl2.SDL_CONTROLLER_BUTTON_DPAD_DOWN,
    sdl2.SDL_CONTROLLER_BUTTON_DPAD_LEFT,
    sdl2.SDL_CONTROLLER_BUTTON_DPAD_RIGHT,
    )

DS4_CONTROLLER_TEST_DIRECTIONAL_PAD = [  # (up, down, left, right)
    (vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NONE, (0, 0, 0, 0)),
    (vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NORTHWEST, (1, 0, 1, 0)),
    (vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_WEST, (0, 0, 1, 0)),
    (vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_SOUTHWEST, (0, 1, 1, 0)),
    (vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_SOUTH, (0, 1, 0, 0)),
    (vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_SOUTHEAST, (0, 1, 0, 1)),
    (vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_EAST, (0, 0, 0, 1)),
    (vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NORTHEAST, (1, 0, 0, 1)),
    (vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NORTH, (1, 0, 0, 0)),
    ]

# GameController triggers are normalized to [0.0, 1.0] (SDL value / 32767); they rest at 0.0

DS4_CONTROLLER_TEST_TRIGGER_INT = [
    (0, 0.0),
    (63, 0.25),
    (127, 0.5),
    (191, 0.75),
    (255, 1.0),
    ]

# Calibration of the virtual DualShock 4 (same as vgamepad.lin.virtual_gamepad.VDS4Gamepad):
DS4_ACCEL_BIAS = (-297, -42, -512)
DS4_GYRO_RAW_TO_DEG_S = (1080 / 17676, 1080 / 17771, 1080 / 17786)  # pitch, yaw, roll
DS4_ACCEL_RAW_PER_G = 16209 / 2  # X axis

# Touchpad positions are normalized by SDL as x / 1920, y / 920 (sic: SDL uses 920, not 942)
DS4_TEST_TOUCHPAD = [  # (finger1, finger2), (expected finger 1 (x, y) or None, expected finger 2 (x, y) or None)
    (((960, 460), None), ((0.5, 0.5), None)),
    (((960, 460), (480, 230)), ((0.5, 0.5), (0.25, 0.25))),
    (((0, 0), (1440, 690)), ((0.0, 0.0), (0.75, 0.75))),
    ((None, (1440, 690)), (None, (0.75, 0.75))),
    ((None, None), (None, None)),
    ]


def _send(g):
    g.update()
    time.sleep(WAIT_S)
    sdl2.SDL_GameControllerUpdate()  # also updates joysticks
    sdl2.SDL_FlushEvents(sdl2.SDL_FIRSTEVENT, sdl2.SDL_LASTEVENT)


class TestVDS4Gamepad(unittest.TestCase):

    def setUp(self):
        print(f"Setting up VDS4Gamepad")

        self.extended = False
        self.g = vg.VDS4Gamepad()
        # press a button to wake the device up
        self.g.press_button(button=vg.DS4_BUTTONS.DS4_BUTTON_CROSS)
        self.g.update()
        time.sleep(WAIT_S)
        self.g.release_button(button=vg.DS4_BUTTONS.DS4_BUTTON_CROSS)
        # wake axes up
        self.g.left_joystick_float(x_value_float=0.3, y_value_float=-0.3)
        self.g.right_joystick_float(x_value_float=-0.3, y_value_float=0.3)
        self.g.left_trigger_float(value_float=0.3)
        self.g.right_trigger_float(value_float=0.3)
        self.g.update()
        time.sleep(WAIT_S)
        self.g.left_joystick_float(x_value_float=-0.3, y_value_float=0.3)
        self.g.right_joystick_float(x_value_float=0.3, y_value_float=-0.3)
        self.g.update()
        time.sleep(WAIT_S)
        self.g.reset()
        self.g.update()
        time.sleep(WAIT_S)

        sdl2.SDL_SetHint(sdl2.SDL_HINT_JOYSTICK_ALLOW_BACKGROUND_EVENTS, b"1")
        self.assertEqual(sdl2.SDL_Init(sdl2.SDL_INIT_JOYSTICK | sdl2.SDL_INIT_GAMECONTROLLER | sdl2.SDL_INIT_SENSOR), 0,
                         sdl2.SDL_GetError())
        self.nb_joysticks = sdl2.SDL_NumJoysticks()
        # the joystick and game controller APIs can both be opened on the same device:
        self.j = sdl2.SDL_JoystickOpen(0) if self.nb_joysticks > 0 else None
        self.c = sdl2.SDL_GameControllerOpen(0) if self.nb_joysticks > 0 and sdl2.SDL_IsGameController(0) else None

    def _reset(self):
        self.g.reset()
        if self.extended:
            self.g.gyroscope(0, 0, 0)

    def _send_and_reset(self):
        self._reset()
        _send(self.g)

    def _axis(self, axis):
        return sdl2.SDL_JoystickGetAxis(self.j, axis) / 32768

    def _c_axis(self, axis):
        return sdl2.SDL_GameControllerGetAxis(self.c, axis) / 32767

    def _c_button(self, button):
        return sdl2.SDL_GameControllerGetButton(self.c, button)

    def _enable_sensor(self, sensor):
        self.assertTrue(sdl2.SDL_GameControllerHasSensor(self.c, sensor))
        self.assertEqual(sdl2.SDL_GameControllerSetSensorEnabled(self.c, sensor, sdl2.SDL_TRUE), 0, sdl2.SDL_GetError())

    def _sensor(self, sensor):
        data = (ctypes.c_float * 3)()
        self.assertEqual(sdl2.SDL_GameControllerGetSensorData(self.c, sensor, data, 3), 0, sdl2.SDL_GetError())
        return tuple(data)

    def _finger(self, finger):
        state, x, y, pressure = ctypes.c_uint8(), ctypes.c_float(), ctypes.c_float(), ctypes.c_float()
        self.assertEqual(sdl2.SDL_GameControllerGetTouchpadFinger(
            self.c, 0, finger, ctypes.byref(state), ctypes.byref(x), ctypes.byref(y), ctypes.byref(pressure)), 0,
            sdl2.SDL_GetError())
        return (x.value, y.value) if state.value else None

    def test_all(self):
        self._test_all()

    def test_all_extended(self):
        self.extended = True
        self._send_and_reset()
        self._test_all()
        if SYSTEM == "Windows":  # SDL2 doesn't support the touchpad and sensors of uinput devices
            self._test_extended()

    def _test_all(self):
        self.assertTrue(SYSTEM in ("Windows", "Linux"))

        # Check that only one gamepad is connected:
        self.assertEqual(self.nb_joysticks, 1)
        self.assertTrue(self.j, sdl2.SDL_GetError())
        self.assertTrue(self.c, f"Not recognized as a game controller: {sdl2.SDL_GetError()}")
        j = self.j
        c = self.c

        # Check that gamepad properties are correct:
        nb_buttons = sdl2.SDL_JoystickNumButtons(j)
        self.assertEqual(sdl2.SDL_JoystickName(j).decode(), DS4_JOYSTICK_NAME)
        self.assertEqual(sdl2.SDL_JoystickNumAxes(j), 6)
        self.assertEqual(sdl2.SDL_JoystickNumBalls(j), 0)
        self.assertEqual(nb_buttons, DS4_NB_BUTTONS)
        self.assertEqual(sdl2.SDL_JoystickNumHats(j), DS4_NB_HATS)
        self.assertEqual(sdl2.SDL_JoystickGetVendor(j), 0x054C)

        # Check that buttons are correct:

        for v_button, j_button in DS4_TEST_BUTTONS:
            self.g.press_button(button=v_button)
            _send(self.g)
            print(f"Testing: {v_button, j_button}")

            for i in range(nb_buttons):
                self.assertEqual(sdl2.SDL_JoystickGetButton(j, i), int(i == j_button), i)

            self.g.release_button(button=v_button)
            _send(self.g)

        # Check that special buttons are correct:

        for v_button, j_button in DS4_TEST_SPECIAL_BUTTONS:
            self.g.press_special_button(special_button=v_button)
            _send(self.g)
            print(f"Testing: {v_button, j_button}")

            for i in range(nb_buttons):
                self.assertEqual(sdl2.SDL_JoystickGetButton(j, i), int(i == j_button), i)

            self.g.release_special_button(special_button=v_button)
            _send(self.g)

        # Check that directional pad is correct:

        for v_value, j_value in DS4_TEST_DIRECTIONAL_PAD:
            self.g.directional_pad(direction=v_value)
            _send(self.g)
            print(f"Testing: {v_value, j_value}")

            if SYSTEM == "Windows":
                self.assertEqual(tuple(sdl2.SDL_JoystickGetButton(j, b) for b in DS4_DIRECTIONAL_PAD), j_value)
            else:
                self.assertEqual(sdl2.SDL_JoystickGetHat(j, 0), j_value)

            self._send_and_reset()

        # Check that triggers are correct (absolute and float):

        for axis, set_int, set_float in (
                (DS4_LEFT_TRIGGER, self.g.left_trigger, self.g.left_trigger_float),
                (DS4_RIGHT_TRIGGER, self.g.right_trigger, self.g.right_trigger_float)):
            for setter, tested_values in ((set_int, DS4_TEST_TRIGGER_INT), (set_float, DS4_TEST_TRIGGER_FLOAT)):
                for v_value, j_value in tested_values:
                    setter(v_value)
                    _send(self.g)
                    print(f"Testing: {axis, v_value, j_value}")
                    self.assertAlmostEqual(self._axis(axis), j_value, delta=0.01)
                    self._send_and_reset()

        # Check that joysticks are correct (absolute and float):

        for axes, set_int, set_float in (
                (DS4_LEFT_JOYSTICK, self.g.left_joystick, self.g.left_joystick_float),
                (DS4_RIGHT_JOYSTICK, self.g.right_joystick, self.g.right_joystick_float)):
            for setter, tested_values in ((set_int, DS4_TEST_JOYSTICK_INT), (set_float, DS4_TEST_JOYSTICK_FLOAT)):
                for v_value, j_value in tested_values:
                    setter(v_value[0], v_value[1])
                    _send(self.g)
                    print(f"Testing: {axes, v_value, j_value}")
                    self.assertAlmostEqual(self._axis(axes[0]), j_value[0], delta=0.01)
                    self.assertAlmostEqual(self._axis(axes[1]), j_value[1], delta=0.01)
                    self._send_and_reset()

        self.assertEqual(sdl2.SDL_GameControllerName(c).decode(), DS4_CONTROLLER_NAME)
        self.assertEqual(sdl2.SDL_GameControllerGetType(c), sdl2.SDL_CONTROLLER_TYPE_PS4)

        # Check that buttons are correct:

        all_buttons = range(sdl2.SDL_CONTROLLER_BUTTON_MAX)
        for press, release, tested_buttons in (
                (self.g.press_button, self.g.release_button, DS4_CONTROLLER_TEST_BUTTONS),
                (self.g.press_special_button, self.g.release_special_button, DS4_CONTROLLER_TEST_SPECIAL_BUTTONS)):
            for v_button, c_button in tested_buttons:
                press(v_button)
                _send(self.g)
                print(f"Testing: {v_button, c_button}")

                for i in all_buttons:
                    self.assertEqual(self._c_button(i), int(i == c_button), i)

                release(v_button)
                _send(self.g)

        # Check that directional pad is correct:

        for v_value, c_value in DS4_CONTROLLER_TEST_DIRECTIONAL_PAD:
            self.g.directional_pad(direction=v_value)
            _send(self.g)
            print(f"Testing: {v_value, c_value}")
            self.assertEqual(tuple(self._c_button(b) for b in DS4_CONTROLLER_DPAD_BUTTONS), c_value)
            self._send_and_reset()

        # Check that triggers are correct:

        for axis, setter in (
                (sdl2.SDL_CONTROLLER_AXIS_TRIGGERLEFT, self.g.left_trigger),
                (sdl2.SDL_CONTROLLER_AXIS_TRIGGERRIGHT, self.g.right_trigger)):
            for v_value, c_value in DS4_CONTROLLER_TEST_TRIGGER_INT:
                setter(v_value)
                _send(self.g)
                print(f"Testing: {axis, v_value, c_value}")
                self.assertAlmostEqual(self._c_axis(axis), c_value, delta=0.01)
                self._send_and_reset()

        # Check that joysticks are correct:

        for axes, setter in (
                ((sdl2.SDL_CONTROLLER_AXIS_LEFTX, sdl2.SDL_CONTROLLER_AXIS_LEFTY), self.g.left_joystick_float),
                ((sdl2.SDL_CONTROLLER_AXIS_RIGHTX, sdl2.SDL_CONTROLLER_AXIS_RIGHTY), self.g.right_joystick_float)):
            for v_value, c_value in DS4_TEST_JOYSTICK_FLOAT:
                setter(v_value[0], v_value[1])
                _send(self.g)
                print(f"Testing: {axes, v_value, c_value}")
                self.assertAlmostEqual(self._c_axis(axes[0]), c_value[0], delta=0.01)
                self.assertAlmostEqual(self._c_axis(axes[1]), c_value[1], delta=0.01)
                self._send_and_reset()

    def _test_extended(self):
        # Check that gyroscope is correct:

        self._enable_sensor(sdl2.SDL_SENSOR_GYRO)
        deg_s_to_rad_s = math.pi / 180

        for v_value in ((0, 0, 0), (1000, 0, 0), (0, -1000, 0), (0, 0, 2000), (-500, 500, -500)):
            self.g.gyroscope(*v_value)
            _send(self.g)
            expected = tuple(v * k * deg_s_to_rad_s for v, k in zip(v_value, DS4_GYRO_RAW_TO_DEG_S))
            print(f"Testing: {v_value, expected}")
            for value, expected_value in zip(self._sensor(sdl2.SDL_SENSOR_GYRO), expected):
                self.assertAlmostEqual(value, expected_value, delta=0.02)

        self._send_and_reset()

        # Check that accelerometer is correct:

        self._enable_sensor(sdl2.SDL_SENSOR_ACCEL)
        bx, by, bz = DS4_ACCEL_BIAS

        # raw value at the calibration bias = no acceleration; 1 g = 9.81 m/s²
        for v_value, expected in (
                ((bx, by, bz), (0.0, 0.0, 0.0)),
                ((bx + round(DS4_ACCEL_RAW_PER_G), by, bz), (STANDARD_GRAVITY, 0.0, 0.0)),
                ((bx - round(DS4_ACCEL_RAW_PER_G), by, bz), (-STANDARD_GRAVITY, 0.0, 0.0))):
            self.g.accelerometer(*v_value)
            _send(self.g)
            print(f"Testing: {v_value, expected}")
            for value, expected_value in zip(self._sensor(sdl2.SDL_SENSOR_ACCEL), expected):
                self.assertAlmostEqual(value, expected_value, delta=0.1)

        self._send_and_reset()

        # Check that sensor timestamps are correct (requires SDL >= 2.26):

        if hasattr(sdl2, "SDL_GameControllerGetSensorDataWithTimestamp"):
            timestamps = []
            for i in range(4):
                self.g.gyroscope(100 * i, 0, 0)  # change the report so that SDL processes it
                _send(self.g)
                timestamp, data = ctypes.c_uint64(), (ctypes.c_float * 3)()
                self.assertEqual(sdl2.SDL_GameControllerGetSensorDataWithTimestamp(
                    self.c, sdl2.SDL_SENSOR_GYRO, ctypes.byref(timestamp), data, 3), 0, sdl2.SDL_GetError())
                timestamps.append(timestamp.value)
            print(f"Testing: {timestamps}")
            for t0, t1 in zip(timestamps, timestamps[1:]):
                self.assertAlmostEqual(t1 - t0, WAIT_S * 1e6, delta=30000)  # microseconds

            self._send_and_reset()

        # Check that touchpad is correct:

        self.assertEqual(sdl2.SDL_GameControllerGetNumTouchpads(self.c), 1)
        self.assertEqual(sdl2.SDL_GameControllerGetNumTouchpadFingers(self.c, 0), 2)

        for v_value, expected in DS4_TEST_TOUCHPAD:
            self.g.touchpad(*v_value)
            _send(self.g)
            print(f"Testing: {v_value, expected}")
            for finger, expected_finger in enumerate(expected):
                value = self._finger(finger)
                if expected_finger is None:
                    self.assertIsNone(value)
                else:
                    self.assertIsNotNone(value)
                    self.assertAlmostEqual(value[0], expected_finger[0], delta=0.01)
                    self.assertAlmostEqual(value[1], expected_finger[1], delta=0.01)

        # touchpad click while touching:
        self.g.touchpad((960, 460), None)
        self.g.press_special_button(vg.DS4_SPECIAL_BUTTONS.DS4_SPECIAL_BUTTON_TOUCHPAD)
        _send(self.g)
        self.assertEqual(self._c_button(sdl2.SDL_CONTROLLER_BUTTON_TOUCHPAD), 1)
        self.assertIsNotNone(self._finger(0))

        self._send_and_reset()

        # Check that power level is correct:

        # SDL only parses the battery level over Bluetooth: a wired DS4 is always reported as wired
        self.g.usb(True)
        self.g.battery(5)
        _send(self.g)
        self.assertEqual(sdl2.SDL_JoystickCurrentPowerLevel(self.j), sdl2.SDL_JOYSTICK_POWER_WIRED)

    def tearDown(self):
        if self.c:
            sdl2.SDL_GameControllerClose(self.c)
        if self.j:
            sdl2.SDL_JoystickClose(self.j)
        sdl2.SDL_Quit()
        del self.g


if __name__ == '__main__':
    unittest.main(verbosity=2)
