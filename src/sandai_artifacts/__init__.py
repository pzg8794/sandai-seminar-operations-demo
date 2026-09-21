"""Shared SaNDAI data-plane and decision logic."""

from .core import (
    CAMPAIGN_SCHEMA_VERSION,
    LEARNER_SCHEMA_VERSION,
    CampaignConfig,
    DecisionEngine,
    build_decision_snapshot,
    build_learner_support_profiles,
    build_parity_snapshot,
    build_weekly_metrics,
    compare_parity_snapshots,
    core_metrics_digest,
    load_campaign_data,
    load_learner_data,
    load_workspace_config,
    resolve_workspace_root,
    write_management_outputs,
)
from .learner_support import StudentProfile, StudentSupportEngine
from .management import CampaignMonitor
from .student_experience import StudentLearningProfile, StudentSeminarExperience

__all__ = [
    "CAMPAIGN_SCHEMA_VERSION",
    "LEARNER_SCHEMA_VERSION",
    "CampaignConfig",
    "DecisionEngine",
    "build_decision_snapshot",
    "build_learner_support_profiles",
    "build_parity_snapshot",
    "build_weekly_metrics",
    "compare_parity_snapshots",
    "core_metrics_digest",
    "load_campaign_data",
    "load_learner_data",
    "load_workspace_config",
    "resolve_workspace_root",
    "write_management_outputs",
    "StudentProfile",
    "StudentSupportEngine",
    "CampaignMonitor",
    "StudentLearningProfile",
    "StudentSeminarExperience",
]
