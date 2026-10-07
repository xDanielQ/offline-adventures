import json
from pathlib import Path

from src.models import Activity

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = PROJECT_ROOT / "data" / "experiments" / "llama-outdoor-batch-01.json"
OUTPUT_PATH = PROJECT_ROOT / "data" / "activities.json"


METADATA = {
    "activity_001": {
        "name": "Nature sound walk",
        "activity_types": ["walking", "nature", "relaxation"],
        "location_types": ["neighborhood", "park", "forest_path"],
        "group_types": ["solo", "couple", "family", "friends"],
    },
    "activity_002": {
        "name": "Public art discovery walk",
        "activity_types": ["walking", "culture", "creative"],
        "location_types": [
            "neighborhood",
            "public_square",
            "public_building",
        ],
        "group_types": ["solo", "couple", "family", "friends"],
    },
    "activity_003": {
        "name": "Wildflower color hunt",
        "activity_types": ["nature", "photography", "creative"],
        "location_types": ["park", "garden", "forest_path"],
        "group_types": ["solo", "couple", "family", "friends"],
    },
    "activity_004": {
        "name": "Casual bird watching",
        "activity_types": ["nature", "relaxation"],
        "location_types": [
            "neighborhood",
            "park",
            "garden",
            "forest_path",
        ],
        "group_types": ["solo", "couple", "family", "friends"],
    },
    "activity_005": {
        "name": "Local history detail walk",
        "activity_types": ["walking", "culture", "photography"],
        "location_types": [
            "neighborhood",
            "public_square",
            "public_building",
        ],
        "group_types": ["solo", "couple", "family", "friends"],
    },
    "activity_006": {
        "name": "Seasonal market visit",
        "activity_types": ["social", "relaxation", "culture"],
        "location_types": ["market"],
        "group_types": ["solo", "couple", "family", "friends"],
    },
    "activity_007": {
        "name": "Public art observation",
        "activity_types": ["culture", "creative", "walking"],
        "location_types": [
            "neighborhood",
            "public_square",
            "public_building",
        ],
        "group_types": ["solo", "couple", "family", "friends"],
    },
    "activity_008": {
        "name": "Community garden visit",
        "activity_types": ["nature", "gardening", "relaxation"],
        "location_types": ["garden", "park"],
        "group_types": ["solo", "couple", "family", "friends"],
    },
    "activity_009": {
        "name": "Street texture photography",
        "activity_types": ["photography", "creative", "walking"],
        "location_types": [
            "neighborhood",
            "public_square",
            "public_building",
        ],
        "group_types": ["solo", "couple", "friends"],
    },
    "activity_010": {
        "name": "Local memory mapping walk",
        "activity_types": ["walking", "creative", "culture"],
        "location_types": [
            "neighborhood",
            "park",
            "public_square",
        ],
        "group_types": ["solo", "couple", "family", "friends"],
    },
}


def main() -> None:
    raw_activities = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))

    validated_activities = []

    for item in raw_activities:
        metadata = METADATA[item["id"]]

        item.update(metadata)

        activity = Activity.model_validate(item)
        validated_activities.append(activity.model_dump(mode="json"))

    OUTPUT_PATH.write_text(
        json.dumps(
            validated_activities,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"Created {len(validated_activities)} starter activities in {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
