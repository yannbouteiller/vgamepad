"""
VGamepad API (Windows)

All API docstrings are defined in vgamepad.api
"""

import ctypes
from ctypes import WINFUNCTYPE, c_void_p, c_ubyte  # Note: replaced CFUNCTYPE with WINFUNCTYPE for x86 compatibility (Windows only)
from abc import ABC, abstractmethod
from inspect import signature

import vgamepad.api as api
import vgamepad.win.vigem_client as vcli


def check_err(err):
    if err != api.VIGEM_ERRORS.VIGEM_ERROR_NONE:
        raise RuntimeError(f"Error: {api.VIGEM_ERRORS(err).name}")


class VBus:
    """
    Virtual USB bus (ViGEmBus)
    """
    def __init__(self):
        self._busp = vcli.vigem_alloc()
        check_err(vcli.vigem_connect(self._busp))

    def get_busp(self):
        return self._busp

    def __del__(self):
        vcli.vigem_disconnect(self._busp)
        vcli.vigem_free(self._busp)


# We instantiate a single global VBus for all controllers
VBUS = VBus()


class VGamepad(ABC):
    def __init__(self, vid=None, pid=None):
        self.cmp_func = None
        self.vbus = VBUS
        self._busp = self.vbus.get_busp()
        self._devicep = self.target_alloc()
        if vid is not None:
            vcli.vigem_target_set_vid(self._devicep, vid)
        if pid is not None:
            vcli.vigem_target_set_pid(self._devicep, pid)
        check_err(vcli.vigem_target_add(self._busp, self._devicep))
        if not vcli.vigem_target_is_attached(self._devicep):
            raise RuntimeError("The virtual device could not connect to ViGEmBus.")

    def __del__(self):
        if self.cmp_func is not None:
            self.unregister_notification()
        vcli.vigem_target_remove(self._busp, self._devicep)
        vcli.vigem_target_free(self._devicep)

    def get_vid(self):
        return vcli.vigem_target_get_vid(self._devicep)

    def get_pid(self):
        return vcli.vigem_target_get_pid(self._devicep)

    def get_index(self):
        return vcli.vigem_target_get_index(self._devicep)

    def get_type(self):
        return vcli.vigem_target_get_type(self._devicep)

    @abstractmethod
    def target_alloc(self):
        pass


class VX360Gamepad(VGamepad, api.VX360Gamepad):
    """
    Virtual XBox360 gamepad
    """
    def __init__(self, vid=None, pid=None):
        VGamepad.__init__(self, vid=vid, pid=pid)
        api.VX360Gamepad.__init__(self)
        self.CMPFUNC = WINFUNCTYPE(None, c_void_p, c_void_p, c_ubyte, c_ubyte, c_ubyte, c_void_p)

    def update_from_report(self, report):
        check_err(vcli.vigem_target_x360_update(self._busp, self._devicep, report))

    def register_notification(self, callback_function):
        if self.cmp_func is not None:
            raise RuntimeError("Cannot register a callback more than once per gamepad.")
        if not api.check_callback_signature(callback_function):
            raise TypeError("Needed callback function signature: {}, but got: {}".format(signature(api.dummy_x360_callback), signature(callback_function)))
        cmp_func = self.CMPFUNC(callback_function)  # keep its reference, otherwise the program will crash when a callback is made.
        check_err(vcli.vigem_target_x360_register_notification(self._busp, self._devicep, cmp_func, None))
        self.cmp_func = cmp_func

    def unregister_notification(self):
        vcli.vigem_target_x360_unregister_notification(self._devicep)

    def target_alloc(self):
        return vcli.vigem_target_x360_alloc()


class VDS4Gamepad(VGamepad, api.VDS4Gamepad):
    """
    Virtual DualShock 4 gamepad
    """

    def __init__(self, vid=None, pid=None):
        VGamepad.__init__(self, vid=vid, pid=pid)
        api.VDS4Gamepad.__init__(self)
        self.CMPFUNC = WINFUNCTYPE(None, c_void_p, c_void_p, c_ubyte, c_ubyte, api.DS4_LIGHTBAR_COLOR, c_void_p)

    def update_from_report(self, report):
        check_err(vcli.vigem_target_ds4_update(self._busp, self._devicep, report))

    def update_from_extended_report(self, extended_report):
        check_err(vcli.vigem_target_ds4_update_ex_ptr(self._busp, self._devicep, ctypes.byref(extended_report)))

    def register_notification(self, callback_function):
        if self.cmp_func is not None:
            raise RuntimeError("Cannot register a callback more than once per gamepad.")
        if not api.check_callback_signature(callback_function):
            raise TypeError("Needed callback function signature: {}, but got: {}".format(signature(api.dummy_ds4_callback), signature(callback_function)))
        cmp_func = self.CMPFUNC(callback_function)
        check_err(vcli.vigem_target_ds4_register_notification(self._busp, self._devicep, cmp_func, None))
        self.cmp_func = cmp_func

    def unregister_notification(self):
        vcli.vigem_target_ds4_unregister_notification(self._devicep)

    def target_alloc(self):
        return vcli.vigem_target_ds4_alloc()
