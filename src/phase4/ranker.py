from src.config import MAX_RECOMMENDATIONS

from src.phase1.loader import deserialize_json_list

from src.phase1.schema import Restaurant

from src.phase2.api.schemas import RecommendationItem, UserPreferences

from src.phase3.filter import score_keyword_match



RATING_WEIGHT = 0.45

VOTES_WEIGHT = 0.15

CUISINE_WEIGHT = 0.15

KEYWORD_WEIGHT = 0.1

BUDGET_WEIGHT = 0.15





def _normalize_votes(votes: int, max_votes: int) -> float:

    if max_votes <= 0:

        return 0.0

    return min(votes / max_votes, 1.0)





def _cuisine_match_score(restaurant: Restaurant, cuisine: str) -> float:

    cuisines = deserialize_json_list(restaurant.cuisines)

    cuisine_lower = cuisine.lower()

    if any(cuisine_lower in c.lower() for c in cuisines):

        return 1.0

    if cuisine_lower in (restaurant.cuisines or "").lower():

        return 1.0

    return 0.0





def _budget_fit_score(restaurant: Restaurant, max_budget: int) -> float:

    cost = restaurant.cost_for_two

    if cost is None:

        return 0.5

    if cost <= max_budget:

        return 1.0

    return 0.0





def score_restaurant(

    restaurant: Restaurant,

    preferences: UserPreferences,

    max_votes: int,

) -> float:

    rating_component = (restaurant.rating or 0.0) / 5.0

    votes_component = _normalize_votes(restaurant.votes, max_votes)

    cuisine_component = _cuisine_match_score(restaurant, preferences.cuisine)

    keyword_raw = score_keyword_match(restaurant, preferences.additional_preferences or "")

    keyword_component = min(keyword_raw / 4.0, 1.0)

    budget_component = _budget_fit_score(restaurant, preferences.max_budget)



    return (

        rating_component * RATING_WEIGHT

        + votes_component * VOTES_WEIGHT

        + cuisine_component * CUISINE_WEIGHT

        + keyword_component * KEYWORD_WEIGHT

        + budget_component * BUDGET_WEIGHT

    )





def rank_candidates(

    candidates: list[Restaurant],

    preferences: UserPreferences,

) -> list[Restaurant]:

    if not candidates:

        return []

    max_votes = max((r.votes for r in candidates), default=0)

    scored = [

        (score_restaurant(r, preferences, max_votes), r)

        for r in candidates

    ]

    scored.sort(key=lambda item: item[0], reverse=True)

    return [restaurant for _, restaurant in scored]





def build_fallback_explanation(

    restaurant: Restaurant,

    preferences: UserPreferences,

) -> str:

    cuisines = deserialize_json_list(restaurant.cuisines)

    cuisine_text = ", ".join(cuisines[:2]) if cuisines else preferences.cuisine

    rating_text = f"{restaurant.rating:.1f}-star" if restaurant.rating else "well-reviewed"

    if restaurant.cost_for_two:

        cost_text = f"₹{restaurant.cost_for_two} for two"

    else:

        cost_text = "a flexible price point"

    area_text = f" in {restaurant.area}" if restaurant.area else ""

    return (

        f"{restaurant.name} is a {rating_text} {cuisine_text} restaurant{area_text} "

        f"in {preferences.location} with an estimated cost of {cost_text}."

    )





def build_fallback_recommendations(

    candidates: list[Restaurant],

    preferences: UserPreferences,

    exclude_ids: set[int] | None = None,

    limit: int | None = None,

) -> list[RecommendationItem]:

    limit = limit or MAX_RECOMMENDATIONS

    exclude_ids = exclude_ids or set()

    ranked = rank_candidates(candidates, preferences)

    items: list[RecommendationItem] = []

    rank = 1

    for restaurant in ranked:

        if restaurant.id in exclude_ids:

            continue

        cuisines = deserialize_json_list(restaurant.cuisines)

        items.append(

            RecommendationItem(

                rank=rank,

                restaurant_id=restaurant.id,

                name=restaurant.name,

                area=restaurant.area,

                cuisines=cuisines,

                rating=restaurant.rating,

                cost_for_two=restaurant.cost_for_two,

                price_range=restaurant.price_range,

                explanation=build_fallback_explanation(restaurant, preferences),

            )

        )

        rank += 1

        if len(items) >= limit:

            break

    return items


