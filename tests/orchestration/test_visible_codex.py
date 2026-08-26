from __future__ import annotations

from io import BytesIO, StringIO
from types import SimpleNamespace

import pytest

from aidp_orchestration import visible_codex
from aidp_orchestration.visible_codex import (
    ConsoleReadinessCode,
    ConsoleReadinessError,
    _present_console,
    _pump,
)


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
    parent=0, root=42, window_thread=7, window_desktop=10, input_desktop=20,
    window_bounds_result=1, monitor_info_result=1,
):
    def window_bounds(_hwnd, pointer):
        pointer._obj.left, pointer._obj.top, pointer._obj.right, pointer._obj.bottom = window_rect
        return window_bounds_result

    def monitor_info(_monitor, pointer):
        work = pointer._obj.rcWork
        work.left, work.top, work.right, work.bottom = 0, 0, 1920, 1080
        return monitor_info_result

    kernel32 = SimpleNamespace(GetConsoleWindow=lambda: hwnd, GetCurrentThreadId=lambda: 8)
    user32 = SimpleNamespace(
        GetAncestor=lambda window, flag: root,
        GetParent=lambda window: parent,
        GetWindowThreadProcessId=lambda window, process: window_thread,
        GetThreadDesktop=lambda thread: window_desktop,
        OpenInputDesktop=lambda flags, inherit, access: calls.append(("desktop_access", access)) or input_desktop,
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
    assert ("desktop_access", 0x0001) in calls


def test_present_console_fails_without_hwnd() -> None:
    kernel32, user32 = _presentation_apis([], hwnd=0)
    with pytest.raises(ConsoleReadinessError) as error:
        _present_console(kernel32=kernel32, user32=user32, desktop_name=lambda api, desktop: "Default")
    assert error.value.code is ConsoleReadinessCode.NO_CONSOLE_HWND


def test_present_console_requires_interactive_input_desktop() -> None:
    kernel32, user32 = _presentation_apis([])
    with pytest.raises(ConsoleReadinessError) as error:
        _present_console(
            kernel32=kernel32, user32=user32,
            desktop_name=lambda api, desktop: "Service" if desktop == 10 else "Default",
        )
    assert error.value.code is ConsoleReadinessCode.DESKTOP_MISMATCH


def test_present_console_fails_when_window_remains_minimized() -> None:
    kernel32, user32 = _presentation_apis([], iconic=1)
    with pytest.raises(ConsoleReadinessError) as error:
        _present_console(kernel32=kernel32, user32=user32, desktop_name=lambda api, desktop: "Default")
    assert error.value.code is ConsoleReadinessCode.WINDOW_MINIMIZED


@pytest.mark.parametrize(
    ("monitor", "window_rect"),
    ((0, (20, 20, 500, 400)), (30, (2000, 20, 2500, 400))),
)
def test_present_console_requires_visible_monitor_intersection(monitor, window_rect) -> None:
    kernel32, user32 = _presentation_apis([], monitor=monitor, window_rect=window_rect)
    with pytest.raises(ConsoleReadinessError) as error:
        _present_console(kernel32=kernel32, user32=user32, desktop_name=lambda api, desktop: "Default")
    expected = ConsoleReadinessCode.VISIBLE_MONITOR_UNAVAILABLE if not monitor else ConsoleReadinessCode.WINDOW_OFFSCREEN
    assert error.value.code is expected


@pytest.mark.parametrize(
    ("options", "expected"),
    (
        ({"parent": -3}, ConsoleReadinessCode.MESSAGE_ONLY_OR_PSEUDOCONSOLE_WINDOW),
        ({"root": 99}, ConsoleReadinessCode.WINDOW_NOT_TOP_LEVEL),
        ({"window_thread": 0}, ConsoleReadinessCode.WINDOW_THREAD_UNAVAILABLE),
        ({"window_desktop": 0}, ConsoleReadinessCode.WINDOW_DESKTOP_UNAVAILABLE),
        ({"input_desktop": 0}, ConsoleReadinessCode.INPUT_DESKTOP_UNAVAILABLE),
        ({"set_position": 0}, ConsoleReadinessCode.WINDOW_PRESENTATION_FAILED),
        ({"visible": 0}, ConsoleReadinessCode.WINDOW_NOT_VISIBLE),
        ({"window_bounds_result": 0}, ConsoleReadinessCode.WINDOW_BOUNDS_UNAVAILABLE),
        ({"monitor_info_result": 0}, ConsoleReadinessCode.MONITOR_WORK_AREA_UNAVAILABLE),
    ),
)
def test_present_console_reports_stable_predicate_code(options, expected) -> None:
    kernel32, user32 = _presentation_apis([], **options)
    with pytest.raises(ConsoleReadinessError) as error:
        _present_console(kernel32=kernel32, user32=user32, desktop_name=lambda api, desktop: "Default")
    assert error.value.code is expected


def test_present_console_sanitizes_desktop_name_failure() -> None:
    kernel32, user32 = _presentation_apis([])
    with pytest.raises(ConsoleReadinessError) as error:
        _present_console(
            kernel32=kernel32,
            user32=user32,
            desktop_name=lambda api, desktop: (_ for _ in ()).throw(OSError("sensitive")),
        )
    assert error.value.code is ConsoleReadinessCode.DESKTOP_NAME_UNAVAILABLE


def test_relay_visibility_failure_prevents_codex_launch(
    monkeypatch: pytest.MonkeyPatch, capfd: pytest.CaptureFixture[str],
) -> None:
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
        console_presenter=lambda: (_ for _ in ()).throw(
            ConsoleReadinessError(ConsoleReadinessCode.WINDOW_NOT_VISIBLE)
        ),
        popen=popen,
        job_factory=FakeJob,
    )
    assert result == 125
    assert not launched
    assert capfd.readouterr().err == "AIDP_VISIBLE_CONSOLE_ERROR_V2:WINDOW_NOT_VISIBLE\n"


def test_offscreen_console_uses_verified_dedicated_surface_before_launch(
    monkeypatch: pytest.MonkeyPatch, capfd: pytest.CaptureFixture[str],
) -> None:
    order: list[str] = []

    class FakeJob:
        def assign(self, _child): order.append("assign")
        def close(self): order.append("close_job")
        def terminate(self, _code): pass

    class FakeSurface(StringIO):
        def __enter__(self):
            order.append("surface_ready")
            return self
        def __exit__(self, *_args):
            order.append("surface_closed")
        def update(self):
            order.append("surface_update")

    class FakeChild:
        stdout = BytesIO(b"live output")
        stderr = BytesIO()
        _handle = 1
        def poll(self): return 0
        def wait(self, timeout=None): return 0

    def launch(*_args, **_kwargs):
        order.append("codex_launch")
        return FakeChild()

    monkeypatch.setattr(visible_codex.os, "name", "nt")
    result = visible_codex.relay(
        ("codex.exe",),
        console_presenter=lambda: (_ for _ in ()).throw(
            ConsoleReadinessError(ConsoleReadinessCode.WINDOW_OFFSCREEN)
        ),
        popen=launch,
        job_factory=FakeJob,
        presentation_factory=FakeSurface,
    )
    captured = capfd.readouterr()
    assert result == 0
    assert captured.err == "AIDP_VISIBLE_CONSOLE_READY_V2\n"
    assert order.index("surface_ready") < order.index("codex_launch")
    assert "surface_update" in order


def test_dedicated_surface_failure_remains_fail_closed(
    monkeypatch: pytest.MonkeyPatch, capfd: pytest.CaptureFixture[str],
) -> None:
    launched = False

    class FakeJob:
        def close(self): pass
        def terminate(self, _code): pass

    def launch(*_args, **_kwargs):
        nonlocal launched
        launched = True

    monkeypatch.setattr(visible_codex.os, "name", "nt")
    result = visible_codex.relay(
        ("codex.exe",),
        console_presenter=lambda: (_ for _ in ()).throw(
            ConsoleReadinessError(ConsoleReadinessCode.WINDOW_OFFSCREEN)
        ),
        popen=launch,
        job_factory=FakeJob,
        presentation_factory=lambda: (_ for _ in ()).throw(
            ConsoleReadinessError(ConsoleReadinessCode.WINDOW_PRESENTATION_FAILED)
        ),
    )
    assert result == 125
    assert not launched
    assert capfd.readouterr().err == "AIDP_VISIBLE_CONSOLE_ERROR_V2:WINDOW_PRESENTATION_FAILED\n"


def test_relay_rendering_replaces_invalid_bytes_but_capture_remains_exact() -> None:
    source = BytesIO(b"before\x81after")
    capture = BytesIO()
    console = StringIO()
    _pump(source, capture, console)
    assert capture.getvalue() == b"before\x81after"
    assert console.getvalue() == "before�after"
