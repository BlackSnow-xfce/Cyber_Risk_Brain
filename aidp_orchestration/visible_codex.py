"""Trusted Windows console relay for one shell-free Codex process."""

from __future__ import annotations

import codecs
import ctypes
import os
import queue
import subprocess
import sys
import threading
from ctypes import wintypes
from enum import Enum
from typing import BinaryIO, Sequence, TextIO


_KILL_ON_JOB_CLOSE = 0x00002000
_EXTENDED_LIMIT_INFORMATION = 9
_SW_SHOWNORMAL = 1
_SW_RESTORE = 9
_SWP_NOSIZE = 0x0001
_SWP_NOMOVE = 0x0002
_SWP_SHOWWINDOW = 0x0040
_MONITOR_DEFAULTTONULL = 0
_DESKTOP_READOBJECTS = 0x0001
_UOI_NAME = 2
_GA_ROOT = 2
_HWND_MESSAGE = ctypes.c_void_p(-3).value
_READY_TOKEN = b"AIDP_VISIBLE_CONSOLE_READY_V2\n"
_ERROR_PREFIX = b"AIDP_VISIBLE_CONSOLE_ERROR_V2:"


class ConsoleReadinessCode(str, Enum):
    NO_CONSOLE_HWND = "NO_CONSOLE_HWND"
    WINDOW_NOT_TOP_LEVEL = "WINDOW_NOT_TOP_LEVEL"
    MESSAGE_ONLY_OR_PSEUDOCONSOLE_WINDOW = "MESSAGE_ONLY_OR_PSEUDOCONSOLE_WINDOW"
    WINDOW_THREAD_UNAVAILABLE = "WINDOW_THREAD_UNAVAILABLE"
    WINDOW_DESKTOP_UNAVAILABLE = "WINDOW_DESKTOP_UNAVAILABLE"
    INPUT_DESKTOP_UNAVAILABLE = "INPUT_DESKTOP_UNAVAILABLE"
    DESKTOP_NAME_UNAVAILABLE = "DESKTOP_NAME_UNAVAILABLE"
    DESKTOP_MISMATCH = "DESKTOP_MISMATCH"
    WINDOW_PRESENTATION_FAILED = "WINDOW_PRESENTATION_FAILED"
    WINDOW_NOT_VISIBLE = "WINDOW_NOT_VISIBLE"
    WINDOW_MINIMIZED = "WINDOW_MINIMIZED"
    VISIBLE_MONITOR_UNAVAILABLE = "VISIBLE_MONITOR_UNAVAILABLE"
    WINDOW_BOUNDS_UNAVAILABLE = "WINDOW_BOUNDS_UNAVAILABLE"
    MONITOR_WORK_AREA_UNAVAILABLE = "MONITOR_WORK_AREA_UNAVAILABLE"
    WINDOW_OFFSCREEN = "WINDOW_OFFSCREEN"
    CONOUT_UNAVAILABLE = "CONOUT_UNAVAILABLE"


READINESS_ERROR_CODES = frozenset(code.value for code in ConsoleReadinessCode)


class ConsoleReadinessError(RuntimeError):
    def __init__(self, code: ConsoleReadinessCode):
        super().__init__(code.value)
        self.code = code


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


def _configure_presentation_apis(kernel32, user32) -> None:
    kernel32 = kernel32 or ctypes.WinDLL("kernel32", use_last_error=True)
    user32 = user32 or ctypes.WinDLL("user32", use_last_error=True)
    kernel32.GetCurrentThreadId.argtypes = ()
    kernel32.GetCurrentThreadId.restype = wintypes.DWORD
    user32.GetWindowThreadProcessId.argtypes = (wintypes.HWND, ctypes.c_void_p)
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD
    user32.GetAncestor.argtypes = (wintypes.HWND, wintypes.UINT)
    user32.GetAncestor.restype = wintypes.HWND
    user32.GetParent.argtypes = (wintypes.HWND,)
    user32.GetParent.restype = wintypes.HWND
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


def _present_window(window, *, kernel32, user32, desktop_name=_desktop_name) -> None:
    _configure_presentation_apis(kernel32, user32)
    if user32.GetParent(window) in (-3, _HWND_MESSAGE):
        raise ConsoleReadinessError(ConsoleReadinessCode.MESSAGE_ONLY_OR_PSEUDOCONSOLE_WINDOW)
    if user32.GetAncestor(window, _GA_ROOT) != window:
        raise ConsoleReadinessError(ConsoleReadinessCode.WINDOW_NOT_TOP_LEVEL)

    window_thread = user32.GetWindowThreadProcessId(window, None)
    if not window_thread:
        raise ConsoleReadinessError(ConsoleReadinessCode.WINDOW_THREAD_UNAVAILABLE)
    window_desktop = user32.GetThreadDesktop(kernel32.GetCurrentThreadId())
    if not window_desktop:
        raise ConsoleReadinessError(ConsoleReadinessCode.WINDOW_DESKTOP_UNAVAILABLE)
    input_desktop = user32.OpenInputDesktop(0, False, _DESKTOP_READOBJECTS)
    if not input_desktop:
        raise ConsoleReadinessError(ConsoleReadinessCode.INPUT_DESKTOP_UNAVAILABLE)
    try:
        try:
            window_desktop_name = desktop_name(user32, window_desktop)
            input_desktop_name = desktop_name(user32, input_desktop)
        except (OSError, RuntimeError):
            raise ConsoleReadinessError(ConsoleReadinessCode.DESKTOP_NAME_UNAVAILABLE) from None
        if window_desktop_name != input_desktop_name:
            raise ConsoleReadinessError(ConsoleReadinessCode.DESKTOP_MISMATCH)
    finally:
        user32.CloseDesktop(input_desktop)

    user32.ShowWindow(window, _SW_RESTORE)
    if not user32.SetWindowPos(window, 0, 0, 0, 0, 0, _SWP_NOMOVE | _SWP_NOSIZE | _SWP_SHOWWINDOW):
        raise ConsoleReadinessError(ConsoleReadinessCode.WINDOW_PRESENTATION_FAILED)
    user32.SetForegroundWindow(window)
    if not user32.IsWindowVisible(window):
        raise ConsoleReadinessError(ConsoleReadinessCode.WINDOW_NOT_VISIBLE)
    if user32.IsIconic(window):
        raise ConsoleReadinessError(ConsoleReadinessCode.WINDOW_MINIMIZED)
    monitor = user32.MonitorFromWindow(window, _MONITOR_DEFAULTTONULL)
    if not monitor:
        raise ConsoleReadinessError(ConsoleReadinessCode.VISIBLE_MONITOR_UNAVAILABLE)
    window_rect = _Rect()
    monitor_info = _MonitorInfo()
    monitor_info.cbSize = ctypes.sizeof(monitor_info)
    if not user32.GetWindowRect(window, ctypes.byref(window_rect)):
        raise ConsoleReadinessError(ConsoleReadinessCode.WINDOW_BOUNDS_UNAVAILABLE)
    if not user32.GetMonitorInfoW(monitor, ctypes.byref(monitor_info)):
        raise ConsoleReadinessError(ConsoleReadinessCode.MONITOR_WORK_AREA_UNAVAILABLE)
    if not _rectangles_intersect(window_rect, monitor_info.rcWork):
        raise ConsoleReadinessError(ConsoleReadinessCode.WINDOW_OFFSCREEN)


def _present_console(*, kernel32=None, user32=None, desktop_name=_desktop_name) -> None:
    kernel32 = kernel32 or ctypes.WinDLL("kernel32", use_last_error=True)
    user32 = user32 or ctypes.WinDLL("user32", use_last_error=True)
    kernel32.GetConsoleWindow.argtypes = ()
    kernel32.GetConsoleWindow.restype = wintypes.HWND
    window = kernel32.GetConsoleWindow()
    if not window:
        raise ConsoleReadinessError(ConsoleReadinessCode.NO_CONSOLE_HWND)
    _present_window(window, kernel32=kernel32, user32=user32, desktop_name=desktop_name)


class WindowsPresentationWindow:
    """Small relay-owned top-level window used when the delegated console is off-screen."""

    def __init__(self) -> None:
        import tkinter

        self._messages: queue.Queue[str | None] = queue.Queue()
        self._closed = False
        try:
            tkinter.NoDefaultRoot()
            self._root = tkinter.Tk()
            self._root.title("AIDP Codex Execution")
            self._root.geometry("1000x700+40+40")
            self._root.protocol("WM_DELETE_WINDOW", lambda: None)
            self._output = tkinter.Text(
                self._root, background="#0b1020", foreground="#e5e7eb",
                insertbackground="#e5e7eb", borderwidth=0, wrap="word",
            )
            self._output.pack(fill="both", expand=True)
            self._output.configure(state="disabled")
            self._root.update_idletasks()
            self._root.deiconify()
            self._root.lift()
            hwnd = self._root.winfo_id()
            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            user32 = ctypes.WinDLL("user32", use_last_error=True)
            _configure_presentation_apis(kernel32, user32)
            hwnd = user32.GetAncestor(hwnd, _GA_ROOT)
            if not hwnd:
                raise ConsoleReadinessError(ConsoleReadinessCode.WINDOW_NOT_TOP_LEVEL)
            _present_window(hwnd, kernel32=kernel32, user32=user32)
            self._root.update()
        except ConsoleReadinessError:
            if hasattr(self, "_root"):
                self._root.destroy()
            raise
        except Exception:
            if hasattr(self, "_root"):
                self._root.destroy()
            raise ConsoleReadinessError(ConsoleReadinessCode.WINDOW_PRESENTATION_FAILED) from None

    def write(self, value: str) -> int:
        self._messages.put(value)
        return len(value)

    def flush(self) -> None:
        return None

    def update(self) -> None:
        while True:
            try:
                message = self._messages.get_nowait()
            except queue.Empty:
                break
            self._output.configure(state="normal")
            self._output.insert("end", message)
            self._output.see("end")
            self._output.configure(state="disabled")
        self._root.update()

    def close(self) -> None:
        if not self._closed:
            self._root.destroy()
            self._closed = True

    def __enter__(self):
        return self

    def __exit__(self, *_args) -> None:
        self.close()


def relay(
    argv: Sequence[str], *, console_presenter=_present_console,
    popen=subprocess.Popen, job_factory=WindowsJob,
    presentation_factory=WindowsPresentationWindow,
) -> int:
    if os.name != "nt" or not argv:
        return 125
    job = job_factory()
    child: subprocess.Popen[bytes] | None = None
    try:
        try:
            console_presenter()
        except ConsoleReadinessError as exc:
            if exc.code is not ConsoleReadinessCode.WINDOW_OFFSCREEN:
                raise
            console = presentation_factory()
        else:
            try:
                console = open("CONOUT$", "w", encoding="utf-8", errors="replace", buffering=1)
            except OSError:
                raise ConsoleReadinessError(ConsoleReadinessCode.CONOUT_UNAVAILABLE) from None
        with console:
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
            while True:
                update = getattr(console, "update", None)
                if update is not None:
                    update()
                try:
                    return_code = child.wait(timeout=0.04)
                    break
                except subprocess.TimeoutExpired:
                    continue
            stdout_thread.join()
            stderr_thread.join()
            update = getattr(console, "update", None)
            if update is not None:
                update()
            return return_code
    except KeyboardInterrupt:
        job.terminate(130)
        return 130
    except ConsoleReadinessError as exc:
        sys.stderr.buffer.write(_ERROR_PREFIX + exc.code.value.encode("ascii") + b"\n")
        sys.stderr.buffer.flush()
        return 125
    except Exception:
        sys.stderr.buffer.write(_ERROR_PREFIX + b"WINDOW_PRESENTATION_FAILED\n")
        sys.stderr.buffer.flush()
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
