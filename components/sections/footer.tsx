// Author: RKOJ-ELENO :: 2026-05-23
import Image from "next/image";
import Link from "next/link";
import { SITE } from "@/lib/site";

export function Footer() {
  const year = new Date().getFullYear();
  return (
    <footer className="bg-ink-2 border-t border-line pt-20 pb-8 text-cream-50 relative">
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-gold-dim to-transparent" />
      <div className="max-w-site mx-auto px-7 grid gap-12 sm:grid-cols-2 lg:grid-cols-5">
        <div className="lg:col-span-2 flex flex-col">
          <Link href="/" className="inline-flex items-start group self-start" aria-label={`${SITE.name} home`}>
            <Image
              src="/img/branding/jbw-wordmark-stacked.png"
              alt={`${SITE.name} - Construction & Fabrication`}
              width={971}
              height={733}
              className="h-28 sm:h-32 w-auto transition-opacity duration-200 group-hover:opacity-90"
            />
          </Link>
          <p className="mt-7 italic font-display text-[1rem] text-cream-50 max-w-[320px]">{SITE.tagline}</p>
          <p className="mt-3 text-[0.85rem] text-cream-30">Serving {SITE.serviceArea}.</p>
          <div className="mt-5 text-[0.85rem] leading-relaxed space-y-1.5">
            <a href={`tel:${SITE.phoneTel}`} className="block hover:text-gold transition-colors">{SITE.phone}</a>
            <a href={`mailto:${SITE.email}`} className="block hover:text-gold transition-colors">{SITE.email}</a>
          </div>
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
          <ul className="space-y-2 text-[0.9rem]">
            <li><a href={SITE.socials.instagram} target="_blank" rel="me noopener noreferrer" className="hover:text-gold transition-colors">Instagram</a></li>
            <li><a href={SITE.socials.facebook} target="_blank" rel="me noopener noreferrer" className="hover:text-gold transition-colors">Facebook</a></li>
            <li><a href={SITE.socials.tiktok} target="_blank" rel="me noopener noreferrer" className="hover:text-gold transition-colors">TikTok</a></li>
            <li><a href={SITE.socials.twitter} target="_blank" rel="me noopener noreferrer" className="hover:text-gold transition-colors">Twitter</a></li>
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
        (C) {year} {SITE.name}. Built in Orlando, FL.
      </div>
    </footer>
  );
}
