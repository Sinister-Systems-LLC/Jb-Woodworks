// Author: RKOJ-ELENO :: 2026-06-01
// v2: Social strip — Instagram, TikTok, YouTube, Facebook, LinkedIn.
// Wood + blue glow on hover (per operator brand-themed contrast).
"use client";
import { SITE } from "@/lib/site";

type Channel = { key: string; label: string; href: string; blurb: string; svg: React.ReactNode };

const CHANNELS: Channel[] = [
  {
    key: "instagram",
    label: "Instagram",
    href: SITE.socials.instagram,
    blurb: "Portfolio + before/afters",
    svg: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" className="w-6 h-6">
        <rect x="3" y="3" width="18" height="18" rx="5" />
        <circle cx="12" cy="12" r="4" />
        <circle cx="17.5" cy="6.5" r="1.2" fill="currentColor" stroke="none" />
      </svg>
    )
  },
  {
    key: "tiktok",
    label: "TikTok",
    href: SITE.socials.tiktok,
    blurb: "Build process, shorts",
    svg: (
      <svg viewBox="0 0 24 24" fill="currentColor" className="w-6 h-6">
        <path d="M14 3v9.5a3.5 3.5 0 1 1-3.5-3.5h.5v3a.5.5 0 0 1-.7.46 1.5 1.5 0 1 0 .7 1.04V3h2.06A4.5 4.5 0 0 0 17 7.5v2A6.5 6.5 0 0 1 14 8.6V3z"/>
      </svg>
    )
  },
  {
    key: "youtube",
    label: "YouTube",
    href: "https://www.youtube.com/@jbwoodworks_fl",
    blurb: "Timelapses + project tours",
    svg: (
      <svg viewBox="0 0 24 24" fill="currentColor" className="w-6 h-6">
        <path d="M22 7.5a3 3 0 0 0-2.1-2.1C18 5 12 5 12 5s-6 0-7.9.4A3 3 0 0 0 2 7.5 31 31 0 0 0 1.5 12 31 31 0 0 0 2 16.5a3 3 0 0 0 2.1 2.1C6 19 12 19 12 19s6 0 7.9-.4A3 3 0 0 0 22 16.5 31 31 0 0 0 22.5 12 31 31 0 0 0 22 7.5zM10 15V9l5 3z"/>
      </svg>
    )
  },
  {
    key: "facebook",
    label: "Facebook",
    href: SITE.socials.facebook,
    blurb: "Orlando market + reviews",
    svg: (
      <svg viewBox="0 0 24 24" fill="currentColor" className="w-6 h-6">
        <path d="M13.5 22v-8h2.7l.4-3.2h-3.1V8.7c0-.9.3-1.6 1.6-1.6h1.6V4.2A23 23 0 0 0 14.4 4c-2.4 0-4 1.4-4 4.2v2.6H7.7V14h2.7v8z"/>
      </svg>
    )
  },
  {
    key: "linkedin",
    label: "LinkedIn",
    href: "https://www.linkedin.com/company/jb-woodworks-fl",
    blurb: "Commercial + B2B",
    svg: (
      <svg viewBox="0 0 24 24" fill="currentColor" className="w-6 h-6">
        <path d="M4 4h4v4H4zm.5 6H8v10H4.5zM10 10h3.4v1.4c.5-.9 1.7-1.7 3.4-1.7 3.6 0 4.2 2.4 4.2 5.4V20h-3.5v-4.4c0-1 0-2.4-1.5-2.4s-1.7 1.2-1.7 2.3V20H10z"/>
      </svg>
    )
  }
];

export function SocialStrip() {
  return (
    <section aria-labelledby="social-heading" className="py-16 sm:py-20 bg-ink relative border-y border-line">
      <div aria-hidden className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-coastal/40 to-transparent" />
      <div className="container-site relative text-center">
        <p className="font-mono text-[0.62rem] tracking-[0.42em] uppercase text-coastal-light mb-3">
          <span className="tabular-nums">06</span> · Follow the build
        </p>
        <h2 id="social-heading" className="font-display text-[clamp(1.8rem,3.6vw,2.6rem)] leading-[1.1] text-white m-0">
          See us in the shop — <em className="text-gold">every channel.</em>
        </h2>

        <ul className="mt-10 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4 sm:gap-5 max-w-[1020px] mx-auto">
          {CHANNELS.map((c) => (
            <li key={c.key}>
              <a
                href={c.href}
                target="_blank"
                rel="me noopener noreferrer"
                aria-label={`${c.label} — ${c.blurb}`}
                className="group block bg-ink-3 border border-line rounded-xl p-5 transition-all duration-300 hover:border-coastal/60 hover:shadow-[0_0_28px_rgba(58,124,165,0.22),inset_0_0_18px_rgba(201,168,76,0.08)] hover:-translate-y-0.5"
              >
                <span className="text-cream-50 group-hover:text-coastal-light transition-colors duration-300 inline-block">{c.svg}</span>
                <p className="mt-3 text-white text-[0.85rem] tracking-[0.14em] uppercase font-semibold">{c.label}</p>
                <p className="mt-1 text-cream-30 text-[0.72rem] leading-snug">{c.blurb}</p>
              </a>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
