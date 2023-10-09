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

DS4_NAME = "PS4 Controller" if SYSTEM == "Windows" else "Sony Interactive Entertainment Wireless Controller"
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
    (vg.DS4_BUTTONS.DS4_BUTTON_SHARE, 9),
    (vg.DS4_BUTTONS.DS4_BUTTON_OPTIONS, 8),
    (vg.DS4_BUTTONS.DS4_BUTTON_THUMB_LEFT, 11),
    (vg.DS4_BUTTONS.DS4_BUTTON_THUMB_RIGHT, 12),
    (vg.DS4_BUTTONS.DS4_BUTTON_SHOULDER_LEFT, 4),
    (vg.DS4_BUTTONS.DS4_BUTTON_SHOULDER_RIGHT, 5),
    ]

DS4_TEST_SPECIAL_BUTTONS = [
    (vg.DS4_SPECIAL_BUTTONS.DS4_SPECIAL_BUTTON_PS, 5),
    (vg.DS4_SPECIAL_BUTTONS.DS4_SPECIAL_BUTTON_TOUCHPAD, 15),
    ] if SYSTEM == "Windows" else [
    (vg.DS4_SPECIAL_BUTTONS.DS4_SPECIAL_BUTTON_PS, 10),
    # (vg.DS4_SPECIAL_BUTTONS.DS4_SPECIAL_BUTTON_TOUCHPAD, 15),  # not implemented on Linux
    ]

DS4_TEST_DIRECTIONAL_PAD = [  # On Windows, pygame detects the directional pad as 4 buttons
    (vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NONE, (0, 0, 0, 0)),
    (vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NORTHWEST, (1, 0, 1, 0)),
    (vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_WEST, (0, 0, 1, 0)),
    (vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_SOUTHWEST, (0, 1, 1, 0)),
    (vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_SOUTH, (0, 1, 0, 0)),
    (vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_SOUTHEAST, (0, 1, 0, 1)),
    (vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_EAST, (0, 0, 0, 1)),
    (vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NORTHEAST, (1, 0, 0, 1)),
    (vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NORTH, (1, 0, 0, 0)),
    ] if SYSTEM == "Windows" else [  # FIXME: On Linux, pygame detects the directional pad as a hat with 2 axes
    (vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NONE, (0, 0)),
    (vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NORTHWEST, (-1, 1)),
    (vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_WEST, (-1, 0)),
    (vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_SOUTHWEST, (-1, -1)),
    (vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_SOUTH, (0, -1)),
    (vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_SOUTHEAST, (1, -1)),
    (vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_EAST, (1, 0)),
    (vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NORTHEAST, (1, 1)),
    (vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NORTH, (0, 1)),
    ]

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


class TestVDS4Gamepad(unittest.TestCase):

    def setUp(self):
        print(f"Setting up VDS4Gamepad")

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
        self.assertTrue(name == DS4_NAME)
        self.assertEqual(nb_axes, 6)
        self.assertEqual(nb_balls, 0)
        self.assertEqual(nb_buttons, DS4_NB_BUTTONS)
        self.assertEqual(nb_hats, DS4_NB_HATS)

        # Check that buttons are correct:

        tested_buttons = DS4_TEST_BUTTONS

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

        # Check that special buttons are correct:

        tested_special_buttons = DS4_TEST_SPECIAL_BUTTONS

        for v_button, j_button in tested_special_buttons:
            self.g.press_special_button(special_button=v_button)
            self.g.update()
            time.sleep(WAIT_S)

            _ = pygame.event.get()
            print(f"Testing: {v_button, j_button}")

            self.assertTrue(j.get_button(j_button))

            for i in range(nb_buttons):
                if i != j_button:
                    self.assertFalse(j.get_button(i))

            self.g.release_special_button(special_button=v_button)
            self.g.update()
            time.sleep(WAIT_S)

        # Check that directional pad is correct:

        tested_values = DS4_TEST_DIRECTIONAL_PAD

        for v_value, j_value in tested_values:
            self.g.directional_pad(direction=v_value)
            self.g.update()
            time.sleep(WAIT_S)

            _ = pygame.event.get()

            print(f"Testing: {v_value, j_value}")

            if SYSTEM == "Windows":
                self.assertEqual(j.get_button(DS4_DIRECTIONAL_PAD[0]), j_value[0])
                self.assertEqual(j.get_button(DS4_DIRECTIONAL_PAD[1]), j_value[1])
                self.assertEqual(j.get_button(DS4_DIRECTIONAL_PAD[2]), j_value[2])
                self.assertEqual(j.get_button(DS4_DIRECTIONAL_PAD[3]), j_value[3])
            else:
                self.assertEqual(j.get_hat(0), j_value)

            self.g.reset()
            self.g.update()
            time.sleep(WAIT_S)

        # Check that triggers are correct (absolute):

        tested_values = DS4_TEST_TRIGGER_INT

        # Left trigger:

        for v_value, j_value in tested_values:
            self.g.left_trigger(value=v_value)
            self.g.update()
            time.sleep(WAIT_S)

            _ = pygame.event.get()
            print(f"Testing: {v_value, j_value}")
            self.assertAlmostEqual(j.get_axis(DS4_LEFT_TRIGGER), j_value, delta=0.01)

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
            self.assertAlmostEqual(j.get_axis(DS4_RIGHT_TRIGGER), j_value, delta=0.01)

            self.g.reset()
            self.g.update()
            time.sleep(WAIT_S)

        # Check that triggers are correct (float):

        tested_values = DS4_TEST_TRIGGER_FLOAT

        # Left trigger:

        for v_value, j_value in tested_values:
            self.g.left_trigger_float(value_float=v_value)
            self.g.update()
            time.sleep(WAIT_S)

            _ = pygame.event.get()
            print(f"Testing: {v_value, j_value}")
            self.assertAlmostEqual(j.get_axis(DS4_LEFT_TRIGGER), j_value, delta=0.01)

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
            self.assertAlmostEqual(j.get_axis(DS4_RIGHT_TRIGGER), j_value, delta=0.01)

            self.g.reset()
            self.g.update()
            time.sleep(WAIT_S)

        # Check that joysticks are correct (absolute):

        tested_values = DS4_TEST_JOYSTICK_INT

        # Left joystick:

        for v_value, j_value in tested_values:
            self.g.left_joystick(x_value=v_value[0], y_value=v_value[1])
            self.g.update()
            time.sleep(WAIT_S)

            _ = pygame.event.get()
            print(f"Testing: {v_value, j_value}")
            self.assertAlmostEqual(j.get_axis(DS4_LEFT_JOYSTICK[0]), j_value[0], delta=0.01)
            self.assertAlmostEqual(j.get_axis(DS4_LEFT_JOYSTICK[1]), j_value[1], delta=0.01)

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
            self.assertAlmostEqual(j.get_axis(DS4_RIGHT_JOYSTICK[0]), j_value[0], delta=0.01)
            self.assertAlmostEqual(j.get_axis(DS4_RIGHT_JOYSTICK[1]), j_value[1], delta=0.01)

            self.g.reset()
            self.g.update()
            time.sleep(WAIT_S)

        # Check that joysticks are correct (float):

        tested_values = DS4_TEST_JOYSTICK_FLOAT

        # Left joystick:

        for v_value, j_value in tested_values:
            self.g.left_joystick_float(x_value_float=v_value[0], y_value_float=v_value[1])
            self.g.update()
            time.sleep(WAIT_S)

            _ = pygame.event.get()
            print(f"Testing: {v_value, j_value}")
            self.assertAlmostEqual(j.get_axis(DS4_LEFT_JOYSTICK[0]), j_value[0], delta=0.01)
            self.assertAlmostEqual(j.get_axis(DS4_LEFT_JOYSTICK[1]), j_value[1], delta=0.01)

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
            self.assertAlmostEqual(j.get_axis(DS4_RIGHT_JOYSTICK[0]), j_value[0], delta=0.01)
            self.assertAlmostEqual(j.get_axis(DS4_RIGHT_JOYSTICK[1]), j_value[1], delta=0.01)

            self.g.reset()
            self.g.update()
            time.sleep(WAIT_S)

    def tearDown(self):
        del self.g
        pygame.quit()


if __name__ == '__main__':
    unittest.main(verbosity=2)
