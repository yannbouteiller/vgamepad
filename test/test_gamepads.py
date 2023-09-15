from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

import copy
import time
import unittest
from threading import Thread, Lock
from multiprocessing import Process

import vgamepad as vg

# We use pygame to test vgamepad.
# pygame must be installed to run these tests.
# Furthermore, these tests can only run with a display (pygame requirement).

import pygame

pygame.init()

WAIT_S = 0.1

# First, the cool pygame display stuff.
# (adapted from https://github.com/pygame-community/pygame-ce/blob/main/examples/joystick.py)


def indent(text, indentation_level=0):
    return ("    " * indentation_level) + text


class JoystickState:
    def __init__(self):
        self.count = 0
        self.name = 0
        self.nb_axes = 0
        self.nb_balls = 0
        self.nb_buttons = 0
        self.nb_hats = 0
        self.axes = {}
        self.balls = {}
        self.buttons = {}
        self.hats = {}

    def set_name(self, name):
        self.name = name

    def set_count(self, count):
        self.count = count

    def set_numaxes(self, nb_axes):
        self.nb_axes = nb_axes
        for i in range(self.nb_axes):
            self.axes[i] = None

    def set_numballs(self, nb_balls):
        self.nb_balls = nb_balls
        for i in range(self.nb_balls):
            self.balls[i] = None

    def set_numbuttons(self, nb_buttons):
        self.nb_buttons = nb_buttons
        for i in range(self.nb_buttons):
            self.buttons[i] = None

    def set_numhats(self, nb_hats):
        self.nb_hats = nb_hats
        for i in range(self.nb_hats):
            self.hats[i] = None

    def set_axis(self, j_axis, val):
        self.axes[j_axis] = val

    def set_ball(self, j_ball, val):
        self.balls[j_ball] = val

    def set_button(self, j_button, val):
        self.buttons[j_button] = val

    def set_hat(self, j_hat, val):
        self.hats[j_hat] = val

    def get_count(self):
        return self.count

    def get_name(self):
        return self.name

    def get_numaxes(self):
        return self.nb_axes

    def get_numballs(self):
        return self.nb_balls

    def get_numbuttons(self):
        return self.nb_buttons

    def get_numhats(self):
        return self.nb_hats

    def get_axis(self, j_axis):
        return self.axes[j_axis]

    def get_ball(self, j_ball):
        return self.balls[j_ball]

    def get_button(self, j_button):
        return self.buttons[j_button]

    def get_hat(self, j_hat):
        return self.hats[j_hat]


class PygameWindow:
    def __init__(self):
        self.__lock = Lock()
        self.__done = False
        self.__j = JoystickState()
        self.__signal_start = False
        self.__signal_end = False

        self.__t = Thread(target=self.main_loop, daemon=True)
        self.__t.start()

    def stop(self):
        with self.__lock:
            self.__done = True
        self.__t.join()

    def pump(self, sleep_duration):
        with self.__lock:
            self.__signal_start = True
        done = False
        while not done:
            time.sleep(sleep_duration)
            with self.__lock:
                done = self.__signal_end
                if done:
                    self.__signal_end = False

    def get_joystick_state(self, sleep_duration=0.02):
        self.pump(sleep_duration)
        with self.__lock:
            res = copy.deepcopy(self.__j)
        return res

    def main_loop(self):

        # pygame.init()

        # Set the size of the screen (width, height), and name the window.
        size = (500, 700)
        screen = pygame.display.set_mode(size)
        pygame.display.set_caption("Joystick")

        # Used to manage how fast the screen updates.
        clock = pygame.Clock()

        # Get ready to print.
        font = pygame.font.SysFont(None, 25)
        wraplength = size[0] - 20

        # This dict can be left as-is, since pygame-ce will generate a
        # pygame.JOYDEVICEADDED event for every joystick connected
        # at the start of the program.
        joysticks = {}

        with self.__lock:
            done = self.__done

        while not done:

            with self.__lock:
                if self.__signal_start:
                    pumping = True
                    self.__signal_start = False
                else:
                    pumping = False

            # Event processing step.
            # Possible joystick events: JOYAXISMOTION, JOYBALLMOTION, JOYBUTTONDOWN,
            # JOYBUTTONUP, JOYHATMOTION, JOYDEVICEADDED, JOYDEVICEREMOVED
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    done = True  # Flag that we are done so we exit this loop.

                if event.type == pygame.JOYBUTTONDOWN:
                    print("Joystick button pressed.")
                    if event.button == 0:
                        joystick = joysticks[event.instance_id]
                        if joystick.rumble(0, 0.7, 500):
                            pass
                            print(f"Rumble effect played on joystick {event.instance_id}")

                if event.type == pygame.JOYBUTTONUP:
                    print("Joystick button released.")

                # Handle hotplugging
                if event.type == pygame.JOYDEVICEADDED:
                    # This event will be generated when the program starts for every
                    # joystick, filling up the list without needing to create them manually.
                    joy = pygame.joystick.Joystick(event.device_index)
                    joysticks[joy.get_instance_id()] = joy
                    print(f"Joystick {joy.get_instance_id()} connected")

                if event.type == pygame.JOYDEVICEREMOVED:
                    if event.instance_id in joysticks:
                        del joysticks[event.instance_id]
                        print(f"Joystick {event.instance_id} disconnected")
                    else:
                        pass
                        # print(
                        #     f"Tried to disconnect Joystick {event.instance_id}, "
                        #     "but couldn't find it in the joystick list"
                        # )

            # Drawing step
            # First, clear the screen to white. Don't put other drawing commands
            # above this, or they will be erased with this command.
            screen.fill((255, 255, 255))
            indentation = 0
            lines = []

            # Get count of joysticks.
            joystick_count = pygame.joystick.get_count()
            with self.__lock:
                self.__j.set_count(joystick_count)
            lines.append(indent(f"Number of joysticks: {joystick_count}", indentation))
            indentation += 1

            # For each joystick:
            for joystick in joysticks.values():
                jid = joystick.get_instance_id()

                lines.append(indent(f"Joystick {jid}", indentation))
                indentation += 1

                # Get the name from the OS for the controller/joystick.
                name = joystick.get_name()
                with self.__lock:
                    self.__j.set_name(name)
                lines.append(indent(f"Joystick name: {name}", indentation))

                guid = joystick.get_guid()
                lines.append(indent(f"GUID: {guid}", indentation))

                power_level = joystick.get_power_level()
                lines.append(indent(f"Joystick's power level: {power_level}", indentation))

                # Usually axis run in pairs, up/down for one, and left/right for
                # the other. Triggers count as axes.
                axes = joystick.get_numaxes()
                with self.__lock:
                    self.__j.set_numaxes(axes)
                lines.append(indent(f"Number of axes: {axes}", indentation))
                indentation += 1

                for i in range(axes):
                    axis = joystick.get_axis(i)
                    with self.__lock:
                        self.__j.set_axis(i, axis)
                    lines.append(indent(f"Axis {i} value: {axis:>6.3f}", indentation))
                indentation -= 1

                buttons = joystick.get_numbuttons()
                with self.__lock:
                    self.__j.set_numbuttons(buttons)
                lines.append(indent(f"Number of buttons: {buttons}", indentation))
                indentation += 1

                for i in range(buttons):
                    button = joystick.get_button(i)
                    with self.__lock:
                        self.__j.set_button(i, button)
                    lines.append(indent(f"Button {i:>2} value: {button}", indentation))
                indentation -= 1

                hats = joystick.get_numhats()
                with self.__lock:
                    self.__j.set_numhats(hats)
                lines.append(indent(f"Number of hats: {hats}", indentation))
                indentation += 1

                # Hat position. All or nothing for direction, not a float like
                # get_axis(). Position is a tuple of int values (x, y).
                for i in range(hats):
                    hat = joystick.get_hat(i)
                    with self.__lock:
                        self.__j.set_hat(i, hat)
                    lines.append(indent(f"Hat {i} value: {str(hat)}", indentation))
                indentation -= 2

            # draw the accumulated text
            screen.blit(
                font.render("\n".join(lines), True, "black", "white", wraplength), (10, 10)
            )

            # Go ahead and update the screen with what we've drawn.
            pygame.display.flip()

            # Limit to 30 frames per second.
            clock.tick(30)

            if not done:
                with self.__lock:
                    done = self.__done

            if pumping:
                with self.__lock:
                    self.__signal_end = True

        pygame.quit()


class TestVX360Gamepad(unittest.TestCase):

    def setUp(self):
        pass

    def test_all(self):

        self.pw = PygameWindow()

        self.g = vg.VX360Gamepad()
        # press a button to wake the device up
        self.g.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
        self.g.update()
        time.sleep(WAIT_S + 1)

        self.g.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
        self.g.update()
        time.sleep(WAIT_S + 1)

        self.g.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
        self.g.update()
        time.sleep(WAIT_S + 1)

        self.g.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
        self.g.update()
        time.sleep(WAIT_S + 1)

        self.g.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
        self.g.update()
        time.sleep(WAIT_S + 1)

        self.g.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
        self.g.update()
        time.sleep(WAIT_S + 1)

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

        self.g.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
        self.g.update()
        time.sleep(WAIT_S + 2)

        print("hey")

        # Check that only one gamepad is connected:

        j = self.pw.get_joystick_state()

        # Check that gamepad properties are correct:
        name = j.get_name()
        nb_axes = j.get_numaxes()
        nb_balls = j.get_numballs()
        nb_buttons = j.get_numbuttons()
        nb_hats = j.get_numhats()
        self.assertTrue(name == "Xbox 360 Controller")
        self.assertEqual(nb_axes, 6)
        self.assertEqual(nb_balls, 0)
        self.assertEqual(nb_buttons, 11)
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
            # (vg.XUSB_BUTTON.XUSB_GAMEPAD_GUIDE, 10),
        ]

        for v_button, j_button in tested_buttons:
            print("yo")
            self.g.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
            self.g.update()
            time.sleep(WAIT_S + 1)

            self.g.press_button(button=v_button)
            self.g.update()
            print("bih")
            time.sleep(WAIT_S + 1)
            print("bah")

            j = self.pw.get_joystick_state()
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

            j = self.pw.get_joystick_state()
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

            j = self.pw.get_joystick_state()
            self.assertAlmostEqual(j.get_axis(4), j_value, delta=0.01)

            self.g.reset()
            self.g.update()
            time.sleep(WAIT_S)

        # Right trigger:

        for v_value, j_value in tested_values:
            self.g.right_trigger(value=v_value)
            self.g.update()
            time.sleep(WAIT_S)

            j = self.pw.get_joystick_state()
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

            j = self.pw.get_joystick_state()
            self.assertAlmostEqual(j.get_axis(4), j_value, delta=0.01)

            self.g.reset()
            self.g.update()
            time.sleep(WAIT_S)

        # Right trigger:

        for v_value, j_value in tested_values:
            self.g.right_trigger_float(value_float=v_value)
            self.g.update()
            time.sleep(WAIT_S)

            j = self.pw.get_joystick_state()
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

            j = self.pw.get_joystick_state()
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

            j = self.pw.get_joystick_state()
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

            j = self.pw.get_joystick_state()
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

            j = self.pw.get_joystick_state()
            self.assertAlmostEqual(j.get_axis(2), j_value[0], delta=0.001)
            self.assertAlmostEqual(j.get_axis(3), j_value[1], delta=0.001)

            self.g.reset()
            self.g.update()
            time.sleep(WAIT_S)

    def tearDown(self):
        self.pw.stop()
        del self.g


if __name__ == '__main__':
    unittest.main(verbosity=2)
