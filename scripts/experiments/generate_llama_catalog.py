import argparse
import json
from pathlib import Path

import httpx

from src.models import ActivityCatalog
from src.settings import (
    OLLAMA_BASE_URL,
    OLLAMA_CONTEXT_LENGTH,
    OLLAMA_MODEL,
    OLLAMA_TIMEOUT_SECONDS,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a validated activity catalog with Ollama."
    )
    parser.add_argument(
        "--prompt",
        type=Path,
        required=True,
        help="Path to the prompt file, relative to the project root.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Path to the output JSON file, relative to the project root.",
    )
    parser.add_argument(
        "--expected-count",
        type=int,
        required=True,
        help="Exact number of activities expected from the model.",
    )
    parser.add_argument(
        "--expected-environment",
        choices=[
            "outdoor",
            "sheltered",
            "indoor_bridge",
        ],
        required=True,
        help="Environment required for every generated activity.",
    )
    return parser.parse_args()


def resolve_project_path(path: Path) -> Path:
    if path.is_absolute():
        return path

    return PROJECT_ROOT / path


def main() -> None:
    args = parse_args()

    prompt_path = resolve_project_path(args.prompt)
    output_path = resolve_project_path(args.output)

    prompt = prompt_path.read_text(encoding="utf-8")
    schema = ActivityCatalog.model_json_schema()

    body = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "format": schema,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Return only machine-readable JSON matching the schema. "
                    "Do not include Markdown, comments, or explanations."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "options": {
            "num_ctx": OLLAMA_CONTEXT_LENGTH,
            "num_predict": 10000,
            "temperature": 0.2,
        },
    }

    response = httpx.post(
        f"{OLLAMA_BASE_URL}/api/chat",
        json=body,
        timeout=max(OLLAMA_TIMEOUT_SECONDS, 300.0),
    )

    if response.is_error:
        print(f"Ollama returned HTTP {response.status_code}")
        print(response.text)
        raise SystemExit(1)

    try:
        content = response.json()["message"]["content"]
        catalog = ActivityCatalog.model_validate_json(content)
    except (KeyError, TypeError, ValueError) as exc:
        print("Ollama returned an invalid catalog response.")
        print(response.text)
        raise SystemExit(1) from exc

    activities = catalog.activities

    if len(activities) != args.expected_count:
        raise ValueError(f"Expected {args.expected_count} activities, received {len(activities)}")

    invalid_environments = [
        activity.id
        for activity in activities
        if activity.environment.value != args.expected_environment
    ]

    if invalid_environments:
        raise ValueError(
            "Activities with an unexpected environment: " + ", ".join(invalid_environments)
        )

    identifiers = [activity.id for activity in activities]
    normalized_names = [activity.name.casefold().strip() for activity in activities]

    if len(identifiers) != len(set(identifiers)):
        raise ValueError("Duplicate activity IDs were generated")

    if len(normalized_names) != len(set(normalized_names)):
        raise ValueError("Duplicate activity names were generated")

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    output_path.write_text(
        json.dumps(
            [activity.model_dump(mode="json") for activity in activities],
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"Saved {len(activities)} {args.expected_environment} activities to {output_path}")


if __name__ == "__main__":
    main()
