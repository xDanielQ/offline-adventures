import json
from pathlib import Path

from src.filters import filter_and_rank
from src.models import Activity, ActivityRequest

CATALOG_PATH = Path("data/activities.json")


def load_activities() -> list[Activity]:
    raw_data = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    return [Activity.model_validate(item) for item in raw_data]


def make_request(**overrides) -> ActivityRequest:
    values = {
        "available_minutes": 60,
        "energy_level": "low",
        "weather": "dry",
        "location_types": [
            "neighborhood",
            "park",
            "garden",
            "public_square",
            "public_building",
            "market",
        ],
        "group_type": "solo",
        "interests": ["nature", "walking", "photography"],
        "excluded_activity_ids": set(),
    }
    values.update(overrides)
    return ActivityRequest.model_validate(values)


def test_filter_returns_only_eligible_activities() -> None:
    request = make_request()
    results = filter_and_rank(load_activities(), request)
    assert results
    for activity in results:
        assert activity.minimum_minutes <= request.available_minutes
        assert request.energy_level in activity.energy_levels
        assert request.weather in activity.weather


def test_filter_excludes_recent_activity() -> None:
    results = filter_and_rank(
        load_activities(), make_request(excluded_activity_ids={"activity_001"})
    )
    assert "activity_001" not in {item.id for item in results}


def test_filter_respects_available_time() -> None:
    results = filter_and_rank(load_activities(), make_request(available_minutes=20))
    assert all(item.minimum_minutes <= 20 for item in results)


def test_filter_respects_location_access() -> None:
    results = filter_and_rank(
        load_activities(), make_request(location_types=["market"], interests=["food", "social"])
    )
    assert results
    assert all("market" in {location.value for location in item.location_types} for item in results)


def test_filter_respects_group_type() -> None:
    results = filter_and_rank(load_activities(), make_request(group_type="family"))
    assert results
    assert all(
        any(group.value in {"family", "any"} for group in item.group_types) for item in results
    )


def test_filter_prefers_matching_interests() -> None:
    results = filter_and_rank(load_activities(), make_request(interests=["photography"]))
    assert results
    assert "photography" in results[0].interests


def test_filter_applies_limit() -> None:
    results = filter_and_rank(load_activities(), make_request(), limit=3)
    assert len(results) <= 3
