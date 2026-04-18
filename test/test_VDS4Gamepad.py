# mypy: disable-error-code="assignment,arg-type,index"
import platform
from os import environ

environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

import logging
import time
import unittest
from typing import Any, Optional

import pygame

import vgamepad as vg

log = logging.getLogger(__name__)

WAIT_S = 0.1
SYSTEM = platform.system()

DS4_NAME = "PS4 Controller" if SYSTEM == "Windows" else "Sony Interactive Entertainment Wireless Controller"
DS4_NB_BUTTONS = 16 if SYSTEM == "Windows" else 14
DS4_NB_HATS = 0 if SYSTEM == "Windows" else 1

DS4_LEFT_TRIGGER = 4 if SYSTEM == "Windows" else 2
DS4_RIGHT_TRIGGER = 5
DS4_LEFT_JOYSTICK = (0, 1)
DS4_RIGHT_JOYSTICK = (2, 3) if SYSTEM == "Windows" else (3, 4)
DS4_DIRECTIONAL_PAD = (11, 12, 13, 14) if SYSTEM == "Windows" else None

DS4_TEST_BUTTONS = (
    [
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
    ]
    if SYSTEM == "Windows"
    else [
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
)

DS4_TEST_SPECIAL_BUTTONS = (
    [
        (vg.DS4_SPECIAL_BUTTONS.DS4_SPECIAL_BUTTON_PS, 5),
        (vg.DS4_SPECIAL_BUTTONS.DS4_SPECIAL_BUTTON_TOUCHPAD, 15),
    ]
    if SYSTEM == "Windows"
    else [
        (vg.DS4_SPECIAL_BUTTONS.DS4_SPECIAL_BUTTON_PS, 10),
        (vg.DS4_SPECIAL_BUTTONS.DS4_SPECIAL_BUTTON_TOUCHPAD, 13),
    ]
)

DS4_TEST_DIRECTIONAL_PAD = (
    [
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
    if SYSTEM == "Windows"
    else [
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
)

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


# ===== pygame helpers ======================================================

def _init_pygame_joystick_subsystem() -> None:
    pygame.init()
    if SYSTEM == "Windows" and pygame.display.get_surface() is None:
        try:
            pygame.display.set_mode((1, 1), pygame.HIDDEN)
        except (AttributeError, TypeError):
            pygame.display.set_mode((1, 1))
    pygame.joystick.init()


def _discover_and_verify_ds4(g: Any) -> tuple[Optional[int], bool]:
    """Discover the DS4 SDL joystick and verify SDL can read its input.

    Returns (sdl_index_or_None, sdl_reads_work).
    """
    _init_pygame_joystick_subsystem()
    deadline = time.time() + 3.0
    while time.time() < deadline and pygame.joystick.get_count() < 1:
        time.sleep(0.15)

    n = pygame.joystick.get_count()
    pygame.event.pump()
    g.reset()
    g.update()
    time.sleep(0.1)
    pygame.event.pump()

    # Button probe — also serves as SDL-can-read-input check
    for _ in range(6):
        g.press_button(button=vg.DS4_BUTTONS.DS4_BUTTON_CROSS)
        g.update()
        time.sleep(0.18)
        pygame.event.pump()
        pygame.event.get()
        for i in range(n):
            j = pygame.joystick.Joystick(i)
            j.init()
            pygame.event.pump()
            pygame.event.get()
            if j.get_button(0):
                g.release_button(button=vg.DS4_BUTTONS.DS4_BUTTON_CROSS)
                g.update()
                time.sleep(0.06)
                pygame.event.pump()
                log.debug("DS4 discovery: button probe matched SDL index %s", i)
                return i, True
        g.release_button(button=vg.DS4_BUTTONS.DS4_BUTTON_CROSS)
        g.update()
        time.sleep(0.1)
        pygame.event.pump()

    # Axis probe
    baseline: list[tuple[float, float]] = []
    for i in range(n):
        j = pygame.joystick.Joystick(i)
        j.init()
        pygame.event.pump()
        baseline.append((j.get_axis(0), j.get_axis(1)))
    g.left_joystick(x_value=255, y_value=128)
    g.update()
    time.sleep(0.22)
    pygame.event.pump()
    for i in range(n):
        j = pygame.joystick.Joystick(i)
        j.init()
        pygame.event.pump()
        b0, b1 = baseline[i]
        a0, a1 = j.get_axis(0), j.get_axis(1)
        if abs(a0 - b0) > 0.2 or abs(a1 - b1) > 0.2:
            g.reset()
            g.update()
            time.sleep(0.08)
            pygame.event.pump()
            log.debug("DS4 discovery: axis probe matched SDL index %s", i)
            return i, True
    g.reset()
    g.update()
    pygame.event.pump()

    # Name-only match (SDL can enumerate but NOT read — known SDL 2.28.x issue)
    for i in range(n):
        j = pygame.joystick.Joystick(i)
        j.init()
        pygame.event.pump()
        if (
            j.get_name() == DS4_NAME
            and j.get_numaxes() == 6
            and j.get_numbuttons() == DS4_NB_BUTTONS
            and j.get_numhats() == DS4_NB_HATS
        ):
            log.debug("DS4 discovery: name match at index %s (SDL reads NOT verified)", i)
            return i, False

    log.debug("DS4 discovery failed (n=%s)", n)
    return None, False


def _wait_button(j: Any, button: int, want: bool = True, timeout: float = 3.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        pygame.event.pump()
        if bool(j.get_button(button)) == want:
            return True
        time.sleep(0.02)
    return False


def _wait_hat(j: Any, expected: tuple[int, int], timeout: float = 1.5) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        pygame.event.pump()
        if j.get_hat(0) == expected:
            return True
        time.sleep(0.02)
    return False


def _wait_axis_near(j: Any, axis: int, value: float, delta: float, timeout: float = 1.5) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        pygame.event.pump()
        if abs(j.get_axis(axis) - value) <= delta:
            return True
        time.sleep(0.02)
    return False


def _wait_two_axes(
    j: Any,
    ax0: int, v0: float, d0: float,
    ax1: int, v1: float, d1: float,
    timeout: float = 1.5,
) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        pygame.event.pump()
        if abs(j.get_axis(ax0) - v0) <= d0 and abs(j.get_axis(ax1) - v1) <= d1:
            return True
        time.sleep(0.02)
    return False


def _wait_dpad_four_buttons(
    j: Any,
    indices: tuple[int, int, int, int],
    want: tuple[int, int, int, int],
    timeout: float = 1.5,
) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        pygame.event.pump()
        got = tuple(int(bool(j.get_button(indices[k]))) for k in range(4))
        if got == want:
            return True
        time.sleep(0.02)
    return False


# ===========================================================================

class TestVDS4Gamepad(unittest.TestCase):
    def setUp(self) -> None:
        log.info("Setting up VDS4Gamepad")

        self.g = vg.VDS4Gamepad()
        self.g.press_button(button=vg.DS4_BUTTONS.DS4_BUTTON_CROSS)
        self.g.update()
        time.sleep(WAIT_S)
        self.g.release_button(button=vg.DS4_BUTTONS.DS4_BUTTON_CROSS)
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

        idx, self._sdl_reads_work = _discover_and_verify_ds4(self.g)
        self._sdl_joy_index: Optional[int] = idx

    def test_all(self) -> None:
        self.assertIn(SYSTEM, ("Windows", "Linux"))

        if self._sdl_joy_index is None:
            self.skipTest(
                "No SDL joystick matched this ViGEm DS4 device. "
                "Disconnect other gamepads or fix SDL/ViGEm; on WSL see readme/linux.md."
            )

        if not self._sdl_reads_work:
            self.skipTest(
                f"SDL {'.'.join(map(str, pygame.get_sdl_version()))} enumerates the DS4 device "
                "but cannot read its input (known limitation with ViGEm + certain SDL builds on Windows). "
                "DS4 has no XInput fallback. Run on Linux or upgrade pygame/SDL for full DS4 input tests."
            )

        j = pygame.joystick.Joystick(self._sdl_joy_index)
        j.init()

        self.assertEqual(j.get_name(), DS4_NAME)
        self.assertEqual(j.get_numaxes(), 6)
        self.assertEqual(j.get_numballs(), 0)
        self.assertEqual(j.get_numbuttons(), DS4_NB_BUTTONS)
        self.assertEqual(j.get_numhats(), DS4_NB_HATS)

        nb_buttons = j.get_numbuttons()

        for v_button, j_button in DS4_TEST_BUTTONS:
            self.g.press_button(button=v_button)
            self.g.update()
            time.sleep(WAIT_S)
            pygame.event.pump()
            log.debug("Testing button: %s -> %s", v_button, j_button)
            self.assertTrue(_wait_button(j, j_button, True), f"button {j_button} did not assert for {v_button}")
            for i in range(nb_buttons):
                if i != j_button:
                    self.assertFalse(j.get_button(i))
            self.g.release_button(button=v_button)
            self.g.update()
            time.sleep(WAIT_S)

        for v_button, j_button in DS4_TEST_SPECIAL_BUTTONS:
            self.g.press_special_button(special_button=v_button)
            self.g.update()
            time.sleep(WAIT_S)
            pygame.event.pump()
            log.debug("Testing special button: %s -> %s", v_button, j_button)
            self.assertTrue(_wait_button(j, j_button, True), f"special button {j_button} for {v_button}")
            for i in range(nb_buttons):
                if i != j_button:
                    self.assertFalse(j.get_button(i))
            self.g.release_special_button(special_button=v_button)
            self.g.update()
            time.sleep(WAIT_S)

        for v_value, j_value in DS4_TEST_DIRECTIONAL_PAD:
            self.g.directional_pad(direction=v_value)
            self.g.update()
            time.sleep(WAIT_S)
            pygame.event.pump()
            log.debug("Testing dpad: %s -> %s", v_value, j_value)
            if SYSTEM == "Windows":
                assert DS4_DIRECTIONAL_PAD is not None
                self.assertTrue(
                    _wait_dpad_four_buttons(j, DS4_DIRECTIONAL_PAD, j_value),
                    f"dpad buttons {j_value}",
                )
            else:
                self.assertTrue(_wait_hat(j, j_value), f"dpad hat {j_value}")
            self.g.reset()
            self.g.update()
            time.sleep(WAIT_S)

        for v_value, j_value in DS4_TEST_TRIGGER_INT:
            self.g.left_trigger(value=v_value)
            self.g.update()
            time.sleep(WAIT_S)
            pygame.event.pump()
            self.assertTrue(
                _wait_axis_near(j, DS4_LEFT_TRIGGER, j_value, 0.01),
                f"left trigger int {v_value} -> {j_value}",
            )
            self.g.reset()
            self.g.update()
            time.sleep(WAIT_S)

        for v_value, j_value in DS4_TEST_TRIGGER_INT:
            self.g.right_trigger(value=v_value)
            self.g.update()
            time.sleep(WAIT_S)
            pygame.event.pump()
            self.assertTrue(
                _wait_axis_near(j, DS4_RIGHT_TRIGGER, j_value, 0.01),
                f"right trigger int {v_value} -> {j_value}",
            )
            self.g.reset()
            self.g.update()
            time.sleep(WAIT_S)

        for v_value, j_value in DS4_TEST_TRIGGER_FLOAT:
            self.g.left_trigger_float(value_float=v_value)
            self.g.update()
            time.sleep(WAIT_S)
            pygame.event.pump()
            self.assertTrue(
                _wait_axis_near(j, DS4_LEFT_TRIGGER, j_value, 0.01),
                f"left trigger float {v_value} -> {j_value}",
            )
            self.g.reset()
            self.g.update()
            time.sleep(WAIT_S)

        for v_value, j_value in DS4_TEST_TRIGGER_FLOAT:
            self.g.right_trigger_float(value_float=v_value)
            self.g.update()
            time.sleep(WAIT_S)
            pygame.event.pump()
            self.assertTrue(
                _wait_axis_near(j, DS4_RIGHT_TRIGGER, j_value, 0.01),
                f"right trigger float {v_value} -> {j_value}",
            )
            self.g.reset()
            self.g.update()
            time.sleep(WAIT_S)

        for v_value, j_value in DS4_TEST_JOYSTICK_INT:
            self.g.left_joystick(x_value=v_value[0], y_value=v_value[1])
            self.g.update()
            time.sleep(WAIT_S)
            pygame.event.pump()
            self.assertTrue(
                _wait_two_axes(j, DS4_LEFT_JOYSTICK[0], j_value[0], 0.01,
                               DS4_LEFT_JOYSTICK[1], j_value[1], 0.01),
                f"left joystick int {v_value} -> {j_value}",
            )
            self.g.reset()
            self.g.update()
            time.sleep(WAIT_S)

        for v_value, j_value in DS4_TEST_JOYSTICK_INT:
            self.g.right_joystick(x_value=v_value[0], y_value=v_value[1])
            self.g.update()
            time.sleep(WAIT_S)
            pygame.event.pump()
            self.assertTrue(
                _wait_two_axes(j, DS4_RIGHT_JOYSTICK[0], j_value[0], 0.01,
                               DS4_RIGHT_JOYSTICK[1], j_value[1], 0.01),
                f"right joystick int {v_value} -> {j_value}",
            )
            self.g.reset()
            self.g.update()
            time.sleep(WAIT_S)

        for v_value, j_value in DS4_TEST_JOYSTICK_FLOAT:
            self.g.left_joystick_float(x_value_float=v_value[0], y_value_float=v_value[1])
            self.g.update()
            time.sleep(WAIT_S)
            pygame.event.pump()
            self.assertTrue(
                _wait_two_axes(j, DS4_LEFT_JOYSTICK[0], j_value[0], 0.01,
                               DS4_LEFT_JOYSTICK[1], j_value[1], 0.01),
                f"left joystick float {v_value} -> {j_value}",
            )
            self.g.reset()
            self.g.update()
            time.sleep(WAIT_S)

        for v_value, j_value in DS4_TEST_JOYSTICK_FLOAT:
            self.g.right_joystick_float(x_value_float=v_value[0], y_value_float=v_value[1])
            self.g.update()
            time.sleep(WAIT_S)
            pygame.event.pump()
            self.assertTrue(
                _wait_two_axes(j, DS4_RIGHT_JOYSTICK[0], j_value[0], 0.01,
                               DS4_RIGHT_JOYSTICK[1], j_value[1], 0.01),
                f"right joystick float {v_value} -> {j_value}",
            )
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
        if pygame.get_init():
            pygame.quit()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s %(message)s")
    unittest.main(verbosity=2)
