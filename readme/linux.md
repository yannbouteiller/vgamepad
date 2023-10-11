# Linux

`vgamepad` is now partly supported on Linux.

Contrary to Windows, support for Linux is experimental and subject to future breaking changes.
If your python project for Linux relies on `vgamepad`, please use the exact `vgamepad` version you are relying on in your project dependencies.

## Differences with Windows
On Windows, `vgamepad` is currently a wrapper around Nefarius' [Virtual Gamepad Emulation](https://github.com/nefarius/ViGEmBus) framework.
As such, it emulates true physical DS4 and X360 gamepads.

On Linux, `vgamepad` currently relies on `libevdev`.
It emulates a subset of the X360 and DS4 capabilities in `evdev` by managing a virtual `uinput` device.

While we are trying to make this emulation as close to the real thing as possible, we are not quite there yet.
If you know how to advance toward this goal, your contribution would be **very appreciated** :heart_eyes:

For now, most basic `vgamepad` calls work on Linux, but you shouldn't expect your app to react exactly as if an actual X360 / DS4 gamepad were connected to your machine.
However, the corresponding `evdev` event should be similar.

**What you should know:**
- Detected buttons, ordering and axes directions are typically different from Windows (depending on your app)
- Force feedback / LEDs are not implemented on Linux yet
- X360 "Mode" ("Guide") button is not implemented on Linux yet
- DS4 touchpad / motion sensor are not implemented on Linux yet (no extended report)
- Real DS4s fire a button event when you press the triggers (on top of the axis event), this button event is not implemented in `vgamepad` at the moment
- Scripts in the `test` folder are useful for understanding the current status of Linux support (read the comments)

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
