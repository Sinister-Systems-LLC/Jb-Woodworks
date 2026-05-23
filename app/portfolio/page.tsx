// Author: RKOJ-ELENO :: 2026-05-23
import type { Metadata } from "next";
import { Suspense } from "react";
import { portfolio } from "@/lib/content";
import { PortfolioFilter } from "@/components/sections/portfolio-filter";

export const metadata: Metadata = {
  title: "Portfolio",
  description: "Pergolas, boat docks, custom pool tables, Trex decks, custom furniture - filter recent JB Woodworks builds by project type."
};

type Props = { searchParams: Promise<{ category?: string }> };

export default async function PortfolioPage({ searchParams }: Props) {
  const { category } = await searchParams;
  return (
    <>
      <section className="pt-40 pb-16 bg-gradient-to-b from-ink-2 to-ink border-b border-line relative overflow-hidden">
        <div aria-hidden className="absolute -top-24 -right-24 w-[400px] h-[400px] pointer-events-none" style={{ background: "radial-gradient(circle, rgba(201,168,76,0.10), transparent 70%)" }} />
        <div className="container-site relative">
          <span className="section-tag">Portfolio</span>
          <h1 className="mb-5">Our<br /><em>signature work.</em></h1>
          <p className="section-subheadline">
            Browse by project type, or scroll through everything. Each tile opens the full project gallery with video and photos.
          </p>
        </div>
      </section>

      <section className="py-24">
        <div className="container-site">
          <Suspense fallback={<div className="text-cream-30 text-[0.8rem] tracking-[0.22em] uppercase">Loading portfolio…</div>}>
            <PortfolioFilter items={portfolio} initialFilter={category ?? "all"} />
          </Suspense>
        </div>
      </section>
    </>
  );
}
