#!/usr/bin/env python3

"""Live Groq LLM flow verification — runs real recommendation scenarios."""



from __future__ import annotations



import sys

from dataclasses import dataclass

from pathlib import Path



PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:

    sys.path.insert(0, str(PROJECT_ROOT))



from src.phase1.database import get_session

from src.phase1.loader import RestaurantRepository

from src.phase2.api.schemas import UserPreferences

from src.phase2.services.orchestrator import run_recommendation

from src.phase3.llm import is_llm_available





@dataclass

class LiveTestCase:

    name: str

    location: str

    max_budget: int

    cuisine: str

    min_rating: float

    area: str | None = None

    additional_preferences: str | None = None





TEST_CASES = [

    LiveTestCase(

        name="Italian ₹800 budget",

        location="Bangalore",

        max_budget=800,

        cuisine="Italian",

        min_rating=4.0,

    ),

    LiveTestCase(

        name="North Indian ₹400 budget",

        location="Bangalore",

        max_budget=400,

        cuisine="North Indian",

        min_rating=3.5,

    ),

    LiveTestCase(

        name="Chinese ₹1200 + HSR area",

        location="Bangalore",

        max_budget=1200,

        cuisine="Chinese",

        min_rating=4.0,

        area="HSR",

        additional_preferences="family friendly, casual dining",

    ),

    LiveTestCase(

        name="Biryani quick service",

        location="Bangalore",

        max_budget=600,

        cuisine="Biryani",

        min_rating=3.5,

        additional_preferences="quick service",

    ),

]





def _quality_checks(case: LiveTestCase, response) -> list[str]:

    issues: list[str] = []

    recs = response.recommendations



    if not response.meta.llm_used:

        issues.append("LLM was NOT used (fallback mode)")

    if len(recs) == 0:

        issues.append("No recommendations returned")

    if not response.summary.strip():

        issues.append("Empty summary")



    for rec in recs:

        if not rec.explanation.strip():

            issues.append(f"Empty explanation for {rec.name}")

        if rec.rating is not None and rec.rating < case.min_rating - 0.6:

            issues.append(

                f"{rec.name} rating {rec.rating} well below min {case.min_rating}"

            )

        cuisine_match = any(

            case.cuisine.lower() in c.lower() for c in rec.cuisines

        )

        if not cuisine_match and case.cuisine.lower() not in rec.name.lower():

            issues.append(f"{rec.name} may not match cuisine '{case.cuisine}'")



    return issues





def run_live_tests(max_cases: int = 4) -> int:

    print("=" * 70)

    print("GROQ LLM LIVE FLOW VERIFICATION")

    print("=" * 70)



    if not is_llm_available():

        print("FAIL: Groq not available. Check GROQ_API_KEY in .env")

        return 1



    print("Groq connection: OK (API key loaded, LLM_ENABLED=true)\n")



    passed = 0

    failed = 0



    with get_session() as session:

        repo = RestaurantRepository(session)



        for i, case in enumerate(TEST_CASES[:max_cases], start=1):

            print(f"--- Test {i}/{min(max_cases, len(TEST_CASES))}: {case.name} ---")

            prefs = UserPreferences(

                location=case.location,

                max_budget=case.max_budget,

                cuisine=case.cuisine,

                min_rating=case.min_rating,

                area=case.area,

                additional_preferences=case.additional_preferences,

            )



            try:

                response = run_recommendation(prefs, repo)

            except Exception as exc:

                print(f"  FAIL: {exc}\n")

                failed += 1

                continue



            issues = _quality_checks(case, response)

            status = "PASS" if not issues else "WARN"



            print(f"  Status:       {status}")

            print(f"  llm_used:     {response.meta.llm_used}")

            print(f"  candidates:   {response.meta.total_candidates}")

            print(f"  relaxed:      {response.meta.filters_relaxed}")

            if response.meta.relaxation_steps:

                print(f"  relaxation:   {', '.join(response.meta.relaxation_steps)}")

            print(f"  latency:      {response.meta.processing_time_ms}ms")

            print(f"  summary:      {response.summary[:100]}...")

            print(f"  picks ({len(response.recommendations)}):")

            for rec in response.recommendations[:3]:

                cuisines = ", ".join(rec.cuisines[:2])

                area = f" [{rec.area}]" if rec.area else ""

                print(

                    f"    #{rec.rank} {rec.name}{area} ({rec.rating}*) "

                    f"[{cuisines}] — {rec.explanation[:80]}..."

                )



            if issues:

                print("  Issues:")

                for issue in issues:

                    print(f"    - {issue}")

                if any("LLM was NOT used" in i for i in issues):

                    failed += 1

                else:

                    passed += 1

            else:

                passed += 1

            print()



    print("=" * 70)

    print(f"Results: {passed} passed, {failed} failed out of {min(max_cases, len(TEST_CASES))} tests")

    print("=" * 70)

    return 0 if failed == 0 else 1





if __name__ == "__main__":

    max_cases = int(sys.argv[1]) if len(sys.argv) > 1 else 4

    raise SystemExit(run_live_tests(max_cases=max_cases))


