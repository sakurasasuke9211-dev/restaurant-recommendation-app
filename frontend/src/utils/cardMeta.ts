import type { RecommendationItem } from "../types";

const FOOD_IMAGES = [
  "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=600&q=80",
  "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?auto=format&fit=crop&w=600&q=80",
  "https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?auto=format&fit=crop&w=600&q=80",
  "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=600&q=80",
  "https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=600&q=80",
];

const CATEGORY_TAGS = [
  { label: "PREMIUM SELECTION", className: "bg-zomato-red" },
  { label: "HEALTH CONSCIOUS", className: "bg-blue-600" },
  { label: "DATE NIGHT FAV", className: "bg-gray-800" },
  { label: "TOP PICK", className: "bg-zomato-red" },
  { label: "LOCAL FAVORITE", className: "bg-indigo-600" },
];

export function foodImageUrl(restaurantId: number): string {
  return FOOD_IMAGES[restaurantId % FOOD_IMAGES.length];
}

export function matchPercent(rank: number, rating: number | null): number {
  const base = 100 - (rank - 1) * 4;
  const ratingBoost = rating != null ? Math.round((rating - 4) * 3) : 0;
  return Math.min(99, Math.max(75, base + ratingBoost));
}

export function categoryTag(item: RecommendationItem, rank: number) {
  if (item.price_range === "high") return CATEGORY_TAGS[0];
  if (rank === 2) return CATEGORY_TAGS[1];
  if (rank === 3) return CATEGORY_TAGS[2];
  return CATEGORY_TAGS[(rank - 1) % CATEGORY_TAGS.length];
}
