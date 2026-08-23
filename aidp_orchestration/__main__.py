"""Explicit local AIDP orchestration entry point."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from .executor import CodexExecutionService, serialize_execution_result
from .repository import AIDPRepository
from .runner import AIDPRunner, serialize_runner_result


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect the PredatorAI AIDP state")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="never mutate the repository")
    mode.add_argument("--execute", action="store_true", help="explicitly execute one Codex request")
    mode.add_argument("--run-ready", action="store_true", help="execute one repository-authorized ready task")
    parser.add_argument("--task-id", help="task to execute (required with --execute)")
    parser.add_argument("--timeout", type=float, default=900.0)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    repository = AIDPRepository(args.root)
    if args.dry_run:
        decision = repository.inspect()
        print(json.dumps(asdict(decision), default=str, indent=2))
        return 0
    if args.run_ready:
        result = AIDPRunner(repository, timeout_seconds=args.timeout).run_ready()
        print(serialize_runner_result(result))
        return 0 if result.status.value in {"NO_ACTION", "EXECUTED"} else 2
    if not args.task_id:
        parser.error("--task-id is required with --execute")
    try:
        request = repository.build_execution_request(args.task_id)
        result = CodexExecutionService(repository_root=args.root, timeout_seconds=args.timeout).execute(request)
    except (ValueError, OSError, RuntimeError) as exc:
        parser.error(str(exc))
    print(serialize_execution_result(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
