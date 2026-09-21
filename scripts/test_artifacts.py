#!/usr/bin/env python3
"""Execute both notebook artifacts cleanly without modifying their source files."""

from __future__ import annotations

import argparse
from hashlib import sha256
import os
from pathlib import Path
import re
import sys
import tempfile

import nbformat
from nbclient import NotebookClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from sandai_artifacts import resolve_workspace_root  # noqa: E402

def notebook_path(name: str) -> Path:
    public_layout = PROJECT_ROOT / "notebooks" / name
    return public_layout if public_layout.is_file() else PROJECT_ROOT / name


MANAGEMENT = notebook_path("Piter_Garcia_SaNDAI_Management_Command_Center.ipynb")
STUDENT = notebook_path("Piter_Garcia_SaNDAI_Student_Seminar_Companion.ipynb")


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def execute(path: Path, workspace_root: Path) -> None:
    before = digest(path)
    notebook = nbformat.read(path, as_version=4)
    source = "\n".join(cell.source for cell in notebook.cells if cell.cell_type == "code")
    forbidden = [r"\brequests\b", r"\bhttpx\b", r"urllib\.request", r"socket\."]
    found = [pattern for pattern in forbidden if re.search(pattern, source)]
    if found:
        raise RuntimeError(f"Unexpected network/process capability in {path.name}: {found}")
    subprocess_lines = [line.strip() for line in source.splitlines() if "subprocess.run" in line]
    allowed_subprocess_markers = (
        '["git", "clone", "--depth", "1"',
        '["git", "-C", str(SOURCE_ROOT), "pull", "--ff-only"]',
        '[sys.executable, "-m", "pip", "install", "-q", "-e", str(SOURCE_ROOT)]',
    )
    unexpected_subprocess = [
        line for line in subprocess_lines
        if not any(marker in line for marker in allowed_subprocess_markers)
    ]
    if unexpected_subprocess:
        raise RuntimeError(
            f"Unexpected subprocess use in {path.name}: {unexpected_subprocess}"
        )
    previous_root = os.environ.get("SANDAI_WORKSPACE_ROOT")
    previous_source = os.environ.get("SANDAI_SOURCE_ROOT")
    previous_write = os.environ.get("SANDAI_WRITE_OUTPUTS")
    os.environ["SANDAI_WORKSPACE_ROOT"] = str(workspace_root)
    os.environ["SANDAI_SOURCE_ROOT"] = str(PROJECT_ROOT)
    os.environ["SANDAI_WRITE_OUTPUTS"] = "0"
    try:
        with tempfile.TemporaryDirectory(prefix="sandai-notebook-test-") as temp:
            NotebookClient(
                notebook,
                timeout=180,
                kernel_name="python3",
                resources={"metadata": {"path": temp}},
            ).execute()
    finally:
        if previous_root is None:
            os.environ.pop("SANDAI_WORKSPACE_ROOT", None)
        else:
            os.environ["SANDAI_WORKSPACE_ROOT"] = previous_root
        if previous_source is None:
            os.environ.pop("SANDAI_SOURCE_ROOT", None)
        else:
            os.environ["SANDAI_SOURCE_ROOT"] = previous_source
        if previous_write is None:
            os.environ.pop("SANDAI_WRITE_OUTPUTS", None)
        else:
            os.environ["SANDAI_WRITE_OUTPUTS"] = previous_write
    if digest(path) != before:
        raise RuntimeError(f"Notebook source changed during execution: {path}")
    print(f"PASS: {path.name} executed cleanly; source hash unchanged.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--management", action="store_true")
    parser.add_argument("--student", action="store_true")
    args = parser.parse_args()
    selected = []
    if args.all or args.management:
        selected.append(MANAGEMENT)
    if args.all or args.student:
        selected.append(STUDENT)
    if not selected:
        parser.error("Choose --all, --management, or --student.")
    root = resolve_workspace_root(source_root=PROJECT_ROOT)
    for notebook in selected:
        execute(notebook, root)


if __name__ == "__main__":
    main()
