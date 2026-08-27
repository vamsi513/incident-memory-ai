import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import { Sidebar } from "@/components/Sidebar";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains",
  display: "swap",
});

export const metadata: Metadata = {
  title: "IncidentMemory AI",
  description: "Hybrid RAG search over incident history — BM25 + dense retrieval, reranked by cross-encoder",
  icons: { icon: "/favicon.svg" },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${inter.variable} ${jetbrainsMono.variable}`}>
      <body>
        <a href="#main" className="skip-nav">
          Skip to main content
        </a>
        <div className="app-shell">
          <Sidebar />
          <main id="main" className="main-content">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
