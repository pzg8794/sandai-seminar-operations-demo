from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = (
    PROJECT_ROOT / "data" / "synthetic"
    if (PROJECT_ROOT / "data" / "synthetic").is_dir()
    else PROJECT_ROOT / "data"
)
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import shared_drive_bridge as bridge  # noqa: E402


def marker() -> dict[str, str]:
    return dict(bridge.EXPECTED_MARKER)


def build_snapshot(tmp_path: Path) -> tuple[Path, dict[str, object]]:
    snapshot = tmp_path / "snapshot"
    (snapshot / "config").mkdir(parents=True)
    (snapshot / "data" / "synthetic").mkdir(parents=True)
    shutil.copy2(PROJECT_ROOT / ".sandai-shared-data-plane.json", snapshot / bridge.MARKER_NAME)
    shutil.copy2(PROJECT_ROOT / "config" / "data_contract.json", snapshot / "config" / "data_contract.json")
    shutil.copy2(PROJECT_ROOT / "config" / "campaign_config.json", snapshot / "config" / "campaign_config.json")
    shutil.copy2(
        DATA_ROOT / "sandai_demo_campaign_data.csv",
        snapshot / "data" / "synthetic" / "sandai_demo_campaign_data.csv",
    )
    shutil.copy2(
        DATA_ROOT / "sandai_demo_learner_engagement.csv",
        snapshot / "data" / "synthetic" / "sandai_demo_learner_engagement.csv",
    )
    locator: dict[str, object] = {
        "shared_drive_id": bridge.EXPECTED_MARKER["shared_drive_id"],
        "shared_drive_name": bridge.EXPECTED_MARKER["workspace_name"],
        "remote_project_root": "",
    }
    contract = bridge.load_contract(snapshot)
    manifest = bridge.build_manifest(snapshot, locator, contract)
    bridge.atomic_json(snapshot / "pull-manifest.json", manifest)
    return snapshot, manifest


def test_marker_must_prove_exact_shared_drive_identity() -> None:
    value = marker()
    value["shared_drive_id"] = "personal-my-drive-folder"
    with pytest.raises(bridge.BridgeError, match="marker mismatch"):
        bridge.validate_marker(value)


def test_snapshot_hash_manifest_passes_then_detects_mutation(tmp_path: Path) -> None:
    snapshot, manifest = build_snapshot(tmp_path)
    assert bridge.validate_snapshot(snapshot) == manifest
    campaign = snapshot / "data" / "synthetic" / "sandai_demo_campaign_data.csv"
    campaign.write_text(campaign.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(bridge.BridgeError, match="hash-mismatch"):
        bridge.validate_snapshot(snapshot)


@pytest.mark.parametrize("value", ["../secret", "/absolute/path", "data/../../secret", "."])
def test_remote_paths_cannot_escape(value: str) -> None:
    with pytest.raises(bridge.BridgeError, match="Unsafe"):
        bridge.safe_relative(value, label="test")


def test_push_allowlist_contains_only_derived_state() -> None:
    assert "config" not in bridge.PUSH_ALLOWLIST
    assert "data/synthetic" not in bridge.PUSH_ALLOWLIST
    assert "data/raw" not in bridge.PUSH_ALLOWLIST
    assert "src" not in bridge.PUSH_ALLOWLIST
    assert all(
        path.startswith(("data/processed", "data/management", "outputs/", "verification/"))
        for path in bridge.PUSH_ALLOWLIST
    )


def test_private_locator_targets_rit_shared_drive(tmp_path: Path) -> None:
    locator_path = tmp_path / "workspace-locator.private.json"
    locator_path.write_text(
        json.dumps({
            "schema_version": bridge.LOCATOR_SCHEMA,
            "account": "rit-demo-account@example.edu",
            "shared_drive_name": bridge.EXPECTED_MARKER["workspace_name"],
            "shared_drive_id": bridge.EXPECTED_MARKER["shared_drive_id"],
            "rclone_remote": "rit_mydrive:",
            "remote_project_root": "",
            "local_runtime_cache": str(PROJECT_ROOT / ".runtime" / "test-cache"),
        }),
        encoding="utf-8",
    )
    value = bridge.load_locator(locator_path)
    assert value["account"] == "rit-demo-account@example.edu"
    assert value["shared_drive_id"] == bridge.EXPECTED_MARKER["shared_drive_id"]
    assert value["rclone_remote"] == "rit_mydrive:"
