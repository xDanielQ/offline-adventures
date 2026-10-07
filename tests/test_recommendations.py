import pytest
from pydantic import ValidationError

from src.models import ActivityRecommendation, RecommendationResult


def recommendation(activity_id: str) -> ActivityRecommendation:
    return ActivityRecommendation(
        activity_id=activity_id,
        reason="This activity fits the available time and selected interests well.",
        personalized_twist=("Pause halfway through and record one detail you nearly missed."),
    )


def test_valid_recommendation_result_is_accepted() -> None:
    result = RecommendationResult(
        primary=recommendation("activity_001"),
        alternatives=[
            recommendation("activity_002"),
            recommendation("activity_003"),
        ],
    )
    assert result.primary.personalized_twist.startswith("Pause halfway")


def test_duplicate_recommendation_ids_are_rejected() -> None:
    with pytest.raises(ValidationError):
        RecommendationResult(
            primary=recommendation("activity_001"),
            alternatives=[
                recommendation("activity_001"),
                recommendation("activity_003"),
            ],
        )


def test_wrong_number_of_alternatives_is_rejected() -> None:
    with pytest.raises(ValidationError):
        RecommendationResult(
            primary=recommendation("activity_001"),
            alternatives=[recommendation("activity_002")],
        )


def test_short_personalized_twist_is_rejected() -> None:
    with pytest.raises(ValidationError):
        ActivityRecommendation(
            activity_id="activity_001",
            reason="This activity fits the available time and selected interests well.",
            personalized_twist="Too short.",
        )
