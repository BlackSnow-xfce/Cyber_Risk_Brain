"""Local, read-only AIDP orchestration dry-run entry point."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from .repository import AIDPRepository


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect the PredatorAI AIDP state")
    parser.add_argument("--dry-run", action="store_true", help="never mutate the repository")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    if not args.dry_run:
        parser.error("only --dry-run is available in this foundation")
    decision = AIDPRepository(args.root).inspect()
    print(json.dumps(asdict(decision), default=str, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
