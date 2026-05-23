// Author: RKOJ-ELENO :: 2026-05-23
// Shared shell for /legal/* pages. Matches site theme + reusable hero band.
import Link from "next/link";
import type { ReactNode } from "react";
import { LEGAL } from "@/lib/legal";

const NAV = [
  { href: "/legal/privacy",       label: "Privacy" },
  { href: "/legal/terms",         label: "Terms" },
  { href: "/legal/cookies",       label: "Cookies" },
  { href: "/legal/accessibility", label: "Accessibility" }
];

export function LegalLayout({
  tag,
  title,
  intro,
  children,
  activeHref
}: {
  tag: string;
  title: ReactNode;
  intro: ReactNode;
  children: ReactNode;
  activeHref: string;
}) {
  return (
    <>
      <section className="pt-40 pb-12 bg-gradient-to-b from-ink-2 to-ink border-b border-line relative overflow-hidden">
        <div aria-hidden className="absolute -top-24 -right-24 w-[400px] h-[400px] pointer-events-none" style={{ background: "radial-gradient(circle, rgba(201,168,76,0.10), transparent 70%)" }} />
        <div aria-hidden className="absolute inset-y-0 right-0 w-[35%] pointer-events-none bg-cover bg-center mix-blend-screen" style={{ backgroundImage: "url(/img/generated/grain-texture.png)", opacity: 0.07 }} />
        <div className="container-site relative">
          <span className="section-tag">{tag}</span>
          <h1 className="mb-5">{title}</h1>
          <p className="section-subheadline">{intro}</p>
          <p className="text-cream-30 text-[0.78rem] tracking-[0.14em] uppercase">Effective: {LEGAL.effectiveDate}</p>
        </div>
      </section>

      <section className="py-16 sm:py-20">
        <div className="container-site grid gap-10 lg:grid-cols-[220px_1fr]">
          <aside aria-label="Legal navigation">
            <p className="text-[0.7rem] tracking-[0.22em] uppercase text-gold font-bold mb-4">Legal</p>
            <ul className="space-y-2 list-none p-0">
              {NAV.map((n) => {
                const active = n.href === activeHref;
                return (
                  <li key={n.href}>
                    <Link
                      href={n.href}
                      className={[
                        "block py-1.5 text-[0.92rem] transition-colors",
                        active ? "text-gold font-semibold" : "text-cream-50 hover:text-white"
                      ].join(" ")}
                      aria-current={active ? "page" : undefined}
                    >
                      {n.label}
                    </Link>
                  </li>
                );
              })}
            </ul>
            <p className="mt-6 text-[0.78rem] text-cream-30 leading-[1.7]">
              Questions about this document? Email{" "}
              <a className="text-gold hover:text-gold-light" href={`mailto:${LEGAL.contactEmail}`}>{LEGAL.contactEmail}</a>{" "}
              or call <a className="text-gold hover:text-gold-light" href="tel:4075611453">{LEGAL.contactPhone}</a>.
            </p>
          </aside>

          <article className="prose prose-invert max-w-none text-cream-50 text-[0.96rem] leading-[1.85]">
            {children}
          </article>
        </div>
      </section>
    </>
  );
}
