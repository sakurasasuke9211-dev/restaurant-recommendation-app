from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.phase2.api.dependencies import get_db
from src.phase2.api.normalizer import CityNotFoundError, normalize_location, normalize_request
from src.phase2.api.schemas import (
    AreasResponse,
    CitiesResponse,
    CuisinesResponse,
    HealthResponse,
    RecommendationRequest,
    RecommendationResponse,
    UserPreferences,
)
from src.phase1.loader import RestaurantRepository
from src.phase2.services.orchestrator import run_recommendation
from src.phase3.llm import is_llm_available

router = APIRouter(prefix="/api/v1")


@router.get("/health", response_model=HealthResponse)
def health_check(session: Session = Depends(get_db)) -> HealthResponse:
    repo = RestaurantRepository(session)
    count = repo.count_all()
    return HealthResponse(
        status="ok",
        database="connected",
        restaurant_count=count,
        llm_available=is_llm_available(),
    )


@router.get("/meta/cities", response_model=CitiesResponse)
def list_cities(session: Session = Depends(get_db)) -> CitiesResponse:
    repo = RestaurantRepository(session)
    return CitiesResponse(cities=repo.get_cities())


@router.get("/meta/areas", response_model=AreasResponse)
def list_areas(
    city: str = Query(..., description="City to list areas for"),
    session: Session = Depends(get_db),
) -> AreasResponse:
    repo = RestaurantRepository(session)
    normalized_city = normalize_location(city)
    known_cities = repo.get_cities()
    if normalized_city not in known_cities:
        raise HTTPException(
            status_code=404,
            detail=f"City '{normalized_city}' not found. See /api/v1/meta/cities.",
        )
    return AreasResponse(areas=repo.get_areas(normalized_city))


@router.get("/meta/cuisines", response_model=CuisinesResponse)
def list_cuisines(
    city: str | None = Query(None, description="Filter cuisines by city"),
    session: Session = Depends(get_db),
) -> CuisinesResponse:
    repo = RestaurantRepository(session)
    normalized_city = None
    if city:
        normalized_city = normalize_location(city)
        known_cities = repo.get_cities()
        if normalized_city not in known_cities:
            raise HTTPException(
                status_code=404,
                detail=f"City '{normalized_city}' not found. See /api/v1/meta/cities.",
            )
    return CuisinesResponse(cuisines=repo.get_cuisines(city=normalized_city))


@router.post("/recommendations", response_model=RecommendationResponse)
def create_recommendations(
    body: RecommendationRequest,
    session: Session = Depends(get_db),
) -> RecommendationResponse:
    preferences: UserPreferences = normalize_request(
        location=body.location,
        max_budget=body.max_budget,
        cuisine=body.cuisine,
        min_rating=body.min_rating,
        additional_preferences=body.additional_preferences,
        area=body.area,
    )
    repo = RestaurantRepository(session)
    try:
        return run_recommendation(preferences, repo)
    except CityNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
