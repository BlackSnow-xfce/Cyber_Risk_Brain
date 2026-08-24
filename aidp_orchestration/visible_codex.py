"""Trusted Windows console relay for one shell-free Codex process."""

from __future__ import annotations

import codecs
import ctypes
import os
import subprocess
import sys
import threading
from ctypes import wintypes
from typing import BinaryIO, Sequence, TextIO


_KILL_ON_JOB_CLOSE = 0x00002000
_EXTENDED_LIMIT_INFORMATION = 9
_SW_SHOWNORMAL = 1
_SW_RESTORE = 9
_SWP_NOSIZE = 0x0001
_SWP_NOMOVE = 0x0002
_SWP_SHOWWINDOW = 0x0040
_MONITOR_DEFAULTTONULL = 0
_GENERIC_READ = 0x00020000
_UOI_NAME = 2
_READY_TOKEN = b"AIDP_VISIBLE_CONSOLE_READY_V1\n"


class _Rect(ctypes.Structure):
    _fields_ = (
        ("left", ctypes.c_long), ("top", ctypes.c_long),
        ("right", ctypes.c_long), ("bottom", ctypes.c_long),
    )


class _MonitorInfo(ctypes.Structure):
    _fields_ = (("cbSize", wintypes.DWORD), ("rcMonitor", _Rect), ("rcWork", _Rect), ("dwFlags", wintypes.DWORD))


class _IoCounters(ctypes.Structure):
    _fields_ = [
        ("ReadOperationCount", ctypes.c_ulonglong),
        ("WriteOperationCount", ctypes.c_ulonglong),
        ("OtherOperationCount", ctypes.c_ulonglong),
        ("ReadTransferCount", ctypes.c_ulonglong),
        ("WriteTransferCount", ctypes.c_ulonglong),
        ("OtherTransferCount", ctypes.c_ulonglong),
    ]


class _BasicLimitInformation(ctypes.Structure):
    _fields_ = [
        ("PerProcessUserTimeLimit", ctypes.c_longlong),
        ("PerJobUserTimeLimit", ctypes.c_longlong),
        ("LimitFlags", wintypes.DWORD),
        ("MinimumWorkingSetSize", ctypes.c_size_t),
        ("MaximumWorkingSetSize", ctypes.c_size_t),
        ("ActiveProcessLimit", wintypes.DWORD),
        ("Affinity", ctypes.c_size_t),
        ("PriorityClass", wintypes.DWORD),
        ("SchedulingClass", wintypes.DWORD),
    ]


class _ExtendedLimitInformation(ctypes.Structure):
    _fields_ = [
        ("BasicLimitInformation", _BasicLimitInformation),
        ("IoInfo", _IoCounters),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t),
        ("PeakJobMemoryUsed", ctypes.c_size_t),
    ]


class WindowsJob:
    def __init__(self) -> None:
        if os.name != "nt":
            raise RuntimeError("Windows process jobs are unavailable")
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CreateJobObjectW.argtypes = (ctypes.c_void_p, wintypes.LPCWSTR)
        kernel32.CreateJobObjectW.restype = wintypes.HANDLE
        kernel32.SetInformationJobObject.argtypes = (
            wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD,
        )
        kernel32.SetInformationJobObject.restype = wintypes.BOOL
        kernel32.AssignProcessToJobObject.argtypes = (wintypes.HANDLE, wintypes.HANDLE)
        kernel32.AssignProcessToJobObject.restype = wintypes.BOOL
        kernel32.TerminateJobObject.argtypes = (wintypes.HANDLE, wintypes.UINT)
        kernel32.TerminateJobObject.restype = wintypes.BOOL
        kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
        kernel32.CloseHandle.restype = wintypes.BOOL
        self._kernel32 = kernel32
        self._handle = kernel32.CreateJobObjectW(None, None)
        if not self._handle:
            raise OSError(ctypes.get_last_error(), "CreateJobObjectW failed")
        information = _ExtendedLimitInformation()
        information.BasicLimitInformation.LimitFlags = _KILL_ON_JOB_CLOSE
        if not kernel32.SetInformationJobObject(
            self._handle, _EXTENDED_LIMIT_INFORMATION,
            ctypes.byref(information), ctypes.sizeof(information),
        ):
            self.close()
            raise OSError(ctypes.get_last_error(), "SetInformationJobObject failed")

    def assign(self, process: subprocess.Popen[bytes]) -> None:
        if not self._kernel32.AssignProcessToJobObject(self._handle, wintypes.HANDLE(process._handle)):
            raise OSError(ctypes.get_last_error(), "AssignProcessToJobObject failed")

    def terminate(self, exit_code: int) -> None:
        if self._handle:
            self._kernel32.TerminateJobObject(self._handle, exit_code)

    def close(self) -> None:
        if self._handle:
            self._kernel32.CloseHandle(self._handle)
            self._handle = None


def _pump(
    source: BinaryIO,
    capture: BinaryIO,
    console: TextIO,
    render_lock: threading.Lock | None = None,
) -> None:
    decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
    while chunk := source.read(4096):
        capture.write(chunk)
        capture.flush()
        rendered = decoder.decode(chunk)
        if rendered:
            with render_lock or _NullLock():
                console.write(rendered)
                console.flush()
    remainder = decoder.decode(b"", final=True)
    if remainder:
        with render_lock or _NullLock():
            console.write(remainder)
            console.flush()


class _NullLock:
    def __enter__(self):
        return self

    def __exit__(self, *_args) -> None:
        return None


def _desktop_name(user32, desktop) -> str:
    needed = wintypes.DWORD()
    user32.GetUserObjectInformationW(desktop, _UOI_NAME, None, 0, ctypes.byref(needed))
    if not needed.value:
        raise OSError(ctypes.get_last_error(), "desktop name query failed")
    buffer = ctypes.create_unicode_buffer(needed.value)
    if not user32.GetUserObjectInformationW(
        desktop, _UOI_NAME, buffer, ctypes.sizeof(buffer), ctypes.byref(needed),
    ):
        raise OSError(ctypes.get_last_error(), "desktop name read failed")
    return buffer.value


def _rectangles_intersect(first: _Rect, second: _Rect) -> bool:
    return first.left < second.right and first.right > second.left and first.top < second.bottom and first.bottom > second.top


def _present_console(*, kernel32=None, user32=None, desktop_name=_desktop_name) -> None:
    kernel32 = kernel32 or ctypes.WinDLL("kernel32", use_last_error=True)
    user32 = user32 or ctypes.WinDLL("user32", use_last_error=True)
    kernel32.GetConsoleWindow.argtypes = ()
    kernel32.GetConsoleWindow.restype = wintypes.HWND
    user32.GetWindowThreadProcessId.argtypes = (wintypes.HWND, ctypes.c_void_p)
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD
    user32.GetThreadDesktop.argtypes = (wintypes.DWORD,)
    user32.GetThreadDesktop.restype = wintypes.HANDLE
    user32.OpenInputDesktop.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    user32.OpenInputDesktop.restype = wintypes.HANDLE
    user32.CloseDesktop.argtypes = (wintypes.HANDLE,)
    user32.CloseDesktop.restype = wintypes.BOOL
    user32.GetUserObjectInformationW.argtypes = (
        wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
    )
    user32.GetUserObjectInformationW.restype = wintypes.BOOL
    user32.ShowWindow.argtypes = (wintypes.HWND, ctypes.c_int)
    user32.ShowWindow.restype = wintypes.BOOL
    user32.SetWindowPos.argtypes = (
        wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int,
        ctypes.c_int, ctypes.c_int, wintypes.UINT,
    )
    user32.SetWindowPos.restype = wintypes.BOOL
    user32.SetForegroundWindow.argtypes = (wintypes.HWND,)
    user32.SetForegroundWindow.restype = wintypes.BOOL
    user32.IsWindowVisible.argtypes = (wintypes.HWND,)
    user32.IsWindowVisible.restype = wintypes.BOOL
    user32.IsIconic.argtypes = (wintypes.HWND,)
    user32.IsIconic.restype = wintypes.BOOL
    user32.MonitorFromWindow.argtypes = (wintypes.HWND, wintypes.DWORD)
    user32.MonitorFromWindow.restype = wintypes.HANDLE
    user32.GetWindowRect.argtypes = (wintypes.HWND, ctypes.POINTER(_Rect))
    user32.GetWindowRect.restype = wintypes.BOOL
    user32.GetMonitorInfoW.argtypes = (wintypes.HANDLE, ctypes.POINTER(_MonitorInfo))
    user32.GetMonitorInfoW.restype = wintypes.BOOL
    window = kernel32.GetConsoleWindow()
    if not window:
        raise RuntimeError("visible console window is unavailable")

    window_thread = user32.GetWindowThreadProcessId(window, None)
    window_desktop = user32.GetThreadDesktop(window_thread) if window_thread else None
    input_desktop = user32.OpenInputDesktop(0, False, _GENERIC_READ)
    if not window_desktop or not input_desktop:
        if input_desktop:
            user32.CloseDesktop(input_desktop)
        raise RuntimeError("interactive desktop cannot be verified")
    try:
        if desktop_name(user32, window_desktop) != desktop_name(user32, input_desktop):
            raise RuntimeError("console window is not on the interactive input desktop")
    finally:
        user32.CloseDesktop(input_desktop)

    user32.ShowWindow(window, _SW_RESTORE)
    if not user32.SetWindowPos(window, 0, 0, 0, 0, 0, _SWP_NOMOVE | _SWP_NOSIZE | _SWP_SHOWWINDOW):
        raise OSError(ctypes.get_last_error(), "console window Z-order update failed")
    user32.SetForegroundWindow(window)
    if not user32.IsWindowVisible(window):
        raise RuntimeError("console window is not visible")
    if user32.IsIconic(window):
        raise RuntimeError("console window remains minimized")
    monitor = user32.MonitorFromWindow(window, _MONITOR_DEFAULTTONULL)
    if not monitor:
        raise RuntimeError("console window does not intersect a visible monitor")
    window_rect = _Rect()
    monitor_info = _MonitorInfo()
    monitor_info.cbSize = ctypes.sizeof(monitor_info)
    if not user32.GetWindowRect(window, ctypes.byref(window_rect)):
        raise OSError(ctypes.get_last_error(), "console window bounds query failed")
    if not user32.GetMonitorInfoW(monitor, ctypes.byref(monitor_info)):
        raise OSError(ctypes.get_last_error(), "monitor work area query failed")
    if not _rectangles_intersect(window_rect, monitor_info.rcWork):
        raise RuntimeError("console window is outside the visible monitor work area")


def relay(
    argv: Sequence[str], *, console_presenter=_present_console,
    popen=subprocess.Popen, job_factory=WindowsJob,
) -> int:
    if os.name != "nt" or not argv:
        return 125
    job = job_factory()
    child: subprocess.Popen[bytes] | None = None
    try:
        console_presenter()
        with (
            open("CONOUT$", "w", encoding="utf-8", errors="replace", buffering=1) as console,
        ):
            sys.stderr.buffer.write(_READY_TOKEN)
            sys.stderr.buffer.flush()
            child = popen(
                tuple(argv), stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, shell=False,
                creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200),
            )
            try:
                job.assign(child)
            except Exception:
                child.kill()
                child.wait()
                raise
            if child.stdout is None or child.stderr is None:
                raise RuntimeError("Codex capture pipes are unavailable")
            render_lock = threading.Lock()
            stdout_thread = threading.Thread(
                target=_pump, args=(child.stdout, sys.stdout.buffer, console, render_lock), daemon=True,
            )
            stderr_thread = threading.Thread(
                target=_pump, args=(child.stderr, sys.stderr.buffer, console, render_lock), daemon=True,
            )
            stdout_thread.start()
            stderr_thread.start()
            return_code = child.wait()
            stdout_thread.join()
            stderr_thread.join()
            return return_code
    except KeyboardInterrupt:
        job.terminate(130)
        return 130
    except Exception as exc:
        message = f"visible Codex relay failed: {exc.__class__.__name__}\n"
        sys.stderr.write(message)
        return 125
    finally:
        job.close()


def main() -> int:
    arguments = sys.argv[1:]
    if not arguments or arguments[0] != "--":
        return 125
    return relay(arguments[1:])


if __name__ == "__main__":
    raise SystemExit(main())
