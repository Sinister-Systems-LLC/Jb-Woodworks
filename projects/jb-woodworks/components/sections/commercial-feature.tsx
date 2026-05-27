// Author: RKOJ-ELENO :: 2026-05-23
// "Commercial Builds" feature section. Anchored on a real retail display
// build (New Balance Ã— Foot Locker) and dressed so the image feels native
// to the dashboard â€” multi-stop radial + linear gradients fade the edges
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
  // Slow vertical parallax on the image (8% travel) â€” subtle, not distracting.
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
      {/* Container â€” tall hero feel */}
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
              alt="JB Woodworks commercial retail display build for New Balance and Foot Locker â€” five custom wood cubbies with branded reveal panels"
              fill
              sizes="100vw"
              priority={false}
              loading="lazy"
              quality={92}
              className="object-cover object-center cinematic-image"
            />
          </div>
        </motion.div>

        {/* Multi-stop fade overlays â€” image melts into the dashboard */}
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
        {/* Subtle gold sheen â€” top + bottom hairlines */}
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
          background: "radial-gradient(circle, rgba(var(--accent-rgb),0.16), transparent 70%)"
        }} />

        {/* Foreground content â€” limited to left column so the build photo reads */}
        <motion.div
          style={{ y: headlineY, opacity: headlineOpacity }}
          className="container-site relative z-[2] py-20 sm:py-24"
        >
          <div className="max-w-[680px]">
            {/* Eyebrow */}
            <p className="font-mono text-[0.62rem] tracking-[0.42em] uppercase text-gold mb-4">
              Commercial &amp; Event Fabrication
            </p>

            {/* Headline with staggered word reveal */}
            <motion.h2
              initial={reduced ? false : "hidden"}
              whileInView="show"
              viewport={{ once: true, amount: 0.5 }}
              transition={{ staggerChildren: 0.08 }}
              className="m-0 mb-6"
            >
              <motion.span
                variants={{ hidden: { opacity: 0, y: 22 }, show: { opacity: 1, y: 0 } }}
                transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
                className="block"
              >
                Built for brands.
              </motion.span>
              <motion.em
                variants={{ hidden: { opacity: 0, y: 22 }, show: { opacity: 1, y: 0 } }}
                transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
                className="inline-block"
              >
                Same shop, same standard.
              </motion.em>
            </motion.h2>

            <p className="text-cream-50 text-[1.1rem] leading-[1.7] max-w-[520px] mb-9 font-display italic">
              Custom fabrication, branded displays, retail installations, event builds, feature walls &mdash; designed and built in-house, photographable from day one.
            </p>

            <div className="flex flex-wrap items-center gap-6">
              <Link
                href="/portfolio?category=commercial-event-fabrication"
                className="link-arrow"
              >
                See more builds
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                  <path d="M3 7h8M7 3l4 4-4 4" />
                </svg>
              </Link>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
