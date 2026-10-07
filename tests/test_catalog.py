import json
from pathlib import Path

from src.models import Activity

CATALOG_PATH = Path("data/activities.json")


def load_activities():
    raw_data = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))

    return [Activity.model_validate(item) for item in raw_data]


def test_catalog_contains_fifty_activities() -> None:
    activities = load_activities()

    assert len(activities) == 50


def test_catalog_identifiers_are_unique() -> None:
    activities = load_activities()
    identifiers = [activity.id for activity in activities]

    assert len(identifiers) == len(set(identifiers))


def test_catalog_names_are_unique() -> None:
    activities = load_activities()
    names = [activity.name.casefold().strip() for activity in activities]

    assert len(names) == len(set(names))


def test_catalog_has_expected_environment_distribution() -> None:
    activities = load_activities()

    counts = {
        environment: sum(activity.environment.value == environment for activity in activities)
        for environment in (
            "outdoor",
            "sheltered",
            "indoor_bridge",
        )
    }

    assert counts == {
        "outdoor": 30,
        "sheltered": 8,
        "indoor_bridge": 12,
    }


def test_activity_007_is_park_picnic() -> None:
    activities = load_activities()
    activity = next(item for item in activities if item.id == "activity_007")

    assert activity.name == "Park picnic mission"
    assert "picnic_items" in activity.requires_equipment
