import json
from typing import Any

import httpx

from src.models import Activity, ActivityRequest, RecommendationResult
from src.settings import (
    OLLAMA_BASE_URL,
    OLLAMA_CONTEXT_LENGTH,
    OLLAMA_MAX_OUTPUT_TOKENS,
    OLLAMA_MODEL,
    OLLAMA_TIMEOUT_SECONDS,
)


class OllamaError(RuntimeError):
    """Raised when Ollama cannot return a valid recommendation."""


def _activity_payload(activity: Activity) -> dict[str, Any]:
    return {
        "id": activity.id,
        "name": activity.name,
        "environment": activity.environment.value,
        "minimum_minutes": activity.minimum_minutes,
        "maximum_minutes": activity.maximum_minutes,
        "energy_levels": [level.value for level in activity.energy_levels],
        "weather": [condition.value for condition in activity.weather],
        "interests": activity.interests,
        "safety_notes": activity.safety_notes,
    }


def recommend_activities(
    request: ActivityRequest,
    candidates: list[Activity],
) -> RecommendationResult:
    if len(candidates) < 3:
        raise ValueError("at least three candidates are required")

    candidate_ids = {activity.id for activity in candidates}

    user_payload = {
        "task": (
            "Select exactly one primary activity and exactly two alternatives. "
            "Use only activity IDs from candidates."
        ),
        "reason_rules": [
            "Write one natural English sentence for every reason.",
            "Use between 12 and 30 words.",
            "Explain a real match with the request.",
            "Mention the activity or its relevant benefit.",
            "Do not list JSON keys or field names.",
            "Do not return comma-separated request properties.",
            "Do not invent places, weather, equipment, or safety claims.",
        ],
        "request": request.model_dump(mode="json"),
        "candidates": [_activity_payload(activity) for activity in candidates],
        "response_schema": (RecommendationResult.model_json_schema()),
    }

    body = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "format": RecommendationResult.model_json_schema(),
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are the local recommendation engine for Offline Adventures. "
                    "Rank only the supplied candidate activities. "
                    "Return one primary activity and exactly two alternatives. "
                    "Every activity ID must come from candidates. "
                    "For every reason, write one natural English sentence of "
                    "12 to 30 words. Explain why that specific activity fits the "
                    "user's request. Never list JSON field names. "
                    "Do not invent activities, places, weather, equipment, "
                    "distances, health advice, or safety claims. "
                    "Return only JSON matching the supplied schema."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(user_payload),
            },
        ],
        "options": {
            "num_ctx": OLLAMA_CONTEXT_LENGTH,
            "num_predict": OLLAMA_MAX_OUTPUT_TOKENS,
            "temperature": 0,
        },
    }

    try:
        response = httpx.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json=body,
            timeout=OLLAMA_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise OllamaError("Ollama request failed") from exc

    try:
        content = response.json()["message"]["content"]
        result = RecommendationResult.model_validate_json(content)
    except (KeyError, TypeError, ValueError) as exc:
        raise OllamaError("Ollama returned an invalid response") from exc

    returned_ids = {
        result.primary.activity_id,
        *(item.activity_id for item in result.alternatives),
    }

    if not returned_ids.issubset(candidate_ids):
        raise OllamaError("Ollama returned an activity outside the candidate list")

    return result
