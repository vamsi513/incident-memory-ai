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

const BASE_URL = "https://incidentmemory-platformvercelapp.vercel.app";
const DESCRIPTION =
  "Hybrid RAG search over engineering incident history — BM25 + FAISS dense retrieval, Reciprocal Rank Fusion, cross-encoder reranking, and parent-document evidence.";

export const metadata: Metadata = {
  metadataBase: new URL(BASE_URL),
  title: "IncidentMemory AI",
  description: DESCRIPTION,
  icons: { icon: "/favicon.svg" },
  openGraph: {
    title: "IncidentMemory AI",
    description: DESCRIPTION,
    url: BASE_URL,
    siteName: "IncidentMemory AI",
    type: "website",
    locale: "en_US",
  },
  twitter: {
    card: "summary_large_image",
    title: "IncidentMemory AI",
    description: DESCRIPTION,
  },
  robots: { index: true, follow: true },
  alternates: { canonical: BASE_URL },
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
