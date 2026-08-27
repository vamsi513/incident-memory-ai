import type { Facets, SearchRequest, SearchResponse } from "./types";

export async function searchIncidents(
  request: SearchRequest
): Promise<SearchResponse> {
  const response = await fetch("/api/search", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    if (response.status >= 500) throw new Error("The search service is temporarily unavailable. Please try again shortly.");
    if (response.status === 404) throw new Error("Search endpoint not found. The backend may be restarting.");
    const text = await response.text().catch(() => "");
    throw new Error(text || `Search failed (${response.status})`);
  }

  return response.json() as Promise<SearchResponse>;
}

export async function getFacets(): Promise<Facets> {
  const response = await fetch("/api/facets");
  if (!response.ok) {
    throw new Error(`Failed to load filter options (${response.status})`);
  }
  return response.json() as Promise<Facets>;
}
