"""Explicit local AIDP orchestration entry point."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from .executor import CodexExecutionService, serialize_execution_result
from .repository import AIDPRepository


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect the PredatorAI AIDP state")
    parser.add_argument("--dry-run", action="store_true", help="never mutate the repository")
    parser.add_argument("--execute", action="store_true", help="explicitly execute one Codex request")
    parser.add_argument("--task-id", help="task to execute (required with --execute)")
    parser.add_argument("--timeout", type=float, default=900.0)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    if args.dry_run == args.execute:
        parser.error("choose exactly one of --dry-run or --execute")
    repository = AIDPRepository(args.root)
    if args.dry_run:
        decision = repository.inspect()
        print(json.dumps(asdict(decision), default=str, indent=2))
        return 0
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
