# Linux

`vgamepad` is fully supported on Linux.

## Installation

### Prerequisite

On Linux, `vgamepad` needs access to `uinput`.

To give yourself permission to access `uinput` for the current session, open a terminal and execute:
```bash
sudo chmod +0666 /dev/uinput
```

Create a `udev` rule to set the permission permanently (otherwise the permission will be removed next time you log in):
```bash
sudo nano /etc/udev/rules.d/50-uinput.rules 
```
In `nano`, paste the following line:
```bash
KERNEL=="uinput", TAG+="uaccess"
```
Save by pressing `CTRL+o`, `ENTER`, and exit `nano` by pressing `CTRL+x`

#### vgamepad installation

Run:
```bash
pip install vgamepad
```

```vgamepad``` is now installed in your active python environment.


## Linux implementation details

On Windows, `vgamepad` wraps Nefarius' [Virtual Gamepad Emulation](https://github.com/nefarius/ViGEmBus) framework.

On Linux, `vgamepad` uses `libevdev` to create virtual `uinput` devices. The Linux backend supports the same API as Windows:

### Supported features
- All X360 buttons including the **Guide/Mode button** (`XUSB_GAMEPAD_GUIDE`)
- All DS4 buttons including **touchpad press** (`DS4_SPECIAL_BUTTON_TOUCHPAD`)
- DS4 **trigger buttons** (`DS4_BUTTON_TRIGGER_LEFT` / `DS4_BUTTON_TRIGGER_RIGHT`) mapped to `BTN_TL2` / `BTN_TR2`
- Joysticks, triggers, and directional pad (hat)
- **Force feedback / Rumble** via `register_notification()` and `unregister_notification()`
- **Extended reports** via `update_extended_report()` (DS4)
- `reset()`, `get_vid()`, `get_pid()`, `set_vid()`, `set_pid()`, `get_type()`, `get_index()`

### Notes
- Detected button ordering and axis directions may differ from Windows depending on the consuming application (e.g. pygame maps button indices differently)
- LED number in the rumble callback is always 0 on Linux
- Force feedback notifications are delivered via a background thread that reads FF events from the uinput device
- DS4 motion sensor data (gyro/accel) and touchpad coordinates from extended reports are not emitted as evdev events; only the standard gamepad fields are forwarded
