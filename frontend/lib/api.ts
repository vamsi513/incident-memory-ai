import type { SearchRequest, SearchResponse } from "./types";

export async function searchIncidents(
  request: SearchRequest
): Promise<SearchResponse> {
  const response = await fetch("/api/search", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const text = await response.text().catch(() => "Unknown error");
    throw new Error(`Search failed (${response.status}): ${text}`);
  }

  return response.json() as Promise<SearchResponse>;
}
