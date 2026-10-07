import pytest
from pydantic import ValidationError

from src.models import RecommendationResult


def test_valid_recommendation_result_is_accepted() -> None:
    result = RecommendationResult.model_validate(
        {
            "primary": {
                "activity_id": "activity_001",
                "reason": "It matches the available time and current weather.",
            },
            "alternatives": [
                {
                    "activity_id": "activity_002",
                    "reason": "It offers a lower-energy outdoor option.",
                },
                {
                    "activity_id": "activity_003",
                    "reason": "It provides a safe indoor bridge activity.",
                },
            ],
        }
    )

    assert result.primary.activity_id == "activity_001"
    assert len(result.alternatives) == 2


def test_duplicate_recommendation_ids_are_rejected() -> None:
    with pytest.raises(ValidationError):
        RecommendationResult.model_validate(
            {
                "primary": {
                    "activity_id": "activity_001",
                    "reason": "It matches the available time and current weather.",
                },
                "alternatives": [
                    {
                        "activity_id": "activity_001",
                        "reason": "This deliberately repeats the primary activity.",
                    },
                    {
                        "activity_id": "activity_003",
                        "reason": "It provides a safe indoor bridge activity.",
                    },
                ],
            }
        )


def test_wrong_number_of_alternatives_is_rejected() -> None:
    with pytest.raises(ValidationError):
        RecommendationResult.model_validate(
            {
                "primary": {
                    "activity_id": "activity_001",
                    "reason": "It matches the available time and current weather.",
                },
                "alternatives": [
                    {
                        "activity_id": "activity_002",
                        "reason": "Only one alternative is deliberately supplied.",
                    }
                ],
            }
        )
