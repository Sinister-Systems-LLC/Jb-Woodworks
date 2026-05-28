// Author: RKOJ-ELENO :: 2026-05-28
// Site-wide default OG image — gold wordmark on inked canvas.
// Replaces the static /img/og-image.svg fallback set in app/layout.tsx for
// the canonical homepage share card. Per-page overrides live next to their
// route (e.g. app/portfolio/[slug]/opengraph-image.tsx).
import { ImageResponse } from "next/og";
import { SITE } from "@/lib/site";

export const runtime = "edge";
export const alt = `${SITE.name} — ${SITE.tagline}`;
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function OG() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
          background: "linear-gradient(135deg, #050505 0%, #0d0d0d 60%, #161109 100%)",
          color: "#f4ead2",
          fontFamily: "serif",
          padding: 80
        }}
      >
        <div
          style={{
            position: "absolute",
            inset: 24,
            border: "1px solid rgba(201,168,76,0.32)",
            borderRadius: 8
          }}
        />
        <div
          style={{
            fontSize: 26,
            letterSpacing: 18,
            color: "#c9a84c",
            textTransform: "uppercase",
            marginBottom: 36
          }}
        >
          Est. 2019 — Orlando FL
        </div>
        <div
          style={{
            fontSize: 168,
            fontWeight: 900,
            fontStyle: "italic",
            letterSpacing: -6,
            color: "#ffffff",
            lineHeight: 1
          }}
        >
          JB Woodworks
        </div>
        <div
          style={{
            marginTop: 36,
            fontSize: 32,
            color: "rgba(244,234,210,0.78)",
            fontStyle: "italic",
            textAlign: "center",
            maxWidth: 880
          }}
        >
          Custom decks, docks, furniture, and outdoor builds.
        </div>
        <div
          style={{
            position: "absolute",
            bottom: 60,
            display: "flex",
            alignItems: "center",
            gap: 18,
            fontSize: 22,
            color: "#c9a84c",
            textTransform: "uppercase",
            letterSpacing: 6
          }}
        >
          <span style={{ width: 60, height: 1, background: "#c9a84c" }} />
          jbwoodworks.co
          <span style={{ width: 60, height: 1, background: "#c9a84c" }} />
        </div>
      </div>
    ),
    { ...size }
  );
}
