"""Build the public demo's view payload from the unchanged notebook models."""
import json
from pathlib import Path
from sandai_artifacts.management import CampaignMonitor
from sandai_artifacts.core import build_decision_snapshot

ROOT = Path(__file__).resolve().parents[1]

def payload():
    monitor = CampaignMonitor.from_workspace(ROOT)
    records = lambda frame: json.loads(frame.to_json(orient="records", date_format="iso"))
    return {
        "mode": "Sample data • illustrative eight-week campaign",
        "targets": {
            "weekly": int(monitor.settings["weekly_attendance_target"]),
            "campaign": int(monitor.settings["total_attendance_target"]),
            "weeks": int(monitor.settings["campaign_weeks"]),
        },
        "weekly": records(monitor.weekly),
        "decision": monitor.decision,
        "weekly_decisions": [
            build_decision_snapshot(monitor.weekly, {**monitor.settings, "current_week": int(week)})
            for week in monitor.weekly["week"]
        ],
        "recovery": records(monitor.recovery_scenario()),
        "channels": records(monitor.channel_summary()),
        "funnel": records(monitor.conversion_funnel()),
        "cadence": records(monitor.operating_cadence()),
    }

if __name__ == "__main__":
    destination = ROOT / "web/src/campaign.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload(), indent=2) + "\n")
    print(destination)
