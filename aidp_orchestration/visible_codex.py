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


def relay(argv: Sequence[str]) -> int:
    if os.name != "nt" or not argv:
        return 125
    job = WindowsJob()
    child: subprocess.Popen[bytes] | None = None
    try:
        child = subprocess.Popen(
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
        with (
            open("CONOUT$", "w", encoding="utf-8", errors="replace", buffering=1) as console,
        ):
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
