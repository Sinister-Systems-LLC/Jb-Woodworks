// Author: RKOJ-ELENO :: 2026-05-23
import type { MetadataRoute } from "next";
import { statSync } from "node:fs";
import { join } from "node:path";
import { SITE } from "@/lib/site";
import { portfolio } from "@/lib/content";

// Read mtime of a content file; fall back to build-time date on any error so
// the sitemap never breaks just because a JSON path moved.
function mtimeOf(...relParts: string[]): Date {
  try {
    return statSync(join(process.cwd(), ...relParts)).mtime;
  } catch {
    return new Date();
  }
}

export default function sitemap(): MetadataRoute.Sitemap {
  const heroM = mtimeOf("lib", "content", "hero_media.json");
  const servicesM = mtimeOf("lib", "content", "services.json");
  const portfolioM = mtimeOf("lib", "content", "portfolio.json");
  const faqM = mtimeOf("lib", "content", "faq.json");
  const legalM = mtimeOf("lib", "legal.ts");

  // Root reflects the most-recent piece of public-facing content.
  const rootM = new Date(Math.max(heroM.getTime(), servicesM.getTime(), portfolioM.getTime()));

  const fixed: MetadataRoute.Sitemap = [
    { url: `${SITE.url}/`,                  lastModified: rootM,      changeFrequency: "monthly",  priority: 1.0 },
    { url: `${SITE.url}/services`,          lastModified: servicesM,  changeFrequency: "monthly",  priority: 0.9 },
    { url: `${SITE.url}/portfolio`,         lastModified: portfolioM, changeFrequency: "monthly",  priority: 0.9 },
    { url: `${SITE.url}/about`,             lastModified: faqM,       changeFrequency: "yearly",   priority: 0.7 },
    { url: `${SITE.url}/contact`,           lastModified: servicesM,  changeFrequency: "yearly",   priority: 0.8 }
  ];

  const items: MetadataRoute.Sitemap = portfolio.map((p) => {
    // Cover lives in /img/projects/ when raw, /media/ when from the optimized pipeline.
    const coverParts = p.is_raw_cover
      ? ["public", "img", "projects", ...p.cover.split("/")]
      : ["public", "media", ...p.cover.split("/")];
    return {
      url: `${SITE.url}/portfolio/${p.slug}`,
      lastModified: mtimeOf(...coverParts),
      changeFrequency: "yearly" as const,
      priority: 0.7
    };
  });

  const legal: MetadataRoute.Sitemap = [
    { url: `${SITE.url}/legal`,               lastModified: legalM, changeFrequency: "yearly", priority: 0.3 },
    { url: `${SITE.url}/legal/privacy`,       lastModified: legalM, changeFrequency: "yearly", priority: 0.3 },
    { url: `${SITE.url}/legal/terms`,         lastModified: legalM, changeFrequency: "yearly", priority: 0.3 },
    { url: `${SITE.url}/legal/cookies`,       lastModified: legalM, changeFrequency: "yearly", priority: 0.3 },
    { url: `${SITE.url}/legal/accessibility`, lastModified: legalM, changeFrequency: "yearly", priority: 0.3 }
  ];

  return [...fixed, ...items, ...legal];
}
