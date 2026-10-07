import json
import secrets
from pathlib import Path

import streamlit as st

from src.filters import filter_and_rank
from src.models import Activity, ActivityRequest
from src.ollama_client import OllamaError, recommend_activities

CATALOG_PATH = Path("data/activities.json")
CANDIDATE_LIMIT = 15
RECOMMENDATION_COUNT = 3


@st.cache_data
def load_activities() -> list[Activity]:
    raw_data = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    return [Activity.model_validate(item) for item in raw_data]


def humanize(value: str) -> str:
    return value.replace("_", " ").title()


def build_candidate_pool(
    activities: list[Activity],
    request: ActivityRequest,
) -> tuple[list[Activity], bool]:
    ranked = filter_and_rank(activities, request, limit=len(activities))
    seen_ids = set(st.session_state.seen_recommendation_ids)
    unseen = [activity for activity in ranked if activity.id not in seen_ids]
    history_reset = False

    if len(unseen) < RECOMMENDATION_COUNT:
        unseen = ranked
        st.session_state.seen_recommendation_ids = []
        history_reset = True

    if len(unseen) < RECOMMENDATION_COUNT:
        return unseen, history_reset

    sample_size = min(CANDIDATE_LIMIT, len(unseen))
    sampled = secrets.SystemRandom().sample(unseen, sample_size)
    return sampled, history_reset


def show_activity(activity: Activity, reason: str, heading: str) -> None:
    st.subheader(heading)
    st.markdown(f"### {activity.name}")
    st.write(reason)

    left, middle, right = st.columns(3)
    with left:
        st.metric(
            "Time",
            f"{activity.minimum_minutes} to {activity.maximum_minutes} min",
        )
    with middle:
        st.metric("Environment", humanize(activity.environment.value))
    with right:
        st.metric(
            "Energy",
            ", ".join(humanize(level.value) for level in activity.energy_levels),
        )

    st.markdown("**Mission**")
    for step in activity.mission_steps:
        st.write(f"- {step}")

    if activity.requires_equipment:
        st.markdown("**Bring**")
        st.write(", ".join(humanize(item) for item in activity.requires_equipment))

    if activity.safety_notes:
        st.markdown("**Keep in mind**")
        for note in activity.safety_notes:
            st.write(f"- {note}")

    st.markdown("**Memory prompt**")
    st.write(activity.memory_prompts[0])


def main() -> None:
    st.set_page_config(
        page_title="Offline Adventures",
        page_icon="🌿",
        layout="centered",
    )

    st.title("Offline Adventures")
    st.caption(
        "A private, local AI activity planner that helps you spend less time "
        "choosing and more time doing."
    )
    st.caption(
        "Adding places broadens the pool. Interests guide ranking without "
        "excluding other activities."
    )

    activities = load_activities()
    if "seen_recommendation_ids" not in st.session_state:
        st.session_state.seen_recommendation_ids = []

    with st.form("adventure_request"):
        available_minutes = st.slider(
            "Available time",
            min_value=10,
            max_value=180,
            value=60,
            step=5,
        )
        energy_level = st.selectbox(
            "Energy level",
            options=["low", "medium", "high"],
            format_func=humanize,
        )
        weather = st.selectbox(
            "Current conditions",
            options=[
                "dry",
                "light_rain",
                "heavy_rain",
                "strong_wind",
                "snow",
                "very_hot",
                "very_cold",
                "unknown",
            ],
            format_func=humanize,
        )
        location_types = st.multiselect(
            "Places available to you",
            options=[
                "neighborhood",
                "park",
                "garden",
                "public_square",
                "market",
                "forest_path",
                "public_building",
                "balcony",
                "home",
            ],
            default=["neighborhood", "park", "garden"],
            format_func=humanize,
        )
        group_type = st.selectbox(
            "Who is joining?",
            options=["solo", "couple", "family", "friends", "any"],
            format_func=humanize,
        )
        interests = st.multiselect(
            "What sounds good?",
            options=[
                "walking",
                "running",
                "cycling",
                "photography",
                "nature",
                "culture",
                "social",
                "games",
                "gardening",
                "creative",
                "relaxation",
                "practical",
                "family",
                "reading",
                "writing",
                "drawing",
                "history",
                "architecture",
            ],
            default=["nature"],
            format_func=humanize,
        )
        submitted = st.form_submit_button(
            "Find another adventure",
            type="primary",
            use_container_width=True,
        )

    if not submitted:
        st.info("Choose your situation, then ask the local AI for an adventure.")
        return

    if not location_types:
        st.error("Select at least one available place.")
        return

    request = ActivityRequest.model_validate(
        {
            "available_minutes": available_minutes,
            "energy_level": energy_level,
            "weather": weather,
            "location_types": location_types,
            "group_type": group_type,
            "interests": interests,
        }
    )
    candidates, history_reset = build_candidate_pool(activities, request)

    if len(candidates) < RECOMMENDATION_COUNT:
        st.warning(
            f"Only {len(candidates)} activities match these hard conditions. "
            "Try more time, another energy level, another group, or more places."
        )
        return

    with st.spinner(f"The local AI is choosing from {len(candidates)} varied candidates..."):
        try:
            result = recommend_activities(request, candidates)
        except OllamaError as exc:
            st.error(
                "Local AI is unavailable. Start Ollama and confirm that the "
                "configured model is installed."
            )
            st.caption(str(exc))
            return

    selected_ids = [
        result.primary.activity_id,
        *(item.activity_id for item in result.alternatives),
    ]
    st.session_state.seen_recommendation_ids.extend(selected_ids)

    candidates_by_id = {activity.id: activity for activity in candidates}
    if history_reset:
        st.info("All unseen matches were used, so the recommendation history reset.")
    st.success("Recommendation selected locally with llama3.1:8b-instruct-q4_K_M.")

    primary = candidates_by_id[result.primary.activity_id]
    show_activity(primary, result.primary.reason, "Your adventure")

    st.divider()
    st.subheader("Alternatives")
    for index, recommendation in enumerate(result.alternatives, start=1):
        activity = candidates_by_id[recommendation.activity_id]
        with st.expander(f"Alternative {index}: {activity.name}"):
            show_activity(activity, recommendation.reason, "Another option")


if __name__ == "__main__":
    main()
