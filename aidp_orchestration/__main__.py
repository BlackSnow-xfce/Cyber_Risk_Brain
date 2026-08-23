"""Explicit local AIDP orchestration entry point."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from .acceptance import AcceptanceHarness, serialize_acceptance_result
from .architect_writer import (
    ArchitectContractWriter,
    blocked_writer_result,
    load_architect_task_contract,
    serialize_writer_result,
)
from .architect_ingress import ArchitectGitIngress
from .architect_ingress_acceptance import (
    ArchitectIngressAcceptanceHarness,
    serialize_architect_ingress_acceptance_result,
)
from .contracts import AcceptanceStatus
from .control_plane import AIDPControlPlane, serialize_control_plane_result
from .executor import CodexExecutionService, serialize_execution_result
from .repository import AIDPRepository
from .runner import AIDPRunner, serialize_runner_result
from .writer_control_plane_acceptance import (
    WriterControlPlaneAcceptanceHarness,
    serialize_writer_control_plane_acceptance_result,
)
from .trigger_publisher import AIDPWatchOnce, serialize_trigger_result
from .trigger_publisher_acceptance import (
    TriggerPublisherAcceptanceHarness,
    serialize_trigger_publisher_acceptance_result,
)
from .watcher_runtime import (
    AIDPLocalWatcherRuntime,
    MINIMUM_WATCH_INTERVAL_SECONDS,
    serialize_watch_runtime_result,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect the PredatorAI AIDP state")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="never mutate the repository")
    mode.add_argument("--execute", action="store_true", help="explicitly execute one Codex request")
    mode.add_argument("--run-ready", action="store_true", help="execute one repository-authorized ready task")
    mode.add_argument("--acceptance-e2e", action="store_true", help="run Codex against an isolated temporary repository")
    mode.add_argument("--control-plane", action="store_true", help="run one fail-closed control-plane decision")
    mode.add_argument("--materialize-architect-contract", type=Path, help="materialize one authorized JSON contract")
    mode.add_argument("--acceptance-writer-control-plane", action="store_true", help="run isolated Writer-to-Control-Plane acceptance")
    mode.add_argument("--watch-once", action="store_true", help="consume and publish at most one local Architect contract")
    mode.add_argument("--acceptance-trigger-publisher", action="store_true", help="run isolated Trigger-to-Git-remote acceptance")
    mode.add_argument("--watch", action="store_true", help="periodically invoke the existing local watch-once boundary")
    mode.add_argument("--acceptance-architect-ingress", action="store_true", help="run isolated Architect Git ingress acceptance")
    parser.add_argument("--task-id", help="task to execute (required with --execute)")
    parser.add_argument("--timeout", type=float, default=900.0)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--watch-interval", type=float, default=10.0)
    parser.add_argument("--architect-contract-branch", help="explicit origin branch enabling Git contract ingress for --watch")
    args = parser.parse_args()
    if args.architect_contract_branch and not args.watch:
        parser.error("--architect-contract-branch is only valid with --watch")
    if args.watch and args.watch_interval < MINIMUM_WATCH_INTERVAL_SECONDS:
        parser.error(f"--watch-interval must be at least {MINIMUM_WATCH_INTERVAL_SECONDS:g} seconds")
    repository = AIDPRepository(args.root)
    if args.acceptance_architect_ingress:
        result = ArchitectIngressAcceptanceHarness(args.root).run()
        print(serialize_architect_ingress_acceptance_result(result))
        return 0 if result.status is AcceptanceStatus.PASS else 2
    if args.watch:
        try:
            ingress = ArchitectGitIngress(repository, branch=args.architect_contract_branch) if args.architect_contract_branch else None
        except ValueError as exc:
            parser.error(str(exc))
        result = AIDPLocalWatcherRuntime(repository, interval_seconds=args.watch_interval, ingress=ingress).run()
        print(serialize_watch_runtime_result(result))
        return 0 if result.status.value == "STOPPED" else 2
    if args.acceptance_trigger_publisher:
        result = TriggerPublisherAcceptanceHarness(args.root, timeout_seconds=args.timeout).run()
        print(serialize_trigger_publisher_acceptance_result(result))
        return 0 if result.status is AcceptanceStatus.PASS else 2
    if args.watch_once:
        result = AIDPWatchOnce(repository, timeout_seconds=args.timeout).run_once()
        print(serialize_trigger_result(result))
        return 0 if result.status.value in {"NO_ACTION", "PUBLISHED"} else 2
    if args.acceptance_writer_control_plane:
        result = WriterControlPlaneAcceptanceHarness(args.root, timeout_seconds=args.timeout).run()
        print(serialize_writer_control_plane_acceptance_result(result))
        return 0 if result.status is AcceptanceStatus.PASS else 2
    if args.materialize_architect_contract is not None:
        try:
            contract = load_architect_task_contract(args.materialize_architect_contract)
            result = ArchitectContractWriter(repository).materialize_task(contract)
        except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
            result = blocked_writer_result(f"invalid ArchitectTaskContract: {exc.__class__.__name__}")
        print(serialize_writer_result(result))
        return 2 if result.decision.action.value == "BLOCKED" else 0
    if args.control_plane:
        result = AIDPControlPlane(repository, timeout_seconds=args.timeout).run_once()
        print(serialize_control_plane_result(result))
        return 2 if result.final_action.value == "BLOCKED" else 0
    if args.acceptance_e2e:
        result = AcceptanceHarness(args.root, timeout_seconds=args.timeout).run()
        print(serialize_acceptance_result(result))
        return 0 if result.status is AcceptanceStatus.PASS else 2
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
