// Author: RKOJ-ELENO :: 2026-05-23
import Image from "next/image";
import Link from "next/link";
import { SITE } from "@/lib/site";

export function Footer() {
  const year = new Date().getFullYear();
  return (
    <footer className="bg-ink-2 border-t border-line pt-16 pb-6 text-cream-50 relative">
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-gold-dim to-transparent" />
      <div className="max-w-site mx-auto px-7 grid gap-9 sm:grid-cols-2 lg:grid-cols-5">
        <div className="lg:col-span-2">
          <Link href="/" className="inline-flex items-start group" aria-label={`${SITE.name} home`}>
            <Image
              src="/img/branding/jbw-wordmark-stacked.png"
              alt={`${SITE.name} - Construction & Fabrication`}
              width={971}
              height={733}
              className="h-24 w-auto transition-opacity duration-200 group-hover:opacity-90"
            />
          </Link>
          <p className="mt-5 italic font-display text-[0.95rem] text-cream-50">{SITE.tagline}</p>
          <p className="mt-2 text-[0.85rem] text-cream-30">Serving {SITE.serviceArea}.</p>
          <p className="mt-3 text-[0.78rem] leading-relaxed">
            <a href={`tel:${SITE.phoneTel}`} className="hover:text-gold transition-colors">{SITE.phone}</a><br />
            <a href={`mailto:${SITE.email}`} className="hover:text-gold transition-colors">{SITE.email}</a>
          </p>
        </div>

        <div>
          <h4 className="text-white text-[0.75rem] tracking-[0.18em] uppercase font-bold mb-4">Site</h4>
          <ul className="space-y-2 text-[0.9rem]">
            <li><Link href="/services" className="hover:text-gold transition-colors">Services</Link></li>
            <li><Link href="/portfolio" className="hover:text-gold transition-colors">Portfolio</Link></li>
            <li><Link href="/about" className="hover:text-gold transition-colors">About / FAQ</Link></li>
            <li><Link href="/contact" className="hover:text-gold transition-colors">Get a quote</Link></li>
          </ul>
        </div>

        <div>
          <h4 className="text-white text-[0.75rem] tracking-[0.18em] uppercase font-bold mb-4">Follow</h4>
          {/* D-series D13 mirror: 7-network grid with gold-glow hover (brand gold #c9a84c, NOT blue). */}
          <ul className="grid grid-cols-2 gap-x-3 gap-y-2 text-[0.85rem]">
            <li><a href={SITE.socials.instagram} target="_blank" rel="me noopener noreferrer" className="jbw-social-link inline-flex items-center gap-1.5 hover:text-gold transition-all duration-200 hover:[text-shadow:0_0_10px_rgba(201,168,76,0.55)]">Instagram</a></li>
            <li><a href={SITE.socials.facebook} target="_blank" rel="me noopener noreferrer" className="jbw-social-link inline-flex items-center gap-1.5 hover:text-gold transition-all duration-200 hover:[text-shadow:0_0_10px_rgba(201,168,76,0.55)]">Facebook</a></li>
            <li><a href={SITE.socials.tiktok} target="_blank" rel="me noopener noreferrer" className="jbw-social-link inline-flex items-center gap-1.5 hover:text-gold transition-all duration-200 hover:[text-shadow:0_0_10px_rgba(201,168,76,0.55)]">TikTok</a></li>
            <li><a href={SITE.socials.twitter} target="_blank" rel="me noopener noreferrer" className="jbw-social-link inline-flex items-center gap-1.5 hover:text-gold transition-all duration-200 hover:[text-shadow:0_0_10px_rgba(201,168,76,0.55)]">X / Twitter</a></li>
            <li><a href="https://www.youtube.com/@jbwoodworks" target="_blank" rel="me noopener noreferrer" className="jbw-social-link inline-flex items-center gap-1.5 hover:text-gold transition-all duration-200 hover:[text-shadow:0_0_10px_rgba(201,168,76,0.55)]">YouTube</a></li>
            <li><a href="https://www.linkedin.com/company/jb-woodworks" target="_blank" rel="me noopener noreferrer" className="jbw-social-link inline-flex items-center gap-1.5 hover:text-gold transition-all duration-200 hover:[text-shadow:0_0_10px_rgba(201,168,76,0.55)]">LinkedIn</a></li>
            <li><a href="https://www.snapchat.com/add/jbwoodworks" target="_blank" rel="me noopener noreferrer" className="jbw-social-link inline-flex items-center gap-1.5 hover:text-gold transition-all duration-200 hover:[text-shadow:0_0_10px_rgba(201,168,76,0.55)]">Snapchat</a></li>
            <li><a href="https://github.com/jbwoodworks" target="_blank" rel="me noopener noreferrer" className="jbw-social-link inline-flex items-center gap-1.5 hover:text-gold transition-all duration-200 hover:[text-shadow:0_0_10px_rgba(201,168,76,0.55)]">GitHub</a></li>
            <li><a href="https://discord.gg/jbwoodworks" target="_blank" rel="me noopener noreferrer" className="jbw-social-link inline-flex items-center gap-1.5 hover:text-gold transition-all duration-200 hover:[text-shadow:0_0_10px_rgba(201,168,76,0.55)]">Discord</a></li>
          </ul>
        </div>

        <div>
          <h4 className="text-white text-[0.75rem] tracking-[0.18em] uppercase font-bold mb-4">Legal</h4>
          <ul className="space-y-2 text-[0.9rem]">
            <li><Link href="/legal/privacy" className="hover:text-gold transition-colors">Privacy</Link></li>
            <li><Link href="/legal/terms" className="hover:text-gold transition-colors">Terms</Link></li>
            <li><Link href="/legal/cookies" className="hover:text-gold transition-colors">Cookies</Link></li>
            <li><Link href="/legal/accessibility" className="hover:text-gold transition-colors">Accessibility</Link></li>
          </ul>
        </div>
      </div>

      <div className="mt-10 pt-5 mx-auto max-w-site px-7 border-t border-line text-center text-[0.78rem] text-cream-30">
        <p>(C) {year} {SITE.name}. Built in Orlando, FL.</p>
        {/* D-series D12 mirror: subtle low-contrast Powered-by-Eve attribution. */}
        <p className="mt-2 text-[0.66rem] tracking-[0.22em] uppercase text-cream-30/60">
          <Link
            href="/eve"
            className="hover:text-gold/80 transition-colors"
            aria-label="Powered by Eve"
          >
            Powered by Eve
          </Link>
        </p>
      </div>
    </footer>
  );
}
