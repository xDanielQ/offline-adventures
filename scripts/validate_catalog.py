import argparse
import json
from collections import Counter
from pathlib import Path

from src.models import Activity, Environment


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate an Offline Adventures activity catalog.")
    parser.add_argument(
        "catalog",
        type=Path,
        help="Path to the catalog JSON file.",
    )
    parser.add_argument(
        "--expected-count",
        type=int,
        default=None,
        help="Optional exact number of expected records.",
    )
    parser.add_argument(
        "--outdoor",
        type=int,
        default=None,
        help="Optional expected number of outdoor records.",
    )
    parser.add_argument(
        "--sheltered",
        type=int,
        default=None,
        help="Optional expected number of sheltered records.",
    )
    parser.add_argument(
        "--indoor-bridge",
        type=int,
        default=None,
        help="Optional expected number of indoor bridge records.",
    )
    return parser.parse_args()


def load_catalog(path: Path):
    raw_data = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(raw_data, list):
        raise ValueError("Catalog root must be a JSON array")

    return [Activity.model_validate(item) for item in raw_data]


def validate_catalog(
    path: Path,
    expected_count: int | None = None,
    expected_environments: dict[Environment, int] | None = None,
) -> None:
    activities = load_catalog(path)

    identifiers = [activity.id for activity in activities]
    normalized_names = [activity.name.casefold().strip() for activity in activities]
    environment_counts = Counter(activity.environment for activity in activities)

    errors: list[str] = []

    if expected_count is not None and len(activities) != expected_count:
        errors.append(f"Expected {expected_count} activities, found {len(activities)}")

    if len(identifiers) != len(set(identifiers)):
        errors.append("Duplicate activity IDs found")

    if len(normalized_names) != len(set(normalized_names)):
        errors.append("Duplicate activity names found")

    if expected_environments:
        for environment, expected in expected_environments.items():
            actual = environment_counts[environment]

            if actual != expected:
                errors.append(f"Expected {expected} {environment.value} activities, found {actual}")

    if errors:
        print(f"Catalog validation failed: {path}")

        for error in errors:
            print(f"- {error}")

        raise SystemExit(1)

    print(f"Catalog validation passed: {path}")
    print(f"Records: {len(activities)}")
    print(f"outdoor: {environment_counts[Environment.OUTDOOR]}")
    print(f"sheltered: {environment_counts[Environment.SHELTERED]}")
    print(f"indoor_bridge: {environment_counts[Environment.INDOOR_BRIDGE]}")


def main() -> None:
    args = parse_args()

    expected_environments = None

    if any(
        value is not None
        for value in (
            args.outdoor,
            args.sheltered,
            args.indoor_bridge,
        )
    ):
        expected_environments = {
            Environment.OUTDOOR: args.outdoor or 0,
            Environment.SHELTERED: args.sheltered or 0,
            Environment.INDOOR_BRIDGE: args.indoor_bridge or 0,
        }

    validate_catalog(
        path=args.catalog,
        expected_count=args.expected_count,
        expected_environments=expected_environments,
    )


if __name__ == "__main__":
    main()
