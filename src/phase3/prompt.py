import json

from src.config import LLM_CANDIDATE_COUNT, MAX_RECOMMENDATIONS
from src.phase1.loader import deserialize_json_list
from src.phase1.schema import Restaurant
from src.phase2.api.schemas import UserPreferences

SYSTEM_PROMPT_TEMPLATE = """You are an expert restaurant recommendation assistant for Indian cities.
You receive a user's dining preferences and a list of candidate restaurants (JSON).
Your job is to:

1. Select the top {max_results} restaurants that best match the user's preferences.
2. Rank them from best (rank 1) to best #{max_results} (rank {max_results}).
3. Write a concise, friendly explanation (2–3 sentences) for each restaurant.
4. Write a brief overall summary (1–2 sentences) of the recommendations.

Rules:
- ONLY recommend restaurants from the provided candidate list.
- Use the exact restaurant_id and restaurant_name from the candidates.
- The recommendations array MUST contain exactly {max_results} items when at least {max_results} candidates are provided.
- Consider rating, budget fit, cuisine match, and any additional preferences.
- Prefer restaurants at or below the user's maximum budget; mention it if slightly over.
- If additional preferences mention "family friendly", favor casual dining / family restaurants.
- If "quick service" is mentioned, favor quick bites / fast food types.
- Respond ONLY with valid JSON matching the required schema."""

USER_PROMPT_TEMPLATE = """User Preferences:
- Location: {location}
{area_line}- Maximum budget: ₹{max_budget} for two
- Cuisine: {cuisine}
- Minimum Rating: {min_rating}
- Additional Preferences: {additional}

Candidate Restaurants ({candidate_count} options):
{candidates}

Respond with JSON in this exact format (include exactly {max_results} recommendations when enough candidates exist):
{{
  "summary": "<overall summary>",
  "recommendations": [
    {{
      "rank": 1,
      "restaurant_id": <id from candidates>,
      "restaurant_name": "<name from candidates>",
      "explanation": "<why this restaurant fits>"
    }},
    {{
      "rank": 2,
      "restaurant_id": <id>,
      "restaurant_name": "<name>",
      "explanation": "<explanation>"
    }}
  ]
}}"""


def restaurant_to_llm_dict(restaurant: Restaurant) -> dict:
    return {
        "restaurant_id": restaurant.id,
        "id": restaurant.id,
        "name": restaurant.name,
        "area": restaurant.area,
        "cuisines": deserialize_json_list(restaurant.cuisines),
        "rating": restaurant.rating,
        "cost_for_two": restaurant.cost_for_two,
        "price_range": restaurant.price_range,
        "restaurant_type": restaurant.restaurant_type,
        "popular_dishes": deserialize_json_list(restaurant.popular_dishes)[:5],
        "online_order": restaurant.online_order,
    }


def build_prompt(
    preferences: UserPreferences,
    candidates: list[Restaurant],
    max_results: int | None = None,
) -> list[dict[str, str]]:
    max_results = max_results or MAX_RECOMMENDATIONS
    candidate_payload = [restaurant_to_llm_dict(r) for r in candidates[:LLM_CANDIDATE_COUNT]]
    area_line = f"- Area: {preferences.area}\n" if preferences.area else ""
    system = SYSTEM_PROMPT_TEMPLATE.format(max_results=max_results)
    user = USER_PROMPT_TEMPLATE.format(
        location=preferences.location,
        area_line=area_line,
        max_budget=preferences.max_budget,
        cuisine=preferences.cuisine,
        min_rating=preferences.min_rating,
        additional=preferences.additional_preferences or "None",
        candidate_count=len(candidate_payload),
        max_results=max_results,
        candidates=json.dumps(candidate_payload, indent=2, ensure_ascii=False),
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def estimate_token_count(messages: list[dict[str, str]]) -> int:
    """Rough token estimate (~4 chars per token) for prompt budget checks."""
    total_chars = sum(len(message["content"]) for message in messages)
    return total_chars // 4
