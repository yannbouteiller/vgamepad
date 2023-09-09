from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

import time
import unittest

import vgamepad as vg

# we use pygame to test vgamepad
# pygame must be installed to run this script:

import pygame

WAIT_S = 0.1


class TestVX360Gamepad(unittest.TestCase):

    def setUp(self):
        self.g = vg.VX360Gamepad()
        # press a button to wake the device up
        self.g.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
        self.g.update()
        time.sleep(WAIT_S)
        self.g.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
        self.g.update()
        time.sleep(WAIT_S)
        pygame.joystick.init()
        self.joysticks = [pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())]

    def test_all(self):

        # Check that only one gamepad is connected:
        self.assertTrue(len(self.joysticks) == 1)
        j = self.joysticks[0]

        self.assertTrue(j.get_name() == "Xbox360 Controller")
        self.assertEqual(j.get_numaxes(), 6)
        self.assertEqual(j.get_numballs(), 0)
        self.assertEqual(j.get_numbuttons(), 11)
        self.assertEqual(j.get_numhats(), 1)

        # Check buttons:
        tested_buttons = [
            (vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP, None),
            (vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN, None),
            (vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT, None),
            (vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT, None),
            (vg.XUSB_BUTTON.XUSB_GAMEPAD_START, None),
            (vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK, None),
            (vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB, None),
            (vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB, None),
            (vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER, None),
            (vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER, None),
            (vg.XUSB_BUTTON.XUSB_GAMEPAD_GUIDE, None),
            (vg.XUSB_BUTTON.XUSB_GAMEPAD_A, None),
            (vg.XUSB_BUTTON.XUSB_GAMEPAD_B, None),
            (vg.XUSB_BUTTON.XUSB_GAMEPAD_X, None),
            (vg.XUSB_BUTTON.XUSB_GAMEPAD_Y, None)
        ]

        # self.assertRaises(AssertionError, lambda : cons.pop(max_items=0, blocking=False))

    def tearDown(self):
        del self.g
        pygame.joystick.quit()


if __name__ == '__main__':
    unittest.main(verbosity=2)
