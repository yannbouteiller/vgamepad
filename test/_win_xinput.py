"""Minimal XInput reader via ctypes for test verification on Windows.

Uses ordinal 100 (XInputGetStateEx) to include the Guide button.
Falls back to the public XInputGetState if ordinal 100 is unavailable.
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes


class XINPUT_GAMEPAD(ctypes.Structure):
    _fields_ = [
        ("wButtons", wintypes.WORD),
        ("bLeftTrigger", ctypes.c_ubyte),
        ("bRightTrigger", ctypes.c_ubyte),
        ("sThumbLX", ctypes.c_short),
        ("sThumbLY", ctypes.c_short),
        ("sThumbRX", ctypes.c_short),
        ("sThumbRY", ctypes.c_short),
    ]


class XINPUT_STATE(ctypes.Structure):
    _fields_ = [
        ("dwPacketNumber", wintypes.DWORD),
        ("Gamepad", XINPUT_GAMEPAD),
    ]


_dll: ctypes.WinDLL | None = None
_get_state = None


def _load() -> None:
    global _dll, _get_state
    if _dll is not None:
        return
    for name in ("xinput1_4", "xinput1_3", "xinput9_1_0"):
        try:
            _dll = ctypes.WinDLL(name, use_last_error=True)
            break
        except OSError:
            continue
    else:
        raise OSError("No XInput DLL found (xinput1_4 / 1_3 / 9_1_0)")

    # Ordinal 100 = XInputGetStateEx (includes Guide button)
    try:
        fn = getattr(_dll, "XInputGetStateEx", None)
        if fn is None:
            fn = _dll[100]  # type: ignore[index]
        fn.argtypes = [wintypes.DWORD, ctypes.POINTER(XINPUT_STATE)]
        fn.restype = wintypes.DWORD
        _get_state = fn
    except (AttributeError, OSError):
        fn = _dll.XInputGetState
        fn.argtypes = [wintypes.DWORD, ctypes.POINTER(XINPUT_STATE)]
        fn.restype = wintypes.DWORD
        _get_state = fn


def get_state(user_index: int = 0) -> XINPUT_STATE | None:
    """Read XInput state for *user_index* (0-3).  Returns None if disconnected."""
    _load()
    assert _get_state is not None
    state = XINPUT_STATE()
    if _get_state(user_index, ctypes.byref(state)) != 0:
        return None
    return state


def find_slot() -> int | None:
    """Return the first connected XInput slot (0-3), or None."""
    for i in range(4):
        if get_state(i) is not None:
            return i
    return None
