"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Brain, Search, GitBranch, X, Menu } from "lucide-react";
import { useState, useEffect, useCallback } from "react";

const SHA = process.env.NEXT_PUBLIC_GIT_SHA ?? "";

const NAV_ITEMS = [
  { href: "/", label: "Query", icon: Search },
  { href: "/pipeline", label: "Pipeline", icon: GitBranch },
];

export function Sidebar() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  const closeMobile = useCallback(() => setMobileOpen(false), []);

  useEffect(() => {
    if (!mobileOpen) return;
    const handler = (e: KeyboardEvent) => { if (e.key === "Escape") closeMobile(); };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [mobileOpen, closeMobile]);

  const sidebarContent = (
    <div style={styles.inner}>
      <div style={styles.brand}>
        <Brain size={28} style={{ color: "var(--accent)" }} />
        <div>
          <div style={styles.brandName}>IncidentMemory AI</div>
          <div style={styles.brandSub}>RAG · Hybrid Search · Reranking</div>
        </div>
      </div>

      <nav style={styles.nav} aria-label="Main navigation">
        {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              aria-current={active ? "page" : undefined}
              style={{
                ...styles.navItem,
                ...(active ? styles.navItemActive : {}),
              }}
              onClick={() => setMobileOpen(false)}
            >
              <Icon size={16} />
              {label}
            </Link>
          );
        })}
      </nav>

      <div style={styles.footer}>
        <div style={{ fontSize: "11px", color: "var(--text-muted)", marginBottom: 6, fontWeight: 500 }}>
          Vamsi Krishna Sadu
        </div>
        {SHA && (
          <div style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--text-muted)", marginBottom: 8 }}>
            {SHA.slice(0, 7)}
          </div>
        )}
        <div style={{ fontSize: "10.5px", color: "var(--text-muted)", marginBottom: 8, fontStyle: "italic" }}>
          Demo corpus: curated incident reports
        </div>
        <a
          href="https://github.com/vamsi513/incident-memory-ai"
          target="_blank"
          rel="noopener noreferrer"
          style={{ fontSize: "11.5px", color: "var(--text-muted)", textDecoration: "none", display: "flex", alignItems: "center", gap: 5 }}
        >
          <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12z" />
          </svg>
          View source on GitHub
        </a>
      </div>
    </div>
  );

  return (
    <>
      {/* Mobile hamburger */}
      <button
        style={styles.hamburger}
        aria-label="Open navigation"
        onClick={() => setMobileOpen(true)}
      >
        <Menu size={20} />
      </button>

      {/* Desktop sidebar */}
      <aside style={styles.sidebar} aria-label="Sidebar">
        {sidebarContent}
      </aside>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div style={styles.overlay} onClick={() => setMobileOpen(false)}>
          <aside
            style={{ ...styles.sidebar, ...styles.mobileSidebar }}
            onClick={(e) => e.stopPropagation()}
          >
            <button
              style={styles.closeBtn}
              aria-label="Close navigation"
              onClick={() => setMobileOpen(false)}
            >
              <X size={20} />
            </button>
            {sidebarContent}
          </aside>
        </div>
      )}
    </>
  );
}

const styles: Record<string, React.CSSProperties> = {
  sidebar: {
    width: "224px",
    minWidth: "224px",
    background: "var(--surface-1)",
    borderRight: "1px solid var(--border)",
    display: "flex",
    flexDirection: "column",
    position: "sticky",
    top: 0,
    height: "100vh",
    overflowY: "auto",
  },
  inner: {
    display: "flex",
    flexDirection: "column",
    height: "100%",
    padding: "20px 0",
  },
  brand: {
    display: "flex",
    alignItems: "flex-start",
    gap: "10px",
    padding: "0 16px 20px",
    borderBottom: "1px solid var(--border)",
    marginBottom: "16px",
  },
  brandName: {
    fontWeight: 700,
    fontSize: "14px",
    color: "var(--text-primary)",
    lineHeight: 1.2,
  },
  brandSub: {
    fontSize: "10px",
    color: "var(--text-muted)",
    marginTop: "3px",
    lineHeight: 1.4,
  },
  nav: {
    display: "flex",
    flexDirection: "column",
    gap: "2px",
    padding: "0 8px",
    flex: 1,
  },
  navItem: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
    padding: "8px 12px",
    borderRadius: "6px",
    fontSize: "13px",
    fontWeight: 500,
    color: "var(--text-secondary)",
    textDecoration: "none",
    transition: "background 0.15s, color 0.15s",
  },
  navItemActive: {
    background: "var(--accent-subtle)",
    color: "var(--accent)",
  },
  footer: {
    padding: "16px",
    borderTop: "1px solid var(--border)",
    marginTop: "auto",
  },
  hamburger: {
    display: "none",
    position: "fixed",
    top: "12px",
    left: "12px",
    zIndex: 200,
    background: "var(--surface-2)",
    border: "1px solid var(--border)",
    borderRadius: "6px",
    padding: "6px 8px",
    color: "var(--text-primary)",
    cursor: "pointer",
  },
  overlay: {
    position: "fixed",
    inset: 0,
    background: "rgba(0,0,0,0.6)",
    zIndex: 300,
    display: "flex",
  },
  mobileSidebar: {
    position: "relative",
    height: "100vh",
  },
  closeBtn: {
    position: "absolute",
    top: "12px",
    right: "12px",
    background: "none",
    border: "none",
    color: "var(--text-muted)",
    cursor: "pointer",
    padding: "4px",
  },
};
