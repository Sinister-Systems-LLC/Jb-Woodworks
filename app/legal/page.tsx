// Author: RKOJ-ELENO :: 2026-05-23
import type { Metadata } from "next";
import Link from "next/link";
import { LEGAL } from "@/lib/legal";

export const metadata: Metadata = {
  title: "Legal",
  description: `Privacy, Terms, Cookies, and Accessibility for the JB Woodworks website. Effective ${LEGAL.effectiveDate}.`
};

const DOCS = [
  { href: "/legal/privacy",       title: "Privacy Policy",         blurb: "What information we collect, why, and the choices you have." },
  { href: "/legal/terms",         title: "Terms of Service",       blurb: "Rules of engagement for the website and the project work we do." },
  { href: "/legal/cookies",       title: "Cookies Notice",         blurb: "We do not use tracking cookies. The full story is here." },
  { href: "/legal/accessibility", title: "Accessibility Statement", blurb: "Our commitment to a site any visitor can use - and how to report an issue." }
];

export default function LegalIndex() {
  return (
    <>
      <section className="pt-40 pb-12 bg-gradient-to-b from-ink-2 to-ink border-b border-line relative overflow-hidden">
        <div aria-hidden className="absolute -top-24 -right-24 w-[400px] h-[400px] pointer-events-none" style={{ background: "radial-gradient(circle, rgba(201,168,76,0.10), transparent 70%)" }} />
        <div className="container-site relative">
          <span className="section-tag">Legal</span>
          <h1 className="mb-5">House<br /><em>policies.</em></h1>
          <p className="section-subheadline">Plain-English documents covering privacy, terms, cookies, and accessibility. Effective {LEGAL.effectiveDate}.</p>
        </div>
      </section>

      <section className="py-20">
        <div className="container-site grid gap-5 sm:grid-cols-2">
          {DOCS.map((d) => (
            <Link
              key={d.href}
              href={d.href}
              className="group block bg-ink-3 border border-line p-7 rounded-xl transition-all hover:border-gold-dim hover:-translate-y-0.5 hover:shadow-[0_18px_40px_-20px_rgba(0,0,0,0.7)]"
            >
              <span aria-hidden className="block w-12 h-px bg-gold mb-5 scale-x-50 origin-left transition-transform duration-500 group-hover:scale-x-100" />
              <h3 className="font-display text-[1.4rem] text-white mb-2">{d.title}</h3>
              <p className="text-cream-50 text-[0.95rem] leading-[1.7]">{d.blurb}</p>
              <p className="mt-4 text-gold text-[0.72rem] font-bold tracking-[0.18em] uppercase">Read &rarr;</p>
            </Link>
          ))}
        </div>
      </section>
    </>
  );
}
