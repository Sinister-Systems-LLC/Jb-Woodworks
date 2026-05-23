// Author: RKOJ-ELENO :: 2026-05-23
import type { Metadata } from "next";
import { Suspense } from "react";
import Link from "next/link";
import { portfolio } from "@/lib/content";
import { PortfolioFilter } from "@/components/sections/portfolio-filter";
import { Icon } from "@/components/ui/icon";
import { SITE } from "@/lib/site";

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
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-gold text-[0.72rem] font-bold tracking-[0.18em] uppercase mb-6 hover:text-gold-light transition-colors group"
          >
            <Icon name="arrow-right" size={14} className="rotate-180 transition-transform duration-300 group-hover:-translate-x-1" />
            Back to home
          </Link>
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

      {/* Bottom CTA band — Get Free Quote + Contact Us */}
      <section className="py-20 sm:py-24 bg-ink-2 border-t border-line relative overflow-hidden">
        <div aria-hidden className="absolute -bottom-24 -left-24 w-[400px] h-[400px] pointer-events-none" style={{ background: "radial-gradient(circle, rgba(201,168,76,0.08), transparent 70%)" }} />
        <div aria-hidden className="absolute -top-24 -right-24 w-[400px] h-[400px] pointer-events-none" style={{ background: "radial-gradient(circle, rgba(201,168,76,0.08), transparent 70%)" }} />
        <div className="container-site relative text-center">
          <span className="section-tag mx-auto inline-block">Like what you see</span>
          <h2 className="mt-2 mb-5">Let&apos;s build<br /><em>something next.</em></h2>
          <p className="text-cream-50 text-[1rem] max-w-[560px] mx-auto mb-10">
            Free estimates. Honest pricing. Same-day response on weekdays. Tell us what you have in mind — we will reply with a real range before we even visit.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-4">
            <Link href="/contact" className="btn btn-primary btn-large jbw-magnetic">Get a Free Quote</Link>
            <a href={`tel:${SITE.phoneTel}`} className="btn btn-ghost btn-large jbw-magnetic">Call {SITE.phone}</a>
          </div>
        </div>
      </section>
    </>
  );
}
