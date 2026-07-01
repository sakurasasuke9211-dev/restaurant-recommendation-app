CITY_ALIASES: dict[str, str] = {
    "Bengaluru": "Bangalore",
    "Bangalore": "Bangalore",
    "Banglore": "Bangalore",
    "Bengalore": "Bangalore",
    "New Delhi": "Delhi",
    "Delhi NCR": "Delhi",
    "Delhi": "Delhi",
    "Gurugram": "Gurgaon",
    "Gurgaon": "Gurgaon",
    "Mumbai": "Mumbai",
    "Hyderabad": "Hyderabad",
    "Chennai": "Chennai",
    "Kolkata": "Kolkata",
    "Pune": "Pune",
}

BANGALORE_VARIANTS = {"bangalore", "bengaluru", "banglore", "bengalore"}

GLOBAL_BUDGET_THRESHOLDS: dict[str, tuple[int | None, int | None]] = {
    "low": (None, 400),
    "medium": (401, 800),
    "high": (801, None),
}

PRICE_RANGE_LOW = "low"
PRICE_RANGE_MEDIUM = "medium"
PRICE_RANGE_HIGH = "high"

ALL_AREAS_LABEL = "All Bangalore"

AREA_ALIASES: dict[str, str] = {
    "HSR Layout": "HSR",
    "Hsr Layout": "HSR",
    "hsr layout": "HSR",
    "Indira Nagar": "Indiranagar",
    "Indiranagar": "Indiranagar",
    "Koramangala 5th Block": "Koramangala",
    "Koramangala 4th Block": "Koramangala",
    "Koramangala 6th Block": "Koramangala",
    "Electronic city": "Electronic City",
    "White field": "Whitefield",
    "Marathahalli ORR": "Marathahalli",
}

RELAXATION_LABELS: dict[str, str] = {
    "max_budget": "Budget limit increased",
    "min_rating": "Minimum rating lowered",
    "cuisine": "Cuisine filter broadened",
    "area": "Area filter broadened to all Bangalore",
    "city_only": "Showing top-rated matches in your area",
}
