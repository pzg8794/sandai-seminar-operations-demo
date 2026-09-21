#!/usr/bin/env python3
"""Compare the latest real local and Colab runs from the same Drive workspace."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from sandai_artifacts import compare_parity_snapshots, resolve_workspace_root  # noqa: E402


def read_latest(root: Path, surface: str) -> dict:
    pointer_path = root / "verification" / surface / "latest.json"
    if not pointer_path.is_file():
        raise SystemExit(f"Missing {surface} verification pointer: {pointer_path}")
    pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
    snapshot_path = root / pointer["verification_file"]
    if not snapshot_path.is_file():
        raise SystemExit(f"Missing {surface} verification snapshot: {snapshot_path}")
    return json.loads(snapshot_path.read_text(encoding="utf-8"))


def main() -> None:
    root = resolve_workspace_root(source_root=PROJECT_ROOT)
    local = read_latest(root, "local")
    colab = read_latest(root, "colab")
    report = compare_parity_snapshots(local, colab)
    report["generated_at_utc"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    output_dir = root / "verification" / "parity"
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output = output_dir / f"parity-report.{timestamp}.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output_dir / "latest.json").write_text(
        json.dumps(
            {
                "schema_version": "sandai.parity-pointer.v1",
                "report_file": str(output.relative_to(root)),
                "match": report["match"],
                "generated_at_utc": report["generated_at_utc"],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    if not report["match"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
