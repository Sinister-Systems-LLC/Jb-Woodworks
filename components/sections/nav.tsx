// Author: RKOJ-ELENO :: 2026-05-23
"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { motion, useReducedMotion } from "framer-motion";
import { SITE } from "@/lib/site";
import { cn } from "@/lib/utils";

export function Nav() {
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);
  const reduced = useReducedMotion();

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <motion.header
      initial={reduced ? false : { y: -100, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.7, delay: 0.15, ease: [0.16, 1, 0.3, 1] }}
      className={cn(
        "fixed top-0 left-0 right-0 z-[1000] transition-all duration-300",
        scrolled && "bg-ink/95 backdrop-blur-xl border-b border-line"
      )}
    >
      <div className="max-w-site mx-auto px-7 h-[82px] flex items-center gap-5">
        <Link href="/" aria-label={`${SITE.name} home`} className="flex items-center gap-3 shrink-0">
          <span className="font-sans text-[1.2rem] font-black tracking-[0.16em] text-white leading-none">
            JB
            <span className="block text-[0.5rem] tracking-[0.42em] text-gold font-bold mt-1">WOODWORKS</span>
          </span>
        </Link>

        <nav className="hidden md:flex gap-9 ml-auto" aria-label="Primary">
          <NavLink href="/#services">Services</NavLink>
          <NavLink href="/portfolio">Portfolio</NavLink>
          <NavLink href="/about#faq">FAQ</NavLink>
          <NavLink href="/contact">Contact</NavLink>
        </nav>

        <button
          type="button"
          aria-label="Toggle menu"
          aria-expanded={open}
          onClick={() => setOpen((v) => !v)}
          className="md:hidden ml-auto p-2.5 flex flex-col gap-[5px] bg-transparent border-0 cursor-pointer"
        >
          <span className={cn("w-[22px] h-px bg-white transition-transform", open && "rotate-45 translate-y-[7px]")} />
          <span className={cn("w-[22px] h-px bg-white transition-opacity", open && "opacity-0")} />
          <span className={cn("w-[22px] h-px bg-white transition-transform", open && "-rotate-45 -translate-y-[7px]")} />
        </button>
      </div>

      <div
        id="mobileMenu"
        className={cn(
          "md:hidden fixed top-[82px] left-0 right-0 bg-ink/[0.98] backdrop-blur-xl px-7 py-8 border-b border-line transition-transform duration-300 z-[999]",
          open ? "translate-y-0" : "-translate-y-[110%]"
        )}
      >
        <ul className="list-none">
          {[
            { href: "/#services", label: "Services" },
            { href: "/portfolio", label: "Portfolio" },
            { href: "/about#faq", label: "FAQ" },
            { href: SITE.socials.instagram, label: "Instagram", external: true },
            { href: SITE.socials.facebook, label: "Facebook", external: true },
            { href: SITE.socials.tiktok, label: "TikTok", external: true },
            { href: SITE.socials.twitter, label: "Twitter", external: true }
          ].map((l, i) => (
            <li key={i} className="border-b border-line">
              <a
                href={l.href}
                target={l.external ? "_blank" : undefined}
                rel={l.external ? "noopener noreferrer" : undefined}
                onClick={() => setOpen(false)}
                className="block py-4 text-white text-[0.95rem] tracking-wider uppercase font-medium"
              >
                {l.label}
              </a>
            </li>
          ))}
          <li className="pt-4">
            <Link href="/contact" onClick={() => setOpen(false)} className="btn btn-primary btn-large">Get a Quote</Link>
          </li>
        </ul>
      </div>
    </motion.header>
  );
}

function NavLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <Link
      href={href}
      className="relative text-[0.78rem] font-medium tracking-wide text-cream-50 uppercase transition-colors hover:text-white after:content-[''] after:absolute after:left-0 after:-bottom-1.5 after:w-0 after:h-px after:bg-gold after:transition-all hover:after:w-full"
    >
      {children}
    </Link>
  );
}
