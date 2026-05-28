// Author: RKOJ-ELENO :: 2026-05-23
// JB Woodworks - typed content loaders. Static JSON, no runtime DB hits for marketing copy.

import servicesData from "./services.json";
import portfolioData from "./portfolio.json";
import faqData from "./faq.json";
import heroData from "./hero_media.json";

export type ServiceIcon =
  | "dock" | "deck" | "table" | "trim" | "pergola" | "wrench";

/** Optional sub-classification on a portfolio item for finer-grained
 *  filtering inside a category. Currently used by Commercial & Event
 *  Fabrication to differentiate Event Builds / Custom Displays / Commercial
 *  Fabrication on the portfolio page. */
export type PortfolioSubcategory =
  | "Event Builds"
  | "Custom Displays"
  | "Commercial Fabrication";

export type Service = {
  slug: string;
  title: string;
  blurb: string;
  details: string;
  icon: ServiceIcon;
  /** Where the "View" link on the home services list takes the visitor.
   *  Direct portfolio item, filtered portfolio listing, or a contact prefill
   *  if no examples exist yet. */
  exampleHref?: string;
  /** Label for the right-edge CTA. "See examples" when exampleHref points at
   *  the portfolio, "Get a quote" when it points at /contact. Defaults to
   *  "See examples". */
  ctaLabel?: string;
};

export type PortfolioMedia =
  | { type: "video"; src: string; poster: string }
  | { type: "raw-image"; src: string }
  | {
      type: "before-after";
      before: string;
      after: string;
      /** Are the `before` / `after` paths raw images in /img/projects (true)
       *  or optimized posters under /media (false)? Defaults to true for both. */
      beforeRaw?: boolean;
      afterRaw?: boolean;
      caption?: string;
    };

export type PortfolioItem = {
  slug: string;
  title: string;
  category: string;
  /** Optional finer-grained type within the parent category. */
  subcategory?: PortfolioSubcategory;
  blurb: string;
  cover: string;
  is_raw_cover?: boolean;
  media: PortfolioMedia[];
  /** Optional editorial metadata rendered on the detail page + folded into the
   *  per-project JSON-LD. Backfill incrementally; missing keys render nothing. */
  meta?: {
    /** Year the build completed (e.g. "2024"). */
    year?: string;
    /** Headline materials, comma-separated for a single line ("Ipe + 316 stainless"). */
    materials?: string;
    /** Where the install happened, neighborhood / city level only. */
    location?: string;
    /** Rough build duration ("4 weeks", "2 days"). */
    duration?: string;
  };
};

export type Faq = { q: string; a: string };

export type HeroSlide =
  | { type: "video"; src: string; poster: string; duration_ms: number }
  | { type: "image"; src: string; duration_ms: number; poster?: string };

export const services: Service[] = servicesData as Service[];
export const portfolio: PortfolioItem[] = portfolioData as PortfolioItem[];
export const faq: Faq[] = faqData as Faq[];
export const hero: HeroSlide[] = heroData as HeroSlide[];

export function getPortfolioItem(slug: string): PortfolioItem | undefined {
  return portfolio.find((p) => p.slug === slug);
}

export function portfolioCategories(): string[] {
  return Array.from(new Set(portfolio.map((p) => p.category)));
}

export function categorySlug(cat: string): string {
  // URL-safe slug: lowercase, strip every non-alphanumeric (handles `&`, `+`,
  // punctuation, etc), collapse runs of dashes, trim leading/trailing dashes.
  return cat
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

export function mediaUrl(rel: string, raw = false): string {
  // raw originals live in public/img/projects (real files, copied from canonical
  // Jah Images at scaffold time). Optimized H.264 + posters live at public/media.
  return raw ? `/img/projects/${rel}` : `/media/${rel}`;
}
