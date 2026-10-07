from src.models import (
    Activity,
    ActivityRequest,
    Environment,
    GroupType,
    LocationType,
)

UNSUITABLE_OUTDOOR_WEATHER = {"heavy_rain", "strong_wind", "very_hot", "very_cold"}


def _matches_location(activity: Activity, request: ActivityRequest) -> bool:
    requested = set(request.location_types)
    available = set(activity.location_types)
    return (
        LocationType.ANY in requested
        or LocationType.ANY in available
        or bool(requested & available)
    )


def _matches_group(activity: Activity, request: ActivityRequest) -> bool:
    return (
        request.group_type == GroupType.ANY
        or GroupType.ANY in activity.group_types
        or request.group_type in activity.group_types
    )


def is_eligible(activity: Activity, request: ActivityRequest) -> bool:
    return all(
        (
            activity.id not in request.excluded_activity_ids,
            activity.minimum_minutes <= request.available_minutes,
            request.energy_level in activity.energy_levels,
            request.weather in activity.weather,
            _matches_location(activity, request),
            _matches_group(activity, request),
        )
    )


def _interest_score(activity: Activity, request: ActivityRequest) -> int:
    requested = {
        item.casefold()
        for item in request.interests
    }
    activity_tags = {
        item.casefold()
        for item in activity.interests
    }
    activity_tags.update(
        item.value.casefold()
        for item in activity.activity_types
    )

    return len(requested & activity_tags)


def _environment_priority(activity: Activity, request: ActivityRequest) -> int:
    unsuitable = request.weather.value in UNSUITABLE_OUTDOOR_WEATHER
    if unsuitable:
        order = {Environment.SHELTERED: 0, Environment.INDOOR_BRIDGE: 1, Environment.OUTDOOR: 2}
    else:
        order = {Environment.OUTDOOR: 0, Environment.SHELTERED: 1, Environment.INDOOR_BRIDGE: 2}
    return order[activity.environment]


def filter_and_rank(
    activities: list[Activity], request: ActivityRequest, limit: int = 15
) -> list[Activity]:
    eligible = [activity for activity in activities if is_eligible(activity, request)]
    return sorted(
        eligible,
        key=lambda activity: (
            _environment_priority(activity, request),
            -_interest_score(activity, request),
            activity.minimum_minutes,
            activity.name.casefold(),
        ),
    )[:limit]
