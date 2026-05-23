// Author: RKOJ-ELENO :: 2026-05-23
import Link from "next/link";
import { Hero } from "@/components/sections/hero";
import { Marquee } from "@/components/sections/marquee";
import { ServicesList } from "@/components/sections/services-list";
import { NumbersBand } from "@/components/sections/numbers-band";
import { ProcessTimeline } from "@/components/sections/process-timeline";
import { PortfolioFeature } from "@/components/sections/portfolio-feature";
import { FaqAccordion } from "@/components/sections/faq-accordion";
import { Reveal } from "@/components/ui/reveal";
import { Icon } from "@/components/ui/icon";
import { services, portfolio, faq } from "@/lib/content";

export default function Home() {
  return (
    <>
      <Hero />

      <Marquee />

      <NumbersBand />

      {/* Services - editorial numbered list */}
      <section id="services" className="py-24 sm:py-32 bg-ink relative">
        <div aria-hidden className="absolute top-10 left-10 w-px h-32 bg-gradient-to-b from-gold-dim to-transparent" />
        <div className="container-site">
          <div className="grid lg:grid-cols-[1fr_2fr] gap-12 mb-12 items-end">
            <div>
              <span className="section-tag">What We Do</span>
              <h2 className="m-0">
                Six lanes.<br /><em>One shop.</em>
              </h2>
            </div>
            <p className="text-cream-50 text-[1rem] leading-[1.75] max-w-[560px] lg:justify-self-end">
              We are deliberate about what we take on. Pick a lane to start the conversation - or just call.
              No upsells, no salespeople, no "premium tier."
            </p>
          </div>

          <ServicesList services={services} />
        </div>
      </section>

      {/* Portfolio feature - alternating large cards */}
      <section id="portfolio-preview" className="py-24 sm:py-32 bg-ink-2 relative">
        <div className="container-site">
          <div className="grid lg:grid-cols-[1fr_auto] gap-8 items-end mb-16">
            <div>
              <span className="section-tag">Selected Work</span>
              <h2 className="m-0">
                Recent builds,<br /><em>up close.</em>
              </h2>
            </div>
            <Link href="/portfolio" className="link-arrow self-end">
              See the full portfolio
              <Icon name="arrow-right" size={14} />
            </Link>
          </div>

          <PortfolioFeature items={portfolio.slice(0, 4)} />

          <div className="text-center mt-20">
            <Link href="/portfolio" className="btn btn-primary btn-large">View Full Portfolio</Link>
          </div>
        </div>
      </section>

      {/* Process timeline */}
      <ProcessTimeline />

      {/* FAQ - editorial accordion */}
      <section id="faq-preview" className="py-24 sm:py-28 bg-ink-2 relative overflow-hidden">
        <div aria-hidden className="absolute -top-32 -left-32 w-[420px] h-[420px] pointer-events-none" style={{ background: "radial-gradient(circle, rgba(201,168,76,0.08), transparent 70%)" }} />
        <div aria-hidden className="absolute -bottom-32 -right-32 w-[420px] h-[420px] pointer-events-none" style={{ background: "radial-gradient(circle, rgba(201,168,76,0.06), transparent 70%)" }} />
        <div className="container-site relative">
          <div className="grid lg:grid-cols-[1fr_1.4fr] gap-10 mb-14 items-end">
            <div>
              <span className="section-tag">Questions</span>
              <h2 className="m-0">
                Everything you<br /><em>need to know.</em>
              </h2>
            </div>
            <div className="lg:justify-self-end max-w-[560px]">
              <p className="text-cream-50 text-[1rem] leading-[1.75]">
                The short answers most people need before reaching out. Tap any question to open it. Anything we missed — <a href="tel:4075611453" className="text-gold underline-offset-4 hover:underline">call us</a>.
              </p>
              <p className="mt-3 text-cream-30 text-[0.65rem] tracking-[0.32em] uppercase font-bold">
                {faq.length} answers · &lt; 60 sec read
              </p>
            </div>
          </div>

          <div className="max-w-[960px] mx-auto bg-ink-3/60 backdrop-blur-sm border border-line rounded-2xl overflow-hidden">
            <FaqAccordion items={faq} initialOpen={0} />
          </div>
        </div>
      </section>

      {/* Big CTA band - asymmetric layout */}
      <section className="py-24 sm:py-32 relative overflow-hidden" style={{ background: "linear-gradient(135deg, #c9a84c, #a8842f)" }}>
        <div aria-hidden className="absolute inset-0 pointer-events-none" style={{ background: "radial-gradient(circle at 20% 50%, rgba(8,8,8,0.18), transparent 45%)" }} />
        <div aria-hidden className="absolute top-0 left-0 right-0 h-px bg-ink/20" />
        <div aria-hidden className="absolute bottom-0 left-0 right-0 h-px bg-ink/20" />
        <div className="container-site relative grid lg:grid-cols-[2fr_1fr] gap-12 items-center">
          <div>
            <p className="text-ink/60 text-[0.7rem] font-bold tracking-[0.28em] uppercase mb-4">Step 01</p>
            <h2 className="text-ink text-[clamp(2.5rem,6vw,4.5rem)] leading-[1.05] mb-4">
              Ready to start?<br /><em className="text-ink/85">Let&apos;s talk.</em>
            </h2>
            <p className="text-ink/75 text-[1.1rem] max-w-[560px]">
              Free estimates. Licensed and insured. We will get back to you within one business day to discuss your vision.
            </p>
          </div>
          <div className="flex flex-col gap-3 lg:items-end">
            <Link href="/contact" className="btn btn-large bg-ink text-white hover:bg-ink-3 transition-colors !px-12">
              Get a Quote
              <Ico