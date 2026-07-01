#!/usr/bin/env python3
"""Phase 4 live verification — end-to-end Groq + engine tests."""

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
class Case:
    name: str
    location: str
    max_budget: int
    cuisine: str
    min_rating: float
    area: str | None = None
    additional: str | None = None


CASES = [
    Case("Italian ₹800", "Bangalore", 800, "Italian", 4.0),
    Case("North Indian ₹400", "Bangalore", 400, "North Indian", 3.5),
    Case("Chinese HSR", "Bangalore", 1200, "Chinese", 4.0, area="HSR", additional="family friendly"),
]


def main(max_cases: int = 3) -> int:
    print("=" * 70)
    print("PHASE 4 LIVE ENGINE VERIFICATION")
    print("=" * 70)

    if not is_llm_available():
        print("FAIL: Groq not configured")
        return 1

    passed = 0
    with get_session() as session:
        repo = RestaurantRepository(session)
        for i, case in enumerate(CASES[:max_cases], 1):
            print(f"\n--- Test {i}: {case.name} ---")
            prefs = UserPreferences(
                location=case.location,
                max_budget=case.max_budget,
                cuisine=case.cuisine,
                min_rating=case.min_rating,
                area=case.area,
                additional_preferences=case.additional,
            )
            resp = run_recommendation(prefs, repo)
            ok = (
                resp.meta.llm_used
                and len(resp.recommendations) >= 3
                and all(r.explanation for r in resp.recommendations)
            )
            print(f"  llm_used:      {resp.meta.llm_used}")
            print(f"  candidates:    {resp.meta.total_candidates}")
            print(f"  recommendations: {len(resp.recommendations)}")
            print(f"  latency:       {resp.meta.processing_time_ms}ms")
            print(f"  summary:       {resp.summary[:90]}...")
            for rec in resp.recommendations[:2]:
                print(f"    #{rec.rank} {rec.name} ({rec.rating}*) — {rec.explanation[:70]}...")
            print(f"  Result:        {'PASS' if ok else 'FAIL'}")
            if ok:
                passed += 1

    print(f"\n{'=' * 70}")
    print(f"Passed {passed}/{min(max_cases, len(CASES))}")
    return 0 if passed == min(max_cases, len(CASES)) else 1


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    raise SystemExit(main(n))
