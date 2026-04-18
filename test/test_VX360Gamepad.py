# mypy: disable-error-code="assignment,index"
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

X360_SDL_NAME = "Xbox 360 Controller"

# ---------------------------------------------------------------------------
# pygame / SDL axis indices (Linux vs Windows differ)
# ---------------------------------------------------------------------------
X360_LEFT_TRIGGER = 4 if SYSTEM == "Windows" else 2
X360_RIGHT_TRIGGER = 5
X360_LEFT_JOYSTICK = (0, 1)
X360_RIGHT_JOYSTICK = (2, 3) if SYSTEM == "Windows" else (3, 4)

# ---------------------------------------------------------------------------
# Test tables — pygame button/hat/axis mapping
# ---------------------------------------------------------------------------
X360_TEST_BUTTONS_PYGAME = [
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

X360_TEST_HAT_PYGAME = [
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

# ---------------------------------------------------------------------------
# XInput test tables — XUSB_BUTTON values match XInput wButtons directly
# ---------------------------------------------------------------------------
X360_ALL_BUTTONS_XINPUT = [
    vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
    vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
    vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
    vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
    vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
    vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
    vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
    vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
    vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,
    vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB,
    vg.XUSB_BUTTON.XUSB_GAMEPAD_GUIDE,
    vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP,
    vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN,
    vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT,
    vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT,
]

X360_XINPUT_TRIGGER_INT = [0, 5, 10, 63, 127, 191, 255]

X360_XINPUT_JOYSTICK_INT = [
    (-32768, 0),
    (-16384, 16383),
    (0, 32767),
    (16383, -32768),
    (32767, -16384),
]

X360_XINPUT_JOYSTICK_FLOAT = [
    (-1.0, 0.0),
    (-0.5, 0.5),
    (0.0, 1.0),
    (0.5, -1.0),
    (1.0, -0.5),
]


# ===== pygame helpers (Linux + Windows fallback) ===========================

def _init_pygame_joystick_subsystem() -> None:
    pygame.init()
    if SYSTEM == "Windows" and pygame.display.get_surface() is None:
        try:
            pygame.display.set_mode((1, 1), pygame.HIDDEN)
        except (AttributeError, TypeError):
            pygame.display.set_mode((1, 1))
    pygame.joystick.init()


def _discover_vgamepad_joystick_index_x360(g: Any) -> Optional[int]:
    """Return SDL index of the joystick that reacts to this ViGEm device."""
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

    for _ in range(6):
        g.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
        g.update()
        time.sleep(0.18)
        pygame.event.pump()
        for i in range(n):
            j = pygame.joystick.Joystick(i)
            j.init()
            pygame.event.pump()
            pygame.event.get()
            if j.get_button(0):
                g.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
                g.update()
                time.sleep(0.06)
                pygame.event.pump()
                return i
        g.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
        g.update()
        time.sleep(0.1)
        pygame.event.pump()

    baseline: list[tuple[float, float]] = []
    for i in range(n):
        j = pygame.joystick.Joystick(i)
        j.init()
        pygame.event.pump()
        baseline.append((j.get_axis(0), j.get_axis(1)))
    g.left_joystick(x_value=28000, y_value=0)
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
            return i
    g.reset()
    g.update()
    pygame.event.pump()

    for i in range(n):
        j = pygame.joystick.Joystick(i)
        j.init()
        pygame.event.pump()
        if (
            j.get_name() == X360_SDL_NAME
            and j.get_numaxes() == 6
            and j.get_numbuttons() == 11
            and j.get_numhats() == 1
        ):
            return i
    return None


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


# ===== XInput helpers (Windows) ============================================

def _have_xinput() -> bool:
    if SYSTEM != "Windows":
        return False
    try:
        from _win_xinput import find_slot
        return find_slot() is not None
    except Exception:
        return False


# ===========================================================================

class TestVX360Gamepad(unittest.TestCase):
    def setUp(self) -> None:
        log.info("Setting up VX360Gamepad")

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

        self._use_xinput = False
        self._xinput_slot: Optional[int] = None
        self._sdl_joy_index: Optional[int] = None

        if SYSTEM == "Windows":
            try:
                from _win_xinput import find_slot, get_state
                slot = find_slot()
                if slot is not None:
                    get_state(slot)  # ensure connection is live
                    self.g.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_B)
                    self.g.update()
                    time.sleep(0.15)
                    st2 = get_state(slot)
                    if st2 is not None and (st2.Gamepad.wButtons & vg.XUSB_BUTTON.XUSB_GAMEPAD_B.value):
                        self._use_xinput = True
                        self._xinput_slot = slot
                        log.debug("Using XInput slot %s for verification", slot)
                    self.g.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_B)
                    self.g.update()
                    time.sleep(0.1)
            except Exception:
                pass

        if not self._use_xinput:
            idx = _discover_vgamepad_joystick_index_x360(self.g)
            self._sdl_joy_index = idx

    def test_all(self) -> None:
        self.assertIn(SYSTEM, ("Windows", "Linux"))

        if self._use_xinput:
            self._test_all_xinput()
        elif self._sdl_joy_index is not None:
            self._test_all_pygame()
        else:
            self.skipTest(
                "No readable joystick found. SDL may not read ViGEm on this Windows/SDL build. "
                "XInput DLL was also unavailable. See readme for details."
            )

    # -- XInput verification (Windows) --------------------------------------

    def _test_all_xinput(self) -> None:
        from _win_xinput import get_state

        slot = self._xinput_slot
        assert slot is not None

        # Buttons: XUSB_BUTTON enum values == XInput wButtons bits
        for btn in X360_ALL_BUTTONS_XINPUT:
            self.g.press_button(button=btn)
            self.g.update()
            time.sleep(WAIT_S)
            st = get_state(slot)
            assert st is not None
            log.debug("XInput button %s (0x%04x) -> wButtons=0x%04x", btn.name, btn.value, st.Gamepad.wButtons)
            self.assertTrue(
                st.Gamepad.wButtons & btn.value,
                f"XInput wButtons should have bit 0x{btn.value:04x} for {btn.name} "
                f"(got 0x{st.Gamepad.wButtons:04x})",
            )
            # No other button bits set (except Guide may be hidden by some XInput versions)
            other_bits = st.Gamepad.wButtons & ~btn.value
            if btn != vg.XUSB_BUTTON.XUSB_GAMEPAD_GUIDE:
                self.assertEqual(other_bits, 0, f"unexpected extra bits 0x{other_bits:04x} for {btn.name}")
            self.g.release_button(button=btn)
            self.g.update()
            time.sleep(WAIT_S)
            st = get_state(slot)
            assert st is not None
            self.assertEqual(
                st.Gamepad.wButtons & btn.value, 0,
                f"bit 0x{btn.value:04x} still set after release",
            )

        # Triggers (int)
        for v_val in X360_XINPUT_TRIGGER_INT:
            self.g.left_trigger(value=v_val)
            self.g.update()
            time.sleep(WAIT_S)
            st = get_state(slot)
            assert st is not None
            log.debug("XInput left trigger int %s -> bLeftTrigger=%s", v_val, st.Gamepad.bLeftTrigger)
            self.assertEqual(st.Gamepad.bLeftTrigger, v_val)
            self.g.reset()
            self.g.update()
            time.sleep(WAIT_S)

        for v_val in X360_XINPUT_TRIGGER_INT:
            self.g.right_trigger(value=v_val)
            self.g.update()
            time.sleep(WAIT_S)
            st = get_state(slot)
            assert st is not None
            log.debug("XInput right trigger int %s -> bRightTrigger=%s", v_val, st.Gamepad.bRightTrigger)
            self.assertEqual(st.Gamepad.bRightTrigger, v_val)
            self.g.reset()
            self.g.update()
            time.sleep(WAIT_S)

        # Triggers (float)
        for v_float in [0.0, 0.5, 1.0]:
            expected = round(v_float * 255)
            self.g.left_trigger_float(value_float=v_float)
            self.g.update()
            time.sleep(WAIT_S)
            st = get_state(slot)
            assert st is not None
            log.debug("XInput left trigger float %s -> bLeftTrigger=%s (expect %s)", v_float, st.Gamepad.bLeftTrigger, expected)
            self.assertAlmostEqual(st.Gamepad.bLeftTrigger, expected, delta=1)
            self.g.reset()
            self.g.update()
            time.sleep(WAIT_S)

        for v_float in [0.0, 0.5, 1.0]:
            expected = round(v_float * 255)
            self.g.right_trigger_float(value_float=v_float)
            self.g.update()
            time.sleep(WAIT_S)
            st = get_state(slot)
            assert st is not None
            log.debug("XInput right trigger float %s -> bRightTrigger=%s (expect %s)", v_float, st.Gamepad.bRightTrigger, expected)
            self.assertAlmostEqual(st.Gamepad.bRightTrigger, expected, delta=1)
            self.g.reset()
            self.g.update()
            time.sleep(WAIT_S)

        # Joystick (int)
        for x_val, y_val in X360_XINPUT_JOYSTICK_INT:
            self.g.left_joystick(x_value=x_val, y_value=y_val)
            self.g.update()
            time.sleep(WAIT_S)
            st = get_state(slot)
            assert st is not None
            log.debug("XInput left stick int (%s,%s) -> (%s,%s)", x_val, y_val, st.Gamepad.sThumbLX, st.Gamepad.sThumbLY)
            self.assertEqual(st.Gamepad.sThumbLX, x_val)
            self.assertEqual(st.Gamepad.sThumbLY, y_val)
            self.g.reset()
            self.g.update()
            time.sleep(WAIT_S)

        for x_val, y_val in X360_XINPUT_JOYSTICK_INT:
            self.g.right_joystick(x_value=x_val, y_value=y_val)
            self.g.update()
            time.sleep(WAIT_S)
            st = get_state(slot)
            assert st is not None
            log.debug("XInput right stick int (%s,%s) -> (%s,%s)", x_val, y_val, st.Gamepad.sThumbRX, st.Gamepad.sThumbRY)
            self.assertEqual(st.Gamepad.sThumbRX, x_val)
            self.assertEqual(st.Gamepad.sThumbRY, y_val)
            self.g.reset()
            self.g.update()
            time.sleep(WAIT_S)

        # Joystick (float)
        for x_f, y_f in X360_XINPUT_JOYSTICK_FLOAT:
            self.g.left_joystick_float(x_value_float=x_f, y_value_float=y_f)
            self.g.update()
            time.sleep(WAIT_S)
            st = get_state(slot)
            assert st is not None
            exp_x = round(x_f * 32767) if x_f >= 0 else round(x_f * 32768)
            exp_y = round(y_f * 32767) if y_f >= 0 else round(y_f * 32768)
            log.debug("XInput left stick float (%.1f,%.1f) -> (%s,%s) expect (%s,%s)",
                       x_f, y_f, st.Gamepad.sThumbLX, st.Gamepad.sThumbLY, exp_x, exp_y)
            self.assertAlmostEqual(st.Gamepad.sThumbLX, exp_x, delta=1)
            self.assertAlmostEqual(st.Gamepad.sThumbLY, exp_y, delta=1)
            self.g.reset()
            self.g.update()
            time.sleep(WAIT_S)

        for x_f, y_f in X360_XINPUT_JOYSTICK_FLOAT:
            self.g.right_joystick_float(x_value_float=x_f, y_value_float=y_f)
            self.g.update()
            time.sleep(WAIT_S)
            st = get_state(slot)
            assert st is not None
            exp_x = round(x_f * 32767) if x_f >= 0 else round(x_f * 32768)
            exp_y = round(y_f * 32767) if y_f >= 0 else round(y_f * 32768)
            log.debug("XInput right stick float (%.1f,%.1f) -> (%s,%s) expect (%s,%s)",
                       x_f, y_f, st.Gamepad.sThumbRX, st.Gamepad.sThumbRY, exp_x, exp_y)
            self.assertAlmostEqual(st.Gamepad.sThumbRX, exp_x, delta=1)
            self.assertAlmostEqual(st.Gamepad.sThumbRY, exp_y, delta=1)
            self.g.reset()
            self.g.update()
            time.sleep(WAIT_S)

    # -- pygame verification (Linux, or Windows when SDL reads work) --------

    def _test_all_pygame(self) -> None:
        assert self._sdl_joy_index is not None
        j = pygame.joystick.Joystick(self._sdl_joy_index)
        j.init()

        self.assertEqual(j.get_name(), X360_SDL_NAME)
        self.assertEqual(j.get_numaxes(), 6)
        self.assertEqual(j.get_numballs(), 0)
        self.assertEqual(j.get_numbuttons(), 11)
        self.assertEqual(j.get_numhats(), 1)

        nb_buttons = j.get_numbuttons()

        for v_button, j_button in X360_TEST_BUTTONS_PYGAME:
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

        for v_hat_button, j_hat_button in X360_TEST_HAT_PYGAME:
            self.g.press_button(button=v_hat_button)
            self.g.update()
            time.sleep(WAIT_S)
            pygame.event.pump()
            log.debug("Testing hat: %s -> %s", v_hat_button, j_hat_button)
            self.assertTrue(_wait_hat(j, j_hat_button), f"hat did not reach {j_hat_button}")
            self.g.release_button(button=v_hat_button)
            self.g.update()
            time.sleep(WAIT_S)

        for v_value, j_value in X360_TEST_TRIGGER_INT:
            self.g.left_trigger(value=v_value)
            self.g.update()
            time.sleep(WAIT_S)
            pygame.event.pump()
            self.assertTrue(
                _wait_axis_near(j, X360_LEFT_TRIGGER, j_value, 0.01),
                f"left trigger int {v_value} -> {j_value}",
            )
            self.g.reset()
            self.g.update()
            time.sleep(WAIT_S)

        for v_value, j_value in X360_TEST_TRIGGER_INT:
            self.g.right_trigger(value=v_value)
            self.g.update()
            time.sleep(WAIT_S)
            pygame.event.pump()
            self.assertTrue(
                _wait_axis_near(j, X360_RIGHT_TRIGGER, j_value, 0.01),
                f"right trigger int {v_value} -> {j_value}",
            )
            self.g.reset()
            self.g.update()
            time.sleep(WAIT_S)

        for v_value, j_value in X360_TEST_TRIGGER_FLOAT:
            self.g.left_trigger_float(value_float=v_value)
            self.g.update()
            time.sleep(WAIT_S)
            pygame.event.pump()
            self.assertTrue(
                _wait_axis_near(j, X360_LEFT_TRIGGER, j_value, 0.01),
                f"left trigger float {v_value} -> {j_value}",
            )
            self.g.reset()
            self.g.update()
            time.sleep(WAIT_S)

        for v_value, j_value in X360_TEST_TRIGGER_FLOAT:
            self.g.right_trigger_float(value_float=v_value)
            self.g.update()
            time.sleep(WAIT_S)
            pygame.event.pump()
            self.assertTrue(
                _wait_axis_near(j, X360_RIGHT_TRIGGER, j_value, 0.01),
                f"right trigger float {v_value} -> {j_value}",
            )
            self.g.reset()
            self.g.update()
            time.sleep(WAIT_S)

        for v_value, j_value in X360_TEST_JOYSTICK_INT:
            self.g.left_joystick(x_value=v_value[0], y_value=v_value[1])
            self.g.update()
            time.sleep(WAIT_S)
            pygame.event.pump()
            self.assertTrue(
                _wait_two_axes(j, X360_LEFT_JOYSTICK[0], j_value[0], 0.001,
                               X360_LEFT_JOYSTICK[1], j_value[1], 0.001),
                f"left joystick int {v_value} -> {j_value}",
            )
            self.g.reset()
            self.g.update()
            time.sleep(WAIT_S)

        for v_value, j_value in X360_TEST_JOYSTICK_INT:
            self.g.right_joystick(x_value=v_value[0], y_value=v_value[1])
            self.g.update()
            time.sleep(WAIT_S)
            pygame.event.pump()
            self.assertTrue(
                _wait_two_axes(j, X360_RIGHT_JOYSTICK[0], j_value[0], 0.001,
                               X360_RIGHT_JOYSTICK[1], j_value[1], 0.001),
                f"right joystick int {v_value} -> {j_value}",
            )
            self.g.reset()
            self.g.update()
            time.sleep(WAIT_S)

        for v_value, j_value in X360_TEST_JOYSTICK_FLOAT:
            self.g.left_joystick_float(x_value_float=v_value[0], y_value_float=v_value[1])
            self.g.update()
            time.sleep(WAIT_S)
            pygame.event.pump()
            self.assertTrue(
                _wait_two_axes(j, X360_LEFT_JOYSTICK[0], j_value[0], 0.001,
                               X360_LEFT_JOYSTICK[1], j_value[1], 0.001),
                f"left joystick float {v_value} -> {j_value}",
            )
            self.g.reset()
            self.g.update()
            time.sleep(WAIT_S)

        for v_value, j_value in X360_TEST_JOYSTICK_FLOAT:
            self.g.right_joystick_float(x_value_float=v_value[0], y_value_float=v_value[1])
            self.g.update()
            time.sleep(WAIT_S)
            pygame.event.pump()
            self.assertTrue(
                _wait_two_axes(j, X360_RIGHT_JOYSTICK[0], j_value[0], 0.001,
                               X360_RIGHT_JOYSTICK[1], j_value[1], 0.001),
                f"right joystick float {v_value} -> {j_value}",
            )
            self.g.reset()
            self.g.update()
            time.sleep(WAIT_S)

    # -- notification test --------------------------------------------------

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
    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s %(message)s")
    unittest.main(verbosity=2)
