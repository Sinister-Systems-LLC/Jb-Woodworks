// Author: RKOJ-ELENO :: 2026-05-23
import type { Metadata, Viewport } from "next";
import { DM_Serif_Display, Inter } from "next/font/google";
import "./globals.css";
import { Nav } from "@/components/sections/nav";
import { Footer } from "@/components/sections/footer";
import { Splash } from "@/components/ui/splash";
import { RouteProgress } from "@/components/ui/route-progress";
import { ScrollToTop } from "@/components/ui/scroll-to-top";
import { PageTransition } from "@/components/ui/page-transition";
import { SITE } from "@/lib/site";

const inter = Inter({ subsets: ["latin"], weight: ["300", "400", "500", "600", "700", "800", "900"], variable: "--font-sans", display: "swap" });
const display = DM_Serif_Display({ subsets: ["latin"], weight: "400", style: ["normal", "italic"], variable: "--font-display", display: "swap" });

export const metadata: Metadata = {
  metadataBase: new URL(SITE.url),
  title: { default: `${SITE.name} - Custom Woodworking and Construction`, template: `%s - ${SITE.name}` },
  description: `${SITE.tagline} Custom woodworking in Orlando, FL: decks, boat docks, pergolas, pool tables, and furniture.`,
  applicationName: SITE.name,
  authors: [{ name: "RKOJ-ELENO" }],
  openGraph: {
    type: "website",
    locale: "en_US",
    siteName: SITE.name,
    title: SITE.name,
    description: SITE.tagline,
    images: [{ url: "/img/og-image.svg" }]
  },
  twitter: { card: "summary_large_image", title: SITE.name, description: SITE.tagline, images: ["/img/og-image.svg"] },
  manifest: "/site.webmanifest",
  icons: {
    icon: [
      { url: "/img/favicon-32.png", sizes: "32x32", type: "image/png" },
      { url: "/img/favicon-16.png", sizes: "16x16", type: "image/png" },
      { url: "/img/favicon-192.png", sizes: "192x192", type: "image/png" },
      { url: "/img/favicon-512.png", sizes: "512x512", type: "image/png" }
    ],
    shortcut: ["/img/favicon.ico"],
    apple: [{ url: "/img/favicon-180.png", sizes: "180x180" }]
  },
  alternates: {
    canonical: SITE.url,
    types: { "application/rss+xml": "/rss.xml" }
  }
};

export const viewport: Viewport = {
  themeColor: "#080808",
  width: "device-width",
  initialScale: 1
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const ld = {
    "@context": "https://schema.org",
    "@type": "LocalBusiness",
    "@id": `${SITE.url}/#business`,
    name: SITE.name,
    description: `${SITE.tagline} ${SITE.subtagline}`,
    telephone: SITE.phone,
    email: SITE.email,
    address: { "@type": "PostalAddress", addressLocality: "Orlando", addressRegion: "FL", addressCountry: "US" },
    areaServed: SITE.serviceArea,
    priceRange: "$$-$$$$",
    sameAs: Object.values(SITE.socials)
  };

  return (
    <html lang="en" className={`${inter.variable} ${display.variable}`}>
      <body>
        <a href="#main" className="skip-link">Skip to main content</a>
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(ld) }} />
        <Splash />
        <RouteProgress />
        <Nav />
        <main id="main">
          <PageTransition>{children}</PageTransition>
        </main>
        <Footer />
        <ScrollToTop />
        {/* Sitewide subtle film grain — fixed overlay, very low opacity */}
        <div aria-hidden className="jbw-grain-overlay" />
      </body>
    </html>
  );
}
