import time
import unittest
import platform

import vgamepad as vg

# PySDL2 and an SDL2 binary must be installed to execute this file:
#   pip install pysdl2 pysdl2-dll

import sdl2


# On Windows, SDL reads the ViGEmBus Xbox 360 controller through its RawInput driver.
# RawInput data arrives as window messages, so the video subsystem must be initialized and events pumped.
# On Linux, vgamepad creates a uinput (evdev) device similar to the xpad driver's, read by the evdev backend.
# The GameController layer maps both to the same layout.

WAIT_S = 0.1
SYSTEM = platform.system()

X360_NAME = "Xbox 360 Controller"
X360_CONTROLLER_NAME = X360_NAME if SYSTEM == "Windows" else "X360 Controller"

X360_LEFT_TRIGGER = 4 if SYSTEM == "Windows" else 2
X360_RIGHT_TRIGGER = 5
X360_LEFT_JOYSTICK = (0, 1)
X360_RIGHT_JOYSTICK = (2, 3) if SYSTEM == "Windows" else (3, 4)

X360_TEST_BUTTONS = [
    (vg.XUSB_BUTTON.XUSB_GAMEPAD_A, 0),
    (vg.XUSB_BUTTON.XUSB_GAMEPAD_B, 1),
    (vg.XUSB_BUTTON.XUSB_GAMEPAD_X, 2),
    (vg.XUSB_BUTTON.XUSB_GAMEPAD_Y, 3),
    (vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER, 4),
    (vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER, 5),
    (vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK, 6),
    (vg.XUSB_BUTTON.XUSB_GAMEPAD_START, 7),
    ] + ([
    (vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB, 8),
    (vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB, 9),
    # (vg.XUSB_BUTTON.XUSB_GAMEPAD_GUIDE, 10),  # opens the game bar on Windows
    ] if SYSTEM == "Windows" else [
    (vg.XUSB_BUTTON.XUSB_GAMEPAD_GUIDE, 8),
    (vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB, 9),
    (vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB, 10),
    ])

X360_TEST_HAT = [
    (vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP, sdl2.SDL_HAT_UP),
    (vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN, sdl2.SDL_HAT_DOWN),
    (vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT, sdl2.SDL_HAT_LEFT),
    (vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT, sdl2.SDL_HAT_RIGHT),
    (vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP | vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT, sdl2.SDL_HAT_LEFTUP),
    (vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN | vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT, sdl2.SDL_HAT_RIGHTDOWN),
    ]

# Joystick axes are normalized to [-1.0, 1.0] (SDL value / 32768); triggers rest at -1.0

X360_TEST_TRIGGER_INT = [
    (0, -1.0),
    (5, -0.96),
    (10, -0.92),
    (63, -0.5),
    (127, 0.0),
    (191, 0.5),
    (255, 1.0),
    ]

X360_TEST_TRIGGER_FLOAT = [
    (0.0, -1.0),
    (0.5, 0.0),
    (1.0, 1.0),
    ]

X360_TEST_JOYSTICK_INT = [
    ((-32768, 0), (-1.0, 0.0)),
    ((-16384, 16383), (-0.5, -0.5)),
    ((0, 32767), (0.0, -1.0)),
    ((16383, -32768), (0.5, 1.0)),
    ((32767, -16384), (1.0, 0.5)),
    ]

X360_TEST_JOYSTICK_FLOAT = [
    ((-1.0, 0.0), (-1.0, 0.0)),
    ((-0.5, 0.5), (-0.5, -0.5)),
    ((0.0, 1.0), (0.0, -1.0)),
    ((0.5, -1.0), (0.5, 1.0)),
    ((1.0, -0.5), (1.0, 0.5)),
    ]

X360_CONTROLLER_TEST_BUTTONS = [
    (vg.XUSB_BUTTON.XUSB_GAMEPAD_A, sdl2.SDL_CONTROLLER_BUTTON_A),
    (vg.XUSB_BUTTON.XUSB_GAMEPAD_B, sdl2.SDL_CONTROLLER_BUTTON_B),
    (vg.XUSB_BUTTON.XUSB_GAMEPAD_X, sdl2.SDL_CONTROLLER_BUTTON_X),
    (vg.XUSB_BUTTON.XUSB_GAMEPAD_Y, sdl2.SDL_CONTROLLER_BUTTON_Y),
    (vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK, sdl2.SDL_CONTROLLER_BUTTON_BACK),
    (vg.XUSB_BUTTON.XUSB_GAMEPAD_START, sdl2.SDL_CONTROLLER_BUTTON_START),
    (vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB, sdl2.SDL_CONTROLLER_BUTTON_LEFTSTICK),
    (vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB, sdl2.SDL_CONTROLLER_BUTTON_RIGHTSTICK),
    (vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER, sdl2.SDL_CONTROLLER_BUTTON_LEFTSHOULDER),
    (vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER, sdl2.SDL_CONTROLLER_BUTTON_RIGHTSHOULDER),
    (vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP, sdl2.SDL_CONTROLLER_BUTTON_DPAD_UP),
    (vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN, sdl2.SDL_CONTROLLER_BUTTON_DPAD_DOWN),
    (vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT, sdl2.SDL_CONTROLLER_BUTTON_DPAD_LEFT),
    (vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT, sdl2.SDL_CONTROLLER_BUTTON_DPAD_RIGHT),
    ] + ([
    # (vg.XUSB_BUTTON.XUSB_GAMEPAD_GUIDE, sdl2.SDL_CONTROLLER_BUTTON_GUIDE),
    ] if SYSTEM == "Windows" else [
    (vg.XUSB_BUTTON.XUSB_GAMEPAD_GUIDE, sdl2.SDL_CONTROLLER_BUTTON_GUIDE),
    ])

# GameController triggers are normalized to [0.0, 1.0] (SDL value / 32767); they rest at 0.0

X360_CONTROLLER_TEST_TRIGGER_INT = [
    (0, 0.0),
    (63, 0.25),
    (127, 0.5),
    (191, 0.75),
    (255, 1.0),
    ]

X360_TEST_RUMBLE = [  # (SDL low frequency, SDL high frequency), (large motor, small motor)
    ((0xFFFF, 0x8000), (255, 128)),
    ((0x4000, 0xFFFF), (64, 255)),
    ((0x8000, 0), (128, 0)),
    ((0, 0), (0, 0)),
    ]


def _wait():
    # pump events regularly, like a game loop
    for _ in range(4):
        time.sleep(WAIT_S / 4)
        sdl2.SDL_PumpEvents()
        sdl2.SDL_GameControllerUpdate()  # also updates joysticks
    sdl2.SDL_FlushEvents(sdl2.SDL_FIRSTEVENT, sdl2.SDL_LASTEVENT)


def _send(g):
    g.update()
    _wait()


class TestVX360Gamepad(unittest.TestCase):

    def setUp(self):
        print(f"Setting up VX360Gamepad")

        self.g = vg.VX360Gamepad()
        # press a button to wake the device up
        self.g.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
        self.g.update()
        time.sleep(WAIT_S)
        self.g.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
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
        video = sdl2.SDL_INIT_VIDEO if SYSTEM == "Windows" else 0
        self.assertEqual(sdl2.SDL_Init(sdl2.SDL_INIT_JOYSTICK | sdl2.SDL_INIT_GAMECONTROLLER | video), 0,
                         sdl2.SDL_GetError())
        self.nb_joysticks = sdl2.SDL_NumJoysticks()
        # the joystick and game controller APIs can both be opened on the same device:
        self.j = sdl2.SDL_JoystickOpen(0) if self.nb_joysticks > 0 else None
        self.c = sdl2.SDL_GameControllerOpen(0) if self.nb_joysticks > 0 and sdl2.SDL_IsGameController(0) else None

        self.notifications = []

        def callback(client, target, large_motor, small_motor, led_number, user_data):
            self.notifications.append((large_motor, small_motor))

        self.g.register_notification(callback_function=callback)

    def _send_and_reset(self):
        self.g.reset()
        _send(self.g)

    def _axis(self, axis):
        return sdl2.SDL_JoystickGetAxis(self.j, axis) / 32768

    def _c_axis(self, axis):
        return sdl2.SDL_GameControllerGetAxis(self.c, axis) / 32767

    def _c_button(self, button):
        return sdl2.SDL_GameControllerGetButton(self.c, button)

    def _rumble(self, low, high, duration_ms):
        self.assertEqual(sdl2.SDL_GameControllerRumble(self.c, low, high, duration_ms), 0, sdl2.SDL_GetError())
        _wait()

    def test_all(self):
        self.assertTrue(SYSTEM in ("Windows", "Linux"))

        # Check that only one gamepad is connected:
        self.assertEqual(self.nb_joysticks, 1)
        self.assertTrue(self.j, sdl2.SDL_GetError())
        self.assertTrue(self.c, f"Not recognized as a game controller: {sdl2.SDL_GetError()}")
        j = self.j
        c = self.c

        # Check that gamepad properties are correct:
        nb_buttons = sdl2.SDL_JoystickNumButtons(j)
        self.assertEqual(sdl2.SDL_JoystickName(j).decode(), X360_NAME)
        self.assertEqual(sdl2.SDL_JoystickNumAxes(j), 6)
        self.assertEqual(sdl2.SDL_JoystickNumBalls(j), 0)
        self.assertEqual(nb_buttons, 11)
        self.assertEqual(sdl2.SDL_JoystickNumHats(j), 1)
        self.assertEqual(sdl2.SDL_JoystickGetVendor(j), 0x045E)

        # Check that buttons are correct:

        for v_button, j_button in X360_TEST_BUTTONS:
            self.g.press_button(button=v_button)
            _send(self.g)
            print(f"Testing: {v_button, j_button}")

            for i in range(nb_buttons):
                self.assertEqual(sdl2.SDL_JoystickGetButton(j, i), int(i == j_button), i)
            self.assertEqual(sdl2.SDL_JoystickGetHat(j, 0), sdl2.SDL_HAT_CENTERED)

            self.g.release_button(button=v_button)
            _send(self.g)

        # Check that hat is correct:

        for v_hat_button, j_hat in X360_TEST_HAT:
            self.g.press_button(button=v_hat_button)
            _send(self.g)
            print(f"Testing: {v_hat_button, j_hat}")

            self.assertEqual(sdl2.SDL_JoystickGetHat(j, 0), j_hat)
            for i in range(nb_buttons):
                self.assertEqual(sdl2.SDL_JoystickGetButton(j, i), 0, i)

            self.g.release_button(button=v_hat_button)
            _send(self.g)

        # Check that triggers are correct (absolute and float):

        for axis, set_int, set_float in (
                (X360_LEFT_TRIGGER, self.g.left_trigger, self.g.left_trigger_float),
                (X360_RIGHT_TRIGGER, self.g.right_trigger, self.g.right_trigger_float)):
            for setter, tested_values in ((set_int, X360_TEST_TRIGGER_INT), (set_float, X360_TEST_TRIGGER_FLOAT)):
                for v_value, j_value in tested_values:
                    setter(v_value)
                    _send(self.g)
                    print(f"Testing: {axis, v_value, j_value}")
                    self.assertAlmostEqual(self._axis(axis), j_value, delta=0.01)
                    self._send_and_reset()

        # Check that joysticks are correct (absolute and float):

        for axes, set_int, set_float in (
                (X360_LEFT_JOYSTICK, self.g.left_joystick, self.g.left_joystick_float),
                (X360_RIGHT_JOYSTICK, self.g.right_joystick, self.g.right_joystick_float)):
            for setter, tested_values in ((set_int, X360_TEST_JOYSTICK_INT), (set_float, X360_TEST_JOYSTICK_FLOAT)):
                for v_value, j_value in tested_values:
                    setter(v_value[0], v_value[1])
                    _send(self.g)
                    print(f"Testing: {axes, v_value, j_value}")
                    self.assertAlmostEqual(self._axis(axes[0]), j_value[0], delta=0.001)
                    self.assertAlmostEqual(self._axis(axes[1]), j_value[1], delta=0.001)
                    self._send_and_reset()

        self.assertEqual(sdl2.SDL_GameControllerName(c).decode(), X360_CONTROLLER_NAME)
        self.assertEqual(sdl2.SDL_GameControllerGetType(c), sdl2.SDL_CONTROLLER_TYPE_XBOX360)

        # Check that buttons are correct:

        for v_button, c_button in X360_CONTROLLER_TEST_BUTTONS:
            self.g.press_button(button=v_button)
            _send(self.g)
            print(f"Testing: {v_button, c_button}")

            for i in range(sdl2.SDL_CONTROLLER_BUTTON_MAX):
                self.assertEqual(self._c_button(i), int(i == c_button), i)

            self.g.release_button(button=v_button)
            _send(self.g)

        # Check that triggers are correct:

        for axis, setter in (
                (sdl2.SDL_CONTROLLER_AXIS_TRIGGERLEFT, self.g.left_trigger),
                (sdl2.SDL_CONTROLLER_AXIS_TRIGGERRIGHT, self.g.right_trigger)):
            for v_value, c_value in X360_CONTROLLER_TEST_TRIGGER_INT:
                setter(v_value)
                _send(self.g)
                print(f"Testing: {axis, v_value, c_value}")
                self.assertAlmostEqual(self._c_axis(axis), c_value, delta=0.01)
                self._send_and_reset()

        # Check that joysticks are correct:

        for axes, setter in (
                ((sdl2.SDL_CONTROLLER_AXIS_LEFTX, sdl2.SDL_CONTROLLER_AXIS_LEFTY), self.g.left_joystick_float),
                ((sdl2.SDL_CONTROLLER_AXIS_RIGHTX, sdl2.SDL_CONTROLLER_AXIS_RIGHTY), self.g.right_joystick_float)):
            for v_value, c_value in X360_TEST_JOYSTICK_FLOAT:
                setter(v_value[0], v_value[1])
                _send(self.g)
                print(f"Testing: {axes, v_value, c_value}")
                self.assertAlmostEqual(self._c_axis(axes[0]), c_value[0], delta=0.01)
                self.assertAlmostEqual(self._c_axis(axes[1]), c_value[1], delta=0.01)
                self._send_and_reset()

        # on Windows, SDL can only rumble once RawInput has correlated the controller with XInput,
        # which happens when buttons are pressed (above)

        self.assertTrue(sdl2.SDL_GameControllerHasRumble(c))

        for v_value, expected in X360_TEST_RUMBLE:
            self._rumble(*v_value, 5000)
            print(f"Testing: {v_value, expected}")
            self.assertTrue(self.notifications)
            self.assertEqual(self.notifications[-1], expected, self.notifications)

        # SDL stops the rumble when its duration expires, during joystick updates:
        self._rumble(0xFFFF, 0xFFFF, 300)
        self.assertEqual(self.notifications[-1], (255, 255), self.notifications)
        for _ in range(5):
            _wait()
        self.assertEqual(self.notifications[-1], (0, 0), self.notifications)

    def tearDown(self):
        self.g.unregister_notification()
        if self.c:
            sdl2.SDL_GameControllerClose(self.c)
        if self.j:
            sdl2.SDL_JoystickClose(self.j)
        sdl2.SDL_Quit()
        del self.g


if __name__ == '__main__':
    unittest.main(verbosity=2)
