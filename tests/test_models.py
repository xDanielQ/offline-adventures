import pytest
from pydantic import ValidationError

from src.models import Activity


def valid_activity() -> dict:
    return {
        "id": "activity_001",
        "name": "Seasonal color walk",
        "environment": "outdoor",
        "minimum_minutes": 20,
        "maximum_minutes": 45,
        "energy_levels": ["low", "medium"],
        "weather": ["dry", "light_rain"],
        "interests": ["nature", "photography"],
        "requires_equipment": ["phone_or_camera"],
        "mission_steps": [
            "Find five seasonal colors.",
            "Photograph one example of each.",
        ],
        "safety_notes": [
            "Stay on public paths.",
        ],
        "memory_prompts": [
            "Which color was hardest to find?",
        ],
    }


def test_valid_activity_is_accepted() -> None:
    activity = Activity.model_validate(valid_activity())

    assert activity.id == "activity_001"
    assert activity.minimum_minutes == 20


def test_invalid_identifier_is_rejected() -> None:
    data = valid_activity()
    data["id"] = "walk-one"

    with pytest.raises(ValidationError):
        Activity.model_validate(data)


def test_invalid_duration_range_is_rejected() -> None:
    data = valid_activity()
    data["minimum_minutes"] = 60
    data["maximum_minutes"] = 20

    with pytest.raises(ValidationError):
        Activity.model_validate(data)
