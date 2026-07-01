import { ApiError } from "../types";
import type {
  RecommendationRequest,
  RecommendationResponse,
} from "../types";

const API_BASE = import.meta.env.VITE_API_URL ?? "";

function backendHint(): string {
  if (!API_BASE) {
    return "VITE_API_URL is not set. Redeploy the frontend with your Streamlit backend URL.";
  }
  return (
    "Check that your Streamlit app is public (Anyone with the link can view) " +
    "and CORS_ORIGINS includes your Vercel URL."
  );
}

async function handleResponse<T>(res: Response): Promise<T> {
  const contentType = res.headers.get("content-type") ?? "";

  if (res.status === 401 || res.status === 403 || res.status === 303) {
    throw new ApiError(
      `Backend requires login (${res.status}). ${backendHint()}`
    );
  }

  if (!contentType.includes("application/json")) {
    const preview = (await res.text()).slice(0, 120);
    if (preview.toLowerCase().includes("auth") || preview.toLowerCase().includes("login")) {
      throw new ApiError(
        `Backend blocked the request (likely a private Streamlit app). ${backendHint()}`
      );
    }
    throw new ApiError(
      `Backend returned a non-JSON response (${res.status}). ${backendHint()}`
    );
  }

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

async function apiFetch(path: string, init?: RequestInit): Promise<Response> {
  return fetch(`${API_BASE}${path}`, {
    ...init,
    redirect: "manual",
    headers: {
      Accept: "application/json",
      ...(init?.headers ?? {}),
    },
  });
}

export async function fetchCities(): Promise<string[]> {
  const res = await apiFetch("/api/v1/meta/cities");
  const data = await handleResponse<{ cities: string[] }>(res);
  return data.cities;
}

export async function fetchAreas(city: string): Promise<string[]> {
  const params = `?city=${encodeURIComponent(city)}`;
  const res = await apiFetch(`/api/v1/meta/areas${params}`);
  const data = await handleResponse<{ areas: string[] }>(res);
  return data.areas;
}

export async function fetchCuisines(city?: string): Promise<string[]> {
  const params = city ? `?city=${encodeURIComponent(city)}` : "";
  const res = await apiFetch(`/api/v1/meta/cuisines${params}`);
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
  const res = await apiFetch("/api/v1/recommendations", {
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
  const res = await apiFetch("/api/v1/health");
  return handleResponse(res);
}
