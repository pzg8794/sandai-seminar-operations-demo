"""Object-oriented student-profile and support views for the synthetic demo."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping

import pandas as pd

from .core import build_learner_support_profiles


@dataclass(frozen=True)
class StudentProfile:
    """One explicitly fictional student profile used in the assignment demo."""

    participant_id: str
    demo_student: str
    student_stage: str
    career_goal: str
    experience_level: str
    preferred_learning_format: str
    campaign_week: int
    seminar_attended: bool
    access_channel: str
    session_status: str
    checkpoints_completed: int
    checkpoint_total: int
    feedback_submitted: bool
    feedback_score: float | None
    follow_up_opt_in: bool
    support_request: str
    last_activity_days_ago: int

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "StudentProfile":
        payload = {field: value.get(field) for field in cls.__dataclass_fields__}
        if pd.isna(payload["feedback_score"]):
            payload["feedback_score"] = None
        return cls(**payload)

    def as_record(self) -> dict[str, Any]:
        return asdict(self)


class StudentSupportEngine:
    """Explainable engagement, risk, and next-best-action engine."""

    def __init__(self, learners: pd.DataFrame):
        self._source = learners.copy()
        self._profiles = build_learner_support_profiles(self._source)

    @property
    def profiles(self) -> pd.DataFrame:
        return self._profiles.copy()

    def profile(self, participant_id: str) -> StudentProfile:
        matches = self._source.loc[self._source["participant_id"].eq(participant_id)]
        if len(matches) != 1:
            raise KeyError(f"Expected one fictional student profile for {participant_id!r}.")
        return StudentProfile.from_mapping(matches.iloc[0].to_dict())

    def support_queue(self) -> pd.DataFrame:
        columns = [
            "demo_student", "participant_id", "campaign_week", "seminar_attended",
            "career_goal", "preferred_learning_format", "engagement_score",
            "risk_status", "support_request", "recommended_intervention",
        ]
        queue = self._profiles.loc[
            self._profiles["risk_status"].isin(["RED", "YELLOW"]), columns
        ].copy()
        order = pd.Categorical(queue["risk_status"], categories=["RED", "YELLOW"], ordered=True)
        return (
            queue.assign(_risk_order=order)
            .sort_values(["_risk_order", "engagement_score", "demo_student"])
            .drop(columns="_risk_order")
            .reset_index(drop=True)
        )

    def weekly_summary(self) -> pd.DataFrame:
        profiles = self._profiles
        weekly = (
            profiles.groupby("campaign_week", as_index=False)
            .agg(
                fictional_students=("participant_id", "nunique"),
                seminar_attendance_rate=("seminar_attended", "mean"),
                completion_rate=("session_status", lambda values: (values == "completed").mean()),
                mean_engagement_score=("engagement_score", "mean"),
                red_students=("risk_status", lambda values: int((values == "RED").sum())),
                yellow_students=("risk_status", lambda values: int((values == "YELLOW").sum())),
                green_students=("risk_status", lambda values: int((values == "GREEN").sum())),
            )
            .sort_values("campaign_week")
            .reset_index(drop=True)
        )
        weekly["mean_engagement_score"] = weekly["mean_engagement_score"].round(1)
        return weekly

    def program_improvement_summary(self) -> pd.DataFrame:
        profiles = self._profiles
        summary = (
            profiles.groupby("preferred_learning_format", as_index=False)
            .agg(
                fictional_students=("participant_id", "nunique"),
                mean_engagement_score=("engagement_score", "mean"),
                support_needed=("risk_status", lambda values: int(values.isin(["RED", "YELLOW"]).sum())),
                completion_rate=("session_status", lambda values: (values == "completed").mean()),
            )
            .sort_values(["support_needed", "mean_engagement_score"], ascending=[False, True])
            .reset_index(drop=True)
        )
        summary["mean_engagement_score"] = summary["mean_engagement_score"].round(1)
        summary["recommended_program_test"] = summary["preferred_learning_format"].map(
            {
                "worked example": "Add one complete worked example before independent practice.",
                "step-by-step checklist": "Publish a one-page Start → Practice → Finish checklist.",
                "short video plus practice": "Test a five-minute recap followed by one hands-on task.",
                "visual walkthrough": "Add a visual notebook map with the quickest path highlighted.",
            }
        )
        return summary
