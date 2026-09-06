"""Sanitized, machine-readable operator events derived from real execution evidence."""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable


ActivitySink = Callable[[str], None]


def emit_activity(sink: ActivitySink | None, source: str, kind: str, **details: object) -> None:
    if sink is None:
        return
    payload = {"source": source, "kind": kind, **details}
    sink(json.dumps({"operator_activity": payload}, sort_keys=True, separators=(",", ":")))


def emit_codex_jsonl(sink: ActivitySink | None, source: str, output: str) -> None:
    """Project allowed Codex JSONL fields without exposing prompts or opaque metadata."""

    for line in output.splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            emit_activity(sink, source, "process_output", stream="stdout", text=line)
            continue
        if not isinstance(event, dict):
            continue
        event_type = event.get("type")
        item = event.get("item")
        if not isinstance(item, dict):
            if isinstance(event_type, str):
                emit_activity(sink, source, "codex_event", event_type=event_type)
            continue
        item_type = item.get("type")
        if item_type == "agent_message" and isinstance(item.get("text"), str):
            emit_activity(sink, source, "agent_message", text=item["text"])
        elif item_type == "command_execution":
            details = _selected(item, ("command", "aggregated_output", "status", "exit_code"))
            emit_activity(sink, source, "command_execution", **details)
        elif item_type == "file_change":
            changes = item.get("changes")
            paths = tuple(
                change["path"] for change in changes
                if isinstance(changes, list) and isinstance(change, dict)
                and isinstance(change.get("path"), str)
            ) if isinstance(changes, list) else ()
            emit_activity(sink, source, "file_change", paths=paths, status=item.get("status"))
        elif isinstance(item_type, str):
            emit_activity(sink, source, "inspection", item_type=item_type, event_type=event_type)


def emit_process_output(sink: ActivitySink | None, source: str, outcome, *, command: Iterable[str] | None = None) -> None:
    details: dict[str, object] = {}
    if command is not None:
        details["command"] = tuple(command)
    emit_activity(sink, source, "process_started", **details)
    if outcome.stdout:
        emit_activity(sink, source, "process_output", stream="stdout", text=outcome.stdout)
    if outcome.stderr:
        emit_activity(sink, source, "process_output", stream="stderr", text=outcome.stderr)
    emit_activity(
        sink, source, "process_completed", returncode=outcome.returncode,
        timed_out=outcome.timed_out, error=outcome.error,
    )


def _selected(value: dict[str, object], names: tuple[str, ...]) -> dict[str, object]:
    return {name: value[name] for name in names if isinstance(value.get(name), (str, int))}
