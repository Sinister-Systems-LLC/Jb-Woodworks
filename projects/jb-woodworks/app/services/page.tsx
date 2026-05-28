// Author: RKOJ-ELENO :: 2026-05-23
import Link from "next/link";
import type { Metadata } from "next";
import { Reveal } from "@/components/ui/reveal";
import { Icon } from "@/components/ui/icon";
import { services } from "@/lib/content";
import { SITE } from "@/lib/site";

export const metadata: Metadata = {
  title: "Services",
  description: "Docks, custom decks, furniture and tables, interior trim and millwork, outdoor living spaces, repairs and staining. JB Woodworks in Orlando, FL."
};

export default function ServicesPage() {
  // Per-service Schema.org `Service` entries (Google rich-results eligible).
  // Each service is provided by the LocalBusiness emitted in app/layout.tsx.
  const ld = {
    "@context": "https://schema.org",
    "@graph": services.map((s) => ({
      "@type": "Service",
      "@id": `${SITE.url}/services#${s.slug}`,
      name: s.title,
      description: s.blurb,
      url: s.exampleHref ? `${SITE.url}${s.exampleHref}` : `${SITE.url}/contact?service=${s.slug}`,
      areaServed: SITE.serviceArea,
      provider: {
        "@type": "LocalBusiness",
        "@id": `${SITE.url}/#business`,
        name: SITE.name
      }
    }))
  };

  return (
    <>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(ld) }} />
      <section className="pt-40 pb-16 bg-gradient-to-b from-ink-2 to-ink border-b border-line relative overflow-hidden">
        <div aria-hidden className="absolute -top-24 -right-24 w-[400px] h-[400px] pointer-events-none" style={{ background: "radial-gradient(circle, rgba(var(--accent-rgb),0.10), transparent 70%)" }} />
        <div className="container-site relative">
          <span className="section-tag">Services</span>
          <h1 className="mb-5">What we<br /><em>build.</em></h1>
          <p className="section-subheadline">
            Six lanes of work. Pick one to read details, or send a message and we will figure out where your project fits.
          </p>
        </div>
      </section>

      <section className="py-24 relative">
        <div aria-hidden className="hidden lg:block sticky top-24 z-10 pointer-events-none">
          <div className="container-site">
            <div className="flex justify-between items-baseline px-1 pb-2 border-b border-line/40">
              <span className="text-[0.62rem] font-bold tracking-[0.22em] uppercase text-gold">Services index</span>
              <span className="text-[0.62rem] tracking-[0.18em] uppercase text-cream-30">{services.length} lanes</span>
            </div>
          </div>
        </div>
        <div className="container-site -mt-9 lg:-mt-12 relative">
          <div className="flex flex-col gap-6 max-w-[920px] mx-auto">
            {services.map((s, i) => (
              <Reveal key={s.slug} as="article" delay={i * 80} className="bg-ink-3 border border-line p-9 sm:p-10 rounded-xl transition-all hover:border-gold-dim hover:translate-x-1">
                <header className="flex items-center gap-4 mb-5">
                  <div className="w-14 h-14 grid place-items-center bg-gold-dim text-gold rounded-md p-3">
                    <Icon name={s.icon} size={26} />
                  </div>
                  <h2 className="text-[clamp(1.5rem,3vw,2rem)] m-0">{s.title}</h2>
                </header>
                <p className="text-white text-[1.05rem] mb-3">{s.blurb}</p>
                <p className="text-cream-50 mb-5">{s.details}</p>
                <Link href={`/contact?service=${s.slug}`} className="link-arrow">
                  Ask about {s.title.toLowerCase()}
                  <Icon name="arrow-right" size={14} />
                </Link>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      <section className="py-20 relative overflow-hidden" style={{ background: "linear-gradient(135deg, var(--accent), var(--accent-deep))" }}>
        <div className="container-site flex items-center justify-between gap-8 flex-wrap relative">
          <div>
            <h2 className="text-ink">Not sure where your project fits?</h2>
            <p className="text-ink/80 mt-2">Send a photo and a few details. Free estimate.</p>
          </div>
          <Link href="/contact" className="btn btn-large bg-ink text-white hover:bg-ink-3">Start the conversation</Link>
        </div>
      </section>
    </>
  );
}
