import json
from pathlib import Path

from src.filters import filter_and_rank
from src.models import Activity, ActivityRequest
from src.ollama_client import recommend_activities


def main() -> None:
    raw_data = json.loads(Path("data/activities.json").read_text(encoding="utf-8"))

    activities = [Activity.model_validate(item) for item in raw_data]

    request = ActivityRequest.model_validate(
        {
            "available_minutes": 60,
            "energy_level": "low",
            "weather": "dry",
            "location_types": ["neighborhood", "park", "garden", "public_square"],
            "group_type": "solo",
            "interests": ["photography", "nature"],
        }
    )

    candidates = filter_and_rank(activities, request, limit=15)

    if len(candidates) < 3:
        raise RuntimeError("Fewer than three eligible activities")

    result = recommend_activities(request, candidates)

    candidates_by_id = {activity.id: activity for activity in candidates}

    primary = candidates_by_id[result.primary.activity_id]

    print("source: local_ai")
    print(f"primary: {primary.name} | {result.primary.reason}")

    for alternative in result.alternatives:
        activity = candidates_by_id[alternative.activity_id]
        print(f"alternative: {activity.name} | {alternative.reason}")


if __name__ == "__main__":
    main()
