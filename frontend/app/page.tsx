"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { Search, ChevronDown, ChevronUp, AlertCircle, Loader2 } from "lucide-react";
import { searchIncidents, getFacets } from "@/lib/api";
import type { SearchResult, SearchFilters, Facets } from "@/lib/types";

const SAMPLE_QUERIES = [
  "database connection pool exhaustion",
  "redis OOM restart",
  "k8s pod eviction memory limit",
  "DNS resolution failure between microservices",
  "deployment rollback procedure",
];

const EMPTY_FACETS: Facets = { services: [], severities: [], sources: [] };

function normalizeScore(score: number): number {
  return 1 / (1 + Math.exp(-score));
}

function formatPct(normalized: number): string {
  const pct = normalized * 100;
  if (pct > 0 && pct < 1) return pct.toFixed(1) + "%";
  return Math.round(pct) + "%";
}

function scoreColor(normalized: number): string {
  if (normalized > 0.8) return "var(--score-high)";
  if (normalized > 0.6) return "var(--score-mid)";
  return "var(--score-low)";
}

function scoreBg(normalized: number): string {
  if (normalized > 0.8) return "var(--score-high-bg)";
  if (normalized > 0.6) return "var(--score-mid-bg)";
  return "var(--score-low-bg)";
}

function ScoreBar({ score }: { score: number }) {
  const normalized = normalizeScore(score);
  const pct = Math.round(normalized * 100);
  return (
    <div style={styles.scoreRow}>
      <span style={{ fontSize: "11px", color: "var(--text-muted)", minWidth: 60, flexShrink: 0 }}>
        Relevance
      </span>
      <div
        style={styles.scoreBarTrack}
        role="progressbar"
        aria-valuenow={pct}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`Relevance score ${pct}%`}
      >
        <div
          style={{
            ...styles.scoreBarFill,
            width: `${pct}%`,
            background: scoreColor(normalized),
          }}
        />
      </div>
      <span
        style={{
          fontFamily: "var(--font-mono)",
          fontSize: "12px",
          fontWeight: 600,
          color: scoreColor(normalized),
          background: scoreBg(normalized),
          padding: "2px 6px",
          borderRadius: "4px",
          minWidth: "44px",
          textAlign: "center",
        }}
      >
        {formatPct(normalized)}
      </span>
    </div>
  );
}

function ResultCard({ result }: { result: SearchResult }) {
  const [expanded, setExpanded] = useState(false);
  const source = result.supporting_chunks[0]?.metadata?.source ?? "unknown";

  return (
    <article style={styles.card}>
      <div style={styles.cardHeader}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <h3 style={styles.cardTitle}>{result.title || result.parent_id}</h3>
          <p style={styles.cardSummary}>{result.summary}</p>
        </div>
        <span style={styles.sourceBadge}>{source}</span>
      </div>

      <ScoreBar score={result.final_score} />

      {result.supporting_chunks.length > 0 && (
        <div style={styles.chunksSection}>
          <button
            style={styles.expandBtn}
            onClick={() => setExpanded((v) => !v)}
            aria-expanded={expanded}
          >
            {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
            {result.supporting_chunks.length} supporting chunk
            {result.supporting_chunks.length !== 1 ? "s" : ""}
          </button>

          {expanded && (
            <div style={styles.chunksList}>
              {result.supporting_chunks.map((chunk) => {
                const chunkNormalized = normalizeScore(chunk.score);
                return (
                  <div key={chunk.chunk_id} style={styles.chunk}>
                    <div style={styles.chunkMeta}>
                      <span style={styles.chunkMetaItem}>
                        {chunk.metadata.section ?? "—"}
                      </span>
                      <span
                        style={{
                          fontFamily: "var(--font-mono)",
                          fontSize: "11px",
                          color: scoreColor(chunkNormalized),
                          background: scoreBg(chunkNormalized),
                          padding: "1px 5px",
                          borderRadius: "3px",
                        }}
                      >
                        {formatPct(chunkNormalized)}
                      </span>
                    </div>
                    <p style={styles.chunkText}>{chunk.text}</p>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </article>
  );
}

function EmptyState({ onQuery }: { onQuery: (q: string) => void }) {
  return (
    <div style={styles.emptyState}>
      <Search size={48} style={{ color: "var(--text-muted)", marginBottom: "16px" }} />
      <h2 style={styles.emptyTitle}>Search incident history</h2>
      <p style={styles.emptyDesc}>
        Query across runbooks, postmortems, and incident reports using hybrid RAG search.
      </p>
      <div style={styles.samplesGrid}>
        {SAMPLE_QUERIES.map((q) => (
          <button key={q} style={styles.sampleBtn} onClick={() => onQuery(q)}>
            {q}
          </button>
        ))}
      </div>
    </div>
  );
}

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [topK, setTopK] = useState(5);
  const [filters, setFilters] = useState<SearchFilters>({
    service: null,
    severity: null,
    source: null,
  });
  const [results, setResults] = useState<SearchResult[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastQuery, setLastQuery] = useState("");
  const [facets, setFacets] = useState<Facets>(EMPTY_FACETS);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    getFacets()
      .then(setFacets)
      .catch(() => setFacets(EMPTY_FACETS));
  }, []);

  const runSearch = useCallback(
    async (q: string) => {
      const trimmed = q.trim();
      if (trimmed.length < 3) return;

      setLoading(true);
      setError(null);
      setLastQuery(trimmed);

      try {
        const resp = await searchIncidents({
          query: trimmed,
          top_k: topK,
          filters,
        });
        setResults(resp.results);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Search failed");
        setResults(null);
      } finally {
        setLoading(false);
      }
    },
    [topK, filters]
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    runSearch(query);
  };

  const handleSampleClick = (q: string) => {
    setQuery(q);
    runSearch(q);
    inputRef.current?.focus();
  };

  const setFilter = (key: keyof SearchFilters, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value === "" ? null : value }));
  };

  return (
    <div style={styles.page}>
      <h1 style={{ position: "absolute", width: 1, height: 1, overflow: "hidden", clip: "rect(0,0,0,0)", whiteSpace: "nowrap" }}>
        IncidentMemory AI — Hybrid RAG Incident Search
      </h1>
      {/* Search bar area */}
      <div style={styles.searchArea}>
        <form onSubmit={handleSubmit} style={styles.form}>
          <div style={styles.inputWrap}>
            <Search size={18} style={styles.searchIcon} />
            <input
              ref={inputRef}
              type="search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search incidents, runbooks, postmortems…"
              style={styles.input}
              minLength={3}
              aria-label="Search query"
            />
            <button
              type="submit"
              disabled={loading || query.trim().length < 3}
              style={styles.searchBtn}
            >
              {loading ? <Loader2 size={16} style={{ animation: "spin 1s linear infinite" }} /> : "Search"}
            </button>
          </div>
        </form>

        {/* Controls row */}
        <div style={styles.controls}>
          <div style={styles.sliderGroup}>
            <label htmlFor="topk-slider" style={styles.label}>
              Top results:{" "}
              <span style={{ fontFamily: "var(--font-mono)", color: "var(--accent)" }}>
                {topK}
              </span>
            </label>
            <input
              id="topk-slider"
              type="range"
              min={1}
              max={10}
              value={topK}
              onChange={(e) => setTopK(Number(e.target.value))}
              style={styles.slider}
            />
          </div>

          <div style={styles.filterRow}>
            {(
              [
                { key: "service" as const, label: "Service", plural: "Services", opts: facets.services },
                { key: "severity" as const, label: "Severity", plural: "Severities", opts: facets.severities },
                { key: "source" as const, label: "Source", plural: "Sources", opts: facets.sources },
              ] as const
            ).map(({ key, label, plural, opts }) => (
              <select
                key={key}
                value={filters[key] ?? ""}
                onChange={(e) => setFilter(key, e.target.value)}
                style={styles.filterSelect}
                aria-label={label}
              >
                <option value="">All {plural}</option>
                {opts.map((o) => (
                  <option key={o} value={o}>
                    {o}
                  </option>
                ))}
              </select>
            ))}
          </div>
        </div>
      </div>

      {/* Results area */}
      <div style={styles.resultsArea}>
        {error && (
          <div style={styles.errorBanner} role="alert">
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        )}

        {loading && (
          <div style={styles.skeletonWrap}>
            {[1, 2, 3].map((i) => (
              <div key={i} style={styles.skeletonCard}>
                <div style={{ ...styles.skeletonBlock, width: "55%", height: "18px", marginBottom: "10px" }} />
                <div style={{ ...styles.skeletonBlock, width: "100%", height: "13px", marginBottom: "6px" }} />
                <div style={{ ...styles.skeletonBlock, width: "80%", height: "13px", marginBottom: "16px" }} />
                <div style={{ ...styles.skeletonBlock, width: "130px", height: "8px" }} />
              </div>
            ))}
          </div>
        )}

        {!loading && results !== null && results.length === 0 && (
          <div style={styles.noResults}>
            <p>No sufficiently relevant incident found for <strong>"{lastQuery}"</strong>.</p>
            <p style={{ color: "var(--text-muted)", marginTop: "4px", fontSize: "14px" }}>
              This demo corpus may not cover that topic. Try a different query or adjust your filters.
            </p>
          </div>
        )}

        {!loading && results !== null && results.length > 0 && (
          <div style={styles.resultsList}>
            <p style={styles.resultsMeta}>
              {results.length} result{results.length !== 1 ? "s" : ""} for{" "}
              <strong>"{lastQuery}"</strong>
            </p>
            {results.map((r) => (
              <ResultCard key={r.parent_id} result={r} />
            ))}
          </div>
        )}

        {!loading && results === null && !error && (
          <EmptyState onQuery={handleSampleClick} />
        )}
      </div>

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes shimmer {
          0% { background-position: -200% 0; }
          100% { background-position: 200% 0; }
        }
      `}</style>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  page: {
    display: "flex",
    flexDirection: "column",
    minHeight: "100vh",
  },
  searchArea: {
    padding: "32px 32px 20px",
    borderBottom: "1px solid var(--border)",
    background: "var(--surface-1)",
    position: "sticky",
    top: 0,
    zIndex: 10,
  },
  form: {
    marginBottom: "16px",
  },
  inputWrap: {
    display: "flex",
    alignItems: "center",
    background: "var(--surface-2)",
    border: "2px solid var(--border)",
    borderRadius: "10px",
    padding: "0 4px 0 14px",
    transition: "border-color 0.15s",
  },
  searchIcon: {
    color: "var(--text-muted)",
    flexShrink: 0,
    marginRight: "8px",
  },
  input: {
    flex: 1,
    background: "none",
    border: "none",
    outline: "none",
    color: "var(--text-primary)",
    fontSize: "16px",
    padding: "12px 0",
    fontFamily: "var(--font-sans)",
  },
  searchBtn: {
    background: "var(--accent)",
    color: "#fff",
    border: "none",
    borderRadius: "7px",
    padding: "8px 18px",
    fontSize: "14px",
    fontWeight: 600,
    cursor: "pointer",
    display: "flex",
    alignItems: "center",
    gap: "6px",
    transition: "background 0.15s",
    flexShrink: 0,
  },
  controls: {
    display: "flex",
    flexWrap: "wrap",
    gap: "16px",
    alignItems: "center",
  },
  sliderGroup: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
  },
  label: {
    fontSize: "13px",
    color: "var(--text-secondary)",
    whiteSpace: "nowrap",
  },
  slider: {
    accentColor: "var(--accent)",
    width: "100px",
    cursor: "pointer",
  },
  filterRow: {
    display: "flex",
    gap: "8px",
    flexWrap: "wrap",
  },
  filterSelect: {
    background: "var(--surface-2)",
    border: "1px solid var(--border)",
    borderRadius: "6px",
    color: "var(--text-secondary)",
    fontSize: "13px",
    padding: "5px 10px",
    cursor: "pointer",
    outline: "none",
  },
  resultsArea: {
    flex: 1,
    padding: "24px 32px",
    maxWidth: "900px",
    margin: "0 auto",
    width: "100%",
  },
  resultsList: {
    display: "flex",
    flexDirection: "column",
    gap: "14px",
  },
  resultsMeta: {
    fontSize: "13px",
    color: "var(--text-muted)",
    marginBottom: "8px",
  },
  card: {
    background: "var(--surface-1)",
    border: "1px solid var(--border)",
    borderRadius: "10px",
    padding: "20px 24px",
    transition: "border-color 0.15s",
  },
  cardHeader: {
    display: "flex",
    gap: "12px",
    alignItems: "flex-start",
    marginBottom: "14px",
  },
  cardTitle: {
    fontSize: "15px",
    fontWeight: 600,
    color: "var(--text-primary)",
    marginBottom: "6px",
    lineHeight: 1.4,
  },
  cardSummary: {
    fontSize: "13px",
    color: "var(--text-secondary)",
    lineHeight: 1.6,
  },
  sourceBadge: {
    background: "var(--accent-subtle)",
    color: "var(--accent)",
    border: "1px solid currentColor",
    borderRadius: "4px",
    padding: "2px 8px",
    fontSize: "11px",
    fontWeight: 600,
    whiteSpace: "nowrap",
    fontFamily: "var(--font-mono)",
    flexShrink: 0,
  },
  scoreRow: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
    marginBottom: "12px",
  },
  scoreBarTrack: {
    flex: 1,
    height: "6px",
    background: "var(--surface-3)",
    borderRadius: "3px",
    overflow: "hidden",
  },
  scoreBarFill: {
    height: "100%",
    borderRadius: "3px",
    transition: "width 0.4s ease",
  },
  chunksSection: {
    borderTop: "1px solid var(--border)",
    paddingTop: "12px",
    marginTop: "4px",
  },
  expandBtn: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    background: "none",
    border: "none",
    color: "var(--text-muted)",
    fontSize: "12px",
    cursor: "pointer",
    padding: "0",
    fontFamily: "var(--font-sans)",
  },
  chunksList: {
    marginTop: "10px",
    display: "flex",
    flexDirection: "column",
    gap: "10px",
  },
  chunk: {
    background: "var(--surface-2)",
    borderRadius: "6px",
    padding: "12px 14px",
    borderLeft: "3px solid var(--border)",
  },
  chunkMeta: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    marginBottom: "6px",
  },
  chunkMetaItem: {
    fontSize: "11px",
    color: "var(--text-muted)",
    fontFamily: "var(--font-mono)",
  },
  chunkText: {
    fontSize: "13px",
    color: "var(--text-secondary)",
    lineHeight: 1.6,
    whiteSpace: "pre-wrap",
    wordBreak: "break-word",
  },
  emptyState: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    paddingTop: "60px",
    textAlign: "center",
  },
  emptyTitle: {
    fontSize: "20px",
    fontWeight: 600,
    color: "var(--text-primary)",
    marginBottom: "8px",
  },
  emptyDesc: {
    fontSize: "14px",
    color: "var(--text-muted)",
    maxWidth: "400px",
    marginBottom: "28px",
  },
  samplesGrid: {
    display: "flex",
    flexWrap: "wrap",
    gap: "8px",
    justifyContent: "center",
    maxWidth: "600px",
  },
  sampleBtn: {
    background: "var(--surface-2)",
    border: "1px solid var(--border)",
    borderRadius: "20px",
    padding: "6px 14px",
    fontSize: "13px",
    color: "var(--text-secondary)",
    cursor: "pointer",
    transition: "border-color 0.15s, color 0.15s",
    fontFamily: "var(--font-sans)",
  },
  errorBanner: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    background: "var(--score-low-bg)",
    color: "var(--score-low)",
    border: "1px solid var(--score-low)",
    borderRadius: "8px",
    padding: "12px 16px",
    fontSize: "14px",
    marginBottom: "16px",
  },
  noResults: {
    padding: "48px 0",
    textAlign: "center",
    color: "var(--text-secondary)",
    fontSize: "15px",
  },
  skeletonWrap: {
    display: "flex",
    flexDirection: "column",
    gap: "14px",
  },
  skeletonCard: {
    background: "var(--surface-1)",
    border: "1px solid var(--border)",
    borderRadius: "10px",
    padding: "20px 24px",
  },
  skeletonBlock: {
    background:
      "linear-gradient(90deg, var(--surface-2) 25%, var(--surface-3) 50%, var(--surface-2) 75%)",
    backgroundSize: "200% 100%",
    animation: "shimmer 1.4s infinite",
    borderRadius: "4px",
  },
};
