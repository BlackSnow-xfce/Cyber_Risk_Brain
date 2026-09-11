import json
import threading
import pytest
from aidp_orchestration.foundation import DurableCAS, canonical_bytes, canonical_digest, parse_canonical_utf8, validate_timestamp

def test_canonical_vectors_and_rejections():
    assert canonical_bytes({"b": 2, "a": 1}) == b'{"a":1,"b":2}'
    assert canonical_digest({}) == "44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a"
    for value in [b"\xef\xbb\xbf{}", b'{"a":1,"a":2}', b'{"a":01}', b'{"a":-0}', b'{"a":1e0}', b'{"a":1.0}', b'{"a":9223372036854775808}', b'{"a":NaN}']:
        with pytest.raises((ValueError, UnicodeDecodeError, json.JSONDecodeError)): parse_canonical_utf8(value)

def test_nfc_and_timestamp_rules():
    composed = chr(0x00e9)
    assert parse_canonical_utf8(("{\"" + composed + "\":1}").encode()) == {composed: 1}
    with pytest.raises(ValueError): parse_canonical_utf8(("{\"" + composed + "\":1,\"e\\u0301\":2}").encode())
    validate_timestamp("2026-09-11T12:00:00.000000Z")
    for value in ("2026-09-11T12:00:00Z", "2026-09-11T12:00:00.000Z", "2026-09-11T12:00:00.000000+00:00", "2026-09-11T12:00:60.000000Z"):
        with pytest.raises(ValueError): validate_timestamp(value)

def test_durable_cas(tmp_path):
    cas = DurableCAS(tmp_path / "state.json")
    first = cas.compare_and_swap(expected_version=None, expected_digest=None, payload={"epoch": 1})
    second = cas.compare_and_swap(expected_version=first["version"], expected_digest=first["digest"], payload={"epoch": 2})
    assert second["version"] == 1
    with pytest.raises(RuntimeError): cas.compare_and_swap(expected_version=0, expected_digest=first["digest"], payload={"epoch": 3})
    cas.path.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError): cas.read()

def test_durable_cas_concurrent_writer_rejected(tmp_path):
    cas = DurableCAS(tmp_path / "state.json"); outcomes = []
    def write():
        try: outcomes.append(cas.compare_and_swap(expected_version=None, expected_digest=None, payload={"x": 1}))
        except RuntimeError: outcomes.append(None)
    threads = [threading.Thread(target=write) for _ in range(2)]
    [thread.start() for thread in threads]; [thread.join() for thread in threads]
    assert sum(value is not None for value in outcomes) == 1
