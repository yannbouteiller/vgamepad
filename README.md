# Virtual Gamepad
Virtual XBox360 and DualShock4 gamepads in python

---

Virtual Gamepad (```vgamepad```) is a small python library that emulates XBox360 and DualShock4 gamepads on your system.
It enables controling e.g. a video-game that requires analog input, directly from your python script.

Under the hood, ```vgamepad``` uses the [ViGEm](https://github.com/ViGEm) C++ framework, for which it essentially provides python bindings and a user-friendly interface.
Thus far, ```vgamepad``` is compatible with Windows only.

## Quick links
- [Installation](#installation)
- [Getting started](#getting-started)
  - [XBox360 gamepad](#xbox360-gamepad)
  - [DualShock4 gamepad](#dualshock4-gamepad)
- [Contribute](#authors)

---

## Installation
Before installing ```vgamepad```, you must install ViGEmBus on your system.
Depending on your Windows version, download and execute the [ViGEmBus 64bit](https://github.com/ViGEm/ViGEmBus/releases/download/setup-v1.17.333/ViGEmBusSetup_x64.msi).
or the [ViGEmBus 32bit](https://github.com/ViGEm/ViGEmBus/releases/download/setup-v1.17.333/ViGEmBusSetup_x64.msi) installer.

Now that ViGEmBus is installed, open your favorite terminal (e.g. anaconda prompt) and run:

```bash
pip install vgamepad
```

This will install ```vgamepad``` in your active python environment.

---

## Getting started

```vgamepad``` provides two main python classes: ```VX360Gamepad```, which emulates a XBox360 gamepad, and ```DS4Gamepad```, which emulates a DualShock4 gamepad.

The state of a virtual gamepad (e.g. pressed buttons, joystick values...) is called a report.
To modify the report, a number of user-friendly API functions are provided by ```vgamepad```.
When the report is modified as desired, it must be sent to the computer thanks to the ```update``` API function.

### XBox360 gamepad

The following python script creates a virtual XBox360 gamepad:

```python
import vgamepad as vg

gamepad = vg.VX360Gamepad()
```

As soon as the ```VX360Gamepad``` object is created, the virtual gamepad is connected to your system via the ViGEmBus driver, and will remain connected until the object is destroyed.

Buttons can be pressed and released through ```press_button``` and ```release_button```:

```python
gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)  # press the A button
gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT)  # press the left hat button

gamepad.update()  # send the updated state to the computer

# (...) A and left hat are pressed...

gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)  # release the A button

gamepad.update()  # send the updated state to the computer

# (...) left hat is still pressed...
```

All available buttons are defined in ```XUSB_BUTTON```:
```python
class XUSB_BUTTON(IntFlag):
    """
    Possible XUSB report buttons.
    """
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

To control the triggers (1 axis each) and the joysticks (2 axis each), two options are provided by the API.

It is possible to input raw integer values directly:
```python
gamepad.left_trigger(value=100)  # value between 0 and 255
gamepad.right_trigger(value=255)  # value between 0 and 255
gamepad.left_joystick(x_value=-10000, y_value=0)  # values between -32768 and 32767
gamepad.right_joystick(x_value=-32768, y_value=15000)  # values between -32768 and 32767

gamepad.update()
```

Or to input float values:
```python
gamepad.left_trigger_float(value_float=0.5)  # value between 0.0 and 1.0
gamepad.right_trigger_float(value_float=1.0)  # value between 0.0 and 1.0
gamepad.left_joystick_float(x_value_float=-0.5, y_value_float=0.0)  # values between -1.0 and 1.0
gamepad.right_joystick_float(x_value_float=-1.0, y_value_float=0.8)  # values between -1.0 and 1.0

gamepad.update()
```

Full example:
```python
import vgamepad as vg
import time

gamepad = vg.VX360Gamepad()

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

gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT)
gamepad.right_trigger_float(value_float=0.0)
gamepad.right_joystick_float(x_value_float=0.0, y_value_float=0.0)

gamepad.update()

time.sleep(1.0)
```

### DualShock4 gamepad

#### Basic:

Using a virtual DS4 gamepad is similar to X360:
```python
import vgamepad as vg

gamepad = vg.VDS4Gamepad()
```

Press and release buttons:
```python
gamepad.press_button(button=vg.DS4_BUTTONS.DS4_BUTTON_TRIANGLE)
gamepad.update()

# (...)

gamepad.release_button(button=vg.DS4_BUTTONS.DS4_BUTTON_TRIANGLE)
gamepad.update()
```

Available buttons are defined in ```DS4_BUTTONS```:
```python
class DS4_BUTTONS(IntFlag):
    """
    DualShock 4 digital buttons
    """
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

# (...)

gamepad.release_special_button(special_button=vg.DS4_SPECIAL_BUTTONS.DS4_SPECIAL_BUTTON_PS)
gamepad.update()
```

Special buttons are defined in ```DS4_SPECIAL_BUTTONS```:
```python
class DS4_SPECIAL_BUTTONS(IntFlag):
    """
    DualShock 4 special buttons
    """
    DS4_SPECIAL_BUTTON_PS = 1 << 0
    DS4_SPECIAL_BUTTON_TOUCHPAD = 1 << 1
```

Triggers and joysticks (integer values):
```python
gamepad.left_trigger(value=100)  # value between 0 and 255
gamepad.right_trigger(value=255)  # value between 0 and 255
gamepad.left_joystick(x_value=0, y_value=128)  # value between 0 and 255
gamepad.right_joystick(x_value=0, y_value=255)  # value between 0 and 255

gamepad.update()
```

Triggers and joysticks (float values):
```python
gamepad.left_trigger_float(value_float=0.5)  # value between 0.0 and 1.0
gamepad.right_trigger_float(value_float=1.0)  # value between 0.0 and 1.0
gamepad.left_joystick_float(x_value_float=-0.5, y_value_float=0.0)  # values between -1.0 and 1.0
gamepad.right_joystick_float(x_value_float=-1.0, y_value_float=0.8)  # values between -1.0 and 1.0

gamepad.update()
```

Directional pad (hat):
```python
gamepad.directional_pad(direction=vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NORTHWEST)
gamepad.update()
```

Directions for the directional pad are defined in ```DS4_DPAD_DIRECTIONS```:
```python
class DS4_DPAD_DIRECTIONS(IntEnum):
    """
    DualShock 4 directional pad (HAT) values
    """
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

---

### Advanced users:
More API functions are available for advanced users, and it is possible to modify the report directly instead of using the API.
See [virtual_gamepad.py](https://github.com/yannbouteiller/vgamepad/blob/main/vgamepad/win/virtual_gamepad.py).

---

## Contribute
All contributions to this project are welcome. Please submit a PR with your name in the Contributors list.

---
## Authors
### Maintainer:
- Yann Bouteiller
### Contributors:

