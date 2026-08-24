from __future__ import annotations

from io import BytesIO, StringIO
from types import SimpleNamespace

import pytest

from aidp_orchestration import visible_codex
from aidp_orchestration.visible_codex import _present_console, _pump


def test_relay_pump_preserves_capture_and_renders_live_utf8() -> None:
    source = BytesIO("live Grüße 完了".encode("utf-8"))
    capture = BytesIO()
    console = StringIO()
    _pump(source, capture, console)
    assert capture.getvalue() == "live Grüße 完了".encode("utf-8")
    assert console.getvalue() == "live Grüße 完了"


def _presentation_apis(
    calls: list[tuple[object, ...]], *, hwnd=42, visible=1, iconic=0,
    monitor=30, set_position=1, window_rect=(20, 20, 500, 400),
):
    def window_bounds(_hwnd, pointer):
        pointer._obj.left, pointer._obj.top, pointer._obj.right, pointer._obj.bottom = window_rect
        return 1

    def monitor_info(_monitor, pointer):
        work = pointer._obj.rcWork
        work.left, work.top, work.right, work.bottom = 0, 0, 1920, 1080
        return 1

    kernel32 = SimpleNamespace(GetConsoleWindow=lambda: hwnd)
    user32 = SimpleNamespace(
        GetWindowThreadProcessId=lambda window, process: 7,
        GetThreadDesktop=lambda thread: 10,
        OpenInputDesktop=lambda flags, inherit, access: 20,
        CloseDesktop=lambda desktop: calls.append(("close_desktop", desktop)) or 1,
        GetUserObjectInformationW=lambda *args: 1,
        ShowWindow=lambda window, mode: calls.append(("show", window, mode)) or 1,
        SetWindowPos=lambda window, after, x, y, width, height, flags: calls.append(("top", window, after, flags)) or set_position,
        SetForegroundWindow=lambda window: calls.append(("foreground", window)) or 1,
        IsWindowVisible=lambda window: visible,
        IsIconic=lambda window: iconic,
        MonitorFromWindow=lambda window, flags: monitor,
        GetWindowRect=window_bounds,
        GetMonitorInfoW=monitor_info,
    )
    return kernel32, user32


def test_present_console_verifies_desktop_restores_tops_and_foregrounds() -> None:
    calls: list[tuple[object, ...]] = []
    kernel32, user32 = _presentation_apis(calls)
    _present_console(kernel32=kernel32, user32=user32, desktop_name=lambda api, desktop: "Default")
    assert ("show", 42, 9) in calls
    assert ("top", 42, 0, 0x43) in calls
    assert ("foreground", 42) in calls
    assert ("close_desktop", 20) in calls


def test_present_console_fails_without_hwnd() -> None:
    kernel32, user32 = _presentation_apis([], hwnd=0)
    with pytest.raises(RuntimeError, match="unavailable"):
        _present_console(kernel32=kernel32, user32=user32, desktop_name=lambda api, desktop: "Default")


def test_present_console_requires_interactive_input_desktop() -> None:
    kernel32, user32 = _presentation_apis([])
    with pytest.raises(RuntimeError, match="interactive input desktop"):
        _present_console(
            kernel32=kernel32, user32=user32,
            desktop_name=lambda api, desktop: "Service" if desktop == 10 else "Default",
        )


def test_present_console_fails_when_window_remains_minimized() -> None:
    kernel32, user32 = _presentation_apis([], iconic=1)
    with pytest.raises(RuntimeError, match="minimized"):
        _present_console(kernel32=kernel32, user32=user32, desktop_name=lambda api, desktop: "Default")


@pytest.mark.parametrize(
    ("monitor", "window_rect"),
    ((0, (20, 20, 500, 400)), (30, (2000, 20, 2500, 400))),
)
def test_present_console_requires_visible_monitor_intersection(monitor, window_rect) -> None:
    kernel32, user32 = _presentation_apis([], monitor=monitor, window_rect=window_rect)
    with pytest.raises(RuntimeError, match="visible monitor"):
        _present_console(kernel32=kernel32, user32=user32, desktop_name=lambda api, desktop: "Default")


def test_relay_visibility_failure_prevents_codex_launch(monkeypatch: pytest.MonkeyPatch) -> None:
    launched = False

    class FakeJob:
        def close(self): pass
        def terminate(self, _code): pass

    def popen(*args, **kwargs):
        nonlocal launched
        launched = True
        raise AssertionError("must not launch")

    monkeypatch.setattr(visible_codex.os, "name", "nt")
    result = visible_codex.relay(
        ("codex.exe",),
        console_presenter=lambda: (_ for _ in ()).throw(RuntimeError("not visible")),
        popen=popen,
        job_factory=FakeJob,
    )
    assert result == 125
    assert not launched


def test_relay_rendering_replaces_invalid_bytes_but_capture_remains_exact() -> None:
    source = BytesIO(b"before\x81after")
    capture = BytesIO()
    console = StringIO()
    _pump(source, capture, console)
    assert capture.getvalue() == b"before\x81after"
    assert console.getvalue() == "before�after"
