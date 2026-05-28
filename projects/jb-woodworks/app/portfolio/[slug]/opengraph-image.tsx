// Author: RKOJ-ELENO :: 2026-05-28
// Per-project OG image. Render the project title + category in the brand
// editorial layout when a portfolio item is shared on socials / Slack /
// iMessage. Edge runtime keeps the render fast (no DB hit; reads static
// portfolio.json bundle).
import { ImageResponse } from "next/og";
import { getPortfolioItem } from "@/lib/content";
import { SITE } from "@/lib/site";

export const runtime = "edge";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export function generateAlt({ params }: { params: { slug: string } }) {
  const item = getPortfolioItem(params.slug);
  return item ? `${item.title} — ${SITE.name}` : SITE.name;
}

export default async function OG({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const item = getPortfolioItem(slug);
  const title = item?.title ?? SITE.name;
  const cat = item?.category ?? "Portfolio";
  const sub = item?.subcategory;
  const blurb = item?.blurb ?? SITE.tagline;

  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          background: "linear-gradient(135deg, #050505 0%, #0d0d0d 55%, #1a1305 100%)",
          color: "#f4ead2",
          padding: "72px 80px",
          position: "relative"
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
        <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
          <div
            style={{
              fontSize: 22,
              color: "#c9a84c",
              letterSpacing: 9,
              textTransform: "uppercase",
              display: "flex",
              alignItems: "center",
              gap: 16
            }}
          >
            <span style={{ width: 40, height: 1, background: "#c9a84c" }} />
            {cat}
            {sub ? ` · ${sub}` : ""}
          </div>
          <div
            style={{
              fontSize: 92,
              fontWeight: 700,
              fontStyle: "italic",
              fontFamily: "serif",
              color: "#ffffff",
              lineHeight: 1.05,
              letterSpacing: -2,
              maxWidth: 1040
            }}
          >
            {title}.
          </div>
          <div
            style={{
              fontSize: 28,
              color: "rgba(244,234,210,0.78)",
              lineHeight: 1.45,
              maxWidth: 980,
              marginTop: 12
            }}
          >
            {blurb}
          </div>
        </div>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-end",
            color: "#c9a84c",
            fontSize: 24,
            letterSpacing: 6,
            textTransform: "uppercase"
          }}
        >
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <span style={{ fontFamily: "serif", fontStyle: "italic", letterSpacing: -2, color: "#ffffff", fontSize: 56 }}>
              JB Woodworks
            </span>
            <span style={{ color: "rgba(244,234,210,0.55)", fontSize: 18, letterSpacing: 4 }}>
              Orlando, FL — Est. 2019
            </span>
          </div>
          <span>jbwoodworks.co</span>
        </div>
      </div>
    ),
    { ...size }
  );
}
