export const config = {
  runtime: "edge",
};

const DEFAULT_BACKEND = "https://restaurant-recommendation-api.onrender.com";

export default async function handler(request: Request): Promise<Response> {
  const backend = (process.env.RENDER_API_URL ?? DEFAULT_BACKEND).replace(/\/$/, "");
  const incoming = new URL(request.url);
  const target = `${backend}${incoming.pathname}${incoming.search}`;

  const headers = new Headers();
  headers.set("Accept", "application/json");
  const contentType = request.headers.get("content-type");
  if (contentType) {
    headers.set("Content-Type", contentType);
  }

  const init: RequestInit = {
    method: request.method,
    headers,
  };

  if (request.method !== "GET" && request.method !== "HEAD") {
    init.body = await request.text();
  }

  const upstream = await fetch(target, init);
  const responseHeaders = new Headers(upstream.headers);
  responseHeaders.set("Access-Control-Allow-Origin", "*");

  return new Response(upstream.body, {
    status: upstream.status,
    headers: responseHeaders,
  });
}
