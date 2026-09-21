# Linux

Support for Linux is experimental and subject to future breaking changes.
If your python project for Linux relies on `vgamepad`, please specify the exact version you are relying on in your project dependencies.

## Installation

### Prerequisite:

#### Install `libevdev`:

- **Debian / Ubuntu:** `sudo apt update && sudo apt install libevdev2`
- **Fedora:** `sudo dnf install libevdev`
- **Arch:** `sudo pacman -S libevdev`


#### Grant user access to `uinput`:

On Linux, `vgamepad` requires permission to access `uinput`.
This can be achieved for the current session by opening a terminal and executing:
```bash
sudo chmod +0666 /dev/uinput
```

To set the permission permanently, create a `udev` rule (otherwise the permission will be removed next time you log in):
```bash
sudo nano /etc/udev/rules.d/50-uinput.rules 
```
In `nano`, paste the following:
```bash
KERNEL=="uinput", TAG+="uaccess"
```
Save by pressing `CTRL+o`, `ENTER`, and exit `nano` by pressing `CTRL+x`

### `vgamepad` installation:

Run:
```bash
pip install vgamepad
```

```vgamepad``` is now installed in your active python environment.


## Linux implementation details

On Windows, `vgamepad` is currently a wrapper around Nefarius' [Virtual Gamepad Emulation](https://github.com/nefarius/ViGEmBus) framework.

On Linux, `vgamepad` instead uses `libevdev` to create virtual `uinput` devices. The Linux backend supports the same API as Windows:

### Supported features:

- All X360 buttons including the **Guide/Mode button** (`XUSB_GAMEPAD_GUIDE`)
- All DS4 buttons including **touchpad press** (`DS4_SPECIAL_BUTTON_TOUCHPAD`)
- DS4 **trigger buttons** (`DS4_BUTTON_TRIGGER_LEFT` / `DS4_BUTTON_TRIGGER_RIGHT`) mapped to `BTN_TL2` / `BTN_TR2`
- Joysticks, triggers, and directional pad (hat)
- **Force feedback / Rumble** via `register_notification()` and `unregister_notification()` when `/dev/uinput` is opened successfully for the uinput device
- **Extended reports** via `update_extended_report()` (DS4)
- `reset()`, `get_vid()`, `get_pid()`, `set_vid()`, `set_pid()`, `get_type()`, `get_index()`

### Developer notes (Palamabron):

- **WSL:** `vgamepad` can create uinput devices, but `pygame` integration tests may not see them (SDL often enumerates zero joysticks). Run those tests on a normal Linux desktop or on Windows; the library itself still works if `libevdev` and `/dev/uinput` are set up.
- Virtual devices spoof `input_id` (vendor/product) matching real hardware so SDL2 uses `SDL_GameControllerDB` for correct button mapping. This avoids the "button order mess" that previously broke `BTN_MODE` (Guide).
- LED number in the rumble callback is always 0 on Linux.
- DS4 motion sensor data (gyro/accel) and touchpad coordinates from extended reports are not emitted as evdev events; only the standard gamepad fields are forwarded.


#### Force feedback (rumble)

``register_notification()`` reads FF events on the same kernel file descriptor libevdev uses for the uinput device. Re-opening ``/dev/input/event*`` will block waiting for events that never arrive. The new implementation opens ``/dev/uinput`` (or ``/dev/input/uinput``) and passes that fd into ``create_uinput_device(uinput_fd=...)``. Without that, libevdev uses managed mode and rumble callbacks stay disabled.


<!-- **What you should know:**
- Detected buttons, ordering and axes directions are typically different from Windows (depending on your app)
- Force feedback / LEDS are not implemented on Linux yet
- DS4 touchpad / motion sensor are not implemented on Linux yet (no extended report)
- Real DS4 gamepads fire a button event when you press the triggers (on top of the axis event), this button event is not implemented in `vgamepad` at the moment
- The X360 "guide" (mode) button is not implemented in `vgamepad` at the moment -->
