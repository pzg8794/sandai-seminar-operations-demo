"""Student-facing learning experience used by the SaNDAI assignment demo."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


READINESS_PROMPTS = {
    "strength_story": "Explain one strength with a specific example",
    "role_direction": "Name a role or problem area to explore",
    "portfolio_evidence": "Show one small project or artifact",
    "verification": "Check AI/data outputs before accepting them",
    "learning_plan": "Name one skill and a realistic practice block",
    "ask_for_help": "Ask a specific question when blocked",
}

ACTION_LIBRARY = {
    "strength_story": (15, "Draft a three-sentence strength story with one example."),
    "role_direction": (15, "Choose one role family and write two questions about it."),
    "portfolio_evidence": (25, "Turn one small artifact into a one-paragraph portfolio note."),
    "verification": (20, "Check one AI/data claim against two sources and record differences."),
    "learning_plan": (20, "Schedule one practice block with a clear finish signal."),
    "ask_for_help": (10, "Draft one help question: context, attempt, blocker, request."),
}


@dataclass(frozen=True)
class StudentLearningProfile:
    demo_student: str
    interests: tuple[str, ...]
    career_direction: str
    seminar_goal: str
    weekly_minutes: int
    preferred_format: str


class StudentSeminarExperience:
    """A complete seminar path: reflect, practice, create evidence, plan."""

    def __init__(self, profile: StudentLearningProfile, self_check: dict[str, int]):
        self.profile = profile
        self.self_check = dict(self_check)
        invalid = {key: value for key, value in self.self_check.items() if value not in {0, 1, 2}}
        missing = set(READINESS_PROMPTS).difference(self.self_check)
        if invalid or missing:
            raise ValueError(f"Invalid self-check values={invalid}; missing={sorted(missing)}")

    @classmethod
    def demo(cls) -> "StudentSeminarExperience":
        return cls(
            StudentLearningProfile(
                demo_student="Demo Student Avery Example (fictional)",
                interests=("community technology", "visual storytelling"),
                career_direction="entry-level data or AI-support role",
                seminar_goal="leave with one portfolio-sized next step",
                weekly_minutes=45,
                preferred_format="worked example plus checklist",
            ),
            {
                "strength_story": 1,
                "role_direction": 1,
                "portfolio_evidence": 0,
                "verification": 2,
                "learning_plan": 1,
                "ask_for_help": 1,
            },
        )

    def profile_table(self) -> pd.DataFrame:
        return pd.DataFrame(
            [
                ("Fictional student", self.profile.demo_student),
                ("Interests", ", ".join(self.profile.interests)),
                ("Career direction", self.profile.career_direction),
                ("Seminar goal", self.profile.seminar_goal),
                ("Time available", f"{self.profile.weekly_minutes} minutes"),
                ("Preferred format", self.profile.preferred_format),
            ],
            columns=["Student input", "Demo value"],
        )

    def readiness_table(self) -> pd.DataFrame:
        meaning = {0: "start small", 1: "practice next", 2: "evidence ready"}
        return pd.DataFrame(
            [
                {
                    "Skill statement": prompt,
                    "Score": self.self_check[key],
                    "Meaning": meaning[self.self_check[key]],
                }
                for key, prompt in READINESS_PROMPTS.items()
            ]
        )

    def focus_keys(self, maximum: int = 2) -> list[str]:
        order = list(READINESS_PROMPTS)
        return sorted(order, key=lambda key: (self.self_check[key], order.index(key)))[:maximum]

    def practice_prompt(self) -> str:
        return (
            "Act as a brainstorming partner. Use only this fictional summary: a campus bicycle-repair "
            "club received 120 synthetic responses; common barriers were schedule conflicts, unclear "
            "skill level, and uncertainty about provided tools. Suggest three small attendance "
            "experiments in a table with idea, reason, evidence needed, and downside. Label assumptions."
        )

    def simulated_ai_response(self) -> pd.DataFrame:
        return pd.DataFrame(
            [
                ("Offer two shorter time slots", "Test schedule conflict", "Compare sign-ups and attendance", "Needs more facilitators"),
                ("Label beginner/returning paths", "Clarify expected level", "Ask one clarity question", "Avoid rigid labels"),
                ("Publish a tools-provided checklist", "Reduce uncertainty", "Track tool-related questions", "Keep it current"),
            ],
            columns=["Idea", "Why it may help", "Evidence to collect", "Tradeoff"],
        )

    def evidence_inventory(self) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "Item": "Intro to Python — fictional practice course",
                    "Status": "complete (demo)",
                    "Evidence": "two small notebooks using synthetic data",
                },
                {
                    "Item": "Bicycle-workshop prompt exercise",
                    "Status": "draft (demo)",
                    "Evidence": "prompt, response table, and verification notes",
                },
            ]
        )

    def resume_bullet(self) -> str:
        return (
            "Designed a structured prompt-practice activity for a fictional community workshop, "
            "producing three testable attendance ideas with evidence needs and tradeoffs."
        )

    def weekly_plan(self) -> pd.DataFrame:
        remaining = self.profile.weekly_minutes
        rows: list[dict[str, object]] = []
        for key in self.focus_keys():
            minutes, action = ACTION_LIBRARY[key]
            if minutes <= remaining:
                rows.append({"Focus": READINESS_PROMPTS[key], "Minutes": minutes, "Action": action})
                remaining -= minutes
        if not rows:
            key = self.focus_keys(1)[0]
            minutes, action = ACTION_LIBRARY[key]
            rows.append({"Focus": READINESS_PROMPTS[key], "Minutes": min(minutes, remaining), "Action": action})
        return pd.DataFrame(rows)

    def outcome_card(self) -> pd.DataFrame:
        plan = self.weekly_plan()
        return pd.DataFrame(
            [
                ("Starting point", "No portfolio evidence yet; career direction is emerging"),
                ("Seminar practice", "Structured AI prompt + evidence and tradeoff review"),
                ("Artifact created", "Prompt exercise, simulated response, and résumé-bullet draft"),
                ("Next step", str(plan.iloc[0]["Action"])),
                ("Time commitment", f"{int(plan['Minutes'].sum())} minutes this week"),
                ("Result", "One concrete, reviewable career-readiness step"),
            ],
            columns=["Before → after", "Demo result"],
        )

    def validate(self) -> dict[str, bool]:
        plan = self.weekly_plan()
        return {
            "fictional profile is explicit": "fictional" in self.profile.demo_student.lower(),
            "readiness scores are bounded": all(value in {0, 1, 2} for value in self.self_check.values()),
            "practice prompt is usable": len(self.practice_prompt()) > 100,
            "student receives a tangible artifact": bool(self.resume_bullet()),
            "weekly plan fits time budget": int(plan["Minutes"].sum()) <= self.profile.weekly_minutes,
        }
