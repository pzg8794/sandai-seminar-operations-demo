"""Portable SaNDAI demo data, campaign metrics, and student-support logic.

The included records are deliberately fictional. The same functions run in
local VS Code and Colab so the assignment can demonstrate one reproducible
solution across both execution surfaces.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any
import json
import math
import os
import shutil

import numpy as np
import pandas as pd


CAMPAIGN_SCHEMA_VERSION = "sandai.campaign.v1"
LEARNER_SCHEMA_VERSION = "sandai.learner-engagement.v1"
WORKSPACE_NAME = os.environ.get("SANDAI_SHARED_DRIVE_NAME", "SaNDAI Shared Workspace")
WORKSPACE_MARKER = ".sandai-shared-data-plane.json"
WORKSPACE_MARKER_SCHEMA = "sandai.workspace-marker.v2"
SHARED_DRIVE_ID = os.environ.get("SANDAI_SHARED_DRIVE_ID", "CONFIGURE_LOCALLY")

CAMPAIGN_REQUIRED_COLUMNS = (
    "week", "seminar_date", "channel", "network_layer", "partner_category",
    "contact_status", "reach", "interested", "registrations", "confirmations",
    "attendees", "opt_in_leads", "qualified_followups", "approved_conversions",
    "outreach_effort_units", "t3_registrations", "t3_confirmations",
    "intervention", "recovery_lift_attendees",
)

LEARNER_REQUIRED_COLUMNS = (
    "participant_id", "demo_student", "student_stage", "career_goal",
    "experience_level", "preferred_learning_format", "campaign_week",
    "seminar_attended", "access_channel", "session_status",
    "checkpoints_completed", "checkpoint_total", "feedback_submitted",
    "feedback_score", "follow_up_opt_in", "support_request",
    "last_activity_days_ago",
)

CAMPAIGN_INTEGER_COLUMNS = (
    "week", "reach", "interested", "registrations", "confirmations", "attendees",
    "opt_in_leads", "qualified_followups", "approved_conversions",
    "outreach_effort_units", "t3_registrations", "t3_confirmations",
    "recovery_lift_attendees",
)


class WorkspaceError(RuntimeError):
    """Raised when the private shared-data contract cannot be satisfied."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _timestamp_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _candidate_source_roots(source_root: Path | None) -> list[Path]:
    candidates: list[Path] = []
    for start in [source_root, Path.cwd()]:
        if start is None:
            continue
        start = Path(start).expanduser().resolve()
        candidates.append(start)
        candidates.extend(list(start.parents)[:6])
    deduped: list[Path] = []
    for candidate in candidates:
        if candidate not in deduped:
            deduped.append(candidate)
    return deduped


def resolve_workspace_root(
    explicit_root: str | Path | None = None,
    *,
    source_root: str | Path | None = None,
) -> Path:
    """Resolve the private Drive workspace without notebook-specific absolute paths.

    Resolution order: explicit argument, ``SANDAI_WORKSPACE_ROOT``, local private
    runtime-cache locator, then the conventional Colab Shared Drive mount. Every
    candidate must contain the Shared Drive marker and data contract. Missing or
    legacy My Drive state fails closed.
    """

    def validate_candidate(candidate: Path, *, label: str) -> Path:
        contract = candidate / "config" / "data_contract.json"
        marker = candidate / WORKSPACE_MARKER
        if not marker.is_file():
            raise WorkspaceError(f"{label} SaNDAI workspace is missing its Shared Drive marker: {marker}")
        if not contract.is_file():
            raise WorkspaceError(f"{label} SaNDAI workspace is missing its data contract: {contract}")
        try:
            marker_value = json.loads(marker.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise WorkspaceError(f"Invalid Shared Drive workspace marker: {marker}") from exc
        expected = {
            "schema_version": WORKSPACE_MARKER_SCHEMA,
            "workspace_name": WORKSPACE_NAME,
            "workspace_type": "google_shared_drive",
            "shared_drive_id": SHARED_DRIVE_ID,
            "privacy": "private",
            "authoritative_data_plane": "private_google_shared_drive",
        }
        mismatches = {
            key: {"expected": expected_value, "actual": marker_value.get(key)}
            for key, expected_value in expected.items()
            if marker_value.get(key) != expected_value
        }
        if mismatches:
            raise WorkspaceError(f"Shared Drive marker mismatch at {marker}: {mismatches}")
        return candidate

    candidates: list[Path] = []
    if explicit_root:
        candidate = Path(explicit_root).expanduser().resolve()
        return validate_candidate(candidate, label="Explicit")
    if os.environ.get("SANDAI_WORKSPACE_ROOT"):
        candidates.append(Path(os.environ["SANDAI_WORKSPACE_ROOT"]).expanduser())

    for base in _candidate_source_roots(Path(source_root) if source_root else None):
        locator = base / "workspace-locator.private.json"
        if locator.is_file():
            try:
                locator_value = json.loads(locator.read_text(encoding="utf-8"))
                cache_value = locator_value["local_runtime_cache"]
            except (KeyError, json.JSONDecodeError) as exc:
                raise WorkspaceError(f"Invalid private workspace locator: {locator}") from exc
            cache_root = Path(cache_value).expanduser()
            if not cache_root.is_absolute():
                cache_root = (base / cache_root).resolve()
            current = cache_root / "current"
            candidates.append(current)
            break

    colab_root = Path("/content/drive/Shareddrives") / WORKSPACE_NAME
    if Path("/content/drive/Shareddrives").is_dir():
        candidates.append(colab_root)

    checked: list[str] = []
    for candidate in candidates:
        candidate = candidate.resolve()
        checked.append(str(candidate))
        contract = candidate / "config" / "data_contract.json"
        marker = candidate / WORKSPACE_MARKER
        if contract.is_file() and marker.is_file():
            return validate_candidate(candidate, label="Resolved")

    raise WorkspaceError(
        "Private SaNDAI Shared Drive workspace was not found. Set SANDAI_WORKSPACE_ROOT, "
        "run scripts/shared_drive_bridge.py pull locally, or mount Google Drive in Colab. "
        f"Checked: {checked or ['no configured candidates']}. A valid workspace also needs "
        f"{WORKSPACE_MARKER}."
    )


def load_workspace_config(workspace_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    contract_path = workspace_root / "config" / "data_contract.json"
    campaign_path = workspace_root / "config" / "campaign_config.json"
    if not contract_path.is_file() or not campaign_path.is_file():
        raise WorkspaceError("Required Drive configuration is missing; no fallback is allowed.")
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    config = json.loads(campaign_path.read_text(encoding="utf-8"))
    if contract.get("schema_version") != "sandai.shared-data-contract.v1":
        raise WorkspaceError("Unsupported shared-data contract schema version.")
    if contract.get("data_plane") != "private_google_shared_drive":
        raise WorkspaceError("SaNDAI operational data must come from the private Google Shared Drive.")
    if config.get("schema_version") != "sandai.campaign-config.v1":
        raise WorkspaceError("Unsupported campaign configuration schema version.")
    if config.get("data_classification") != "SYNTHETIC_DEMO_ONLY":
        raise WorkspaceError("Only SYNTHETIC_DEMO_ONLY data is authorized in this workspace.")
    return contract, config


def _required_path(workspace_root: Path, relative_path: str) -> Path:
    path = (workspace_root / relative_path).resolve()
    try:
        path.relative_to(workspace_root.resolve())
    except ValueError as exc:
        raise WorkspaceError(f"Data contract escapes the private workspace: {relative_path}") from exc
    if not path.is_file():
        raise WorkspaceError(f"Required shared-data file is missing: {path}")
    return path


def _validate_required_columns(frame: pd.DataFrame, required: tuple[str, ...], label: str) -> None:
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise WorkspaceError(f"{label} schema is missing columns: {missing}")


def load_campaign_data(workspace_root: Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    contract, _ = load_workspace_config(workspace_root)
    path = _required_path(workspace_root, contract["campaign_input"])
    frame = pd.read_csv(path)
    _validate_required_columns(frame, CAMPAIGN_REQUIRED_COLUMNS, "Campaign")
    frame = frame.loc[:, list(CAMPAIGN_REQUIRED_COLUMNS)].copy()
    frame["seminar_date"] = pd.to_datetime(frame["seminar_date"], errors="raise")
    for column in CAMPAIGN_INTEGER_COLUMNS:
        values = pd.to_numeric(frame[column], errors="raise")
        if not np.equal(values, np.floor(values)).all():
            raise WorkspaceError(f"Campaign column must contain integers: {column}")
        frame[column] = values.astype(int)
    if (frame[list(CAMPAIGN_INTEGER_COLUMNS)] < 0).any().any():
        raise WorkspaceError("Campaign counts cannot be negative.")
    if sorted(frame["week"].unique().tolist()) != list(range(1, 9)):
        raise WorkspaceError("Campaign data must contain exactly weeks 1 through 8.")
    funnel_order = (
        frame["reach"].ge(frame["interested"])
        & frame["interested"].ge(frame["registrations"])
        & frame["registrations"].ge(frame["confirmations"])
        & frame["confirmations"].ge(frame["attendees"])
        & frame["attendees"].ge(frame["opt_in_leads"])
        & frame["opt_in_leads"].ge(frame["qualified_followups"])
        & frame["qualified_followups"].ge(frame["approved_conversions"])
    )
    if not funnel_order.all():
        raise WorkspaceError("Campaign funnel order is invalid in one or more rows.")
    week_constants = frame.groupby("week")[["t3_registrations", "t3_confirmations", "intervention"]].nunique()
    if not week_constants.le(1).all().all():
        raise WorkspaceError("T-3 and intervention fields must be constant within each week.")
    metadata = {
        "schema_version": CAMPAIGN_SCHEMA_VERSION,
        "source_relative_path": contract["campaign_input"],
        "source_sha256": _sha256_file(path),
        "row_count": int(len(frame)),
        "data_classification": "SYNTHETIC_DEMO_ONLY",
    }
    return frame, metadata


def load_learner_data(workspace_root: Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    contract, _ = load_workspace_config(workspace_root)
    path = _required_path(workspace_root, contract["learner_input"])
    frame = pd.read_csv(path)
    _validate_required_columns(frame, LEARNER_REQUIRED_COLUMNS, "Learner")
    analysis = frame.loc[:, list(LEARNER_REQUIRED_COLUMNS)].copy()
    if analysis.empty:
        raise WorkspaceError("No synthetic student rows are available.")
    if not analysis["participant_id"].astype(str).str.startswith("SYN-").all():
        raise WorkspaceError("Every fictional student ID must start with SYN-.")
    if not analysis["participant_id"].is_unique:
        raise WorkspaceError("Learner participant IDs must be unique.")
    if not analysis["demo_student"].astype(str).str.startswith("Demo Student ").all():
        raise WorkspaceError("Every fictional profile label must start with 'Demo Student '.")
    if not analysis["demo_student"].is_unique:
        raise WorkspaceError("Fictional profile labels must be unique.")
    numeric = [
        "campaign_week", "checkpoints_completed", "checkpoint_total",
        "feedback_score", "last_activity_days_ago",
    ]
    analysis[numeric] = analysis[numeric].apply(pd.to_numeric, errors="coerce")
    analysis["seminar_attended"] = analysis["seminar_attended"].astype(str).str.lower().eq("true")
    analysis["feedback_submitted"] = analysis["feedback_submitted"].astype(str).str.lower().eq("true")
    analysis["follow_up_opt_in"] = analysis["follow_up_opt_in"].astype(str).str.lower().eq("true")
    if analysis["campaign_week"].dropna().lt(1).any() or analysis["campaign_week"].dropna().gt(8).any():
        raise WorkspaceError("Learner campaign_week must be between 1 and 8.")
    if analysis["checkpoint_total"].le(0).any():
        raise WorkspaceError("Learner checkpoint_total must be positive.")
    if not analysis["checkpoints_completed"].between(0, analysis["checkpoint_total"]).all():
        raise WorkspaceError("Learner checkpoint progress is outside valid bounds.")
    allowed_stages = {"undergraduate", "graduate", "career changer"}
    allowed_experience = {"beginner", "developing", "intermediate"}
    if not set(analysis["student_stage"]).issubset(allowed_stages):
        raise WorkspaceError("Fictional student_stage contains an unsupported value.")
    if not set(analysis["experience_level"]).issubset(allowed_experience):
        raise WorkspaceError("Fictional experience_level contains an unsupported value.")
    for column in ["career_goal", "preferred_learning_format"]:
        if analysis[column].isna().any() or analysis[column].astype(str).str.strip().eq("").any():
            raise WorkspaceError(f"Fictional learner profile is missing {column}.")
    metadata = {
        "schema_version": LEARNER_SCHEMA_VERSION,
        "source_relative_path": contract["learner_input"],
        "source_sha256": _sha256_file(path),
        "row_count": int(len(frame)),
        "fictional_student_count": int(len(analysis)),
        "data_classification": "SYNTHETIC_DEMO_ONLY",
    }
    return analysis, metadata


def build_learner_support_profiles(learners: pd.DataFrame) -> pd.DataFrame:
    """Turn fictional participation signals into an explainable next-action view.

    The function is intentionally simple enough to defend in the case interview:
    attendance, progress, recent activity, feedback, and an explicit help request
    determine the risk color and the recommended follow-up.
    """

    frame = learners.copy()
    _validate_required_columns(frame, LEARNER_REQUIRED_COLUMNS, "Learner")
    frame["checkpoint_rate"] = frame["checkpoints_completed"] / frame["checkpoint_total"]
    status_points = frame["session_status"].map(
        {"completed": 20, "accessed": 10, "not_started": 0}
    )
    if status_points.isna().any():
        raise WorkspaceError("Learner session_status must be completed, accessed, or not_started.")
    recency_points = np.select(
        [frame["last_activity_days_ago"].ge(7), frame["last_activity_days_ago"].ge(4)],
        [0, 4],
        default=10,
    )
    frame["engagement_score"] = (
        frame["checkpoint_rate"] * 50
        + status_points
        + frame["seminar_attended"].astype(int) * 15
        + frame["feedback_submitted"].astype(int) * 5
        + recency_points
    ).round().astype(int)

    red = (
        ~frame["seminar_attended"]
        | frame["session_status"].eq("not_started")
        | frame["checkpoint_rate"].lt(0.34)
        | frame["last_activity_days_ago"].ge(7)
    )
    yellow = (
        frame["checkpoint_rate"].lt(0.67)
        | frame["last_activity_days_ago"].ge(4)
        | frame["support_request"].ne("none")
        | (frame["feedback_submitted"] & frame["feedback_score"].le(2))
    )
    frame["risk_status"] = np.select([red, yellow], ["RED", "YELLOW"], default="GREEN")

    def recommend(row: pd.Series) -> str:
        if not row["seminar_attended"]:
            return "Invite to the next seminar and share the five-minute catch-up path."
        if row["session_status"] == "not_started":
            return "Send the Start Here link and one clear first step."
        if row["support_request"] == "navigation":
            return "Share the notebook navigation guide and the quickest route."
        if row["support_request"] == "pacing":
            return "Offer the 10-minute path and split the next checkpoint in two."
        if row["checkpoint_rate"] < 0.67 or row["last_activity_days_ago"] >= 4:
            return "Send one checkpoint reminder tied to the student's stated goal."
        if row["feedback_submitted"] and row["feedback_score"] <= 2:
            return "Ask one short follow-up question and revise the confusing step."
        return "Invite to the next practice activity and optional peer referral."

    frame["recommended_intervention"] = frame.apply(recommend, axis=1)
    frame["profile_summary"] = (
        frame["student_stage"]
        + " | "
        + frame["experience_level"]
        + " | goal: "
        + frame["career_goal"]
        + " | prefers: "
        + frame["preferred_learning_format"]
    )
    return frame


def build_weekly_metrics(campaign: pd.DataFrame, *, weekly_minimum: int, total_target: int) -> pd.DataFrame:
    weekly = (
        campaign.groupby(["week", "seminar_date"], as_index=False)
        .agg(
            reach=("reach", "sum"), interested=("interested", "sum"),
            registrations=("registrations", "sum"), confirmations=("confirmations", "sum"),
            attendees=("attendees", "sum"), opt_in_leads=("opt_in_leads", "sum"),
            qualified_followups=("qualified_followups", "sum"),
            approved_conversions=("approved_conversions", "sum"),
            outreach_effort_units=("outreach_effort_units", "sum"),
            t3_registrations=("t3_registrations", "first"),
            t3_confirmations=("t3_confirmations", "first"),
            intervention=("intervention", "first"),
            recovery_lift_attendees=("recovery_lift_attendees", "first"),
        )
        .sort_values("week")
        .reset_index(drop=True)
    )
    if weekly["registrations"].le(0).any():
        raise WorkspaceError("Show rate is undefined because at least one week has zero registrations.")
    weekly["show_rate"] = weekly["attendees"] / weekly["registrations"]
    weekly["confirmation_rate"] = weekly["confirmations"] / weekly["registrations"]
    weekly["weekly_goal_met"] = weekly["attendees"] >= weekly_minimum
    weekly["cumulative_attendance"] = weekly["attendees"].cumsum()
    weekly["cumulative_target"] = weekly["week"] * weekly_minimum
    weekly["remaining_to_target"] = (total_target - weekly["cumulative_attendance"]).clip(lower=0)
    return weekly


@dataclass(frozen=True)
class CampaignConfig:
    weekly_minimum: int = 20
    total_target: int = 160
    campaign_weeks: int = 8
    confidence_level: float = 0.80
    operational_buffer_ppts: float = 0.05
    unconfirmed_attend_rate: float = 0.15
    random_seed: int = 20260921

    def __post_init__(self) -> None:
        if self.weekly_minimum <= 0 or self.total_target <= 0 or self.campaign_weeks != 8:
            raise ValueError("Targets must be positive and campaign_weeks must equal 8.")
        if not 0.50 <= self.confidence_level < 1.0:
            raise ValueError("confidence_level must be in [0.50, 1.00).")
        if not 0 <= self.operational_buffer_ppts < 0.50:
            raise ValueError("operational_buffer_ppts must be in [0.00, 0.50).")
        if not 0 <= self.unconfirmed_attend_rate <= 1.0:
            raise ValueError("unconfirmed_attend_rate must be in [0.00, 1.00].")

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "CampaignConfig":
        return cls(
            weekly_minimum=int(value["weekly_attendance_target"]),
            total_target=int(value["total_attendance_target"]),
            campaign_weeks=int(value["campaign_weeks"]),
            confidence_level=float(value["confidence_level"]),
            operational_buffer_ppts=float(value["operational_buffer_ppts"]),
            unconfirmed_attend_rate=float(value["unconfirmed_attend_rate"]),
            random_seed=int(value["random_seed"]),
        )


class DecisionEngine:
    """History-to-forecast API. It recommends but never performs outreach."""

    def __init__(self, config: CampaignConfig, weekly_metrics: pd.DataFrame):
        self.config = config
        self.weekly_metrics = weekly_metrics.copy()

    def history_before(self, week_number: int) -> pd.DataFrame:
        return self.weekly_metrics.loc[self.weekly_metrics["week"] < week_number].copy()

    def registration_target(self, history: pd.DataFrame) -> dict[str, Any]:
        minimum = self.config.weekly_minimum
        registrations = int(history["registrations"].sum())
        attendees = int(history["attendees"].sum())
        if registrations:
            observed_rate = attendees / registrations
            alpha = 2 + attendees
            beta = 2 + registrations - attendees
            rng = np.random.default_rng(self.config.random_seed + 11)
            posterior_rates = rng.beta(alpha, beta, size=50_000)
            lower_quantile = float(np.quantile(posterior_rates, 1 - self.config.confidence_level))
            conservative_rate = max(0.40, lower_quantile - self.config.operational_buffer_ppts)
            posterior_mean = alpha / (alpha + beta)
        else:
            observed_rate = posterior_mean = lower_quantile = conservative_rate = 0.60
        registration_floor = math.ceil(minimum / conservative_rate)
        return {
            "observed_rate": observed_rate,
            "posterior_mean": posterior_mean,
            "lower_quantile": lower_quantile,
            "conservative_rate": conservative_rate,
            "basic_required": math.ceil(minimum / max(observed_rate, 0.05)),
            "registration_floor": registration_floor,
            "safety_target": math.ceil(registration_floor * 1.10),
        }

    def attendance_forecast(
        self,
        history: pd.DataFrame,
        registrations: int,
        confirmations: int,
        *,
        seed_offset: int = 0,
        required_controls_complete: bool = True,
    ) -> dict[str, Any]:
        minimum = self.config.weekly_minimum
        registrations = int(max(0, registrations))
        confirmations = int(min(max(0, confirmations), registrations))
        hist_confirmations = int(history["confirmations"].sum())
        hist_attendees = int(history["attendees"].sum())
        if hist_confirmations:
            alpha = 2 + hist_attendees
            beta = 2 + max(0, hist_confirmations - hist_attendees)
        else:
            alpha, beta = 6, 4
        rng = np.random.default_rng(self.config.random_seed + 101 + seed_offset)
        confirmed = rng.binomial(confirmations, rng.beta(alpha, beta, size=50_000))
        unconfirmed = rng.binomial(
            registrations - confirmations,
            self.config.unconfirmed_attend_rate,
            size=50_000,
        )
        draws = confirmed + unconfirmed
        expected = float(draws.mean())
        probability = float((draws >= minimum).mean())
        low, high = np.quantile(draws, [0.10, 0.90])
        if not required_controls_complete or expected < minimum:
            status = "RED"
        elif expected >= minimum + 2 and probability >= self.config.confidence_level:
            status = "GREEN"
        else:
            status = "YELLOW"
        return {
            "expected": expected,
            "probability": probability,
            "p10": int(low),
            "p90": int(high),
            "gap": max(0, minimum - round(expected)),
            "status": status,
            "registrations": registrations,
            "confirmations": confirmations,
        }


def _recommended_intervention(status: str, extra_registrations: int, extra_confirmations: int) -> str:
    if status == "GREEN":
        return "Maintain T-1 reminders; hold reserve partners without expanding volume."
    if status == "YELLOW":
        return f"Run a targeted confirmation sprint and add up to {extra_registrations} registrations."
    return (
        "Activate a secondary partner channel now and secure "
        f"{extra_registrations} registrations / {extra_confirmations} confirmations."
    )


def build_decision_snapshot(weekly: pd.DataFrame, config_value: dict[str, Any]) -> dict[str, Any]:
    config = CampaignConfig.from_mapping(config_value)
    current_week = int(config_value["current_week"])
    selected_rows = weekly.loc[weekly["week"] == current_week]
    if len(selected_rows) != 1:
        raise WorkspaceError(f"Expected one weekly row for current_week={current_week}.")
    selected = selected_rows.iloc[0]
    engine = DecisionEngine(config, weekly)
    history = engine.history_before(current_week)
    target = engine.registration_target(history)
    forecast = engine.attendance_forecast(
        history,
        int(selected["t3_registrations"]),
        int(selected["t3_confirmations"]),
        seed_offset=current_week,
    )
    recommendation = _recommended_intervention(
        forecast["status"],
        int(config_value["planned_extra_registrations"]),
        int(config_value["planned_extra_confirmations"]),
    )
    return {
        "week": current_week,
        "seminar_date": selected["seminar_date"].date().isoformat(),
        "weekly_attendance": int(selected["attendees"]),
        "cumulative_attendance": int(selected["cumulative_attendance"]),
        "show_rate": round(float(selected["show_rate"]), 12),
        "basic_required_registrations": int(target["basic_required"]),
        "confidence_floor_registrations": int(target["registration_floor"]),
        "safety_target_registrations": int(target["safety_target"]),
        "forecast_expected_attendance": round(float(forecast["expected"]), 12),
        "forecast_probability_at_least_20": round(float(forecast["probability"]), 12),
        "forecast_p10": int(forecast["p10"]),
        "forecast_p90": int(forecast["p90"]),
        "risk_status": forecast["status"],
        "source_intervention": str(selected["intervention"]),
        "recommended_intervention": recommendation,
    }


def build_parity_snapshot(workspace_root: Path, *, surface: str) -> dict[str, Any]:
    if surface not in {"local", "colab"}:
        raise WorkspaceError("surface must be 'local' or 'colab'.")
    contract, config_value = load_workspace_config(workspace_root)
    campaign, campaign_meta = load_campaign_data(workspace_root)
    _, learner_meta = load_learner_data(workspace_root)
    weekly = build_weekly_metrics(
        campaign,
        weekly_minimum=int(config_value["weekly_attendance_target"]),
        total_target=int(config_value["total_attendance_target"]),
    )
    decision = build_decision_snapshot(weekly, config_value)
    weekly_records = []
    for row in weekly.itertuples(index=False):
        weekly_records.append({
            "week": int(row.week),
            "seminar_date": row.seminar_date.date().isoformat(),
            "weekly_attendance": int(row.attendees),
            "cumulative_attendance": int(row.cumulative_attendance),
            "show_rate": round(float(row.show_rate), 12),
        })
    return {
        "schema_version": "sandai.parity-snapshot.v1",
        "surface": surface,
        "generated_at_utc": _utc_now(),
        "data_classification": config_value["data_classification"],
        "contract_schema_version": contract["schema_version"],
        "contract_source_sha256": _sha256_file(workspace_root / "config" / "data_contract.json"),
        "configuration_source_sha256": _sha256_file(workspace_root / "config" / "campaign_config.json"),
        "algorithm_source_sha256": _sha256_file(Path(__file__).resolve()),
        "runtime_versions": {"numpy": np.__version__, "pandas": pd.__version__},
        "campaign_source": campaign_meta,
        "learner_source": learner_meta,
        "weekly_metrics": weekly_records,
        "decision": decision,
        "external_action_performed": False,
    }


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def core_metrics_digest(snapshot: dict[str, Any]) -> str:
    """Hash only the fields that must be identical across execution surfaces."""
    core = {
        "campaign_source_sha256": snapshot["campaign_source"]["source_sha256"],
        "learner_source_sha256": snapshot["learner_source"]["source_sha256"],
        "contract_source_sha256": snapshot["contract_source_sha256"],
        "configuration_source_sha256": snapshot["configuration_source_sha256"],
        "algorithm_source_sha256": snapshot["algorithm_source_sha256"],
        "weekly_metrics": snapshot["weekly_metrics"],
        "decision": snapshot["decision"],
    }
    return sha256(json.dumps(core, sort_keys=True).encode("utf-8")).hexdigest()


def compare_parity_snapshots(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    """Compare the seven assignment-critical outputs and shared input hashes."""
    fields = {
        "weekly_attendance": (
            [row["weekly_attendance"] for row in left["weekly_metrics"]],
            [row["weekly_attendance"] for row in right["weekly_metrics"]],
        ),
        "cumulative_attendance": (
            [row["cumulative_attendance"] for row in left["weekly_metrics"]],
            [row["cumulative_attendance"] for row in right["weekly_metrics"]],
        ),
        "show_rate": (
            [row["show_rate"] for row in left["weekly_metrics"]],
            [row["show_rate"] for row in right["weekly_metrics"]],
        ),
        "required_registrations": (
            {
                key: left["decision"][key]
                for key in (
                    "basic_required_registrations",
                    "confidence_floor_registrations",
                    "safety_target_registrations",
                )
            },
            {
                key: right["decision"][key]
                for key in (
                    "basic_required_registrations",
                    "confidence_floor_registrations",
                    "safety_target_registrations",
                )
            },
        ),
        "attendance_forecast": (
            {
                key: left["decision"][key]
                for key in (
                    "forecast_expected_attendance",
                    "forecast_probability_at_least_20",
                    "forecast_p10",
                    "forecast_p90",
                )
            },
            {
                key: right["decision"][key]
                for key in (
                    "forecast_expected_attendance",
                    "forecast_probability_at_least_20",
                    "forecast_p10",
                    "forecast_p90",
                )
            },
        ),
        "risk_status": (left["decision"]["risk_status"], right["decision"]["risk_status"]),
        "recommended_intervention": (
            left["decision"]["recommended_intervention"],
            right["decision"]["recommended_intervention"],
        ),
    }
    mismatches = {
        name: {"left": values[0], "right": values[1]}
        for name, values in fields.items()
        if values[0] != values[1]
    }
    source_match = (
        left["campaign_source"]["source_sha256"] == right["campaign_source"]["source_sha256"]
        and left["learner_source"]["source_sha256"] == right["learner_source"]["source_sha256"]
    )
    configuration_match = (
        left["contract_source_sha256"] == right["contract_source_sha256"]
        and left["configuration_source_sha256"] == right["configuration_source_sha256"]
    )
    algorithm_match = left["algorithm_source_sha256"] == right["algorithm_source_sha256"]
    comparable = source_match and configuration_match and algorithm_match
    status = "PASS" if comparable and not mismatches else ("NOT_COMPARABLE" if not comparable else "FAIL")
    return {
        "schema_version": "sandai.cross-environment-parity.v1",
        "status": status,
        "match": status == "PASS",
        "same_input_data": source_match,
        "same_configuration": configuration_match,
        "same_algorithm": algorithm_match,
        "left_surface": left["surface"],
        "right_surface": right["surface"],
        "metrics_compared": list(fields),
        "mismatches": mismatches,
    }


def _write_csv_new(path: Path, frame: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise WorkspaceError(f"Refusing to overwrite a derived run artifact: {path}")
    frame.to_csv(path, index=False)


def write_management_outputs(workspace_root: Path, *, surface: str) -> dict[str, str]:
    contract, config_value = load_workspace_config(workspace_root)
    campaign, _ = load_campaign_data(workspace_root)
    learners, _ = load_learner_data(workspace_root)
    learner_profiles = build_learner_support_profiles(learners)
    weekly = build_weekly_metrics(
        campaign,
        weekly_minimum=int(config_value["weekly_attendance_target"]),
        total_target=int(config_value["total_attendance_target"]),
    )
    snapshot = build_parity_snapshot(workspace_root, surface=surface)
    slug = _timestamp_slug()

    weekly_path = workspace_root / "data" / "processed" / f"weekly_metrics.{surface}.{slug}.csv"
    channel_path = workspace_root / "data" / "management" / f"channel_metrics.{surface}.{slug}.csv"
    partner_path = workspace_root / "data" / "management" / f"partner_pipeline.{surface}.{slug}.csv"
    learner_path = workspace_root / "data" / "management" / f"student_support_queue.{surface}.{slug}.csv"
    decision_path = workspace_root / "outputs" / "management" / f"decision_snapshot.{surface}.{slug}.json"
    verification_path = workspace_root / "verification" / surface / f"verification.{slug}.json"

    channel = (
        campaign.groupby("channel", as_index=False)
        .agg(
            reach=("reach", "sum"), registrations=("registrations", "sum"),
            confirmations=("confirmations", "sum"), attendees=("attendees", "sum"),
            effort_units=("outreach_effort_units", "sum"),
        )
    )
    channel["show_rate"] = np.where(channel["registrations"] > 0, channel["attendees"] / channel["registrations"], np.nan)
    partner = (
        campaign.groupby(["partner_category", "contact_status"], as_index=False)
        .agg(
            reach=("reach", "sum"), registrations=("registrations", "sum"),
            confirmations=("confirmations", "sum"), attendees=("attendees", "sum"),
        )
    )

    _write_csv_new(weekly_path, weekly)
    _write_csv_new(channel_path, channel)
    _write_csv_new(partner_path, partner)
    _write_csv_new(
        learner_path,
        learner_profiles.loc[
            learner_profiles["risk_status"].isin(["RED", "YELLOW"]),
            [
                "demo_student", "participant_id", "campaign_week", "seminar_attended",
                "career_goal", "preferred_learning_format", "engagement_score",
                "risk_status", "support_request", "recommended_intervention",
            ],
        ],
    )
    _atomic_json(decision_path, snapshot["decision"])
    _atomic_json(verification_path, snapshot)

    latest_path = workspace_root / "verification" / surface / "latest.json"
    latest = {
        "schema_version": "sandai.verification-pointer.v1",
        "surface": surface,
        "generated_at_utc": snapshot["generated_at_utc"],
        "verification_file": str(verification_path.relative_to(workspace_root)),
        "campaign_sha256": snapshot["campaign_source"]["source_sha256"],
        "core_metrics_sha256": core_metrics_digest(snapshot),
    }
    _atomic_json(latest_path, latest)
    return {
        "weekly_metrics": str(weekly_path),
        "channel_metrics": str(channel_path),
        "partner_pipeline": str(partner_path),
        "student_support_queue": str(learner_path),
        "decision_snapshot": str(decision_path),
        "verification": str(verification_path),
        "latest_pointer": str(latest_path),
    }


def safe_copy_new(source: Path, destination: Path) -> str:
    """Copy only when missing or byte-identical; never silently overwrite."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if _sha256_file(source) == _sha256_file(destination):
            return "UNCHANGED"
        raise WorkspaceError(f"Drive candidate differs; refusing overwrite: {destination}")
    shutil.copy2(source, destination)
    return "CREATED"
