// Author: RKOJ-ELENO :: 2026-05-23
// "Commercial Builds" feature section. Anchored on a real retail display
// build (New Balance × Foot Locker) and dressed so the image feels native
// to the dashboard — multi-stop radial + linear gradients fade the edges
// into the ink-2 surface, slow Ken-Burns zoom on the image, parallax pull
// on scroll, plus a slim gold rule + cinematic film-grain accent.
"use client";

import Image from "next/image";
import Link from "next/link";
import { motion, useReducedMotion, useScroll, useTransform } from "framer-motion";
import { useRef } from "react";

export function CommercialFeature() {
  const reduced = useReducedMotion();
  const ref = useRef<HTMLElement | null>(null);
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start end", "end start"]
  });
  // Slow vertical parallax on the image (8% travel) — subtle, not distracting.
  const yParallax = useTransform(scrollYProgress, [0, 1], reduced ? ["0%", "0%"] : ["-4%", "4%"]);
  // Headline slides in from below as section enters
  const headlineY = useTransform(scrollYProgress, [0, 0.4, 0.6, 1], reduced ? ["0%", "0%", "0%", "0%"] : ["8%", "0%", "0%", "-2%"]);
  const headlineOpacity = useTransform(scrollYProgress, [0, 0.25, 0.75, 1], [0.2, 1, 1, 0.4]);

  return (
    <section
      ref={ref}
      id="commercial"
      aria-label="Commercial builds"
      className="relative overflow-hidden bg-ink-2 isolate"
    >
      {/* Container — tall hero feel */}
      <div className="relative min-h-[680px] sm:min-h-[760px] flex items-center">
        {/* Image layer with parallax + Ken-Burns zoom */}
        <motion.div
          aria-hidden
          style={{ y: yParallax }}
          className="absolute inset-0 pointer-events-none"
        >
          <div className={`absolute inset-0 ${reduced ? "" : "jbw-ken-burns"}`}>
            <Image
              src="/img/featured/new-balance-reveal.jpg"
              alt="JB Woodworks commercial retail display build for New Balance and Foot Locker — five custom wood cubbies with branded reveal panels"
              fill
              sizes="100vw"
              priority={false}
              loading="lazy"
              quality={92}
              className="object-cover object-center cinematic-image"
            />
          </div>
        </motion.div>

        {/* Multi-stop fade overlays — image melts into the dashboard */}
        {/* Top + bottom dark falloff */}
        <div aria-hidden className="absolute inset-0 pointer-events-none" style={{
          background:
            "linear-gradient(180deg, #080808 0%, rgba(8,8,8,0.45) 18%, rgba(8,8,8,0.25) 50%, rgba(8,8,8,0.55) 80%, #080808 100%)"
        }} />
        {/* Left edge fade so headline column reads clean */}
        <div aria-hidden className="absolute inset-y-0 left-0 w-3/5 sm:w-2/5 pointer-events-none" style={{
          background:
            "linear-gradient(90deg, #080808 0%, rgba(8,8,8,0.85) 25%, rgba(8,8,8,0.4) 70%, transparent 100%)"
        }} />
        {/* Right edge fade for symmetry */}
        <div aria-hidden className="absolute inset-y-0 right-0 w-1/4 pointer-events-none" style={{
          background:
            "linear-gradient(-90deg, rgba(8,8,8,0.85) 0%, rgba(8,8,8,0.35) 50%, transparent 100%)"
        }} />
        {/* Radial vignette over the whole image */}
        <div aria-hidden className="absolute inset-0 pointer-events-none" style={{
          background:
            "radial-gradient(ellipse at center, transparent 0%, rgba(8,8,8,0.18) 60%, rgba(8,8,8,0.55) 100%)"
        }} />
        {/* Subtle gold sheen — top + bottom hairlines */}
        <div aria-hidden className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-gold-dim to-transparent opacity-70" />
        <div aria-hidden className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-gold-dim to-transparent opacity-70" />
        {/* Film grain overlay */}
        <div aria-hidden className="absolute inset-0 pointer-events-none opacity-25 mix-blend-overlay" style={{
          backgroundImage: "url(/img/generated/grain-texture.png)",
          backgroundSize: "cover",
          backgroundPosition: "right center"
        }} />
        {/* Gold radial accent in corner */}
        <div aria-hidden className="absolute -top-24 -right-24 w-[500px] h-[500px] pointer-events-none" style={{
          background: "radial-gradient(circle, rgba(201,168,76,0.16), transparent 70%)"
        }} />

        {/* Foreground content — limited to left column so the build photo reads */}
        <motion.div
          style={{ y: headlineY, opacity: headlineOpacity }}
          className="container-site relative z-[2] py-20 sm:py-24"
        >
          <div className="max-w-[640px]">
            {/* Slim badge with case-study reference */}
            <div className="inline-flex items-center gap-3 px-4 py-2 bg-ink/55 backdrop-blur-md border border-gold/30 rounded-full mb-7 shadow-[0_2px_30px_-8px_rgba(0,0,0,0.7)]">
              <span aria-hidden className="block w-1.5 h-1.5 rounded-full bg-gold animate-pulse" />
              <span className="text-[0.65rem] tracking-[0.32em] uppercase font-bold text-gold">Latest build</span>
              <span className="w-px h-3 bg-gold/30" aria-hidden />
              <span className="text-[0.65rem] tracking-[0.18em] uppercase font-semibold text-cream-50">
                New Balance × Foot Locker
              </span>
            </div>

            <span className="section-tag">Commercial Builds</span>

            <h2 className="m-0 mb-5">
              Beyond the backyard.<br /><em>Brands trust us too.</em>
            </h2>

            <p className="text-cream-50 text-[1.05rem] leading-[1.8] max-w-[520px] mb-8">
              Retail displays, branded reveal walls, pop-up environments, restaurant fit-outs.
              When a brand needs custom wood that has to land on the first day of install — and
              be photographable on the second — we are the shop on speed dial.
            </p>

            <div className="flex flex-wrap items-center gap-5">
              <Link
                href="/contact?service=commercial"
                className="btn btn-primary btn-large"
              >
                Discuss your project
              </Link>
              <Link
                href="/portfolio"
                className="link-arrow"
              >
                See more builds
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                  <path d="M3 7h8M7 3l4 4-4 4" />
                </svg>
              </Link>
            </div>

            {/* Stat strip - reads as editorial chrome, not bragging */}
            <ul className="mt-12 grid grid-cols-3 gap-6 max-w-[460px] border-t border-line pt-6">
              <li>
                <p className="font-display text-[1.8rem] leading-none text-white tabular-nums">5</p>
                <p className="text-[0.6rem] tracking-[0.28em] uppercase font-bold text-cream-30 mt-1.5">Cubbies built</p>
              </li>
              <li>
                <p className="font-display text-[1.8rem] leading-none text-white tabular-nums">48h</p>
                <p className="text-[0.6rem] tracking-[0.28em] uppercase font-bold text-cream-30 mt-1.5">On-site install</p>
              </li>
              <li>
                <p className="font-display text-[1.8rem] leading-none text-white tabular-nums">1<span className="text-gold">/1</span></p>
                <p className="text-[0.6rem] tracking-[0.28em] uppercase font-bold text-cream-30 mt-1.5">Brand approval</p>
              </li>
            </ul>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
