from enum import StrEnum

from pydantic import BaseModel, Field, model_validator


class Environment(StrEnum):
    OUTDOOR = "outdoor"
    SHELTERED = "sheltered"
    INDOOR_BRIDGE = "indoor_bridge"


class EnergyLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Weather(StrEnum):
    DRY = "dry"
    LIGHT_RAIN = "light_rain"
    HEAVY_RAIN = "heavy_rain"
    STRONG_WIND = "strong_wind"
    SNOW = "snow"
    VERY_HOT = "very_hot"
    VERY_COLD = "very_cold"
    UNKNOWN = "unknown"


class ActivityType(StrEnum):
    WALKING = "walking"
    RUNNING = "running"
    CYCLING = "cycling"
    PHOTOGRAPHY = "photography"
    NATURE = "nature"
    CULTURE = "culture"
    SOCIAL = "social"
    GAMES = "games"
    GARDENING = "gardening"
    CREATIVE = "creative"
    RELAXATION = "relaxation"
    PRACTICAL = "practical"


class LocationType(StrEnum):
    NEIGHBORHOOD = "neighborhood"
    PARK = "park"
    GARDEN = "garden"
    PUBLIC_SQUARE = "public_square"
    MARKET = "market"
    FOREST_PATH = "forest_path"
    PUBLIC_BUILDING = "public_building"
    BALCONY = "balcony"
    HOME = "home"
    ANY = "any"


class GroupType(StrEnum):
    SOLO = "solo"
    COUPLE = "couple"
    FAMILY = "family"
    FRIENDS = "friends"
    ANY = "any"


class Activity(BaseModel):
    id: str = Field(pattern=r"^activity_[0-9]{3}$")
    name: str = Field(min_length=3, max_length=100)
    environment: Environment
    activity_types: list[ActivityType] = Field(min_length=1)
    location_types: list[LocationType] = Field(min_length=1)
    group_types: list[GroupType] = Field(min_length=1)
    minimum_minutes: int = Field(ge=5, le=240)
    maximum_minutes: int = Field(ge=5, le=240)
    energy_levels: list[EnergyLevel] = Field(min_length=1)
    weather: list[Weather] = Field(min_length=1)
    interests: list[str] = Field(min_length=1)
    requires_equipment: list[str] = Field(default_factory=list)
    mission_steps: list[str] = Field(min_length=1, max_length=5)
    safety_notes: list[str] = Field(default_factory=list)
    memory_prompts: list[str] = Field(min_length=1, max_length=3)

    @model_validator(mode="after")
    def validate_duration(self) -> "Activity":
        if self.minimum_minutes > self.maximum_minutes:
            raise ValueError("minimum_minutes cannot exceed maximum_minutes")
        return self


class ActivityRequest(BaseModel):
    available_minutes: int = Field(ge=5, le=240)
    energy_level: EnergyLevel
    weather: Weather
    location_types: list[LocationType] = Field(default_factory=lambda: [LocationType.ANY])
    group_type: GroupType = GroupType.ANY
    interests: list[str] = Field(default_factory=list)
    excluded_activity_ids: set[str] = Field(default_factory=set)


class ActivityRecommendation(BaseModel):
    activity_id: str = Field(pattern=r"^activity_[0-9]{3}$")
    reason: str = Field(min_length=10, max_length=300)


class RecommendationResult(BaseModel):
    primary: ActivityRecommendation
    alternatives: list[ActivityRecommendation] = Field(min_length=2, max_length=2)

    @model_validator(mode="after")
    def validate_unique_activity_ids(self) -> "RecommendationResult":
        identifiers = [
            self.primary.activity_id,
            *(item.activity_id for item in self.alternatives),
        ]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("recommended activity IDs must be unique")
        return self


class ActivityCatalog(BaseModel):
    activities: list[Activity] = Field(min_length=1, max_length=50)
