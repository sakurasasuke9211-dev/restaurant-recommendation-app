from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.phase2.api.normalizer import normalize_min_rating, sanitize_additional_preferences


class RecommendationRequest(BaseModel):
    location: str = Field(..., min_length=2, max_length=100)
    max_budget: int = Field(..., ge=100, le=10000, description="Maximum cost for two (INR)")
    cuisine: str = Field(..., min_length=2, max_length=50)
    min_rating: float = Field(..., ge=0.0, le=5.0)
    area: str | None = Field(None, max_length=150)
    additional_preferences: str | None = Field(None, max_length=500)

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "location": "Bangalore",
                    "area": "HSR",
                    "max_budget": 800,
                    "cuisine": "Italian",
                    "min_rating": 4.0,
                    "additional_preferences": "family friendly",
                }
            ]
        }
    )

    @field_validator("location", "cuisine", "area")
    @classmethod
    def strip_whitespace(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip()

    @field_validator("min_rating")
    @classmethod
    def round_min_rating(cls, value: float) -> float:
        return normalize_min_rating(value)

    @field_validator("additional_preferences")
    @classmethod
    def validate_additional_preferences(cls, value: str | None) -> str | None:
        return sanitize_additional_preferences(value)


class UserPreferences(BaseModel):
    """Normalized preferences passed to the recommendation orchestrator."""

    model_config = ConfigDict(from_attributes=True)

    location: str
    max_budget: int
    cuisine: str
    min_rating: float
    area: str | None = None
    additional_preferences: str | None = None


class RecommendationItem(BaseModel):
    rank: int
    restaurant_id: int
    name: str
    area: str | None = None
    cuisines: list[str]
    rating: float | None
    cost_for_two: int | None
    price_range: str
    explanation: str


class RecommendationMeta(BaseModel):
    total_candidates: int
    filters_relaxed: bool
    llm_used: bool
    processing_time_ms: int
    relaxation_steps: list[str] = Field(default_factory=list)
    budget_blocked: bool = False


class RecommendationResponse(BaseModel):
    summary: str
    recommendations: list[RecommendationItem]
    meta: RecommendationMeta


class HealthResponse(BaseModel):
    status: str
    database: str
    restaurant_count: int
    llm_available: bool


class CitiesResponse(BaseModel):
    cities: list[str]


class CuisinesResponse(BaseModel):
    cuisines: list[str]


class AreasResponse(BaseModel):
    areas: list[str]


class ErrorResponse(BaseModel):
    detail: str
    request_id: str | None = None
