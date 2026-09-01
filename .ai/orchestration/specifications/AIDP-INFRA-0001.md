# AIDP-INFRA-0001 — Autonomous Architect Review & Rework Lifecycle

Status: ARCHITECT APPROVED / READY FOR CODEX

## Authority and bootstrap

This specification is AIDP infrastructure authority. It does not consume
`TASK-0131` and grants no PredatorAI product authority.

The current production parser predates the approved `AIDP-INFRA-\d{4}`
namespace. Therefore this first infrastructure contract is a one-time
Product-Owner-authorized bootstrap contract executed only against
`D:\CyberRiskBrain-orchestration-execution` at expected HEAD
`0179487d003761dc15dbdfe2bf465171bace871b`. It must never be ingressed or
materialized as a Product task in `D:\CyberRiskBrain`.

The first implementation responsibility is the narrowly bounded parser change
that accepts existing task identities plus exactly `AIDP-INFRA-\d{4}`. No
broader task identifier is authorized.

## Immutable review contracts

`ArchitectReviewRequest` contains:

- deterministic `review_request_id`;
- task ID, zero-based initial/positive rework review iteration and execution ID;
- resolved Product repository, Git common-directory identity, branch and remote;
- original immutable task contract ID, digest and complete execution authority;
- review-envelope path and digest;
- execution status, start/result/envelope commits, changed files, validator
  results and scope compliance;
- expected current HEAD, observed current HEAD, reviewed HEAD and reviewed tree;
- previous result, rework contract and canonical finding identities;
- timezone-aware creation time.

The request ID is the lowercase SHA-256 digest of canonical versioned JSON over
task ID, review iteration, execution ID, authority digest, review-envelope
digest, expected current HEAD, reviewed HEAD and reviewed tree. No random ID is
permitted for the same evidence.

`ArchitectFinding` contains a caller-supplied stable finding ID, rule ID,
severity, summary, sorted evidence paths and required change. Its authoritative
fingerprint is SHA-256 over canonical versioned JSON containing rule ID,
severity, sorted normalized evidence paths and a normalized machine action ID.
Human prose and free-text similarity are excluded from identity.

`ArchitectReviewResult` contains:

- deterministic result ID and exact request ID;
- task ID, execution ID and review iteration;
- `PASS`, `FAIL` or `BLOCKED` disposition;
- reviewed HEAD, expected HEAD and reviewed tree;
- ordered machine-readable findings;
- allowed rework scope and required validations;
- sanitized provenance: Architect process identity, validated launcher identity,
  selected model identifier, invocation timestamps, schema version and digest;
- bounded failure reason and timezone-aware creation time.

The result ID is SHA-256 over the canonical result payload excluding only its
own ID. A repeated ID with different bytes is invalid.

PASS requires exact request binding, no remediation findings, empty rework scope,
empty rework validators and no failure reason. FAIL requires exact binding, one
or more findings, non-empty scope wholly contained by original task authority,
and non-empty validators wholly contained by the original registry-backed
authority. BLOCKED requires empty rework scope and validators and cannot approve
or project lifecycle state.

No result field may assert Product Owner approval, Product Owner rejection,
`DONE`, or next-task authority.

## Product-worktree identity

Before every inspection, launch, persistence-driven transition and Git write,
the lifecycle boundary verifies:

1. configured root resolves exactly to the configured Product root;
2. `git rev-parse --show-toplevel` equals that resolved root;
3. Git common-directory identity equals the configured Product repository;
4. branch equals the explicit Product lifecycle branch;
5. origin exists and branch upstream is the expected origin branch;
6. local HEAD and upstream relationship satisfy the transition precondition;
7. the resolved root is neither the orchestration-execution worktree nor the
   architect-contracts worktree.

Mismatch is `BLOCKED / ESCALATION_REQUIRED`; cwd is never sufficient authority.

## Architect process

`ArchitectReviewCoordinator` reuses `ProcessRunner`/`SubprocessRunner`. It runs
headless with `shell=False`, explicit argv, Product cwd, read-only sandbox,
non-interactive stdin, explicit timeout, ephemeral Codex session and a checked
JSON Schema final output. CLI/version capabilities are preflighted without
falling back to weaker flags.

Captured stdout and stderr are independently bounded. Truncation, invalid UTF-8,
timeout, non-zero exit, missing schema output or capability mismatch blocks.
Raw streams and prompts never enter review-result Git envelopes.

## Lifecycle projection

One `AIDPLifecycleOnce` is called by the existing watcher runtime after ingress:

```text
READY_FOR_CODEX     -> existing contract/Codex execution
REWORK_REQUIRED     -> existing ReworkContract/Codex execution
READY_FOR_ARCHITECT -> ArchitectReviewCoordinator
WAITING_FOR_PRODUCT_OWNER -> NO_ACTION
unsafe/ambiguous    -> BLOCKED
```

The existing watcher lock covers the complete iteration and both agent types.

Codex success publication commits only authorized implementation files, then
commits the review envelope together with the deterministic READY-to-REVIEW task
and handoff projection as one exact publication transaction before push. A
partial or dirty projection grants no state authority.

Architect results are persisted with exclusive creation, read back and digest
verified before mutation. A sanitized result envelope is committed under:

`.ai/orchestration/architect-review-results/{task_id}-{review_iteration}-{review_result_id}.json`

PASS then commits the exact ARCHITECT_APPROVED task/handoff projection. With the
mandatory Product Owner gate, inspection yields `WAITING_FOR_PRODUCT_OWNER` and
all automation stops.

FAIL commits the exact `REVIEW / REWORK REQUIRED` projection. The deterministic
iteration-addressed `ReworkContract` uses the committed post-projection HEAD,
validated scope, canonical findings, validated validators and result timestamp.
The existing writer, admission and Codex execution path then take over.

## Iteration and no-progress policy

- Initial review is iteration 0.
- Rework executions are numbered 1 through 3.
- A review following Rework N has review iteration N.
- A FAIL at review iteration 3 would require Rework 4 and therefore blocks with
  `ESCALATION_REQUIRED`.
- No review iteration may jump, replay with different evidence or bind another
  execution ID.
- The same canonical finding fingerprint in two consecutive post-rework FAIL
  results blocks immediately.
- An unchanged reviewed tree after rework blocks.
- No changed finding-relevant authorized file after rework blocks.

No unsafe condition is silently retried.

## Persistence and restart behavior

The Product Git-internal runtime contains immutable, iteration-addressed:

- `architect-review-requests/`;
- `architect-review-results/`;
- `architect-review-attempts/`;
- `rework-contracts/{task_id}/{iteration}-{contract_id}.json`;
- `lifecycle-events.jsonl`;
- existing `audit.jsonl`.

Persisted requests resume before launch. A live or unverifiable attempt prevents
duplicate launch. A persisted verified result is reused. After a lifecycle
commit, its result ID permits continuation of only the remaining deterministic
steps. A crash after FAIL projection regenerates the same rework contract.

A crash after Codex execution but before review publication remains deliberately
fail-closed: preserve evidence, detect the abandoned execution, block with a
precise `ESCALATION_REQUIRED` diagnostic and never execute Codex again.

## Acceptance and validation

Isolated temporary repositories and fake process runners must prove the complete
PASS, FAIL, multiple-rework, fourth-rework limit, identical-finding no-progress,
Product Owner hard-stop, Product-worktree identity and restart paths. They must
also cover every malformed, stale, duplicate, widening, dirty, divergent,
timeout, wrong-commit and unauthorized-authority condition in the execution
contract.

Required validators are the complete Python test suite and `git diff --check`.
No TypeScript or product build is required because Product code is prohibited.

## Architect specification review

Result: PASS / APPROVED.

The specification is finite, preserves existing execution and governance
boundaries, introduces no parallel supervisor or launcher, makes all new
authority immutable and machine-verifiable, and stops unconditionally at the
Product Owner gate.
