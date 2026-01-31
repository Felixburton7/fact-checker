from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from checker_of_facts.engine import EngineFactory
from checker_of_facts.mcp.workspace import FileWorkspace


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Internal-knowledge fact checker")
    parser.add_argument("claim", help="Claim text to fact check")
    parser.add_argument(
        "--workspace",
        default=Path(".workspace"),
        help="Workspace directory for logs and evidence",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    workspace = FileWorkspace(args.workspace)
    try:
        engine = EngineFactory(workspace=workspace).build()
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
    result = engine.run(args.claim)
    print(json.dumps(asdict(result), indent=2))


if __name__ == "__main__":
    main()
