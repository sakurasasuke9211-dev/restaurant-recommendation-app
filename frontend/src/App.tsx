import { useCallback, useEffect, useState } from "react";
import { ApiError } from "./types";
import { fetchHealth, getRecommendations } from "./api/recommendations";
import HeroSection from "./components/layout/HeroSection";
import LoadingState from "./components/LoadingState";
import RecommendationCard from "./components/RecommendationCard";
import SearchCard from "./components/SearchCard";
import SummaryBanner from "./components/SummaryBanner";
import type { PreferenceFormData, RecommendationItem, RecommendationResponse } from "./types";
import "./index.css";

type AppState = "idle" | "loading" | "success" | "error";

const PLACEHOLDER_CARDS = [
  { name: "The Spice Route", match: 98, tag: "PREMIUM SELECTION", rating: 4.9 },
  { name: "Modern Bistro", match: 94, tag: "HEALTH CONSCIOUS", rating: 4.7 },
  { name: "Trattoria Roma", match: 89, tag: "DATE NIGHT FAV", rating: 4.8 },
];

function sortByRatingDesc(items: RecommendationItem[]): RecommendationItem[] {
  return [...items]
    .sort((a, b) => {
      const ratingA = a.rating ?? -1;
      const ratingB = b.rating ?? -1;
      if (ratingB !== ratingA) return ratingB - ratingA;
      return a.name.localeCompare(b.name);
    })
    .map((item, index) => ({ ...item, rank: index + 1 }));
}

export default function App() {
  const [state, setState] = useState<AppState>("idle");
  const [result, setResult] = useState<RecommendationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [requestId, setRequestId] = useState<string | null>(null);
  const [restaurantCount, setRestaurantCount] = useState<number | null>(null);
  const [llmAvailable, setLlmAvailable] = useState<boolean | null>(null);
  const [lastRequest, setLastRequest] = useState<PreferenceFormData | null>(null);
  const [selectedArea, setSelectedArea] = useState<string>("All Bangalore");

  useEffect(() => {
    fetchHealth()
      .then((h) => {
        setRestaurantCount(h.restaurant_count);
        setLlmAvailable(h.llm_available);
      })
      .catch(() => {
        setRestaurantCount(null);
        setLlmAvailable(null);
      });
  }, []);

  const runSearch = useCallback(async (data: PreferenceFormData) => {
    setState("loading");
    setError(null);
    setRequestId(null);
    setLastRequest(data);
    setSelectedArea(data.area);

    try {
      const response = await getRecommendations({
        location: data.location,
        area: data.area !== "All Bangalore" ? data.area : undefined,
        max_budget: data.max_budget,
        cuisine: data.cuisine,
        min_rating: data.min_rating,
        additional_preferences: data.additional_preferences || undefined,
      });
      setResult(response);
      setState("success");
    } catch (err) {
      setResult(null);
      if (err instanceof ApiError) {
        setError(err.message);
        setRequestId(err.requestId ?? null);
      } else {
        setError(err instanceof Error ? err.message : "Something went wrong");
      }
      setState("error");
    }
  }, []);

  const retry = () => {
    if (lastRequest) runSearch(lastRequest);
  };

  const showAreaOnCards =
    selectedArea !== "All Bangalore" && selectedArea !== "";

  return (
    <div className="min-h-screen bg-zomato-cream">
      <HeroSection restaurantCount={restaurantCount} llmAvailable={llmAvailable} />

      <section className="relative z-10 mx-auto max-w-4xl -mt-1 px-4 pb-10 sm:px-6 sm:pb-14">
        <SearchCard onSubmit={runSearch} loading={state === "loading"} />
      </section>

      <main className="mx-auto max-w-6xl px-4 pb-16 sm:px-6">
        <div className="mb-6 flex items-center justify-between">
          <h2 className="text-xl font-bold text-zomato-dark sm:text-2xl">
            Top Matches for you
          </h2>
          <div className="flex gap-2">
            <button
              type="button"
              className="flex h-9 w-9 items-center justify-center rounded-full bg-white text-zomato-muted shadow-sm ring-1 ring-gray-100 hover:text-zomato-dark"
              aria-label="Filter results"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" d="M4 6h16M7 12h10M10 18h4" />
              </svg>
            </button>
            <button
              type="button"
              className="flex h-9 w-9 items-center justify-center rounded-full bg-white text-zomato-muted shadow-sm ring-1 ring-gray-100 hover:text-zomato-dark"
              aria-label="Grid view"
            >
              <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                <path d="M5 3a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2V5a2 2 0 00-2-2H5zM5 11a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2v-2a2 2 0 00-2-2H5zM11 5a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V5zM11 13a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
              </svg>
            </button>
          </div>
        </div>

        {state === "idle" && (
          <div className="grid gap-6 opacity-50 sm:grid-cols-2 lg:grid-cols-3" aria-hidden>
            {PLACEHOLDER_CARDS.map((card) => (
              <div key={card.name} className="overflow-hidden rounded-2xl bg-white shadow-card">
                <div className="aspect-[4/3] bg-gray-200" />
                <div className="p-4">
                  <div className="flex justify-between">
                    <div className="h-5 w-32 rounded bg-gray-200" />
                    <div className="h-5 w-12 rounded bg-green-100" />
                  </div>
                  <div className="mt-2 h-4 w-48 rounded bg-gray-100" />
                  <div className="mt-3 h-14 rounded-lg bg-gray-50" />
                </div>
              </div>
            ))}
          </div>
        )}

        {state === "idle" && (
          <p className="mt-6 text-center text-sm text-zomato-muted">
            Describe your vibe above and click <strong className="text-zomato-dark">Find Places</strong> to
            see AI-ranked matches.
          </p>
        )}

        {state === "loading" && <LoadingState />}

        {state === "error" && (
          <div className="rounded-xl border border-red-200 bg-red-50 px-5 py-4 text-red-800">
            <p className="font-medium">{error}</p>
            {requestId && (
              <p className="mt-2 text-sm">
                Request ID: <code className="rounded bg-red-100 px-1">{requestId}</code>
              </p>
            )}
            <button
              type="button"
              onClick={retry}
              className="mt-4 rounded-lg bg-zomato-red px-4 py-2 text-sm font-semibold text-white hover:bg-red-700"
            >
              Retry
            </button>
          </div>
        )}

        {state === "success" && result && (
          <>
            <SummaryBanner
              summary={result.summary}
              llmUsed={result.meta.llm_used}
              filtersRelaxed={result.meta.filters_relaxed}
              relaxationSteps={result.meta.relaxation_steps}
              candidateCount={result.meta.total_candidates}
              processingMs={result.meta.processing_time_ms}
            />

            {result.recommendations.length === 0 ? (
              result.meta.budget_blocked ? (
                <p className="py-8 text-center text-lg font-semibold text-red-600">
                  have nothing in this budget !
                </p>
              ) : (
                <p className="py-8 text-center text-zomato-muted">
                  No restaurants matched. Try a higher budget or lower minimum rating.
                </p>
              )
            ) : (
              <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
                {sortByRatingDesc(result.recommendations).map((item) => (
                  <RecommendationCard
                    key={item.restaurant_id}
                    item={item}
                    showArea={showAreaOnCards}
                  />
                ))}
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}
