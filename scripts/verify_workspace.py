#!/usr/bin/env python3
"""Run one reproducible management calculation against the private Drive data plane."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from sandai_artifacts import (  # noqa: E402
    build_parity_snapshot,
    resolve_workspace_root,
    write_management_outputs,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--surface", choices=("local", "colab"), required=True)
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args()

    root = resolve_workspace_root(source_root=PROJECT_ROOT)
    snapshot = build_parity_snapshot(root, surface=args.surface)
    result: dict[str, object] = {
        "workspace_root": str(root),
        "snapshot": snapshot,
    }
    if not args.no_write:
        result["written"] = write_management_outputs(root, surface=args.surface)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
