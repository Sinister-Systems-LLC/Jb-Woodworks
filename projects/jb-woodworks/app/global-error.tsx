// Author: RKOJ-ELENO :: 2026-05-23
// Root-level error boundary. Used when the error happens above the layout
// (e.g. fatal render error in app/layout.tsx itself). Must include <html> +
// <body> per Next.js docs.
"use client";

import { useEffect } from "react";

export default function GlobalError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => {
    // eslint-disable-next-line no-console
    console.error("[jbw] root error:", error);
  }, [error]);

  return (
    <html lang="en">
      <body style={{ background: "#080808", color: "rgba(255,255,255,0.85)", fontFamily: "Inter, sans-serif", margin: 0, padding: 0 }}>
        <main style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", padding: "2rem", textAlign: "center" }}>
          <div style={{ maxWidth: 560 }}>
            <p style={{ fontSize: "0.7rem", letterSpacing: "0.22em", textTransform: "uppercase", color: "#c9a84c", fontWeight: 700, margin: 0 }}>JB Woodworks &middot; Critical Error</p>
            <h1 style={{ fontFamily: "'DM Serif Display', Georgia, serif", fontSize: "clamp(2rem, 5vw, 3rem)", color: "#fff", margin: "1rem 0 0.5rem", lineHeight: 1.1 }}>
              Site is briefly down.
            </h1>
            <p style={{ color: "rgba(255,255,255,0.6)", lineHeight: 1.7, marginBottom: "1.5rem" }}>
              An error reached the root of the application. Reload the page, or call <a style={{ color: "#c9a84c" }} href="tel:4075611453">(407) 561-1453</a>.
            </p>
            <button
              type="button"
              onClick={() => reset()}
              style={{ background: "#c9a84c", color: "#080808", border: 0, padding: "0.9rem 2rem", fontSize: "0.82rem", fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", cursor: "pointer", borderRadius: 6 }}
            >
              Try again
            </button>
            {error?.digest && (
              <p style={{ marginTop: "1.5rem", fontSize: "0.7rem", letterSpacing: "0.18em", textTransform: "uppercase", color: "rgba(255,255,255,0.4)" }}>Ref: {error.digest}</p>
            )}
          </div>
        </main>
      </body>
    </html>
  );
}
