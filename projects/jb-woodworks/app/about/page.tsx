// Author: RKOJ-ELENO :: 2026-05-23
import type { Metadata } from "next";
import Link from "next/link";
import { Reveal } from "@/components/ui/reveal";
import { FaqAccordion } from "@/components/sections/faq-accordion";
import { faq } from "@/lib/content";
import { SITE } from "@/lib/site";

export const metadata: Metadata = {
  title: "About / FAQ",
  description: "JB Woodworks is a custom woodworking shop in Orlando, Florida. Licensed and insured. Free quotes. Answers to common questions."
};

const blocks = [
  {
    title: "How we work.",
    body: (
      <ol className="pl-6 space-y-3">
        {[
          ["Reach out.", "Phone, email, or the form. Tell us what you need. Free estimate."],
          ["Site visit + sketch.", "Measurements, photos, and a rough sketch so we are quoting the actual job."],
          ["Honest quote.", "Fixed-bid where possible, with a stated material spec."],
          ["Build.", "Photos at major milestones. Licensed and insured on every site."],
          ["Walk-through.", "We do not call it done until you do."]
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
        <p>Pressure-treated pine, cedar, and composite (Trex, TimberTech) for outdoor work. Hardwoods (oak, walnut, cherry, maple) for furniture and trim. Marine-grade hardware on docks. Stain and seal chosen to outlast the Florida sun.</p>
        <p>We do not cut corners on hardware or wood grade. You will see what we used on the invoice.</p>
      </>
    )
  },
  {
    title: "Licensed and insured.",
    body: <p>Every job is fully licensed and insured. We carry general liability and workers comp. We are happy to send certificates before we start work.</p>
  },
  {
    title: "Service area.",
    body: <p>Based in {SITE.serviceArea}. For larger custom builds we travel further - just tell us where.</p>
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
            JB Woodworks is a custom woodworking shop based in Orlando. We build docks, decks, pergolas, custom pool tables, furniture, and interior trim - and we travel for the right project anywhere in the surrounding areas and across the USA.
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

      <section id="faq" className="py-24 bg-ink-2 relative overflow-hidden">
        <div aria-hidden className="absolute -top-32 -left-32 w-[420px] h-[420px] pointer-events-none" style={{ background: "radial-gradient(circle, rgba(201,168,76,0.08), transparent 70%)" }} />
        <div className="container-site relative">
          <span className="section-tag">FAQ</span>
          <h2 className="mb-14">Everything you<br /><em>need to know.</em></h2>
          <div className="max-w-[960px] mx-auto bg-ink-3/60 backdrop-blur-sm border border-line rounded-2xl overflow-hidden">
            <FaqAccordion items={faq} initialOpen={-1} />
          </div>
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
