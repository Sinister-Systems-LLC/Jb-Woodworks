// Author: RKOJ-ELENO :: 2026-05-23 (v2 form swap 2026-06-01 — project type + zip + timeline + budget)
import type { Metadata } from "next";
import { Suspense } from "react";
import { ContactFormV2 as ContactForm } from "@/components/sections/contact-form-v2";
import { SITE } from "@/lib/site";

export const metadata: Metadata = {
  title: "Contact",
  description: `Get a free quote from JB Woodworks. Call ${SITE.phone} or email ${SITE.email}. Orlando, FL.`
};

export default function ContactPage() {
  return (
    <>
      <section className="pt-40 pb-16 bg-gradient-to-b from-ink-2 to-ink border-b border-line relative overflow-hidden">
        {/* Nano Banana atmospheric backdrop — single chisel on walnut, cool window light. Sets a tone of careful craft. */}
        <div
          aria-hidden
          className="absolute inset-0 pointer-events-none bg-cover bg-center"
          style={{ backgroundImage: "url(/img/generated/contact-tools.png)", opacity: 0.22 }}
        />
        <div aria-hidden className="absolute inset-0 pointer-events-none" style={{ background: "linear-gradient(180deg, rgba(8,8,8,0.5) 0%, rgba(8,8,8,0.75) 60%, #080808 100%)" }} />
        <div aria-hidden className="absolute -top-24 -right-24 w-[400px] h-[400px] pointer-events-none" style={{ background: "radial-gradient(circle, rgba(201,168,76,0.12), transparent 70%)" }} />
        <div aria-hidden className="absolute inset-0 pointer-events-none mix-blend-overlay" style={{ backgroundImage: "url(/img/generated/grain-texture.png)", backgroundSize: "cover", opacity: 0.06 }} />
        <div className="container-site relative">
          <span className="section-tag">Contact</span>
          <h1 className="mb-5">Start your next<br /><em>project with us.</em></h1>
          <p className="section-subheadline">
            Ready to transform your space? Send us a message detailing what you are looking to get done, and we will get back to you to discuss your vision.
          </p>
        </div>
      </section>

      <section className="py-24">
        <div className="container-site grid gap-14 lg:grid-cols-[1fr_1.2fr] items-start">
          <div>
            <div className="space-y-5">
              <div>
                <span className="block text-[0.7rem] font-bold tracking-[0.2em] uppercase text-gold mb-1">Phone</span>
                <a href={`tel:${SITE.phoneTel}`} className="font-display text-[1.7rem] text-white hover:text-gold transition-colors">{SITE.phone}</a>
              </div>
              <div>
                <span className="block text-[0.7rem] font-bold tracking-[0.2em] uppercase text-gold mb-1">Email</span>
                <a href={`mailto:${SITE.email}`} className="font-display text-[1.7rem] text-white hover:text-gold transition-colors break-all">{SITE.email}</a>
              </div>
            </div>

            <ul className="mt-9 space-y-2.5 list-none p-0">
              {["Free estimates", "Custom design consultations", "Same-day response on weekdays"].map((s, i) => (
                <li key={i} className="flex items-center gap-3 text-cream-80 text-[0.95rem]">
                  <span className="w-2 h-2 bg-gold rounded-full inline-block" />{s}
                </li>
              ))}
            </ul>

            <div className="mt-9">
              <p className="text-[0.7rem] font-bold tracking-[0.2em] uppercase text-gold mb-3">Follow</p>
              <ul className="flex flex-wrap gap-5 list-none p-0">
                {Object.entries(SITE.socials).map(([k, v]) => (
                  <li key={k}>
                    <a href={v} target="_blank" rel="noopener noreferrer" className="text-cream-50 hover:text-gold transition-colors text-[0.85rem] font-semibold tracking-wide uppercase">
                      {k.charAt(0).toUpperCase() + k.slice(1)}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <Suspense fallback={<div className="bg-ink-3 border border-line p-9 rounded-xl text-cream-50">Loading form...</div>}>
            <ContactForm />
          </Suspense>
        </div>
      </section>
    </>
  );
}
