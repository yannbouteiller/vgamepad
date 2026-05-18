# Linux

`vgamepad` is fully supported on Linux (desktop distributions). **WSL** can create `uinput` devices, but SDL/pygame-based tests often see zero joysticks; run integration tests on a real desktop session or on Windows if needed.

---

## How to run on Linux

### 1. System packages

Install the **native** libevdev library (the `libevdev` package on PyPI is only Python bindings; it does not ship `libevdev.so`):

- **Debian / Ubuntu:** `sudo apt update && sudo apt install libevdev2`
- **Fedora:** `sudo dnf install libevdev`
- **Arch:** `sudo pacman -S libevdev`

### 2. Allow access to `uinput`

The library creates virtual devices through `/dev/uinput`. Your user must be able to open it.

**Temporary (current session):**

```bash
sudo chmod 0666 /dev/uinput
```

**Persistent (udev rule):**

```bash
sudo nano /etc/udev/rules.d/50-uinput.rules
```

Paste:

```text
KERNEL=="uinput", TAG+="uaccess"
```

Reload rules and replug or reboot as needed (distribution-specific).

### 3. Install `vgamepad`

In the virtual environment you use for your project:

```bash
pip install vgamepad
```

### 4. Smoke test

```bash
python -c "import vgamepad as vg; g = vg.VX360Gamepad(); g.reset(); g.update(); print('ok')"
```

If this raises `Permission denied` on `/dev/uinput`, fix step 2.

### 5. Development install (from a clone)

```bash
cd vgamepad
pip install -e ".[dev]"
```

This pulls `ruff`, `mypy`, `pytest`, and `pygame` for linting, typing, and tests.

### 6. Tests

With ViGEm not applicable on Linux, tests use **pygame** (and on Windows, X360 tests may use **XInput** instead when SDL cannot read the virtual device). From the repo root:

```bash
python -m pytest test/ -v
```

Some cases may **skip** if SDL does not expose the virtual device (common on WSL).

### 7. Force feedback (`register_notification`)

Rumble callbacks need the same kernel file descriptor libevdev uses for the uinput device. The implementation opens `/dev/uinput` and passes it into `create_uinput_device(uinput_fd=...)` when possible. If opening `/dev/uinput` fails (permissions), libevdev falls back to *managed* mode and **force-feedback notifications will not work**, while normal button/stick output still works.

---

## Linux implementation details

On Windows, `vgamepad` wraps Nefarius' [Virtual Gamepad Emulation](https://github.com/nefarius/ViGEmBus) framework.

On Linux, `vgamepad` uses `libevdev` to create virtual `uinput` devices. The Linux backend supports the same API as Windows:

### Supported features

- All X360 buttons including the **Guide/Mode button** (`XUSB_GAMEPAD_GUIDE`)
- All DS4 buttons including **touchpad press** (`DS4_SPECIAL_BUTTON_TOUCHPAD`)
- DS4 **trigger buttons** (`DS4_BUTTON_TRIGGER_LEFT` / `DS4_BUTTON_TRIGGER_RIGHT`) mapped to `BTN_TL2` / `BTN_TR2`
- Joysticks, triggers, and directional pad (hat)
- **Force feedback / Rumble** via `register_notification()` and `unregister_notification()` when `/dev/uinput` is opened successfully for the uinput device
- **Extended reports** via `update_extended_report()` (DS4)
- `reset()`, `get_vid()`, `get_pid()`, `set_vid()`, `set_pid()`, `get_type()`, `get_index()`

### Notes

- **WSL:** `vgamepad` can create uinput devices, but **pygame** integration tests may not see them (SDL often enumerates zero joysticks). Run those tests on a normal Linux desktop or on Windows; the library itself still works if `libevdev` and `/dev/uinput` are set up.
- Detected button ordering and axis directions may differ from Windows depending on the consuming application (e.g. pygame maps button indices differently).
- LED number in the rumble callback is always 0 on Linux.
- DS4 motion sensor data (gyro/accel) and touchpad coordinates from extended reports are not emitted as evdev events; only the standard gamepad fields are forwarded.
