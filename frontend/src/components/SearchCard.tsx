import { useEffect, useState } from "react";
import { fetchAreas, fetchCities, fetchCuisines } from "../api/recommendations";
import type { PreferenceFormData } from "../types";

interface Props {
  onSubmit: (data: PreferenceFormData) => void;
  loading: boolean;
}

const MIN_BUDGET = 100;
const MAX_BUDGET = 10000;
const DEFAULT_BUDGET = 800;

const RATING_OPTIONS = [
  { label: "Any rating", value: 0 },
  { label: "3.0+", value: 3.0 },
  { label: "3.5+", value: 3.5 },
  { label: "4.0+", value: 4.0 },
  { label: "4.5+", value: 4.5 },
];

function PinIcon() {
  return (
    <svg className="h-3.5 w-3.5 text-zomato-red" fill="currentColor" viewBox="0 0 20 20">
      <path fillRule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
    </svg>
  );
}

function WalletIcon() {
  return (
    <svg className="h-3.5 w-3.5 text-zomato-red" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
    </svg>
  );
}

function ForkIcon() {
  return (
    <svg className="h-3.5 w-3.5 text-zomato-red" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v14M8 3v7M16 3v7M4 10h16" />
    </svg>
  );
}

function StarIcon() {
  return (
    <svg className="h-3.5 w-3.5 text-zomato-red" fill="currentColor" viewBox="0 0 20 20">
      <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
    </svg>
  );
}

export default function SearchCard({ onSubmit, loading }: Props) {
  const [city, setCity] = useState("Bangalore");
  const [areas, setAreas] = useState<string[]>(["All Bangalore"]);
  const [cuisines, setCuisines] = useState<string[]>([]);
  const [metaLoading, setMetaLoading] = useState(true);
  const [budgetInput, setBudgetInput] = useState(String(DEFAULT_BUDGET));
  const [budgetError, setBudgetError] = useState<string | null>(null);
  const [form, setForm] = useState<PreferenceFormData>({
    location: "Bangalore",
    area: "All Bangalore",
    max_budget: DEFAULT_BUDGET,
    cuisine: "",
    min_rating: 4.0,
    additional_preferences: "",
  });

  useEffect(() => {
    fetchCities()
      .then((list) => {
        const selected = list[0] ?? "Bangalore";
        setCity(selected);
        setForm((prev) => ({ ...prev, location: selected }));
      })
      .catch(() => {
        setCity("Bangalore");
        setForm((prev) => ({ ...prev, location: "Bangalore" }));
      })
      .finally(() => setMetaLoading(false));
  }, []);

  useEffect(() => {
    if (!city) return;
    fetchAreas(city)
      .then((list) => {
        setAreas(list.length > 0 ? list : ["All Bangalore"]);
        setForm((prev) => ({
          ...prev,
          area: list.includes(prev.area) ? prev.area : list[0] ?? "All Bangalore",
        }));
      })
      .catch(() => setAreas(["All Bangalore"]));
  }, [city]);

  useEffect(() => {
    if (!city) return;
    fetchCuisines(city)
      .then((list) => {
        setCuisines(list);
        setForm((prev) => ({
          ...prev,
          cuisine: list.includes(prev.cuisine) ? prev.cuisine : list[0] ?? "",
        }));
      })
      .catch(() => setCuisines([]));
  }, [city]);

  const parseBudget = (raw: string): number | null => {
    const trimmed = raw.trim();
    if (!trimmed) return null;
    const value = parseInt(trimmed, 10);
    if (Number.isNaN(value)) return null;
    return Math.min(MAX_BUDGET, Math.max(MIN_BUDGET, value));
  };

  const handleBudgetChange = (raw: string) => {
    if (raw === "" || /^\d+$/.test(raw)) {
      setBudgetInput(raw);
      setBudgetError(null);
    }
  };

  const handleBudgetBlur = () => {
    const parsed = parseBudget(budgetInput);
    if (parsed == null) {
      setBudgetError(`Enter a budget for two between ₹${MIN_BUDGET} and ₹${MAX_BUDGET.toLocaleString("en-IN")}`);
      return;
    }
    setBudgetInput(String(parsed));
    setForm((prev) => ({ ...prev, max_budget: parsed }));
    setBudgetError(null);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.cuisine) return;

    const parsed = parseBudget(budgetInput);
    if (parsed == null) {
      setBudgetError(`Enter a budget for two between ₹${MIN_BUDGET} and ₹${MAX_BUDGET.toLocaleString("en-IN")}`);
      return;
    }

    onSubmit({ ...form, max_budget: parsed });
  };

  const budgetValid = parseBudget(budgetInput) != null;

  return (
    <form
      onSubmit={handleSubmit}
      className="rounded-2xl bg-white p-5 text-left shadow-search sm:p-6"
    >
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <label className="filter-cell">
          <span className="field-label">
            <PinIcon /> Location
          </span>
          <select
            className="field-input"
            value={form.area}
            disabled={metaLoading || loading || areas.length === 0}
            onChange={(e) => setForm((prev) => ({ ...prev, area: e.target.value }))}
          >
            {areas.map((area) => (
              <option key={area} value={area}>
                {area === "All Bangalore" ? `${city}, India` : `${area}, ${city}`}
              </option>
            ))}
          </select>
        </label>

        <label className="filter-cell">
          <span className="field-label">
            <WalletIcon /> Budget for two
          </span>
          <div className="flex items-center gap-1">
            <span className="text-sm font-medium text-zomato-muted">₹</span>
            <input
              type="text"
              inputMode="numeric"
              className="field-input"
              value={budgetInput}
              disabled={loading}
              placeholder="800"
              aria-invalid={budgetError != null}
              onChange={(e) => handleBudgetChange(e.target.value)}
              onBlur={handleBudgetBlur}
            />
          </div>
          <p className="mt-1 text-[10px] text-zomato-muted">
            Maximum budget for two people (₹)
          </p>
          {budgetError && (
            <p className="mt-1 text-[10px] font-medium text-red-600">{budgetError}</p>
          )}
        </label>

        <label className="filter-cell">
          <span className="field-label">
            <ForkIcon /> Cuisine
          </span>
          <select
            className="field-input"
            value={form.cuisine}
            disabled={loading || cuisines.length === 0}
            onChange={(e) => setForm((prev) => ({ ...prev, cuisine: e.target.value }))}
          >
            {cuisines.length === 0 ? (
              <option value="">Loading…</option>
            ) : (
              cuisines.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))
            )}
          </select>
        </label>

        <label className="filter-cell">
          <span className="field-label">
            <StarIcon /> Min Rating
          </span>
          <select
            className="field-input"
            value={form.min_rating}
            disabled={loading}
            onChange={(e) =>
              setForm((prev) => ({
                ...prev,
                min_rating: parseFloat(e.target.value),
              }))
            }
          >
            {RATING_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-stretch">
        <label className="filter-cell min-h-[120px] flex-1">
          <span className="field-label">Describe your vibe</span>
          <textarea
            rows={3}
            className="field-input mt-1 min-h-[72px] resize-none placeholder:font-normal placeholder:text-gray-400"
            placeholder="e.g., 'A cozy date night spot with authentic carbonara and candlelight...'"
            value={form.additional_preferences}
            disabled={loading}
            onChange={(e) =>
              setForm((prev) => ({
                ...prev,
                additional_preferences: e.target.value,
              }))
            }
          />
        </label>

        <button
          type="submit"
          className="shrink-0 rounded-xl bg-zomato-red px-8 py-4 text-base font-semibold text-white shadow-md transition hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-60 sm:self-auto"
          disabled={loading || !form.cuisine || !budgetValid}
        >
          {loading ? "Searching…" : "Find Places"}
        </button>
      </div>
    </form>
  );
}
