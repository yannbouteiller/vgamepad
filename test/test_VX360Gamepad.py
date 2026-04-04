from os import environ

environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

import platform
import time
import unittest

import pygame
from loguru import logger

import vgamepad as vg

WAIT_S = 0.1
SYSTEM = platform.system()

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
    (vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB, 8),
    (vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB, 9),
    (vg.XUSB_BUTTON.XUSB_GAMEPAD_GUIDE, 10),
]

X360_TEST_HAT = [
    (vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP, (0, 1)),
    (vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN, (0, -1)),
    (vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT, (-1, 0)),
    (vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT, (1, 0)),
]

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

X360_TEST_JOYSTICK_INT = (
    [
        ((-32768, 0), (-1.0, 0.0)),
        ((-16384, 16383), (-0.5, -0.5)),
        ((0, 32767), (0.0, -1.0)),
        ((16383, -32768), (0.5, 1.0)),
        ((32767, -16384), (1.0, 0.5)),
    ]
    if SYSTEM == "Windows"
    else [
        ((-32768, 0), (-1.0, 0.0)),
        ((-16384, 16383), (-0.5, 0.5)),
        ((0, 32767), (0.0, 1.0)),
        ((16383, -32768), (0.5, -1.0)),
        ((32767, -16384), (1.0, -0.5)),
    ]
)

X360_TEST_JOYSTICK_FLOAT = (
    [
        ((-1.0, 0.0), (-1.0, 0.0)),
        ((-0.5, 0.5), (-0.5, -0.5)),
        ((0.0, 1.0), (0.0, -1.0)),
        ((0.5, -1.0), (0.5, 1.0)),
        ((1.0, -0.5), (1.0, 0.5)),
    ]
    if SYSTEM == "Windows"
    else [
        ((-1.0, 0.0), (-1.0, 0.0)),
        ((-0.5, 0.5), (-0.5, 0.5)),
        ((0.0, 1.0), (0.0, 1.0)),
        ((0.5, -1.0), (0.5, -1.0)),
        ((1.0, -0.5), (1.0, -0.5)),
    ]
)


class TestVX360Gamepad(unittest.TestCase):
    def setUp(self) -> None:
        logger.info("Setting up VX360Gamepad")

        self.g = vg.VX360Gamepad()
        self.g.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
        self.g.update()
        time.sleep(WAIT_S)
        self.g.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
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

    def test_all(self) -> None:
        self.assertIn(SYSTEM, ("Windows", "Linux"))
        self.assertEqual(len(self.joysticks), 1)
        j = self.joysticks[0]

        self.assertEqual(j.get_name(), "Xbox 360 Controller")
        self.assertEqual(j.get_numaxes(), 6)
        self.assertEqual(j.get_numballs(), 0)
        self.assertEqual(j.get_numbuttons(), 11)
        self.assertEqual(j.get_numhats(), 1)

        nb_buttons = j.get_numbuttons()

        for v_button, j_button in X360_TEST_BUTTONS:
            self.g.press_button(button=v_button)
            self.g.update()
            time.sleep(WAIT_S)
            _ = pygame.event.get()
            logger.debug("Testing button: {} -> {}", v_button, j_button)
            self.assertTrue(j.get_button(j_button))
            for i in range(nb_buttons):
                if i != j_button:
                    self.assertFalse(j.get_button(i))
            self.g.release_button(button=v_button)
            self.g.update()
            time.sleep(WAIT_S)

        for v_hat_button, j_hat_button in X360_TEST_HAT:
            self.g.press_button(button=v_hat_button)
            self.g.update()
            time.sleep(WAIT_S)
            _ = pygame.event.get()
            logger.debug("Testing hat: {} -> {}", v_hat_button, j_hat_button)
            self.assertEqual(j.get_hat(0), j_hat_button)
            self.g.release_button(button=v_hat_button)
            self.g.update()
            time.sleep(WAIT_S)

        for v_value, j_value in X360_TEST_TRIGGER_INT:
            self.g.left_trigger(value=v_value)
            self.g.update()
            time.sleep(WAIT_S)
            _ = pygame.event.get()
            logger.debug("Testing left trigger int: {} -> {}", v_value, j_value)
            self.assertAlmostEqual(j.get_axis(X360_LEFT_TRIGGER), j_value, delta=0.01)
            self.g.reset()
            self.g.update()
            time.sleep(WAIT_S)

        for v_value, j_value in X360_TEST_TRIGGER_INT:
            self.g.right_trigger(value=v_value)
            self.g.update()
            time.sleep(WAIT_S)
            _ = pygame.event.get()
            logger.debug("Testing right trigger int: {} -> {}", v_value, j_value)
            self.assertAlmostEqual(j.get_axis(X360_RIGHT_TRIGGER), j_value, delta=0.01)
            self.g.reset()
            self.g.update()
            time.sleep(WAIT_S)

        for v_value, j_value in X360_TEST_TRIGGER_FLOAT:
            self.g.left_trigger_float(value_float=v_value)
            self.g.update()
            time.sleep(WAIT_S)
            _ = pygame.event.get()
            logger.debug("Testing left trigger float: {} -> {}", v_value, j_value)
            self.assertAlmostEqual(j.get_axis(X360_LEFT_TRIGGER), j_value, delta=0.01)
            self.g.reset()
            self.g.update()
            time.sleep(WAIT_S)

        for v_value, j_value in X360_TEST_TRIGGER_FLOAT:
            self.g.right_trigger_float(value_float=v_value)
            self.g.update()
            time.sleep(WAIT_S)
            _ = pygame.event.get()
            logger.debug("Testing right trigger float: {} -> {}", v_value, j_value)
            self.assertAlmostEqual(j.get_axis(X360_RIGHT_TRIGGER), j_value, delta=0.01)
            self.g.reset()
            self.g.update()
            time.sleep(WAIT_S)

        for v_value, j_value in X360_TEST_JOYSTICK_INT:
            self.g.left_joystick(x_value=v_value[0], y_value=v_value[1])
            self.g.update()
            time.sleep(WAIT_S)
            _ = pygame.event.get()
            logger.debug("Testing left joystick int: {} -> {}", v_value, j_value)
            self.assertAlmostEqual(j.get_axis(X360_LEFT_JOYSTICK[0]), j_value[0], delta=0.001)
            self.assertAlmostEqual(j.get_axis(X360_LEFT_JOYSTICK[1]), j_value[1], delta=0.001)
            self.g.reset()
            self.g.update()
            time.sleep(WAIT_S)

        for v_value, j_value in X360_TEST_JOYSTICK_INT:
            self.g.right_joystick(x_value=v_value[0], y_value=v_value[1])
            self.g.update()
            time.sleep(WAIT_S)
            _ = pygame.event.get()
            logger.debug("Testing right joystick int: {} -> {}", v_value, j_value)
            self.assertAlmostEqual(j.get_axis(X360_RIGHT_JOYSTICK[0]), j_value[0], delta=0.001)
            self.assertAlmostEqual(j.get_axis(X360_RIGHT_JOYSTICK[1]), j_value[1], delta=0.001)
            self.g.reset()
            self.g.update()
            time.sleep(WAIT_S)

        for v_value, j_value in X360_TEST_JOYSTICK_FLOAT:
            self.g.left_joystick_float(x_value_float=v_value[0], y_value_float=v_value[1])
            self.g.update()
            time.sleep(WAIT_S)
            _ = pygame.event.get()
            logger.debug("Testing left joystick float: {} -> {}", v_value, j_value)
            self.assertAlmostEqual(j.get_axis(X360_LEFT_JOYSTICK[0]), j_value[0], delta=0.001)
            self.assertAlmostEqual(j.get_axis(X360_LEFT_JOYSTICK[1]), j_value[1], delta=0.001)
            self.g.reset()
            self.g.update()
            time.sleep(WAIT_S)

        for v_value, j_value in X360_TEST_JOYSTICK_FLOAT:
            self.g.right_joystick_float(x_value_float=v_value[0], y_value_float=v_value[1])
            self.g.update()
            time.sleep(WAIT_S)
            _ = pygame.event.get()
            logger.debug("Testing right joystick float: {} -> {}", v_value, j_value)
            self.assertAlmostEqual(j.get_axis(X360_RIGHT_JOYSTICK[0]), j_value[0], delta=0.001)
            self.assertAlmostEqual(j.get_axis(X360_RIGHT_JOYSTICK[1]), j_value[1], delta=0.001)
            self.g.reset()
            self.g.update()
            time.sleep(WAIT_S)

    def test_notification(self) -> None:
        """Test that register/unregister notification work without error."""
        received: list = []

        def my_callback(client, target, large_motor, small_motor, led_number, user_data):  # type: ignore[no-untyped-def]
            received.append((large_motor, small_motor, led_number))

        self.g.register_notification(callback_function=my_callback)
        time.sleep(0.2)
        self.g.unregister_notification()

    def tearDown(self) -> None:
        del self.g
        pygame.quit()


if __name__ == "__main__":
    unittest.main(verbosity=2)
