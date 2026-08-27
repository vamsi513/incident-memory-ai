"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Brain, Search, GitBranch, X, Menu } from "lucide-react";
import { useState } from "react";

const NAV_ITEMS = [
  { href: "/", label: "Query", icon: Search },
  { href: "/pipeline", label: "Pipeline", icon: GitBranch },
];

export function Sidebar() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

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
        <span style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--text-muted)" }}>
          v1.0.0
        </span>
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
