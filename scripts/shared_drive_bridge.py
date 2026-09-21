#!/usr/bin/env python3
"""Fail-closed bridge between local VS Code and the SaNDAI Google Shared Drive.

The local checkout owns code. The RIT Shared Drive owns operational data,
configuration, and monitoring outputs. A versioned, ignored local cache is used
only to execute the local code against an exact Shared Drive snapshot.

Commands:
  status          Verify connectivity, identity, marker, and local cache state.
  pull            Pull and hash a new immutable input snapshot.
  run-monitoring  Pull, validate, then run local monitoring against that snapshot.
  push-results    Push only derived outputs/verification; never inputs or code.
  cycle           Pull, run monitoring, then push derived results.

No command deletes remote files. No command copies code or source inputs from
the local checkout into the Shared Drive.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
from hashlib import sha256
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
from typing import Any, Iterator


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOCATOR_PATH = PROJECT_ROOT / "workspace-locator.private.json"
MARKER_NAME = ".sandai-shared-data-plane.json"
EXPECTED_MARKER = {
    "schema_version": "sandai.workspace-marker.v2",
    "workspace_name": os.environ.get("SANDAI_SHARED_DRIVE_NAME", "SaNDAI Shared Workspace"),
    "workspace_type": "google_shared_drive",
    "shared_drive_id": os.environ.get("SANDAI_SHARED_DRIVE_ID", "CONFIGURE_LOCALLY"),
    "privacy": "private",
    "authoritative_data_plane": "private_google_shared_drive",
}
LOCATOR_SCHEMA = "sandai.shared-drive-locator.v1"
MANIFEST_SCHEMA = "sandai.shared-drive-pull-manifest.v1"
RUN_SCHEMA = "sandai.shared-drive-local-run.v1"
PUSH_ALLOWLIST = (
    "data/processed",
    "data/management",
    "outputs/management",
    "verification/local",
    "verification/parity",
)


class BridgeError(RuntimeError):
    """Raised when the Shared Drive contract cannot be proved."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def timestamp_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def safe_relative(value: str, *, label: str, allow_empty: bool = False) -> str:
    if value == "" and allow_empty:
        return ""
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or ".." in path.parts or "." in path.parts:
        raise BridgeError(f"Unsafe {label}: {value!r}")
    return str(path)


def load_locator(path: Path = LOCATOR_PATH) -> dict[str, Any]:
    if not path.is_file():
        raise BridgeError(
            f"Missing private Shared Drive locator: {path}. Copy workspace-locator.example.json first."
        )
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise BridgeError(f"Invalid JSON in private Shared Drive locator: {path}") from exc
    required = {
        "schema_version", "account", "shared_drive_name", "shared_drive_id",
        "rclone_remote", "remote_project_root", "local_runtime_cache",
    }
    missing = sorted(required.difference(value))
    if missing:
        raise BridgeError(f"Private locator is missing fields: {missing}")
    if value["schema_version"] != LOCATOR_SCHEMA:
        raise BridgeError(f"Unsupported locator schema: {value['schema_version']!r}")
    if value["shared_drive_id"] != EXPECTED_MARKER["shared_drive_id"]:
        raise BridgeError("Private locator Shared Drive ID does not match the SaNDAI contract.")
    if value["shared_drive_name"] != EXPECTED_MARKER["workspace_name"]:
        raise BridgeError("Private locator Shared Drive name does not match the SaNDAI contract.")
    remote = str(value["rclone_remote"])
    if not re.fullmatch(r"[A-Za-z0-9_.-]+:", remote):
        raise BridgeError(f"Unsafe rclone remote name: {remote!r}")
    value["remote_project_root"] = safe_relative(
        str(value["remote_project_root"]), label="remote_project_root", allow_empty=True
    )
    cache = Path(str(value["local_runtime_cache"])).expanduser()
    if not cache.is_absolute():
        cache = (PROJECT_ROOT / cache).resolve()
    try:
        cache.relative_to(PROJECT_ROOT.resolve())
    except ValueError as exc:
        raise BridgeError("The local runtime cache must stay inside the private project root.") from exc
    value["local_runtime_cache_resolved"] = cache
    return value


def validate_marker(value: dict[str, Any]) -> None:
    mismatches = {
        key: {"expected": expected, "actual": value.get(key)}
        for key, expected in EXPECTED_MARKER.items()
        if value.get(key) != expected
    }
    if mismatches:
        raise BridgeError(f"Shared Drive marker mismatch: {json.dumps(mismatches, sort_keys=True)}")


def remote_path(locator: dict[str, Any], relative: str = "") -> str:
    relative = safe_relative(relative, label="remote path", allow_empty=True)
    pieces = [part for part in (locator["remote_project_root"], relative) if part]
    suffix = "/".join(pieces)
    return f"{locator['rclone_remote']}{suffix}"


def rclone_command(locator: dict[str, Any], *args: str) -> list[str]:
    executable = shutil.which("rclone")
    if not executable:
        raise BridgeError("rclone is not installed or is not on PATH.")
    return [executable, *args, "--drive-team-drive", locator["shared_drive_id"]]


def run_command(command: list[str], *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(command, text=True, capture_output=True, env=env, check=False)
    if completed.returncode:
        detail = (completed.stderr or completed.stdout).strip()
        raise BridgeError(f"Command failed ({completed.returncode}): {' '.join(command[:4])}\n{detail}")
    return completed


def read_remote_marker(locator: dict[str, Any]) -> dict[str, Any]:
    completed = run_command(rclone_command(locator, "cat", remote_path(locator, MARKER_NAME)))
    try:
        value = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise BridgeError("The Shared Drive marker exists but is not valid JSON.") from exc
    validate_marker(value)
    return value


def read_remote_drive_identity(locator: dict[str, Any]) -> dict[str, str]:
    completed = run_command(rclone_command(locator, "backend", "drives", locator["rclone_remote"]))
    try:
        drives = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise BridgeError("rclone did not return a valid Shared Drive inventory.") from exc
    match = next(
        (drive for drive in drives if drive.get("id") == locator["shared_drive_id"]),
        None,
    )
    if match is None:
        raise BridgeError(
            f"RIT account {locator['account']} cannot see Shared Drive {locator['shared_drive_id']}."
        )
    if match.get("name") != locator["shared_drive_name"]:
        raise BridgeError(
            "Shared Drive ID is visible but its live name does not match the private locator: "
            f"{match.get('name')!r}"
        )
    return {"id": str(match["id"]), "name": str(match["name"])}


def copy_remote_file(locator: dict[str, Any], relative: str, destination: Path) -> None:
    relative = safe_relative(relative, label="remote file")
    destination.parent.mkdir(parents=True, exist_ok=True)
    run_command(rclone_command(locator, "copyto", remote_path(locator, relative), str(destination)))


def copy_remote_directory(locator: dict[str, Any], relative: str, destination: Path) -> None:
    relative = safe_relative(relative, label="remote directory")
    destination.mkdir(parents=True, exist_ok=True)
    run_command(rclone_command(locator, "copy", remote_path(locator, relative), str(destination)))


def load_contract(snapshot: Path) -> dict[str, Any]:
    path = snapshot / "config" / "data_contract.json"
    if not path.is_file():
        raise BridgeError(f"Shared Drive is missing required data contract: {path.relative_to(snapshot)}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise BridgeError("Shared Drive data contract is invalid JSON.") from exc
    if value.get("schema_version") != "sandai.shared-data-contract.v1":
        raise BridgeError(f"Unsupported data contract schema: {value.get('schema_version')!r}")
    for key in ("campaign_input", "learner_input"):
        if key not in value:
            raise BridgeError(f"Shared Drive data contract is missing {key!r}.")
        relative = safe_relative(str(value[key]), label=key)
        if not relative.startswith("data/"):
            raise BridgeError(f"Shared input must remain under data/: {relative}")
    return value


def snapshot_input_files(snapshot: Path, contract: dict[str, Any]) -> list[Path]:
    files = [snapshot / MARKER_NAME]
    files.extend(sorted(path for path in (snapshot / "config").rglob("*") if path.is_file()))
    for key in ("campaign_input", "learner_input"):
        files.append(snapshot / safe_relative(str(contract[key]), label=key))
    deduped: list[Path] = []
    for path in files:
        if path not in deduped:
            deduped.append(path)
    missing = [str(path.relative_to(snapshot)) for path in deduped if not path.is_file()]
    if missing:
        raise BridgeError(f"Pulled Shared Drive snapshot is incomplete: {missing}")
    return deduped


def build_manifest(snapshot: Path, locator: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    files = snapshot_input_files(snapshot, contract)
    return {
        "schema_version": MANIFEST_SCHEMA,
        "pulled_at_utc": utc_now(),
        "shared_drive_id": locator["shared_drive_id"],
        "shared_drive_name": locator["shared_drive_name"],
        "remote_project_root": locator["remote_project_root"],
        "files": {
            str(path.relative_to(snapshot)): {
                "sha256": sha256_file(path),
                "size": path.stat().st_size,
            }
            for path in files
        },
    }


def validate_snapshot(snapshot: Path) -> dict[str, Any]:
    marker_path = snapshot / MARKER_NAME
    manifest_path = snapshot / "pull-manifest.json"
    if not marker_path.is_file() or not manifest_path.is_file():
        raise BridgeError(f"Runtime snapshot is incomplete: {snapshot}")
    try:
        marker = json.loads(marker_path.read_text(encoding="utf-8"))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise BridgeError(f"Runtime snapshot metadata is invalid: {snapshot}") from exc
    validate_marker(marker)
    if manifest.get("schema_version") != MANIFEST_SCHEMA:
        raise BridgeError("Runtime snapshot has an unsupported pull manifest.")
    if manifest.get("shared_drive_id") != EXPECTED_MARKER["shared_drive_id"]:
        raise BridgeError("Runtime snapshot came from the wrong Shared Drive.")
    problems: list[str] = []
    for relative, expected in manifest.get("files", {}).items():
        relative = safe_relative(relative, label="manifest file")
        path = snapshot / relative
        if not path.is_file():
            problems.append(f"missing:{relative}")
            continue
        actual_hash = sha256_file(path)
        if actual_hash != expected.get("sha256"):
            problems.append(f"hash-mismatch:{relative}")
    if problems:
        raise BridgeError(f"Runtime snapshot integrity failure: {problems}")
    return manifest


def current_snapshot(locator: dict[str, Any]) -> Path:
    current = Path(locator["local_runtime_cache_resolved"]) / "current"
    if not current.exists():
        raise BridgeError("No validated local runtime snapshot exists. Run the pull command first.")
    resolved = current.resolve()
    snapshots_root = (Path(locator["local_runtime_cache_resolved"]) / "snapshots").resolve()
    try:
        resolved.relative_to(snapshots_root)
    except ValueError as exc:
        raise BridgeError("The runtime cache current pointer escapes its snapshots directory.") from exc
    return resolved


@contextmanager
def bridge_lock(locator: dict[str, Any]) -> Iterator[None]:
    cache = Path(locator["local_runtime_cache_resolved"])
    cache.mkdir(parents=True, exist_ok=True)
    lock_path = cache / ".bridge.lock"
    with lock_path.open("a+", encoding="utf-8") as handle:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise BridgeError("Another SaNDAI Shared Drive bridge process is already running.") from exc
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def pull(locator: dict[str, Any]) -> Path:
    read_remote_drive_identity(locator)
    read_remote_marker(locator)
    cache = Path(locator["local_runtime_cache_resolved"])
    snapshot = cache / "snapshots" / timestamp_slug()
    snapshot.mkdir(parents=True, exist_ok=False)
    try:
        copy_remote_file(locator, MARKER_NAME, snapshot / MARKER_NAME)
        copy_remote_directory(locator, "config", snapshot / "config")
        contract = load_contract(snapshot)
        for key in ("campaign_input", "learner_input"):
            relative = safe_relative(str(contract[key]), label=key)
            copy_remote_file(locator, relative, snapshot / relative)
        manifest = build_manifest(snapshot, locator, contract)
        atomic_json(snapshot / "pull-manifest.json", manifest)
        validate_snapshot(snapshot)
    except Exception:
        # The incomplete directory is retained as evidence and never becomes current.
        (snapshot / "PULL-FAILED.txt").write_text(
            f"Pull failed at {utc_now()}; this snapshot was never activated.\n",
            encoding="utf-8",
        )
        raise

    current = cache / "current"
    if current.exists() and not current.is_symlink():
        raise BridgeError(f"Refusing to replace non-symlink runtime pointer: {current}")
    temporary_link = cache / f".current.{os.getpid()}.tmp"
    if temporary_link.exists() or temporary_link.is_symlink():
        temporary_link.unlink()
    temporary_link.symlink_to(Path("snapshots") / snapshot.name)
    temporary_link.replace(current)
    return snapshot


def run_monitoring(locator: dict[str, Any], *, refresh: bool = True) -> dict[str, Any]:
    snapshot = pull(locator) if refresh else current_snapshot(locator)
    manifest = validate_snapshot(snapshot)
    input_hashes_before = {
        relative: sha256_file(snapshot / relative)
        for relative in manifest["files"]
    }
    env = os.environ.copy()
    env["SANDAI_WORKSPACE_ROOT"] = str(snapshot)
    command = [
        sys.executable,
        str(PROJECT_ROOT / "scripts" / "verify_workspace.py"),
        "--surface",
        "local",
    ]
    completed = run_command(command, env=env)
    try:
        monitoring_result = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise BridgeError("Monitoring command completed but did not return valid JSON.") from exc
    input_hashes_after = {
        relative: sha256_file(snapshot / relative)
        for relative in manifest["files"]
    }
    if input_hashes_before != input_hashes_after:
        raise BridgeError("Monitoring modified Shared Drive source inputs; results will not be pushed.")

    written = monitoring_result.get("written")
    if not isinstance(written, dict) or not written:
        raise BridgeError("Monitoring produced no derived outputs.")
    result_files: dict[str, dict[str, Any]] = {}
    for label, raw_path in written.items():
        path = Path(str(raw_path)).resolve()
        try:
            relative = path.relative_to(snapshot.resolve())
        except ValueError as exc:
            raise BridgeError(f"Monitoring output escaped the runtime snapshot: {path}") from exc
        allowed = any(str(relative).startswith(prefix + "/") for prefix in PUSH_ALLOWLIST)
        if not allowed:
            raise BridgeError(f"Monitoring wrote outside the derived-output allowlist: {relative}")
        if not path.is_file():
            raise BridgeError(f"Monitoring reported a missing output: {path}")
        result_files[str(relative)] = {"label": label, "sha256": sha256_file(path), "size": path.stat().st_size}

    run_record = {
        "schema_version": RUN_SCHEMA,
        "generated_at_utc": utc_now(),
        "shared_drive_id": locator["shared_drive_id"],
        "snapshot": snapshot.name,
        "pull_manifest_sha256": sha256_file(snapshot / "pull-manifest.json"),
        "input_hashes": input_hashes_before,
        "results": result_files,
        "source_inputs_modified": False,
        "external_action_performed": False,
    }
    run_path = snapshot / "verification" / "local" / f"bridge-run.{timestamp_slug()}.json"
    atomic_json(run_path, run_record)
    return {"snapshot": str(snapshot), "run_record": str(run_path), "monitoring": monitoring_result}


def push_results(locator: dict[str, Any]) -> dict[str, Any]:
    snapshot = current_snapshot(locator)
    manifest = validate_snapshot(snapshot)
    run_records = sorted((snapshot / "verification" / "local").glob("bridge-run.*.json"))
    if not run_records:
        raise BridgeError("No validated bridge run exists in the current snapshot. Run monitoring first.")
    for relative, expected in manifest["files"].items():
        if sha256_file(snapshot / relative) != expected["sha256"]:
            raise BridgeError(f"Input changed after monitoring; refusing result push: {relative}")

    pushed: list[dict[str, str]] = []
    for relative in PUSH_ALLOWLIST:
        source = snapshot / relative
        if not source.is_dir() or not any(path.is_file() for path in source.rglob("*")):
            continue
        destination = remote_path(locator, relative)
        command = rclone_command(
            locator,
            "copy",
            str(source),
            destination,
            "--immutable",
            "--exclude",
            "latest.json",
            "--exclude",
            ".DS_Store",
        )
        run_command(command)
        pushed.append({"local": str(source), "remote": destination})
    latest = snapshot / "verification" / "local" / "latest.json"
    if latest.is_file():
        # The live pointer is derived state. Preserve any prior pointer in a
        # timestamped history directory before replacing it; nothing is deleted.
        latest_remote = remote_path(locator, "verification/local/latest.json")
        history_remote = remote_path(locator, f"verification/local/history/{timestamp_slug()}")
        run_command(rclone_command(
            locator,
            "copyto",
            str(latest),
            latest_remote,
            "--backup-dir",
            history_remote,
        ))
        pushed.append({"local": str(latest), "remote": latest_remote})
    if not pushed:
        raise BridgeError("No derived output directories contained files; nothing was pushed.")
    return {
        "shared_drive_id": locator["shared_drive_id"],
        "snapshot": str(snapshot),
        "pushed": pushed,
        "source_inputs_pushed": False,
        "remote_deletions_performed": False,
    }


def status(locator: dict[str, Any]) -> dict[str, Any]:
    remote_identity = read_remote_drive_identity(locator)
    remote_marker = read_remote_marker(locator)
    cache = Path(locator["local_runtime_cache_resolved"])
    snapshots = sorted((cache / "snapshots").glob("*")) if (cache / "snapshots").is_dir() else []
    current: dict[str, Any] | None = None
    try:
        active = current_snapshot(locator)
        manifest = validate_snapshot(active)
        current = {
            "path": str(active),
            "pulled_at_utc": manifest["pulled_at_utc"],
            "file_count": len(manifest["files"]),
            "integrity": "PASS",
        }
    except BridgeError as exc:
        current = {"integrity": "NOT_READY", "detail": str(exc)}
    return {
        "account": locator["account"],
        "rclone_remote": locator["rclone_remote"],
        "shared_drive_name": locator["shared_drive_name"],
        "shared_drive_id": locator["shared_drive_id"],
        "live_shared_drive_identity": remote_identity,
        "remote_marker": remote_marker,
        "runtime_cache": str(cache),
        "retained_snapshots": len(snapshots),
        "current_snapshot": current,
        "local_code_root": str(PROJECT_ROOT),
        "policy": {
            "local_code_authoritative": True,
            "shared_drive_operational_state_authoritative": True,
            "automatic_remote_deletion": False,
            "push_allowlist": list(PUSH_ALLOWLIST),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("status", "pull", "run-monitoring", "push-results", "cycle"))
    parser.add_argument(
        "--use-current",
        action="store_true",
        help="For run-monitoring only: reuse the already validated cache instead of pulling. Default is a fresh pull.",
    )
    args = parser.parse_args()
    try:
        locator = load_locator()
        with bridge_lock(locator):
            if args.command == "status":
                result: Any = status(locator)
            elif args.command == "pull":
                snapshot = pull(locator)
                result = {"snapshot": str(snapshot), "integrity": "PASS"}
            elif args.command == "run-monitoring":
                result = run_monitoring(locator, refresh=not args.use_current)
            elif args.command == "push-results":
                result = push_results(locator)
            else:
                run_result = run_monitoring(locator, refresh=True)
                push_result = push_results(locator)
                result = {"run": run_result, "push": push_result}
        print(json.dumps(result, indent=2, sort_keys=True))
    except BridgeError as exc:
        print(f"SaNDAI Shared Drive bridge STOPPED: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc


if __name__ == "__main__":
    main()
