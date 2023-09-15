from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

import time
import unittest
import platform

import vgamepad as vg

# We use pygame to test vgamepad.
# pygame must be installed to run these tests.
# Furthermore, these tests can only run with a display (pygame requirement).

import pygame


WAIT_S = 0.1
SYSTEM = platform.system()

class TestVX360Gamepad(unittest.TestCase):

    def setUp(self):
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
        pygame.init()
        self.joysticks = [pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())]

    def test_all(self):
        self.assertTrue(SYSTEM in ("Windows", "Linux"))

        # Check that only one gamepad is connected:
        self.assertTrue(len(self.joysticks) == 1)
        j = self.joysticks[0]

        # Check that gamepad properties are correct:
        name = j.get_name()
        nb_axes = j.get_numaxes()
        nb_balls = j.get_numballs()
        nb_buttons = j.get_numbuttons()
        nb_hats = j.get_numhats()
        self.assertTrue(name == "Xbox 360 Controller")
        self.assertEqual(nb_axes, 6)
        self.assertEqual(nb_balls, 0)
        self.assertEqual(nb_buttons, 11 if SYSTEM == "Windows" else 10)  # No GUIDE button on Linux
        self.assertEqual(nb_hats, 1)

        # Check that buttons are correct:

        tested_buttons = [
            (vg.XUSB_BUTTON.XUSB_GAMEPAD_A, 0),
            (vg.XUSB_BUTTON.XUSB_GAMEPAD_B, 1),
            (vg.XUSB_BUTTON.XUSB_GAMEPAD_X, 2),
            (vg.XUSB_BUTTON.XUSB_GAMEPAD_Y, 3),
            (vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER, 4),
            (vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER, 5),
            (vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK, 6),
            (vg.XUSB_BUTTON.XUSB_GAMEPAD_START, 7),
            (vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB, 8),
            (vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB, 9),
            # (vg.XUSB_BUTTON.XUSB_GAMEPAD_GUIDE, 10),  # Does not exist on Linux
        ]

        for v_button, j_button in tested_buttons:
            self.g.press_button(button=v_button)
            self.g.update()
            time.sleep(WAIT_S)

            _ = pygame.event.get()
            print(f"Testing: {v_button, j_button}")
            self.assertTrue(j.get_button(j_button))

            for i in range(nb_buttons):
                if i != j_button:
                    self.assertFalse(j.get_button(i))

            self.g.release_button(button=v_button)
            self.g.update()
            time.sleep(WAIT_S)

        # Check that hat is correct:

        tested_hat_buttons = [
            (vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP, (0, 1)),
            (vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN, (0, -1)),
            (vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT, (-1, 0)),
            (vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT, (1, 0))
        ]

        for v_hat_button, j_hat_button in tested_hat_buttons:
            self.g.press_button(button=v_hat_button)
            self.g.update()
            time.sleep(WAIT_S)

            _ = pygame.event.get()
            print(f"Testing: {v_hat_button, j_hat_button}")
            self.assertEqual(j.get_hat(0), j_hat_button)

            self.g.release_button(button=v_hat_button)
            self.g.update()
            time.sleep(WAIT_S)

        # Check that triggers are correct (absolute):

        tested_values = [
            (0, -1.0),
            (5, -0.96),
            (10, -0.92),
            (63, -0.5),
            (127, 0.0),
            (191, 0.5),
            (255, 1.0),
        ]

        # Left trigger:

        for v_value, j_value in tested_values:
            self.g.left_trigger(value=v_value)
            self.g.update()
            time.sleep(WAIT_S)

            _ = pygame.event.get()
            print(f"Testing: {v_value, j_value}")
            self.assertAlmostEqual(j.get_axis(4), j_value, delta=0.01)

            self.g.reset()
            self.g.update()
            time.sleep(WAIT_S)

        # Right trigger:

        for v_value, j_value in tested_values:
            self.g.right_trigger(value=v_value)
            self.g.update()
            time.sleep(WAIT_S)

            _ = pygame.event.get()
            print(f"Testing: {v_value, j_value}")
            self.assertAlmostEqual(j.get_axis(5), j_value, delta=0.01)

            self.g.reset()
            self.g.update()
            time.sleep(WAIT_S)

        # Check that triggers are correct (float):

        tested_values = [
            (0.0, -1.0),
            (0.5, 0.0),
            (1.0, 1.0),
        ]

        # Left trigger:

        for v_value, j_value in tested_values:
            self.g.left_trigger_float(value_float=v_value)
            self.g.update()
            time.sleep(WAIT_S)

            _ = pygame.event.get()
            print(f"Testing: {v_value, j_value}")
            self.assertAlmostEqual(j.get_axis(4), j_value, delta=0.01)

            self.g.reset()
            self.g.update()
            time.sleep(WAIT_S)

        # Right trigger:

        for v_value, j_value in tested_values:
            self.g.right_trigger_float(value_float=v_value)
            self.g.update()
            time.sleep(WAIT_S)

            _ = pygame.event.get()
            print(f"Testing: {v_value, j_value}")
            self.assertAlmostEqual(j.get_axis(5), j_value, delta=0.01)

            self.g.reset()
            self.g.update()
            time.sleep(WAIT_S)

        # Check that joysticks are correct (absolute):

        tested_values = [
            ((-32768, 0), (-1.0, 0.0)),
            ((-16384, 16383), (-0.5, -0.5)),
            ((0, 32767), (0.0, -1.0)),
            ((16383, -32768), (0.5, 1.0)),
            ((32767, -16384), (1.0, 0.5)),
        ]

        # Left joystick:

        for v_value, j_value in tested_values:
            self.g.left_joystick(x_value=v_value[0], y_value=v_value[1])
            self.g.update()
            time.sleep(WAIT_S)

            _ = pygame.event.get()
            print(f"Testing: {v_value, j_value}")
            self.assertAlmostEqual(j.get_axis(0), j_value[0], delta=0.001)
            self.assertAlmostEqual(j.get_axis(1), j_value[1], delta=0.001)

            self.g.reset()
            self.g.update()
            time.sleep(WAIT_S)

        # Right joystick:

        for v_value, j_value in tested_values:
            self.g.right_joystick(x_value=v_value[0], y_value=v_value[1])
            self.g.update()
            time.sleep(WAIT_S)

            _ = pygame.event.get()
            print(f"Testing: {v_value, j_value}")
            self.assertAlmostEqual(j.get_axis(2), j_value[0], delta=0.001)
            self.assertAlmostEqual(j.get_axis(3), j_value[1], delta=0.001)

            self.g.reset()
            self.g.update()
            time.sleep(WAIT_S)

        # Check that joysticks are correct (float):

        tested_values = [
            ((-1.0, 0.0), (-1.0, 0.0)),
            ((-0.5, 0.5), (-0.5, -0.5)),
            ((0.0, 1.0), (0.0, -1.0)),
            ((0.5, -1.0), (0.5, 1.0)),
            ((1.0, -0.5), (1.0, 0.5)),
        ]

        # Left joystick:

        for v_value, j_value in tested_values:
            self.g.left_joystick_float(x_value_float=v_value[0], y_value_float=v_value[1])
            self.g.update()
            time.sleep(WAIT_S)

            _ = pygame.event.get()
            print(f"Testing: {v_value, j_value}")
            self.assertAlmostEqual(j.get_axis(0), j_value[0], delta=0.001)
            self.assertAlmostEqual(j.get_axis(1), j_value[1], delta=0.001)

            self.g.reset()
            self.g.update()
            time.sleep(WAIT_S)

        # Right joystick:

        for v_value, j_value in tested_values:
            self.g.right_joystick_float(x_value_float=v_value[0], y_value_float=v_value[1])
            self.g.update()
            time.sleep(WAIT_S)

            _ = pygame.event.get()
            print(f"Testing: {v_value, j_value}")
            self.assertAlmostEqual(j.get_axis(2), j_value[0], delta=0.001)
            self.assertAlmostEqual(j.get_axis(3), j_value[1], delta=0.001)

            self.g.reset()
            self.g.update()
            time.sleep(WAIT_S)

    def tearDown(self):
        del self.g
        pygame.quit()


if __name__ == '__main__':
    unittest.main(verbosity=2)
