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


def test_present_console_requires_hwnd_and_explicitly_shows_it(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[object, ...]] = []
    kernel32 = SimpleNamespace(GetConsoleWindow=lambda: 42)
    user32 = SimpleNamespace(
        ShowWindow=lambda hwnd, mode: calls.append(("show", hwnd, mode)) or 1,
        IsWindowVisible=lambda hwnd: calls.append(("visible", hwnd)) or 1,
    )
    monkeypatch.setattr(visible_codex.ctypes, "WinDLL", lambda name, **kwargs: kernel32 if name == "kernel32" else user32)
    _present_console()
    assert calls == [("show", 42, 1), ("visible", 42)]


def test_present_console_fails_without_hwnd(monkeypatch: pytest.MonkeyPatch) -> None:
    kernel32 = SimpleNamespace(GetConsoleWindow=lambda: 0)
    user32 = SimpleNamespace(ShowWindow=lambda *args: 1, IsWindowVisible=lambda *args: 1)
    monkeypatch.setattr(visible_codex.ctypes, "WinDLL", lambda name, **kwargs: kernel32 if name == "kernel32" else user32)
    with pytest.raises(RuntimeError, match="unavailable"):
        _present_console()


def test_present_console_fails_when_window_remains_invisible(monkeypatch: pytest.MonkeyPatch) -> None:
    kernel32 = SimpleNamespace(GetConsoleWindow=lambda: 42)
    user32 = SimpleNamespace(ShowWindow=lambda *args: 1, IsWindowVisible=lambda *args: 0)
    monkeypatch.setattr(visible_codex.ctypes, "WinDLL", lambda name, **kwargs: kernel32 if name == "kernel32" else user32)
    with pytest.raises(RuntimeError, match="not visible"):
        _present_console()


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
