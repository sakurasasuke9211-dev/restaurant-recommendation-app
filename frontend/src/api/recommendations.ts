import { ApiError } from "../types";
import type {
  RecommendationRequest,
  RecommendationResponse,
} from "../types";

const API_BASE = import.meta.env.VITE_API_URL ?? "";

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let message = `Request failed (${res.status})`;
    let requestId: string | undefined;
    try {
      const body = await res.json();
      if (body.detail) {
        message =
          typeof body.detail === "string"
            ? body.detail
            : JSON.stringify(body.detail);
      }
      if (body.request_id) {
        requestId = body.request_id;
      }
    } catch {
      message = await res.text();
    }
    const headerRequestId = res.headers.get("X-Request-ID");
    throw new ApiError(message, requestId ?? headerRequestId ?? undefined);
  }
  return res.json() as Promise<T>;
}

export async function fetchCities(): Promise<string[]> {
  const res = await fetch(`${API_BASE}/api/v1/meta/cities`);
  const data = await handleResponse<{ cities: string[] }>(res);
  return data.cities;
}

export async function fetchAreas(city: string): Promise<string[]> {
  const params = `?city=${encodeURIComponent(city)}`;
  const res = await fetch(`${API_BASE}/api/v1/meta/areas${params}`);
  const data = await handleResponse<{ areas: string[] }>(res);
  return data.areas;
}

export async function fetchCuisines(city?: string): Promise<string[]> {
  const params = city ? `?city=${encodeURIComponent(city)}` : "";
  const res = await fetch(`${API_BASE}/api/v1/meta/cuisines${params}`);
  const data = await handleResponse<{ cuisines: string[] }>(res);
  return data.cuisines;
}

export async function getRecommendations(
  request: RecommendationRequest
): Promise<RecommendationResponse> {
  const payload: RecommendationRequest = { ...request };
  if (payload.area === "All Bangalore" || payload.area === "") {
    delete payload.area;
  }
  const res = await fetch(`${API_BASE}/api/v1/recommendations`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return handleResponse<RecommendationResponse>(res);
}

export async function fetchHealth(): Promise<{
  status: string;
  restaurant_count: number;
  llm_available: boolean;
}> {
  const res = await fetch(`${API_BASE}/api/v1/health`);
  return handleResponse(res);
}
