import type { RecommendationItem } from "../types";
import { categoryTag, foodImageUrl, matchPercent } from "../utils/cardMeta";

interface Props {
  item: RecommendationItem;
  showArea?: boolean;
}

export default function RecommendationCard({ item, showArea = true }: Props) {
  const match = matchPercent(item.rank, item.rating);
  const tag = categoryTag(item, item.rank);
  const cuisineLabel = item.cuisines.slice(0, 2).join(" • ");
  const locationLabel = showArea && item.area ? item.area : "Bangalore";

  return (
    <article className="overflow-hidden rounded-2xl bg-white shadow-card transition hover:-translate-y-0.5 hover:shadow-lg">
      <div className="relative aspect-[4/3] overflow-hidden">
        <img
          src={foodImageUrl(item.restaurant_id)}
          alt=""
          className="h-full w-full object-cover"
          loading="lazy"
        />

        <div className="absolute right-3 top-3 rounded-lg bg-white/95 px-2.5 py-1.5 shadow-sm backdrop-blur">
          <p className="text-xs font-bold text-zomato-dark">{match}% Match</p>
          <div className="mt-1 h-1 w-16 overflow-hidden rounded-full bg-gray-200">
            <div
              className="h-full rounded-full bg-zomato-red"
              style={{ width: `${match}%` }}
            />
          </div>
        </div>

        <span
          className={`absolute bottom-3 left-3 rounded px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-white ${tag.className}`}
        >
          {tag.label}
        </span>
      </div>

      <div className="p-4">
        <div className="flex items-start justify-between gap-2">
          <h3 className="text-lg font-bold text-zomato-dark">{item.name}</h3>
          {item.rating != null && (
            <span className="flex shrink-0 items-center gap-1 rounded-md bg-green-50 px-2 py-1 text-sm font-semibold text-zomato-rating">
              {item.rating.toFixed(1)} <span aria-hidden>★</span>
            </span>
          )}
        </div>

        <p className="mt-1 text-sm text-zomato-muted">
          {cuisineLabel}
          {cuisineLabel && " · "}
          {locationLabel}
          {item.cost_for_two != null && ` · ₹${item.cost_for_two} for two`}
        </p>

        <blockquote className="mt-3 rounded-lg bg-gray-50 px-3 py-2.5 text-sm italic leading-relaxed text-zomato-muted">
          &ldquo;{item.explanation}&rdquo;
        </blockquote>
      </div>
    </article>
  );
}
