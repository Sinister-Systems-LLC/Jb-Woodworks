// Author: RKOJ-ELENO :: 2026-05-23
"use client";
import { useEffect, useRef, useState } from "react";
import Image from "next/image";
import { motion, useReducedMotion } from "framer-motion";
import { hero, type HeroSlide } from "@/lib/content";
import { SITE } from "@/lib/site";

const stagger = {
  hidden: { opacity: 0, y: 28 },
  show: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.85, delay: 0.45 + i * 0.15, ease: [0.16, 1, 0.3, 1] as const }
  })
};

export function Hero() {
  const slides = hero;
  const [active, setActive] = useState(0);
  const [readyMap, setReadyMap] = useState<Record<number, boolean>>({});
  const videoRefs = useRef<(HTMLVideoElement | null)[]>([]);
  const reduced = useReducedMotion();

  const markReady = (i: number) => setReadyMap((m) => (m[i] ? m : { ...m, [i]: true }));

  useEffect(() => {
    slides.forEach((s, i) => {
      const v = videoRefs.current[i];
      if (!v) return;
      if (i === active) {
        v.preload = "auto";
        try { v.currentTime = 0; v.play().catch(() => {}); } catch {}
      } else {
        try { v.pause(); } catch {}
      }
    });
    const nextIdx = (active + 1) % slides.length;
    const nextV = videoRefs.current[nextIdx];
    if (nextV && nextV.preload !== "auto") { nextV.preload = "auto"; nextV.load(); }
  }, [active, slides]);

  useEffect(() => {
    if (reduced || slides.length <= 1) return;
    const dur = slides[active]?.duration_ms ?? 7000;
    const t = setTimeout(() => setActive((a) => (a + 1) % slides.length), dur);
    return () => clearTimeout(t);
  }, [active, slides, reduced]);

  const currentLabel = labelFor(slides[active]);

  return (
    <section id="hero" aria-label="Introduction" className="relative h-screen min-h-[680px] overflow-hidden bg-ink-2">
      {/* Slides */}
      <div className="absolute inset-0" aria-hidden="true">
        {slides.map((s, i) => (
          <Slide
            key={i}
            slide={s}
            active={i === active}
            ready={!!readyMap[i]}
            onReady={() => markReady(i)}
            videoRef={(el) => (videoRefs.current[i] = el)}
            preload={i === 0 ? "auto" : "none"}
            eager={i === 0}
          />
        ))}
      </div>

      {/* Overlay */}
      <div className="absolute inset-0 z-[2] bg-gradient-to-b from-black/65 via-black/35 to-black/95" />
      <div className="absolute inset-0 z-[2] bg-gradient-to-r from-ink/70 via-transparent to-transparent" />

      {/* Intro curtain */}
      {!reduced && (
        <motion.div
          aria-hidden="true"
          className="absolute inset-0 z-[4] bg-ink pointer-events-none"
          initial={{ scaleY: 1, originY: 0 }}
          animate={{ scaleY: 0 }}
          transition={{ duration: 1.0, delay: 0.1, ease: [0.16, 1, 0.3, 1] }}
        />
      )}
      {!reduced && (
        <motion.div
          aria-hidden="true"
          className="absolute left-0 right-0 z-[3] h-px"
          style={{ top: 82, background: "linear-gradient(90deg, transparent, #c9a84c, transparent)" }}
          initial={{ scaleX: 0, opacity: 0 }}
          animate={{ scaleX: 1, opacity: 0.45 }}
          transition={{ duration: 1.4, delay: 1.1, ease: [0.16, 1, 0.3, 1] }}
        />
      )}

      {/* Vertical metadata strip - left edge, editorial detail */}
      <div className="hidden md:block absolute top-1/2 -translate-y-1/2 left-7 z-[3] writing-vertical text-cream-30 text-[0.65rem] tracking-[0.4em] uppercase font-semibold">
        <div className="space-y-8" style={{ writingMode: "vertical-rl", transform: "rotate(180deg)" }}>
          <span>EST. 2025  /  ORLANDO FL</span>
          <span>CUSTOM WOODWORKING</span>
        </div>
      </div>

      {/* Slide counter + label - right edge */}
      <div className="hidden md:flex absolute top-1/2 -translate-y-1/2 right-7 z-[3] flex-col items-end gap-3">
        <motion.span
          key={`num-${active}`}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="font-display text-[3.5rem] leading-none text-gold tabular-nums"
        >
          {String(active + 1).padStart(2, "0")}
        </motion.span>
        <span className="text-cream-30 text-[0.65rem] tracking-[0.32em] uppercase font-semibold">/ {String(slides.length).padStart(2, "0")}</span>
        <motion.span
          key={`lbl-${active}`}
          initial={{ opacity: 0, x: 10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="text-cream-50 text-[0.7rem] tracking-[0.28em] uppercase font-semibold mt-2 max-w-[140px] text-right"
        >
          {currentLabel}
        </motion.span>
      </div>

      {/* Slide dots */}
      <div className="absolute bottom-7 left-1/2 -translate-x-1/2 z-[3] hidden sm:flex gap-2">
        {slides.map((_, i) => (
          <button
            key={i}
            type="button"
            onClick={() => setActive(i)}
            aria-label={`Jump to slide ${i + 1}`}
            className={`h-1 rounded-full transition-all duration-500 ${i === active ? "bg-gold w-8" : "bg-cream-30 w-4 hover:bg-cream-50"}`}
          />
        ))}
      </div>

      {/* Content - centered editorial layout */}
      <div className="container-site relative z-[3] h-full flex flex-col items-center justify-center text-center pt-[82px] pb-24">
        <motion.p custom={0} variants={stagger} initial={reduced ? false : "hidden"} animate="show" className="eyebrow !mb-7">
          <span className="eyebrow-dot" /> ORLANDO, FLORIDA <span className="eyebrow-dot" /> EST. 2025 <span className="eyebrow-dot" />
        </motion.p>

        {/* Lead lockup - owner's stacked JBW wordmark, centered, sole hero focus */}
        <motion.div
          custom={1}
          variants={stagger}
          initial={reduced ? false : "hidden"}
          animate="show"
          className="select-none"
        >
          <Image
            src="/img/branding/jbw-wordmark-stacked.png"
            alt="JB Woodworks - Construction & Fabrication"
            width={971}
            height={733}
            priority
            className="h-[clamp(8rem,22vw,15rem)] w-auto mx-auto drop-shadow-[0_4px_28px_rgba(0,0,0,0.55)]"
          />
        </motion.div>
      </div>

      {/* Scroll indicator */}
      <motion.a
        href="#services"
        aria-label="Scroll to services"
        className="absolute bottom-7 right-7 z-[3] hidden sm:flex flex-col items-center gap-2.5 text-cream-30 text-[0.6rem] tracking-[0.3em] hover:text-gold transition-colors"
        initial={reduced ? false : { opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 1.2, delay: 1.6 }}
      >
        <span className="font-semibold">SCROLL</span>
        <span className="relative block w-px h-11 overflow-hidden bg-gradient-to-b from-gold to-transparent scroll-line-anim" />
      </motion.a>
    </section>
  );
}

function labelFor(slide?: HeroSlide): string {
  if (!slide) return "";
  const path = slide.type === "video" ? slide.src : slide.src;
  return path.split("/")[0].toUpperCase();
}

function Slide({
  slide, active, ready, onReady, videoRef, preload, eager
}: {
  slide: HeroSlide; active: boolean; ready: boolean;
  onReady: () => void; videoRef: (el: HTMLVideoElement | null) => void;
  preload: "auto" | "none" | "metadata";
  eager: boolean;
}) {
  const posterSrc = slide.type === "image"
    ? `/media/${slide.src}`
    : slide.poster ? `/media/${slide.poster}` : undefined;

  return (
    <div
      className={[
        "absolute inset-0 transition-opacity duration-[1400ms] ease-linear",
        active ? "opacity-100" : "opacity-0"
      ].join(" ")}
      style={{
        transform: active ? "scale(1.06)" : "scale(1)",
        transition: active
          ? "opacity 1400ms ease, transform 11000ms linear"
          : "opacity 1400ms ease, transform 0ms linear"
      }}
    >
      {posterSrc && (
        <Image
          src={posterSrc}
          alt=""
          aria-hidden="true"
          fill
          sizes="100vw"
          priority={eager}
          loading={eager ? undefined : "lazy"}
          className="object-cover object-center"
        />
      )}
      {slide.type === "video" && (
        <video
          ref={videoRef}
          className={`absolute inset-0 w-full h-full object-cover transition-opacity duration-700 ${ready && active ? "opacity-100" : "opacity-0"}`}
          loop
          muted
          playsInline
          preload={preload}
          poster={`/media/${slide.poster}`}
          onCanPlay={onReady}
          onLoadedData={onReady}
        >
          <source src={`/media/${slide.src}`} type="video/mp4" />
        </video>
      )}
    </div>
  );
}
