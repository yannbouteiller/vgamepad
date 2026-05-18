# vgamepad

[![PyPI version](https://img.shields.io/pypi/v/vgamepad.svg)](https://pypi.org/project/vgamepad/)
[![Python versions](https://img.shields.io/pypi/pyversions/vgamepad.svg)](https://pypi.org/project/vgamepad/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Virtual Xbox 360 and DualShock 4 gamepads in Python.

`vgamepad` is a small Python library that emulates Xbox 360 and DualShock 4 gamepads on your system.
It enables controlling e.g. a video-game that requires analog input, directly from your Python script.

| Windows | Linux |
|:-------:|:-----:|
| Stable  | Stable |

On **Windows**, `vgamepad` wraps Nefarius' [Virtual Gamepad Emulation](https://github.com/nefarius/ViGEmBus) C++ framework.
On **Linux**, `vgamepad` uses `libevdev` to create virtual `uinput` devices.

---

## Table of Contents

- [Installation](#installation)
- [Getting started](#getting-started)
  - [Xbox 360 gamepad](#xbox-360-gamepad)
  - [DualShock 4 gamepad](#dualshock-4-gamepad)
  - [Rumble and LEDs](#rumble-and-leds)
- [Logging](#logging)
- [Advanced](#advanced)
- [Contributing](#contributing)

---

## Installation

### Windows

```bash
pip install vgamepad
```

This automatically runs the installer for the ViGEmBus driver.
Accept the licence agreement, click **Install**, allow the installer to modify your PC, wait for completion and click **Finish**.

> To skip ViGEmBus installation, set the environment variable `VGAMEPAD_SKIP_VIGEMBUS_INSTALL=true` before installing.

### Linux

See [Linux setup notes](readme/linux.md) for `uinput` permissions.

```bash
pip install vgamepad
```

### Development

```bash
pip install -e ".[dev]"
```

This installs `ruff`, `mypy`, `pytest`, and `pygame` for linting, type-checking and testing.

---

## Getting started

`vgamepad` provides two main classes: `VX360Gamepad` (Xbox 360) and `VDS4Gamepad` (DualShock 4).

The state of a virtual gamepad (pressed buttons, joystick values, etc.) is called a **report**.
Modify the report with the provided API functions, then call `update()` to send it.

### Xbox 360 gamepad

Create a virtual Xbox 360 gamepad:

```python
import vgamepad as vg

gamepad = vg.VX360Gamepad()
```

As soon as the `VX360Gamepad` object is created, the virtual gamepad is connected and will remain connected until the object is destroyed.

Press and release buttons:

```python
gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT)
gamepad.update()

# (...) A and left hat are pressed...

gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
gamepad.update()
```

All available buttons are defined in `XUSB_BUTTON`:

```python
class XUSB_BUTTON(IntFlag):
    XUSB_GAMEPAD_DPAD_UP = 0x0001
    XUSB_GAMEPAD_DPAD_DOWN = 0x0002
    XUSB_GAMEPAD_DPAD_LEFT = 0x0004
    XUSB_GAMEPAD_DPAD_RIGHT = 0x0008
    XUSB_GAMEPAD_START = 0x0010
    XUSB_GAMEPAD_BACK = 0x0020
    XUSB_GAMEPAD_LEFT_THUMB = 0x0040
    XUSB_GAMEPAD_RIGHT_THUMB = 0x0080
    XUSB_GAMEPAD_LEFT_SHOULDER = 0x0100
    XUSB_GAMEPAD_RIGHT_SHOULDER = 0x0200
    XUSB_GAMEPAD_GUIDE = 0x0400
    XUSB_GAMEPAD_A = 0x1000
    XUSB_GAMEPAD_B = 0x2000
    XUSB_GAMEPAD_X = 0x4000
    XUSB_GAMEPAD_Y = 0x8000
```

Triggers and joysticks (raw integer values):

```python
gamepad.left_trigger(value=100)  # 0-255
gamepad.right_trigger(value=255)  # 0-255
gamepad.left_joystick(x_value=-10000, y_value=0)  # -32768 to 32767
gamepad.right_joystick(x_value=-32768, y_value=15000)  # -32768 to 32767
gamepad.update()
```

Triggers and joysticks (float values):

```python
gamepad.left_trigger_float(value_float=0.5)  # 0.0-1.0
gamepad.right_trigger_float(value_float=1.0)  # 0.0-1.0
gamepad.left_joystick_float(x_value_float=-0.5, y_value_float=0.0)  # -1.0 to 1.0
gamepad.right_joystick_float(x_value_float=-1.0, y_value_float=0.8)  # -1.0 to 1.0
gamepad.update()
```

Reset to default state:

```python
gamepad.reset()
gamepad.update()
```

Full example:

```python
import vgamepad as vg
import time

gamepad = vg.VX360Gamepad()

# Press a button to wake the device up
gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
gamepad.update()
time.sleep(0.5)
gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
gamepad.update()
time.sleep(0.5)

# Press buttons and set axes
gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER)
gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN)
gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT)
gamepad.left_trigger_float(value_float=0.5)
gamepad.right_trigger_float(value_float=0.5)
gamepad.left_joystick_float(x_value_float=0.0, y_value_float=0.2)
gamepad.right_joystick_float(x_value_float=-1.0, y_value_float=1.0)
gamepad.update()
time.sleep(1.0)

# Release some buttons and axes
gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT)
gamepad.right_trigger_float(value_float=0.0)
gamepad.right_joystick_float(x_value_float=0.0, y_value_float=0.0)
gamepad.update()
time.sleep(1.0)

# Reset to default
gamepad.reset()
gamepad.update()
time.sleep(1.0)
```

### DualShock 4 gamepad

Using a virtual DS4 gamepad is similar to Xbox 360:

```python
import vgamepad as vg

gamepad = vg.VDS4Gamepad()
```

Press and release buttons:

```python
gamepad.press_button(button=vg.DS4_BUTTONS.DS4_BUTTON_TRIANGLE)
gamepad.update()

gamepad.release_button(button=vg.DS4_BUTTONS.DS4_BUTTON_TRIANGLE)
gamepad.update()
```

Available buttons are defined in `DS4_BUTTONS`:

```python
class DS4_BUTTONS(IntFlag):
    DS4_BUTTON_THUMB_RIGHT = 1 << 15
    DS4_BUTTON_THUMB_LEFT = 1 << 14
    DS4_BUTTON_OPTIONS = 1 << 13
    DS4_BUTTON_SHARE = 1 << 12
    DS4_BUTTON_TRIGGER_RIGHT = 1 << 11
    DS4_BUTTON_TRIGGER_LEFT = 1 << 10
    DS4_BUTTON_SHOULDER_RIGHT = 1 << 9
    DS4_BUTTON_SHOULDER_LEFT = 1 << 8
    DS4_BUTTON_TRIANGLE = 1 << 7
    DS4_BUTTON_CIRCLE = 1 << 6
    DS4_BUTTON_CROSS = 1 << 5
    DS4_BUTTON_SQUARE = 1 << 4
```

Press and release special buttons:

```python
gamepad.press_special_button(special_button=vg.DS4_SPECIAL_BUTTONS.DS4_SPECIAL_BUTTON_PS)
gamepad.update()

gamepad.release_special_button(special_button=vg.DS4_SPECIAL_BUTTONS.DS4_SPECIAL_BUTTON_PS)
gamepad.update()
```

Special buttons are defined in `DS4_SPECIAL_BUTTONS`:

```python
class DS4_SPECIAL_BUTTONS(IntFlag):
    DS4_SPECIAL_BUTTON_PS = 1 << 0
    DS4_SPECIAL_BUTTON_TOUCHPAD = 1 << 1
```

Triggers and joysticks (integer values):

```python
gamepad.left_trigger(value=100)  # 0-255
gamepad.right_trigger(value=255)  # 0-255
gamepad.left_joystick(x_value=0, y_value=128)  # 0-255
gamepad.right_joystick(x_value=0, y_value=255)  # 0-255
gamepad.update()
```

Triggers and joysticks (float values):

```python
gamepad.left_trigger_float(value_float=0.5)  # 0.0-1.0
gamepad.right_trigger_float(value_float=1.0)  # 0.0-1.0
gamepad.left_joystick_float(x_value_float=-0.5, y_value_float=0.0)  # -1.0 to 1.0
gamepad.right_joystick_float(x_value_float=-1.0, y_value_float=0.8)  # -1.0 to 1.0
gamepad.update()
```

> **Note:** Since version 0.1.0, the DS4 Y axis on joysticks is inverted compared to the Xbox 360 API (native ViGEm behavior).

Directional pad (hat):

```python
gamepad.directional_pad(direction=vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NORTHWEST)
gamepad.update()
```

Directions for the directional pad are defined in `DS4_DPAD_DIRECTIONS`:

```python
class DS4_DPAD_DIRECTIONS(IntEnum):
    DS4_BUTTON_DPAD_NONE = 0x8
    DS4_BUTTON_DPAD_NORTHWEST = 0x7
    DS4_BUTTON_DPAD_WEST = 0x6
    DS4_BUTTON_DPAD_SOUTHWEST = 0x5
    DS4_BUTTON_DPAD_SOUTH = 0x4
    DS4_BUTTON_DPAD_SOUTHEAST = 0x3
    DS4_BUTTON_DPAD_EAST = 0x2
    DS4_BUTTON_DPAD_NORTHEAST = 0x1
    DS4_BUTTON_DPAD_NORTH = 0x0
```

Reset to default state:

```python
gamepad.reset()
gamepad.update()
```

Full example:

```python
import vgamepad as vg
import time

gamepad = vg.VDS4Gamepad()

# Press a button to wake the device up
gamepad.press_button(button=vg.DS4_BUTTONS.DS4_BUTTON_TRIANGLE)
gamepad.update()
time.sleep(0.5)
gamepad.release_button(button=vg.DS4_BUTTONS.DS4_BUTTON_TRIANGLE)
gamepad.update()
time.sleep(0.5)

# Press buttons and set axes
gamepad.press_button(button=vg.DS4_BUTTONS.DS4_BUTTON_TRIANGLE)
gamepad.press_button(button=vg.DS4_BUTTONS.DS4_BUTTON_CIRCLE)
gamepad.press_button(button=vg.DS4_BUTTONS.DS4_BUTTON_THUMB_RIGHT)
gamepad.press_button(button=vg.DS4_BUTTONS.DS4_BUTTON_TRIGGER_LEFT)
gamepad.press_special_button(special_button=vg.DS4_SPECIAL_BUTTONS.DS4_SPECIAL_BUTTON_TOUCHPAD)
gamepad.left_trigger_float(value_float=0.5)
gamepad.right_trigger_float(value_float=0.5)
gamepad.left_joystick_float(x_value_float=0.0, y_value_float=0.2)
gamepad.right_joystick_float(x_value_float=-1.0, y_value_float=1.0)
gamepad.update()
time.sleep(1.0)

# Release some buttons and axes
gamepad.release_button(button=vg.DS4_BUTTONS.DS4_BUTTON_TRIANGLE)
gamepad.right_trigger_float(value_float=0.0)
gamepad.right_joystick_float(x_value_float=0.0, y_value_float=0.0)
gamepad.update()
time.sleep(1.0)

# Reset to default
gamepad.reset()
gamepad.update()
time.sleep(1.0)
```

---

### Rumble and LEDs

`vgamepad` enables registering custom callback functions to handle updates of the rumble motors and the LED ring.

Custom callback functions require 6 parameters:

```python
def my_callback(client, target, large_motor, small_motor, led_number, user_data):
    """
    Callback function triggered at each received state change.

    :param client: vigem bus ID
    :param target: vigem device ID
    :param large_motor: integer in [0, 255] representing the state of the large motor
    :param small_motor: integer in [0, 255] representing the state of the small motor
    :param led_number: integer in [0, 255] representing the state of the LED ring
    :param user_data: placeholder, do not use
    """
    print(f"large motor: {large_motor}, small motor: {small_motor}, led: {led_number}")
```

Register the callback:

```python
gamepad.register_notification(callback_function=my_callback)
```

Each time the state of the gamepad is changed (e.g. by a video game sending rumble requests), the callback will be invoked.

If no longer needed, the callback can be unregistered:

```python
gamepad.unregister_notification()
```

---

## Logging

`vgamepad` uses [loguru](https://github.com/Delgan/loguru) for internal logging, which is **disabled** by default.
To enable diagnostic output:

```python
from loguru import logger
logger.enable("vgamepad")
```

---

## Advanced

More API functions are available for advanced users, and it is possible to modify the report directly instead of using the convenience API.
See [virtual_gamepad.py](https://github.com/yannbouteiller/vgamepad/blob/main/vgamepad/win/virtual_gamepad.py).

> Only ViGEmBus `1.17.333.0` is tested.

---

## Contributing

All contributions to this project are welcome.
Please submit a pull request with your name and a short description of your contribution added to the list below.

### Maintainer

- Yann Bouteiller

### Contributors

- JumpyzZ (rumble and LEDs)
- willRicard (Linux support)
