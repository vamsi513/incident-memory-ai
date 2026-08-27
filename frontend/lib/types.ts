export interface SearchFilters {
  service: string | null;
  severity: string | null;
  source: string | null;
}

export interface SearchRequest {
  query: string;
  top_k: number;
  filters: SearchFilters;
}

export interface ChunkMetadata {
  source: string;
  parent_id: string;
  section: string | null;
  service: string | null;
  created_at: string | null;
  extra: Record<string, unknown>;
}

export interface SupportingChunk {
  chunk_id: string;
  document_id: string;
  text: string;
  score: number;
  metadata: ChunkMetadata;
}

export interface SearchResult {
  parent_id: string;
  title: string;
  summary: string;
  final_score: number;
  supporting_chunks: SupportingChunk[];
  metadata: Record<string, unknown>;
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
}
