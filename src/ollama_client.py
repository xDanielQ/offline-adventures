import json

import httpx

from src.models import Activity, ActivityRequest, RecommendationResult
from src.settings import (
    OLLAMA_BASE_URL,
    OLLAMA_CONTEXT_LENGTH,
    OLLAMA_MODEL,
    OLLAMA_TIMEOUT_SECONDS,
)


class OllamaError(RuntimeError):
    """Raised when Ollama cannot return a valid recommendation."""


def _activity_payload(activity: Activity) -> dict:
    return activity.model_dump(mode="json")


def recommend_activities(
    request: ActivityRequest,
    candidates: list[Activity],
) -> RecommendationResult:
    if len(candidates) < 3:
        raise ValueError("At least three candidates are required")

    candidate_ids = {activity.id for activity in candidates}
    schema = RecommendationResult.model_json_schema()
    user_payload = {
        "task": (
            "Select exactly one primary activity and exactly two alternatives. "
            "Use only activity IDs from candidates."
        ),
        "reason_rules": [
            "Write one natural English sentence for every reason.",
            "Use between 12 and 30 words for every reason.",
            "Explain a real match with the request.",
            "Do not list JSON keys or field names.",
        ],
        "twist_rules": [
            "Write one personalized_twist sentence for every recommendation.",
            "Use between 8 and 30 words for every personalized_twist.",
            "Make each twist concrete, playful, and relevant to the user's interests.",
            "Keep the candidate's core activity, place, weather, time, and equipment.",
            "Do not add purchases, health advice, risky behavior, or exact locations.",
            "Never suggest bringing or using a laptop or computer.",
            "Only mention equipment already listed in the candidate.",
            "Keep screen use brief and directly connected with completing the activity.",
        ],
        "request": request.model_dump(mode="json"),
        "candidates": [_activity_payload(activity) for activity in candidates],
        "response_schema": schema,
    }
    body = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "format": schema,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are the local recommendation engine for Offline Adventures. "
                    "Rank only supplied candidates and return one primary activity and "
                    "exactly two alternatives. Every ID must come from candidates. "
                    "Write natural reasons of 12 to 30 words. For every recommendation, "
                    "create one personalized_twist: a small concrete variation of the "
                    "approved activity, not a new activity. Respect its place, weather, "
                    "time, equipment, and safety boundaries. Do not invent places, "
                    "equipment, distances, health advice, or safety claims. Return only "
                    "JSON matching the supplied schema."
                    "Never suggest bringing or using a laptop or computer. "
                    "Only use equipment already declared by the candidate. "
                    "Keep any phone or camera use brief and directly related to the mission. "
                ),
            },
            {"role": "user", "content": json.dumps(user_payload)},
        ],
        "options": {
            "num_ctx": OLLAMA_CONTEXT_LENGTH,
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
        content = response.json()["message"]["content"]
        result = RecommendationResult.model_validate_json(content)
    except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
        raise OllamaError(f"Ollama recommendation failed: {exc}") from exc

    selected_ids = {
        result.primary.activity_id,
        *(item.activity_id for item in result.alternatives),
    }
    unknown_ids = selected_ids - candidate_ids
    if unknown_ids:
        raise OllamaError(
            "Ollama returned IDs outside the candidate set: " + ", ".join(sorted(unknown_ids))
        )
    return result
