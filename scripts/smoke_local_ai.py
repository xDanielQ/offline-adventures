import json
from pathlib import Path

from src.filters import filter_and_rank
from src.models import Activity, ActivityRequest
from src.ollama_client import recommend_activities


def main() -> None:
    raw = json.loads(Path("data/activities.json").read_text(encoding="utf-8"))
    activities = [Activity.model_validate(item) for item in raw]
    request = ActivityRequest.model_validate(
        {
            "available_minutes": 60,
            "energy_level": "low",
            "weather": "dry",
            "location_types": [
                "neighborhood",
                "park",
                "garden",
                "public_square",
            ],
            "group_type": "solo",
            "interests": ["photography", "nature"],
        }
    )
    candidates = filter_and_rank(activities, request, limit=15)
    result = recommend_activities(request, candidates)
    by_id = {activity.id: activity for activity in candidates}

    print(f"primary: {by_id[result.primary.activity_id].name} | {result.primary.reason}")
    print(f"primary twist: {result.primary.personalized_twist}")
    for item in result.alternatives:
        print(f"alternative: {by_id[item.activity_id].name} | {item.reason}")
        print(f"alternative twist: {item.personalized_twist}")


if __name__ == "__main__":
    main()
