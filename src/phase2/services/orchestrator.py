import logging
import time

from src.phase1.loader import RestaurantRepository
from src.phase2.api.normalizer import CityNotFoundError
from src.phase2.api.schemas import RecommendationResponse, UserPreferences
from src.phase3.filter import FilterService
from src.phase4.engine import RecommendationEngine

logger = logging.getLogger(__name__)
_engine = RecommendationEngine()


def run_recommendation(
    preferences: UserPreferences,
    repo: RestaurantRepository,
) -> RecommendationResponse:
    start = time.perf_counter()
    known_cities = repo.get_cities()
    if preferences.location not in known_cities:
        raise CityNotFoundError(preferences.location)

    filter_service = FilterService(repo)
    filter_result = filter_service.get_shortlist(preferences)
    elapsed_ms = int((time.perf_counter() - start) * 1000)

    return _engine.run(
        preferences=preferences,
        candidates=filter_result.candidates,
        filters_relaxed=filter_result.filters_relaxed,
        processing_time_ms=elapsed_ms,
        relaxation_steps=filter_result.relaxation_steps,
        budget_blocked=filter_result.budget_blocked,
    )
