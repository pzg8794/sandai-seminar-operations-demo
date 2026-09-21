"""High-level management interface for the SaNDAI seminar prototype."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from .core import (
    CampaignConfig,
    DecisionEngine,
    build_decision_snapshot,
    build_weekly_metrics,
    load_campaign_data,
    load_learner_data,
    load_workspace_config,
)
from .learner_support import StudentSupportEngine


@dataclass
class CampaignMonitor:
    """One object that joins campaign, student, and intervention evidence."""

    workspace_root: Path
    settings: dict[str, Any]
    campaign: pd.DataFrame
    learners: pd.DataFrame
    campaign_metadata: dict[str, Any]
    learner_metadata: dict[str, Any]

    @classmethod
    def from_workspace(cls, workspace_root: str | Path) -> "CampaignMonitor":
        root = Path(workspace_root).resolve()
        _, settings = load_workspace_config(root)
        campaign, campaign_metadata = load_campaign_data(root)
        learners, learner_metadata = load_learner_data(root)
        return cls(root, settings, campaign, learners, campaign_metadata, learner_metadata)

    @property
    def weekly(self) -> pd.DataFrame:
        return build_weekly_metrics(
            self.campaign,
            weekly_minimum=int(self.settings["weekly_attendance_target"]),
            total_target=int(self.settings["total_attendance_target"]),
        )

    @property
    def decision(self) -> dict[str, Any]:
        return build_decision_snapshot(self.weekly, self.settings)

    @property
    def student_support(self) -> StudentSupportEngine:
        return StudentSupportEngine(self.learners)

    def executive_card(self) -> pd.DataFrame:
        decision = self.decision
        rows = [
            ("Current decision week", decision["week"]),
            ("Observed attendance", decision["weekly_attendance"]),
            ("Cumulative attendance", decision["cumulative_attendance"]),
            ("T-3 expected attendance", round(decision["forecast_expected_attendance"], 1)),
            ("Probability of at least 20", f"{decision['forecast_probability_at_least_20']:.0%}"),
            ("Risk status", decision["risk_status"]),
            ("Next campaign action", decision["recommended_intervention"]),
        ]
        return pd.DataFrame(rows, columns=["Management question", "Answer"])

    def recovery_scenario(self) -> pd.DataFrame:
        week = int(self.settings["current_week"])
        weekly = self.weekly
        selected = weekly.loc[weekly["week"].eq(week)].iloc[0]
        engine = DecisionEngine(CampaignConfig.from_mapping(self.settings), weekly)
        history = engine.history_before(week)
        registrations = int(selected["t3_registrations"])
        confirmations = int(selected["t3_confirmations"])
        pre = engine.attendance_forecast(history, registrations, confirmations, seed_offset=week)
        post = engine.attendance_forecast(
            history,
            registrations + int(self.settings["planned_extra_registrations"]),
            confirmations + int(self.settings["planned_extra_confirmations"]),
            seed_offset=week,
        )
        return pd.DataFrame(
            [
                {
                    "Scenario": "T-3 before intervention",
                    "Registrations": pre["registrations"],
                    "Confirmations": pre["confirmations"],
                    "Expected attendance": round(pre["expected"], 1),
                    "P(attendance ≥20)": pre["probability"],
                    "Risk": pre["status"],
                },
                {
                    "Scenario": "After partner + confirmation recovery",
                    "Registrations": post["registrations"],
                    "Confirmations": post["confirmations"],
                    "Expected attendance": round(post["expected"], 1),
                    "P(attendance ≥20)": post["probability"],
                    "Risk": post["status"],
                },
            ]
        )

    def channel_summary(self) -> pd.DataFrame:
        result = (
            self.campaign.groupby(["channel", "network_layer"], as_index=False)
            .agg(
                reach=("reach", "sum"),
                registrations=("registrations", "sum"),
                attendees=("attendees", "sum"),
                effort_units=("outreach_effort_units", "sum"),
            )
        )
        result["show_rate"] = result["attendees"] / result["registrations"]
        result["attendees_per_effort"] = result["attendees"] / result["effort_units"]
        return result.sort_values("attendees", ascending=False).reset_index(drop=True)

    def program_improvement_summary(self) -> pd.DataFrame:
        return self.student_support.program_improvement_summary()

    def conversion_funnel(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "Stage": [
                    "Attended free seminar",
                    "Opted in for follow-up",
                    "Qualified follow-up",
                    "Converted to an approved offering",
                ],
                "Synthetic count": [
                    int(self.campaign["attendees"].sum()),
                    int(self.campaign["opt_in_leads"].sum()),
                    int(self.campaign["qualified_followups"].sum()),
                    int(self.campaign["approved_conversions"].sum()),
                ],
                "Business purpose": [
                    "Deliver useful free career-readiness value",
                    "Continue only with students who want more information",
                    "Match interest to a relevant credential or service",
                    "Measure attributable downstream value",
                ],
            }
        )

    def operating_cadence(self) -> pd.DataFrame:
        return pd.DataFrame(
            [
                ("T-7", "Open registrations; activate at least three partner channels", "Piter"),
                ("T-5", "Check registration pace and channel contribution", "Piter"),
                ("T-3", "Run forecast; trigger recovery if RED/YELLOW", "Piter"),
                ("T-1", "Run confirmation reminder and waitlist/backfill", "Piter"),
                ("T", "Deliver seminar; record actual attendance", "Piter"),
                ("T+1", "Review results, student signals, and next program test", "Piter"),
            ],
            columns=["Gate", "Required action", "Owner"],
        )

    def requirement_traceability(self) -> pd.DataFrame:
        rows = [
            ("20 students each week", "Weekly attendance and goal-met flag"),
            ("160 attendances over eight weeks", "Cumulative attendance trajectory"),
            ("Expand beyond immediate network", "Four-layer channel summary"),
            ("Track results", "Funnel, attendance, show rate, risk, and student engagement"),
            ("Monetization path", "Free seminar → opt-in → qualified follow-up → conversion"),
            ("Recover when under target", "T-3 forecast and pre/post recovery scenario"),
            ("Own the outcome", "Owner, threshold, recommended action, and weekly decision cycle"),
            ("Use generative AI", "Research, outreach drafting, content variants, and analysis support"),
            ("Improve the program", "Fictional student profiles → support queue → format-level tests"),
        ]
        return pd.DataFrame(rows, columns=["Assignment requirement", "Prototype evidence"])
