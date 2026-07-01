export interface RecommendationRequest {
  location: string;
  max_budget: number;
  cuisine: string;
  min_rating: number;
  area?: string;
  additional_preferences?: string;
}

export interface RecommendationItem {
  rank: number;
  restaurant_id: number;
  name: string;
  area: string | null;
  cuisines: string[];
  rating: number | null;
  cost_for_two: number | null;
  price_range: string;
  explanation: string;
}

export interface RecommendationMeta {
  total_candidates: number;
  filters_relaxed: boolean;
  llm_used: boolean;
  processing_time_ms: number;
  relaxation_steps: string[];
  budget_blocked: boolean;
}

export interface RecommendationResponse {
  summary: string;
  recommendations: RecommendationItem[];
  meta: RecommendationMeta;
}

export interface PreferenceFormData {
  location: string;
  area: string;
  max_budget: number;
  cuisine: string;
  min_rating: number;
  additional_preferences: string;
}

export class ApiError extends Error {
  requestId?: string;

  constructor(message: string, requestId?: string) {
    super(message);
    this.name = "ApiError";
    this.requestId = requestId;
  }
}
