from __future__ import annotations

from io import BytesIO, StringIO

from aidp_orchestration.visible_codex import _pump


def test_relay_pump_preserves_capture_and_renders_live_utf8() -> None:
    source = BytesIO("live Grüße 完了".encode("utf-8"))
    capture = BytesIO()
    console = StringIO()
    _pump(source, capture, console)
    assert capture.getvalue() == "live Grüße 完了".encode("utf-8")
    assert console.getvalue() == "live Grüße 完了"


def test_relay_rendering_replaces_invalid_bytes_but_capture_remains_exact() -> None:
    source = BytesIO(b"before\x81after")
    capture = BytesIO()
    console = StringIO()
    _pump(source, capture, console)
    assert capture.getvalue() == b"before\x81after"
    assert console.getvalue() == "before�after"
