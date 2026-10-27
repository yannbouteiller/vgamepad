import ctypes
import errno
import fcntl
import os
import select
import struct
import threading
import time
import traceback


EV_FF = 0x15
EV_UINPUT = 0x0101
UI_FF_UPLOAD = 1
UI_FF_ERASE = 2
FF_RUMBLE = 0x50


class FFEnvelope(ctypes.Structure):
    _fields_ = [
        ("attack_length", ctypes.c_uint16),
        ("attack_level", ctypes.c_uint16),
        ("fade_length", ctypes.c_uint16),
        ("fade_level", ctypes.c_uint16)
    ]


class FFPeriodic(ctypes.Structure):
    _fields_ = [
        ("waveform", ctypes.c_uint16),
        ("period", ctypes.c_uint16),
        ("magnitude", ctypes.c_int16),
        ("offset", ctypes.c_int16),
        ("phase", ctypes.c_uint16),
        ("envelope", FFEnvelope),
        ("custom_len", ctypes.c_uint32),
        ("custom_data", ctypes.c_void_p)
    ]


class FFRumble(ctypes.Structure):
    _fields_ = [
        ("strong_magnitude", ctypes.c_uint16),
        ("weak_magnitude", ctypes.c_uint16)
    ]


class FFUnion(ctypes.Union):
    _fields_ = [
        ("periodic", FFPeriodic),
        ("rumble", FFRumble)
    ]


class FFTrigger(ctypes.Structure):
    _fields_ = [
        ("button", ctypes.c_uint16),
        ("interval", ctypes.c_uint16)
    ]


class FFReplay(ctypes.Structure):
    _fields_ = [
        ("length", ctypes.c_uint16),
        ("delay", ctypes.c_uint16)
    ]


class FFEffect(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_uint16),
        ("id", ctypes.c_int16),
        ("direction", ctypes.c_uint16),
        ("trigger", FFTrigger),
        ("replay", FFReplay),
        ("u", FFUnion)]


class UinputFFUpload(ctypes.Structure):
    _fields_ = [
        ("request_id", ctypes.c_uint32),
        ("retval", ctypes.c_int32),
        ("effect", FFEffect),
        ("old", FFEffect)
    ]


class UinputFFErase(ctypes.Structure):
    _fields_ = [
        ("request_id", ctypes.c_uint32),
        ("retval", ctypes.c_int32),
        ("effect_id", ctypes.c_uint32)
    ]


def _ioc(direction, nr, size):
    return (direction << 30) | (size << 16) | (ord('U') << 8) | nr


UI_BEGIN_FF_UPLOAD = _ioc(3, 200, ctypes.sizeof(UinputFFUpload))  # _IOWR
UI_END_FF_UPLOAD = _ioc(1, 201, ctypes.sizeof(UinputFFUpload))  # _IOW
UI_BEGIN_FF_ERASE = _ioc(3, 202, ctypes.sizeof(UinputFFErase))  # _IOWR
UI_END_FF_ERASE = _ioc(1, 203, ctypes.sizeof(UinputFFErase))  # _IOW
INPUT_EVENT = struct.Struct('llHHi')  # timeval, type, code, value


class ForceFeedback:
    """
    Answers the force feedback requests of a uinput device.
    """

    def __init__(self, uinput_file):
        self.__lock = threading.Lock()
        self.__rumble_callback = None
        self._effect_currently_playing = None
        self._time_stop = None
        self._effects = {}
        self._fd = uinput_file.fileno()
        self.pipe_in, self.pipe_out = os.pipe()
        self._closed = False
        self._thread = threading.Thread(target=self._thread_run, daemon=True)
        self._thread.start()
    
    def set_rumble_callback(self, rumble_callback):
        with self.__lock:
            self.__rumble_callback = rumble_callback

    def close(self):
        if not self._closed:
            self._closed = True
            os.write(self.pipe_out, b's')
            self._thread.join()
            os.close(self.pipe_in)
            os.close(self.pipe_out)

    def _thread_run(self):
        while True:
            timeout = None if self._time_stop is None else max(0.0, self._time_stop - time.monotonic())
            ready, _, _ = select.select([self._fd, self.pipe_in], [], [], timeout)
            if not ready:
                self._stop()
                continue
            if self.pipe_in in ready:
                # received stop signal, exit
                return
            else:
                _, _, event_type, event_code, event_value = INPUT_EVENT.unpack(os.read(self._fd, INPUT_EVENT.size))
                if event_type == EV_UINPUT and event_code == UI_FF_UPLOAD:
                    self._upload(event_value)
                elif event_type == EV_UINPUT and event_code == UI_FF_ERASE:
                    self._erase(event_value)
                elif event_type == EV_FF:
                    self._play(event_code, event_value)
    
    def _upload(self, request_id):
        upload = UinputFFUpload(request_id=request_id)
        fcntl.ioctl(self._fd, UI_BEGIN_FF_UPLOAD, upload)
        effect = upload.effect
        if effect.type == FF_RUMBLE:
            self._effects[effect.id] = (effect.u.rumble.strong_magnitude, effect.u.rumble.weak_magnitude, effect.replay.length)
            upload.retval = 0
        else:
            upload.retval = -errno.EINVAL  # only rumble is supported
        fcntl.ioctl(self._fd, UI_END_FF_UPLOAD, upload)

    def _erase(self, request_id):
        erase = UinputFFErase(request_id=request_id)
        fcntl.ioctl(self._fd, UI_BEGIN_FF_ERASE, erase)
        self._effects.pop(erase.effect_id, None)
        erase.retval = 0
        fcntl.ioctl(self._fd, UI_END_FF_ERASE, erase)
        self._stop(erase.effect_id)
    
    def _execute_callback(self, strong, weak):
        with self.__lock:
            if self.__rumble_callback is None:
                return
            try:
                self.__rumble_callback(strong, weak)
            except Exception:
                traceback.print_exc()
    
    def _play(self, event_code, event_value):
        if event_code in self._effects:
            if event_value == 0:
                self._stop(event_code)
            else:
                strong, weak, length_ms = self._effects[event_code]
                self._effect_currently_playing = event_code
                self._time_stop = time.monotonic() + length_ms * event_value / 1000 if length_ms else None
                self._execute_callback(strong, weak)
    
    def _stop(self, effect_id=None):
        if effect_id is not None and effect_id != self._effect_currently_playing:
            return
        self._effect_currently_playing = None
        self._time_stop = None
        self._execute_callback(0, 0)




