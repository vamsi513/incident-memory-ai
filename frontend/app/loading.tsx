export default function Loading() {
  return (
    <div style={styles.container}>
      {[1, 2, 3].map((i) => (
        <div key={i} style={styles.card}>
          <div style={{ ...styles.skeleton, width: "60%", height: "18px", marginBottom: "10px" }} />
          <div style={{ ...styles.skeleton, width: "100%", height: "14px", marginBottom: "6px" }} />
          <div style={{ ...styles.skeleton, width: "85%", height: "14px", marginBottom: "6px" }} />
          <div style={{ ...styles.skeleton, width: "72%", height: "14px", marginBottom: "16px" }} />
          <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
            <div style={{ ...styles.skeleton, width: "120px", height: "8px", borderRadius: "4px" }} />
            <div style={{ ...styles.skeleton, width: "48px", height: "22px", borderRadius: "4px" }} />
          </div>
        </div>
      ))}
    </div>
  );
}

const shimmer = `@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}`;

const styles: Record<string, React.CSSProperties> = {
  container: {
    padding: "32px",
    display: "flex",
    flexDirection: "column",
    gap: "16px",
    maxWidth: "860px",
    margin: "0 auto",
  },
  card: {
    background: "var(--surface-1)",
    border: "1px solid var(--border)",
    borderRadius: "10px",
    padding: "20px 24px",
  },
  skeleton: {
    background:
      "linear-gradient(90deg, var(--surface-2) 25%, var(--surface-3) 50%, var(--surface-2) 75%)",
    backgroundSize: "200% 100%",
    animation: "shimmer 1.4s infinite",
    borderRadius: "4px",
  },
};
