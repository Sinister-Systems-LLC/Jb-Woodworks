// Author: RKOJ-ELENO :: 2026-05-23
import type { Metadata } from "next";
import Link from "next/link";
import { Reveal } from "@/components/ui/reveal";
import { FaqTabs } from "@/components/sections/faq-tabs";
import { faqCategorized } from "@/lib/content/faq-categorized";
import { SITE } from "@/lib/site";

export const metadata: Metadata = {
  title: "About / FAQ",
  description: "Custom woodworking + commercial fabrication in Orlando, FL. Decks, docks, pergolas, furniture, branded displays. Free quotes."
};

const blocks = [
  {
    title: "How we work.",
    body: (
      <ol className="pl-6 space-y-3">
        {[
          ["Reach out.", "Phone, email, or the form. Free estimate."],
          ["Site visit.", "Measurements + photos so we quote the actual job."],
          ["Honest quote.", "Fixed-bid where possible, with the material spec stated."],
          ["Build.", "Photos at every milestone. On-site daily until walk-through."],
          ["Walk-through.", "Not done until you say it's done."]
        ].map(([k, v], i) => (
          <li key={i} className="text-cream-50">
            <strong className="text-white mr-1">{k}</strong>{v}
          </li>
        ))}
      </ol>
    )
  },
  {
    title: "What we use.",
    body: (
      <>
        <p>Cedar, pressure-treated pine, and composite (Trex, TimberTech) outdoors. Hardwoods (oak, walnut, cherry, maple) for furniture, millwork, and feature builds. Marine-grade hardware on docks. Stain + seal chosen for Florida sun.</p>
        <p>No corner-cutting on grade or hardware. Every line item is on the invoice.</p>
      </>
    )
  },
  {
    title: "Service area.",
    body: <p>Based in {SITE.serviceArea}. We travel for the right project &mdash; tell us where.</p>
  }
];

export default function AboutPage() {
  return (
    <>
      <section className="pt-40 pb-16 bg-gradient-to-b from-ink-2 to-ink border-b border-line relative overflow-hidden">
        {/* In-theme atmospheric backdrop (Nano Banana, 2026-05-23). Low opacity so typography reads. */}
        <div
          aria-hidden
          className="absolute inset-0 pointer-events-none bg-cover bg-center"
          style={{ backgroundImage: "url(/img/generated/about-workshop.png)", opacity: 0.22 }}
        />
        <div aria-hidden className="absolute inset-0 pointer-events-none" style={{ background: "linear-gradient(180deg, rgba(8,8,8,0.55) 0%, rgba(8,8,8,0.85) 80%, #080808 100%)" }} />
        <div aria-hidden className="absolute -top-24 -right-24 w-[400px] h-[400px] pointer-events-none" style={{ background: "radial-gradient(circle, rgba(201,168,76,0.10), transparent 70%)" }} />
        <div className="container-site relative">
          <span className="section-tag">About</span>
          <h1 className="mb-5">Built in<br /><em>Orlando, Florida.</em></h1>
          <p className="section-subheadline">
            Custom woodworking + commercial fabrication. Decks, docks, pergolas, furniture, millwork &mdash; plus branded displays, event builds, and feature walls for brands.
          </p>
        </div>
      </section>

      <section className="py-24">
        <div className="container-site grid gap-8 [grid-template-columns:repeat(auto-fit,minmax(320px,1fr))]">
          {blocks.map((b, i) => (
            <Reveal key={i} as="article" delay={i * 100} className="bg-ink-3 border border-line p-8 rounded-xl transition-all hover:border-gold-dim hover:-translate-y-0.5">
              <h2 className="mb-4 text-[clamp(1.4rem,2.6vw,1.9rem)]">{b.title}</h2>
              {b.body}
            </Reveal>
          ))}
        </div>
      </section>

      <section id="faq" className="py-24 sm:py-28 bg-ink-2 relative overflow-hidden">
        <div aria-hidden className="absolute -top-32 -left-32 w-[420px] h-[420px] pointer-events-none" style={{ background: "radial-gradient(circle, rgba(201,168,76,0.08), transparent 70%)" }} />
        <div aria-hidden className="absolute -bottom-32 -right-32 w-[420px] h-[420px] pointer-events-none" style={{ background: "radial-gradient(circle, rgba(201,168,76,0.06), transparent 70%)" }} />
        <div className="container-site relative max-w-[920px]">
          <div className="text-center mb-12">
            <p className="font-display italic text-gold text-[1rem] mb-3">Common questions</p>
            <h2 className="font-display text-[clamp(2.2rem,4.6vw,3.4rem)] leading-[1.05] m-0 text-white tracking-[0.18em] uppercase">
              FAQ
            </h2>
            <span aria-hidden className="block h-px w-16 mx-auto mt-5 bg-gradient-to-r from-transparent via-gold to-transparent" />
          </div>
          <FaqTabs categories={faqCategorized} initialTab="general" initialOpen={-1} />
        </div>
      </section>

      <section className="py-20 relative overflow-hidden" style={{ background: "linear-gradient(135deg, #c9a84c, #a8842f)" }}>
        <div className="container-site flex items-center justify-between gap-8 flex-wrap relative">
          <div>
            <h2 className="text-ink">Have a project in mind?</h2>
            <p className="text-ink/80 mt-2">Free quote, no pressure.</p>
          </div>
          <Link href="/contact" className="btn btn-large bg-ink text-white hover:bg-ink-3">Start the conversation</Link>
        </div>
      </section>
    </>
  );
}
