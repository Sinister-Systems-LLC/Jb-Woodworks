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
import { Icon } from "@/components/ui/icon";
import { services, portfolio, faq } from "@/lib/content";

export default function Home() {
  // Avoid duplication: CommercialFeature already showcases New Balance + the
  // category. The "Recent builds, up close" preview pulls from non-commercial
  // items so visitors see a fresh slice on the main page.
  const previewItems = portfolio.filter((p) => p.category !== "Commercial Builds").slice(0, 4);

  return (
    <>
      <Hero />

      <Marquee />

      <NumbersBand />

      {/* Commercial builds — moved above What We Do per operator. Anchored on a real retail display project. */}
      <CommercialFeature />

      {/* Smooth transition strip — CommercialFeature dark → Services dark */}
      <div aria-hidden className="h-16 bg-gradient-to-b from-ink to-ink-2" />

      {/* Services - editorial numbered list with NB walnut accent */}
      <section id="services" className="py-24 sm:py-32 bg-ink-2 relative overflow-hidden">
        {/* Nano Banana atmospheric — walnut tabletop with raking light. Left-edge fade. */}
        <div
          aria-hidden
          className="absolute inset-y-0 -left-12 w-[55%] pointer-events-none bg-cover bg-center"
          style={{ backgroundImage: "url(/img/generated/services-accent.png)", opacity: 0.40, transform: "scaleX(-1)" }}
        />
        <div aria-hidden className="absolute inset-y-0 left-0 w-[55%] pointer-events-none" style={{ background: "linear-gradient(-90deg, #0f0f0f 0%, rgba(15,15,15,0.55) 30%, rgba(15,15,15,0.85) 75%, #0f0f0f 100%)" }} />
        <div aria-hidden className="absolute inset-0 pointer-events-none mix-blend-overlay" style={{ backgroundImage: "url(/img/generated/grain-texture.png)", backgroundSize: "cover", opacity: 0.06 }} />
        <div aria-hidden className="absolute top-10 left-10 w-px h-32 bg-gradient-to-b from-gold-dim to-transparent" />
        <div className="container-site relative">
          <div className="grid lg:grid-cols-[1fr_2fr] gap-12 mb-12 items-end">
            <div>
              <span className="section-tag">What We Do</span>
              <h2 className="m-0">
                Six lanes.<br /><em>One shop.</em>
              </h2>
            </div>
            <p className="text-cream-50 text-[1rem] leading-[1.75] max-w-[560px] lg:justify-self-end">
              We are deliberate about what we take on. Pick a lane to start the conversation - or just call.
              No upsells, no salespeople, no &ldquo;premium tier.&rdquo;
            </p>
          </div>

          <ServicesList services={services} />
        </div>
      </section>

      {/* Portfolio feature - alternating large cards. Filtered to NON-commercial so we don't repeat NB. */}
      <section id="portfolio-preview" className="py-24 sm:py-32 bg-ink relative overflow-hidden">
        {/* Smooth top fade so Services -> PortfolioFeature reads as one continuous canvas */}
        <div aria-hidden className="absolute top-0 left-0 right-0 h-24 pointer-events-none" style={{ background: "linear-gradient(180deg, #0f0f0f, transparent)" }} />
        <div className="container-site relative">
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

          <PortfolioFeature items={previewItems} />

          <div className="text-center mt-20">
            <Link href="/portfolio" className="btn btn-primary btn-large jbw-magnetic">View Full Portfolio</Link>
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
                {faq.length} real answers · honest pricing · no fluff
              </p>
            </div>
          </div>

          <div className="max-w-[960px] mx-auto bg-ink-3/60 backdrop-blur-sm border border-line rounded-2xl overflow-hidden">
            <FaqAccordion items={faq} initialOpen={-1} />
          </div>
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
            <Link href="/contact" className="btn btn-large bg-ink text-white hover:bg-ink-3 transition-colors !px-12 jbw-magnetic">
              Get a Quote
              <Icon name="arrow-right" size={16} className="ml-2" />
            </Link>
            <a href="tel:4075611453" className="text-ink/80 text-[0.85rem] font-semibold tracking-wider uppercase hover:text-ink transition-colors">
              or call (407) 561-1453
            </a>
          </div>
        </div>
      </section>
    </>
  );
}
