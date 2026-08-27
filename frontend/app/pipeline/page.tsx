import { ArrowRight, ArrowDown } from "lucide-react";

const PIPELINE_STEPS = [
  {
    id: "query",
    label: "User Query",
    detail: "Natural language question or keyword search",
    color: "#6366f1",
  },
  {
    id: "parallel",
    label: "Parallel Retrieval",
    detail: null,
    color: "#8b5cf6",
    parallel: [
      { label: "BM25 Keyword Search", detail: "Sparse retrieval over inverted index" },
      { label: "Dense Vector Search", detail: "FAISS IndexFlatIP with sentence-transformers embeddings" },
    ],
  },
  {
    id: "rrf",
    label: "RRF Fusion",
    detail: "Reciprocal Rank Fusion merges BM25 + dense rankings",
    color: "#a855f7",
  },
  {
    id: "rerank",
    label: "Cross-Encoder Reranking",
    detail: "ms-marco-MiniLM-L-6-v2 scores each candidate pair",
    color: "#ec4899",
  },
  {
    id: "parent",
    label: "Parent Document Retrieval",
    detail: "Expands matched chunks to their parent documents for full context",
    color: "#f97316",
  },
  {
    id: "results",
    label: "Results",
    detail: "Ranked incidents with scores, summaries, and supporting evidence",
    color: "#22c55e",
  },
];

const TECH_STACK = [
  { component: "API Server", technology: "FastAPI", note: "Python async REST" },
  { component: "Vector Store", technology: "FAISS", note: "In-memory IndexFlatIP, CPU-optimised" },
  { component: "Sparse Retrieval", technology: "BM25 (rank_bm25)", note: "Inverted index over corpus" },
  { component: "Embeddings", technology: "sentence-transformers", note: "all-MiniLM-L6-v2" },
  { component: "Reranker", technology: "cross-encoder", note: "ms-marco-MiniLM-L-6-v2" },
  { component: "Frontend", technology: "Next.js 16", note: "App Router, React 19, Vercel" },
];

export default function PipelinePage() {
  return (
    <div style={styles.page}>
      <header style={styles.header}>
        <h1 style={styles.title}>Search Pipeline</h1>
        <p style={styles.subtitle}>
          How queries flow from input to ranked incident results using hybrid RAG.
        </p>
      </header>

      {/* Pipeline diagram */}
      <section style={styles.section} aria-label="Pipeline diagram">
        <h2 style={styles.sectionTitle}>Architecture</h2>
        <div style={styles.pipeline}>
          {PIPELINE_STEPS.map((step, idx) => (
            <div key={step.id}>
              {/* Parallel split step */}
              {step.parallel ? (
                <div>
                  <div style={styles.parallelLabel}>Parallel Retrieval</div>
                  <div style={styles.parallelRow}>
                    {step.parallel.map((p, pi) => (
                      <div key={pi} style={{ ...styles.stepCard, borderTopColor: step.color }}>
                        <div style={{ ...styles.stepName, color: step.color }}>{p.label}</div>
                        <div style={styles.stepDetail}>{p.detail}</div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div style={{ ...styles.stepCard, borderTopColor: step.color }}>
                  <div style={{ ...styles.stepName, color: step.color }}>{step.label}</div>
                  {step.detail && <div style={styles.stepDetail}>{step.detail}</div>}
                </div>
              )}

              {/* Arrow between steps */}
              {idx < PIPELINE_STEPS.length - 1 && (
                <div style={styles.arrow} aria-hidden="true">
                  <ArrowDown size={20} style={{ color: "var(--text-muted)" }} />
                </div>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* Scoring explanation */}
      <section style={styles.section} aria-label="Scoring">
        <h2 style={styles.sectionTitle}>Score Interpretation</h2>
        <div style={styles.scoreGrid}>
          {[
            { label: "High relevance", range: "> 80%", color: "var(--score-high)", bg: "var(--score-high-bg)" },
            { label: "Moderate relevance", range: "60 – 80%", color: "var(--score-mid)", bg: "var(--score-mid-bg)" },
            { label: "Low relevance", range: "< 60%", color: "var(--score-low)", bg: "var(--score-low-bg)" },
          ].map((s) => (
            <div
              key={s.label}
              style={{ ...styles.scoreCard, background: s.bg, borderColor: s.color }}
            >
              <div
                style={{
                  fontFamily: "var(--font-mono)",
                  fontWeight: 700,
                  fontSize: "18px",
                  color: s.color,
                  marginBottom: "4px",
                }}
              >
                {s.range}
              </div>
              <div style={{ fontSize: "13px", color: "var(--text-secondary)" }}>{s.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Tech stack table */}
      <section style={styles.section} aria-label="Technology stack">
        <h2 style={styles.sectionTitle}>Technology Stack</h2>
        <div style={styles.tableWrap}>
          <table style={styles.table} aria-label="Tech stack">
            <thead>
              <tr>
                {["Component", "Technology", "Notes"].map((h) => (
                  <th key={h} style={styles.th}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {TECH_STACK.map((row, i) => (
                <tr key={i} style={i % 2 === 0 ? {} : { background: "var(--surface-2)" }}>
                  <td style={{ ...styles.td, color: "var(--text-primary)", fontWeight: 500 }}>
                    {row.component}
                  </td>
                  <td style={{ ...styles.td, fontFamily: "var(--font-mono)", color: "var(--accent)", fontSize: "13px" }}>
                    {row.technology}
                  </td>
                  <td style={{ ...styles.td, color: "var(--text-muted)", fontSize: "13px" }}>
                    {row.note}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  page: {
    padding: "32px",
    maxWidth: "860px",
    margin: "0 auto",
  },
  header: {
    marginBottom: "36px",
  },
  title: {
    fontSize: "26px",
    fontWeight: 700,
    color: "var(--text-primary)",
    marginBottom: "8px",
  },
  subtitle: {
    fontSize: "15px",
    color: "var(--text-muted)",
    lineHeight: 1.6,
  },
  section: {
    marginBottom: "40px",
  },
  sectionTitle: {
    fontSize: "16px",
    fontWeight: 600,
    color: "var(--text-primary)",
    marginBottom: "16px",
    paddingBottom: "10px",
    borderBottom: "1px solid var(--border)",
  },
  pipeline: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: "0",
  },
  stepCard: {
    background: "var(--surface-1)",
    border: "1px solid var(--border)",
    borderTop: "3px solid #6366f1",
    borderRadius: "8px",
    padding: "16px 20px",
    width: "100%",
    maxWidth: "520px",
    textAlign: "center",
  },
  stepName: {
    fontSize: "15px",
    fontWeight: 600,
    marginBottom: "4px",
  },
  stepDetail: {
    fontSize: "13px",
    color: "var(--text-muted)",
    lineHeight: 1.5,
  },
  parallelLabel: {
    textAlign: "center",
    fontSize: "12px",
    color: "var(--text-muted)",
    fontWeight: 600,
    textTransform: "uppercase",
    letterSpacing: "0.06em",
    marginBottom: "8px",
  },
  parallelRow: {
    display: "flex",
    gap: "12px",
    width: "100%",
    maxWidth: "520px",
    margin: "0 auto",
  },
  arrow: {
    display: "flex",
    justifyContent: "center",
    padding: "4px 0",
  },
  scoreGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
    gap: "12px",
  },
  scoreCard: {
    border: "1px solid",
    borderRadius: "8px",
    padding: "16px 18px",
    textAlign: "center",
  },
  tableWrap: {
    overflowX: "auto",
    borderRadius: "8px",
    border: "1px solid var(--border)",
  },
  table: {
    width: "100%",
    borderCollapse: "collapse",
    fontSize: "14px",
  },
  th: {
    padding: "10px 16px",
    textAlign: "left",
    fontSize: "12px",
    fontWeight: 600,
    textTransform: "uppercase",
    letterSpacing: "0.05em",
    color: "var(--text-muted)",
    background: "var(--surface-2)",
    borderBottom: "1px solid var(--border)",
    whiteSpace: "nowrap",
  },
  td: {
    padding: "11px 16px",
    borderBottom: "1px solid var(--border)",
    color: "var(--text-secondary)",
    verticalAlign: "top",
  },
};
