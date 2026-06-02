// Author: RKOJ-ELENO :: 2026-05-23
import Link from "next/link";
import { Hero } from "@/components/sections/hero";
import { Marquee } from "@/components/sections/marquee";
import { ServicesList } from "@/components/sections/services-list";
import { NumbersBand } from "@/components/sections/numbers-band";
import { ProcessTimeline } from "@/components/sections/process-timeline";
import { PortfolioFeature } from "@/components/sections/portfolio-feature";
import { CommercialFeature } from "@/components/sections/commercial-feature";
import { FaqTabs } from "@/components/sections/faq-tabs";
// D-series Lane F mirror — cycling banner + JP-aesthetic separators (brand gold).
import { CyclingBanner } from "@/components/sections/CyclingBanner";
import { SectionSeparator } from "@/components/landing/SectionSeparator";
import { faqCategorized } from "@/lib/content/faq-categorized";
import { Icon } from "@/components/ui/icon";
import { services, portfolio } from "@/lib/content";

export default function Home() {
  // Recent work preview: lead with the New Balance × Foot Locker reveal (per
  // operator, the headline brand build belongs in Recent work, not buried in
  // the Commercial section), then alternate with high-impact residential
  // builds so the editorial cadence stays varied. Falls back gracefully if the
  // NB entry is ever renamed/removed.
  const newBalance = portfolio.find((p) => p.slug === "new-balance-reveal");
  const residential = portfolio.filter(
    (p) => p.category !== "Commercial & Event Fabrication"
  );
  const previewItems = (
    newBalance ? [newBalance, ...residential] : residential
  ).slice(0, 4);

  return (
    <>
      <Hero />

      {/* landonorris-style half-stripe — single thin horizontal accent in brand gold. */}
      <div aria-hidden className="relative h-[2px] w-full overflow-hidden bg-ink">
        <div className="absolute inset-y-0 left-0 w-1/2 bg-gradient-to-r from-transparent via-gold/70 to-gold" />
      </div>

      {/* D-series D5 mirror — cycling banner between Hero and Marquee. */}
      <CyclingBanner />

      <Marquee />

      <NumbersBand />

      {/* Commercial builds — moved above What We Do per operator. Anchored on a real retail display project. */}
      <CommercialFeature />

      {/* Smooth transition strip — CommercialFeature dark → Services dark */}
      <div aria-hidden className="h-16 bg-gradient-to-b from-ink to-ink-2" />

      {/* Services - typographic chapter feel: huge oversized mono label
        + condensed manifesto. Breaks from the "line1. italic line2." pattern. */}
      <section id="services" className="py-24 sm:py-36 bg-ink-2 relative overflow-hidden">
        {/* Nano Banana atmospheric — walnut tabletop. Lower opacity, right-edge fade for variety. */}
        <div
          aria-hidden
          className="absolute inset-y-0 right-0 w-[50%] pointer-events-none bg-cover bg-center"
          style={{ backgroundImage: "url(/img/generated/services-accent.png)", opacity: 0.32 }}
        />
        <div aria-hidden className="absolute inset-y-0 right-0 w-[50%] pointer-events-none" style={{ background: "linear-gradient(90deg, rgba(15,15,15,0.95) 0%, rgba(15,15,15,0.55) 35%, rgba(15,15,15,0.8) 100%)" }} />
        <div aria-hidden className="absolute inset-0 pointer-events-none mix-blend-overlay" style={{ backgroundImage: "url(/img/generated/grain-texture.png)", backgroundSize: "cover", opacity: 0.05 }} />

        <div className="container-site relative">
          {/* Vertical chapter mark — left rail */}
          <div className="hidden md:flex absolute top-0 left-7 bottom-0 items-start pt-2 pointer-events-none">
            <div className="flex items-baseline gap-3 -rotate-90 origin-top-left translate-x-2 mt-32 whitespace-nowrap">
              <span className="font-mono text-[0.6rem] tracking-[0.45em] uppercase text-gold/60">Chapter 02</span>
              <span className="h-px w-8 bg-gold/40" aria-hidden />
              <span className="font-mono text-[0.55rem] tracking-[0.3em] uppercase text-cream-30">Services</span>
            </div>
          </div>

          <div className="md:pl-16">
            {/* Eyebrow + giant statement (no italic kicker, intentionally different) */}
            <p className="font-mono text-[0.65rem] tracking-[0.42em] uppercase text-gold mb-8">
              <span className="tabular-nums">{String(services.length).padStart(2, "0")}</span>
              <span className="mx-3 text-cream-30">·</span>
              <span>What we build</span>
              <span className="mx-3 text-cream-30">·</span>
              <span className="text-cream-30">Custom-focused</span>
            </p>
            <h2 className="font-display text-[clamp(2.4rem,5.5vw,4.4rem)] leading-[1.05] text-white m-0 max-w-[920px]">
              Residential craftsmanship and commercial fabrication &mdash; <em className="text-gold">all built custom, in-house.</em>
            </h2>
            <div className="mt-8 flex flex-col sm:flex-row gap-4 sm:gap-12 items-start max-w-[820px] text-cream-50 text-[0.95rem] leading-[1.8]">
              <p className="flex-1">
                Decks, docks, pergolas, outdoor living, hardwoods, and custom furniture &mdash; plus <em className="text-gold not-italic font-semibold">custom fabrication, branded displays, commercial &amp; event builds, and specialty installations</em> for brands and retailers.
              </p>
              <p className="flex-1 italic font-display">
                Premium. Modern. Made for your space &mdash; not pulled from a catalog.
              </p>
            </div>
          </div>

          <div className="mt-16">
            <ServicesList services={services} />
          </div>
        </div>
      </section>

      {/* Portfolio feature — operator asked for a redo. Header now sits on a
          single editorial baseline: massive serif "Recent work." running left,
          a thin gold seam, and the small archive link tucked on the right. No
          number badge, no two-column eyebrow + sub-paragraph. */}
      <section id="portfolio-preview" className="py-24 sm:py-32 bg-ink relative overflow-hidden">
        <div aria-hidden className="absolute top-0 left-0 right-0 h-24 pointer-events-none" style={{ background: "linear-gradient(180deg, #0f0f0f, transparent)" }} />
        <div className="container-site relative">
          <div className="mb-14 flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
            <h2 className="m-0 font-display text-[clamp(2.6rem,7vw,5.4rem)] leading-[0.9] text-white">
              Recent <em className="text-gold">work.</em>
            </h2>
            <Link
              href="/portfolio"
              className="self-start sm:self-end inline-flex items-center gap-2 text-[0.72rem] tracking-[0.3em] uppercase font-semibold text-cream-50 hover:text-gold transition-colors"
            >
              Open the archive
              <Icon name="arrow-right" size={14} />
            </Link>
          </div>
          <div aria-hidden className="h-px w-full mb-16 bg-gradient-to-r from-transparent via-gold-dim/60 to-transparent" />

          <PortfolioFeature items={previewItems} />

          <div className="text-center mt-20">
            <Link href="/portfolio" className="link-arrow text-[0.78rem] tracking-[0.3em] uppercase text-cream-50 hover:text-gold transition-colors inline-flex items-center gap-2">
              View full portfolio
              <Icon name="arrow-right" size={14} />
            </Link>
          </div>
        </div>
      </section>

      {/* D-series D8 mirror — JP-aesthetic separator (asanoha, brand gold). */}
      <div className="bg-ink">
        <SectionSeparator variant="asanoha" label="process" />
      </div>

      {/* Process timeline */}
      <ProcessTimeline />

      {/* FAQ — tabbed accordion. Italic gold eyebrow, large letter-spaced
        title with gold rule under it, pill bar of categories, accordion list.
        Pattern: editorial-magazine FAQ. */}
      <section id="faq-preview" className="py-24 sm:py-28 bg-ink-2 relative overflow-hidden">
        <div aria-hidden className="absolute -top-32 -left-32 w-[420px] h-[420px] pointer-events-none" style={{ background: "radial-gradient(circle, rgba(201,168,76,0.08), transparent 70%)" }} />
        <div aria-hidden className="absolute -bottom-32 -right-32 w-[420px] h-[420px] pointer-events-none" style={{ background: "radial-gradient(circle, rgba(201,168,76,0.06), transparent 70%)" }} />
        <div className="container-site relative max-w-[920px]">
          <div className="text-center mb-12">
            <h2 className="font-display text-[clamp(2.4rem,5.2vw,3.8rem)] leading-[1.05] m-0 text-white tracking-[0.16em] uppercase">
              FAQ
            </h2>
            <span aria-hidden className="block h-px w-16 mx-auto mt-5 bg-gradient-to-r from-transparent via-gold to-transparent" />
          </div>

          <FaqTabs categories={faqCategorized} initialTab="general" initialOpen={0} />
        </div>
      </section>

      {/* D-series D8 mirror — JP-aesthetic separator (torii, brand gold) before CTA. */}
      <div className="bg-ink-2">
        <SectionSeparator variant="torii" label="contact" />
      </div>

      {/* Closing CTA — operator asked for a fresh background. Drops the bright
          gold gradient + shavings overlay; goes inverse instead: deep ink with
          a single warm spotlight pulled to the lower-right and an animated gold
          underline rule under the headline. Reads quieter, feels more cinematic. */}
      <section className="py-24 sm:py-32 relative overflow-hidden bg-[#080808]">
        <div aria-hidden className="absolute inset-0 pointer-events-none" style={{
          background: "radial-gradient(120% 80% at 78% 90%, rgba(201,168,76,0.30), rgba(201,168,76,0.06) 30%, transparent 60%)"
        }} />
        <div aria-hidden className="absolute inset-0 pointer-events-none" style={{
          background: "linear-gradient(180deg, rgba(8,8,8,0.95) 0%, transparent 25%, transparent 75%, rgba(8,8,8,0.95) 100%)"
        }} />
        <div aria-hidden className="absolute inset-0 pointer-events-none mix-blend-overlay" style={{ backgroundImage: "url(/img/generated/grain-texture.png)", backgroundSize: "cover", opacity: 0.08 }} />
        <div aria-hidden className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-gold-dim/60 to-transparent" />
        <div aria-hidden className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-gold-dim/40 to-transparent" />
        <div className="container-site relative">
          <p className="font-mono text-[0.62rem] tracking-[0.45em] uppercase text-cream-30 mb-6 text-center">
            <span aria-hidden className="inline-block h-px w-10 bg-gold-dim/50 align-middle mr-3" />
            One number · One shop · No salespeople
            <span aria-hidden className="inline-block h-px w-10 bg-gold-dim/50 align-middle ml-3" />
          </p>
          <h2 className="text-white text-center font-display text-[clamp(2.4rem,7vw,5.6rem)] leading-[0.95] m-0 max-w-[940px] mx-auto">
            Send us the space, get a number back <em className="text-gold">the same day.</em>
          </h2>
          <div aria-hidden className="mx-auto mt-8 h-px w-32 bg-gradient-to-r from-transparent via-gold to-transparent" />
          <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
            <Link href="/contact" className="btn btn-large bg-gold text-ink hover:bg-gold-light transition-colors !px-12 jbw-magnetic">
              Start the quote
              <Icon name="arrow-right" size={16} className="ml-2" />
            </Link>
            <a href="tel:4075611453" className="inline-flex items-center gap-2 px-7 py-[15px] bg-transparent border border-cream-30/50 text-cream-50 rounded-md font-bold text-[0.82rem] tracking-[0.08em] uppercase hover:border-gold hover:text-gold transition-colors jbw-magnetic">
              <Icon name="phone" size={15} />
              (407) 561-1453
            </a>
          </div>
        </div>
      </section>
    </>
  );
}
