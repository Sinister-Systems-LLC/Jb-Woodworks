// Author: RKOJ-ELENO :: 2026-05-23
import Link from "next/link";
import { Hero } from "@/components/sections/hero";
import { Marquee } from "@/components/sections/marquee";
import { ServicesList } from "@/components/sections/services-list";
import { NumbersBand } from "@/components/sections/numbers-band";
import { ProcessTimeline } from "@/components/sections/process-timeline";
import { PortfolioFeature } from "@/components/sections/portfolio-feature";
import { CommercialFeature } from "@/components/sections/commercial-feature";
import { FaqAccordion } from "@/components/sections/faq-accordion";
import { FaqTabs } from "@/components/sections/faq-tabs";
import { faqCategorized } from "@/lib/content/faq-categorized";
import { Icon } from "@/components/ui/icon";
import { services, portfolio, faq } from "@/lib/content";

export default function Home() {
  // Avoid duplication: CommercialFeature already showcases the New Balance +
  // SKU Snipers commercial work. The "Recent builds, up close" preview pulls
  // from non-commercial items so visitors see a fresh slice on the main page.
  const previewItems = portfolio
    .filter((p) => p.category !== "Commercial & Event Fabrication")
    .slice(0, 4);

  return (
    <>
      <Hero />

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
            </p>
            <h2 className="font-display text-[clamp(2.4rem,5.5vw,4.4rem)] leading-[1.05] text-white m-0 max-w-[820px]">
              Residential and commercial &mdash; <em className="text-gold">all built in-house.</em>
            </h2>
            <p className="mt-8 max-w-[640px] text-cream-50 text-[1rem] leading-[1.75]">
              Decks, docks, pergolas, custom furniture &mdash; plus <em className="text-gold not-italic font-semibold">branded displays, event builds, and specialty fabrication</em> for brands.
            </p>
          </div>

          <div className="mt-16">
            <ServicesList services={services} />
          </div>
        </div>
      </section>

      {/* Portfolio feature - editorial gallery. Different header treatment:
        right-aligned with a thin rule, the title small + the link big. */}
      <section id="portfolio-preview" className="py-24 sm:py-32 bg-ink relative overflow-hidden">
        <div aria-hidden className="absolute top-0 left-0 right-0 h-24 pointer-events-none" style={{ background: "linear-gradient(180deg, #0f0f0f, transparent)" }} />
        <div className="container-site relative">
          <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-8 mb-16 border-b border-line pb-10">
            <div className="lg:max-w-[420px]">
              <span className="font-mono text-[0.62rem] tracking-[0.42em] uppercase text-cream-30 block mb-3">
                <span className="tabular-nums">04</span> · Selected work · Portfolio
              </span>
              <p className="text-cream-50 text-[1rem] leading-[1.7]">
                A handful of recent builds, photographed in the field. Hover any card with a video for a quick preview.
              </p>
            </div>
            <div className="lg:text-right">
              <h2 className="font-display text-[clamp(2.6rem,6.2vw,5rem)] leading-[1] text-white m-0">
                <em className="not-italic text-gold">/</em>Recent.
              </h2>
              <Link href="/portfolio" className="link-arrow mt-4 inline-flex">
                See the full archive
                <Icon name="arrow-right" size={14} />
              </Link>
            </div>
          </div>

          <PortfolioFeature items={previewItems} />

          <div className="text-center mt-20">
            <Link href="/portfolio" className="btn btn-primary btn-large jbw-magnetic">View Full Portfolio</Link>
          </div>
        </div>
      </section>

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
            <p className="font-display italic text-gold text-[1rem] mb-3">Common questions</p>
            <h2 className="font-display text-[clamp(2.2rem,4.6vw,3.4rem)] leading-[1.05] m-0 text-white tracking-[0.18em] uppercase">
              FAQ
            </h2>
            <span aria-hidden className="block h-px w-16 mx-auto mt-5 bg-gradient-to-r from-transparent via-gold to-transparent" />
            <p className="mt-7 text-cream-50 text-[0.98rem] max-w-[540px] mx-auto leading-[1.75]">
              Pick a category. Anything we missed — <a href="tel:4075611453" className="text-gold underline underline-offset-4 hover:text-gold-light">call (407) 561-1453</a>.
            </p>
          </div>

          <FaqTabs categories={faqCategorized} initialTab="general" initialOpen={0} />
        </div>
      </section>

      {/* Big CTA band - asymmetric layout, NB cinematic shavings overlay */}
      <section className="py-24 sm:py-32 relative overflow-hidden" style={{ background: "linear-gradient(135deg, #c9a84c, #a8842f)" }}>
        {/* Nano Banana atmospheric — golden shavings mid-fall against black */}
        <div
          aria-hidden
          className="absolute inset-0 pointer-events-none bg-cover bg-center mix-blend-multiply"
          style={{ backgroundImage: "url(/img/generated/cta-shavings.png)", opacity: 0.35 }}
        />
        <div aria-hidden className="absolute inset-0 pointer-events-none" style={{ background: "radial-gradient(circle at 20% 50%, rgba(8,8,8,0.18), transparent 45%)" }} />
        <div aria-hidden className="absolute inset-0 pointer-events-none mix-blend-overlay" style={{ backgroundImage: "url(/img/generated/grain-texture.png)", backgroundSize: "cover", opacity: 0.10 }} />
        <div aria-hidden className="absolute top-0 left-0 right-0 h-px bg-ink/20" />
        <div aria-hidden className="absolute bottom-0 left-0 right-0 h-px bg-ink/20" />
        <div className="container-site relative">
          {/* Single-line manifesto across the band — different from the "first line. italic second." pattern */}
          <p className="font-mono text-[0.65rem] tracking-[0.42em] uppercase text-ink/60 mb-6 text-center">
            <span aria-hidden className="inline-block h-px w-10 bg-ink/40 align-middle mr-3" />
            One number · One shop · No salespeople
            <span aria-hidden className="inline-block h-px w-10 bg-ink/40 align-middle ml-3" />
          </p>
          <h2 className="text-ink text-center font-display text-[clamp(2.4rem,7vw,5.6rem)] leading-[0.95] m-0 max-w-[940px] mx-auto">
            Send us the space, get a number back the same day.
          </h2>
          <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
            <Link href="/contact" className="btn btn-large bg-ink text-white hover:bg-ink-3 transition-colors !px-12 jbw-magnetic">
              Start the quote
              <Icon name="arrow-right" size={16} className="ml-2" />
            </Link>
            <a href="tel:4075611453" className="inline-flex items-center gap-2 px-7 py-[15px] bg-transparent border border-ink/40 text-ink rounded-md font-bold text-[0.82rem] tracking-[0.08em] uppercase hover:bg-ink hover:text-white transition-colors jbw-magnetic">
              <Icon name="phone" size={15} />
              (407) 561-1453
            </a>
          </div>
        </div>
      </section>
    </>
  );
}
