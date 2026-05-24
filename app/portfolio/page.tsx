// Author: RKOJ-ELENO :: 2026-05-23
import type { Metadata } from "next";
import { Suspense } from "react";
import Link from "next/link";
import Image from "next/image";
import { portfolio } from "@/lib/content";
import { PortfolioFilter } from "@/components/sections/portfolio-filter";
import { Icon } from "@/components/ui/icon";
import { BackLink } from "@/components/ui/back-link";
import { SITE } from "@/lib/site";

export const metadata: Metadata = {
  title: "Portfolio",
  description: "Pergolas, boat docks, custom pool tables, Trex decks, custom furniture - filter recent JB Woodworks builds by project type."
};

type Props = { searchParams: Promise<{ category?: string }> };

export default async function PortfolioPage({ searchParams }: Props) {
  const { category } = await searchParams;

  // Stats for the eyebrow strip — derived from real content, not hand-typed.
  const projectCount = portfolio.length;
  const categoryCount = new Set(portfolio.map((p) => p.category)).size;

  return (
    <>
      {/* Editorial header — vertical chapter rail, atmospheric backdrop, 2-column
          headline + featured bento. Replaces the flat left-aligned block. */}
      <section className="relative overflow-hidden bg-ink border-b border-line">
        {/* Atmospheric backdrop — walnut grain at low opacity, right-edge-anchored
            so the headline column stays legible on the left. */}
        <div
          aria-hidden
          className="absolute inset-y-0 right-0 w-[55%] pointer-events-none bg-cover bg-center"
          style={{ backgroundImage: "url(/img/generated/services-accent.png)", opacity: 0.18 }}
        />
        <div aria-hidden className="absolute inset-y-0 right-0 w-[55%] pointer-events-none" style={{ background: "linear-gradient(90deg, #080808 0%, rgba(8,8,8,0.55) 35%, rgba(8,8,8,0.85) 100%)" }} />
        <div aria-hidden className="absolute inset-0 pointer-events-none mix-blend-overlay" style={{ backgroundImage: "url(/img/generated/grain-texture.png)", backgroundSize: "cover", opacity: 0.05 }} />
        <div aria-hidden className="absolute -top-24 -right-24 w-[500px] h-[500px] pointer-events-none" style={{ background: "radial-gradient(circle, rgba(201,168,76,0.10), transparent 70%)" }} />

        {/* Vertical chapter rail — matches the home services Chapter 02 detail */}
        <div className="hidden md:flex absolute top-0 left-7 bottom-0 items-start pt-40 pointer-events-none">
          <div className="flex items-baseline gap-3 -rotate-90 origin-top-left translate-x-2 mt-16 whitespace-nowrap">
            <span className="font-mono text-[0.6rem] tracking-[0.45em] uppercase text-gold/60">Chapter 03</span>
            <span className="h-px w-8 bg-gold/40" aria-hidden />
            <span className="font-mono text-[0.55rem] tracking-[0.3em] uppercase text-cream-30">Portfolio</span>
          </div>
        </div>

        <div className="container-site relative pt-32 pb-20 md:pt-40 md:pb-24 md:pl-16">
          <BackLink href="/" label="Back to home" section="Portfolio" />

          {/* Editorial 2-column: headline left, bento right (desktop) */}
          <div className="grid lg:grid-cols-[1.15fr_1fr] gap-12 lg:gap-16 items-start">
            {/* Left column — headline + manifesto */}
            <div>
              <p className="font-mono text-[0.65rem] tracking-[0.42em] uppercase text-gold mb-7">
                <span className="tabular-nums">{String(projectCount).padStart(2, "0")}</span>
                <span className="mx-3 text-cream-30">·</span>
                <span>Your eyes here</span>
              </p>

              <h1 className="font-display text-[clamp(2.8rem,7vw,5.6rem)] leading-[0.98] text-white m-0">
                Ten years<br />
                of builds.<br />
                <em className="text-gold">Pick a lane.</em>
              </h1>

              <div className="mt-8 max-w-[520px]">
                <p className="text-cream-50 text-[1.05rem] leading-[1.75]">
                  Pergolas, docks, pool tables, decks, commercial fit-outs, custom furniture.
                  Every tile opens the full gallery — video, raw photography, project notes.
                </p>
              </div>

              {/* Stats strip — real numbers from real content */}
              <dl className="mt-10 grid grid-cols-3 gap-4 max-w-[480px]">
                <div className="border-l-2 border-gold/40 pl-4">
                  <dt className="text-cream-30 font-mono text-[0.55rem] tracking-[0.3em] uppercase mb-1">Projects</dt>
                  <dd className="font-display text-[2rem] text-white leading-none tabular-nums">{projectCount}</dd>
                </div>
                <div className="border-l-2 border-gold/40 pl-4">
                  <dt className="text-cream-30 font-mono text-[0.55rem] tracking-[0.3em] uppercase mb-1">Lanes</dt>
                  <dd className="font-display text-[2rem] text-white leading-none tabular-nums">{categoryCount}</dd>
                </div>
                <div className="border-l-2 border-gold/40 pl-4">
                  <dt className="text-cream-30 font-mono text-[0.55rem] tracking-[0.3em] uppercase mb-1">Since</dt>
                  <dd className="font-display text-[2rem] text-white leading-none tabular-nums">2025</dd>
                </div>
              </dl>
            </div>

            {/* Right column — bento of 3 feature images. Hidden on mobile to keep
                hero short, restored at lg. */}
            <div className="hidden lg:grid grid-cols-2 gap-3 self-stretch">
              {portfolio.slice(0, 3).map((p, idx) => {
                const src = p.is_raw_cover ? `/img/projects/${p.cover}` : `/media/${p.cover}`;
                const isBig = idx === 0;
                return (
                  <Link
                    key={p.slug}
                    href={`/portfolio/${p.slug}`}
                    className={`group relative overflow-hidden rounded-xl border border-line bg-ink-3 ${isBig ? "row-span-2 aspect-[3/4]" : "aspect-[4/3]"}`}
                  >
                    <Image
                      src={encodeURI(src)}
                      alt={p.title}
                      fill
                      sizes="(max-width: 1024px) 100vw, 30vw"
                      className="object-cover transition-transform duration-700 group-hover:scale-105"
                      priority={isBig}
                    />
                    <div aria-hidden className="absolute inset-0 pointer-events-none" style={{ background: "linear-gradient(180deg, transparent 50%, rgba(8,8,8,0.85) 100%)" }} />
                    <div className="absolute bottom-3 left-3 right-3">
                      <span className="font-mono text-[0.55rem] tracking-[0.3em] uppercase text-gold block mb-1">{p.category}</span>
                      <span className="font-display text-[0.95rem] text-white leading-tight block truncate">{p.title}</span>
                    </div>
                  </Link>
                );
              })}
            </div>
          </div>
        </div>

        {/* Bottom rule — separates header from filter section */}
        <div className="container-site relative">
          <div className="h-px bg-gradient-to-r from-transparent via-gold/30 to-transparent" />
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
