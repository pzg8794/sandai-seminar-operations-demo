from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import shutil
import sys

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = (
    PROJECT_ROOT / "data" / "synthetic"
    if (PROJECT_ROOT / "data" / "synthetic").is_dir()
    else PROJECT_ROOT / "data"
)
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from sandai_artifacts import (  # noqa: E402
    CampaignMonitor,
    StudentSeminarExperience,
    StudentSupportEngine,
    build_parity_snapshot,
    compare_parity_snapshots,
    resolve_workspace_root,
    write_management_outputs,
)
from sandai_artifacts.core import WorkspaceError  # noqa: E402


@pytest.fixture()
def workspace(tmp_path: Path) -> Path:
    root = tmp_path / "SaNDAI Shared Workspace"
    for relative in [
        "config", "data/synthetic", "data/processed", "data/management",
        "outputs/management", "verification/local", "verification/colab",
    ]:
        (root / relative).mkdir(parents=True, exist_ok=True)
    shutil.copy2(PROJECT_ROOT / ".sandai-shared-data-plane.json", root / ".sandai-shared-data-plane.json")
    for name in ["campaign_config.json", "data_contract.json", "student_public_config.json"]:
        shutil.copy2(PROJECT_ROOT / "config" / name, root / "config" / name)
    shutil.copy2(
        DATA_ROOT / "sandai_demo_campaign_data.csv",
        root / "data" / "synthetic" / "sandai_demo_campaign_data.csv",
    )
    shutil.copy2(
        DATA_ROOT / "sandai_demo_learner_engagement.csv",
        root / "data" / "synthetic" / "sandai_demo_learner_engagement.csv",
    )
    return root


def file_hash(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def test_local_and_colab_adapters_match_required_metrics(workspace: Path) -> None:
    left = build_parity_snapshot(workspace, surface="local")
    right = build_parity_snapshot(workspace, surface="colab")
    report = compare_parity_snapshots(left, right)
    assert report["match"] is True
    assert report["metrics_compared"] == [
        "weekly_attendance", "cumulative_attendance", "show_rate",
        "required_registrations", "attendance_forecast", "risk_status",
        "recommended_intervention",
    ]


def test_known_assignment_scenario_is_reproducible(workspace: Path) -> None:
    snapshot = build_parity_snapshot(workspace, surface="local")
    assert [row["weekly_attendance"] for row in snapshot["weekly_metrics"]] == [22, 24, 18, 23, 21, 26, 24, 25]
    assert [row["cumulative_attendance"] for row in snapshot["weekly_metrics"]] == [22, 46, 64, 87, 108, 134, 158, 183]
    assert snapshot["decision"]["risk_status"] == "RED"
    assert "secondary partner channel" in snapshot["decision"]["recommended_intervention"].lower()


def test_missing_shared_input_fails_closed(workspace: Path) -> None:
    campaign = workspace / "data" / "synthetic" / "sandai_demo_campaign_data.csv"
    campaign.unlink()
    with pytest.raises(WorkspaceError, match="missing"):
        build_parity_snapshot(workspace, surface="local")
    assert not campaign.exists()


def test_schema_failure_is_explicit(workspace: Path) -> None:
    campaign_path = workspace / "data" / "synthetic" / "sandai_demo_campaign_data.csv"
    frame = pd.read_csv(campaign_path).drop(columns=["attendees"])
    frame.to_csv(campaign_path, index=False)
    with pytest.raises(WorkspaceError, match="attendees"):
        build_parity_snapshot(workspace, surface="local")


def test_source_inputs_are_unchanged_by_output_writer(workspace: Path) -> None:
    sources = [
        workspace / "config" / "data_contract.json",
        workspace / "config" / "campaign_config.json",
        workspace / "data" / "synthetic" / "sandai_demo_campaign_data.csv",
        workspace / "data" / "synthetic" / "sandai_demo_learner_engagement.csv",
    ]
    before = {path: file_hash(path) for path in sources}
    written = write_management_outputs(workspace, surface="local")
    assert Path(written["verification"]).is_file()
    assert before == {path: file_hash(path) for path in sources}


def test_parity_detects_metric_and_input_drift(workspace: Path) -> None:
    left = build_parity_snapshot(workspace, surface="local")
    right = deepcopy(build_parity_snapshot(workspace, surface="colab"))
    right["campaign_source"]["source_sha256"] = "different"
    right["decision"]["risk_status"] = "GREEN"
    report = compare_parity_snapshots(left, right)
    assert report["match"] is False
    assert report["same_input_data"] is False
    assert "risk_status" in report["mismatches"]


def test_private_marker_is_required(workspace: Path) -> None:
    (workspace / ".sandai-shared-data-plane.json").unlink()
    with pytest.raises(WorkspaceError, match="marker"):
        resolve_workspace_root(workspace)


def test_fictional_student_profiles_produce_explainable_support_actions(workspace: Path) -> None:
    monitor = CampaignMonitor.from_workspace(workspace)
    engine = StudentSupportEngine(monitor.learners)
    profiles = engine.profiles
    queue = engine.support_queue()

    assert len(profiles) == 32
    assert profiles["demo_student"].str.startswith("Demo Student ").all()
    assert set(profiles["risk_status"]) == {"GREEN", "YELLOW", "RED"}
    assert profiles["engagement_score"].between(0, 100).all()
    assert not queue.empty
    assert queue["recommended_intervention"].str.len().gt(20).all()
    assert "Invite to the next seminar" in queue.iloc[0]["recommended_intervention"]


def test_program_improvement_view_connects_student_evidence_to_a_test(workspace: Path) -> None:
    monitor = CampaignMonitor.from_workspace(workspace)
    improvements = monitor.program_improvement_summary()
    assert set(improvements["preferred_learning_format"]) == {
        "worked example", "step-by-step checklist",
        "short video plus practice", "visual walkthrough",
    }
    assert improvements["recommended_program_test"].str.len().gt(20).all()


def test_student_seminar_demo_produces_a_tangible_next_step() -> None:
    experience = StudentSeminarExperience.demo()
    checks = experience.validate()
    assert all(checks.values())
    assert experience.profile.demo_student == "Demo Student Avery Example (fictional)"
    assert not experience.weekly_plan().empty
    assert "Designed" in experience.resume_bullet()
