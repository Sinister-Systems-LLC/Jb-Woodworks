// Author: RKOJ-ELENO :: 2026-05-23
"use client";
import Link from "next/link";
import Image from "next/image";
import { motion, useReducedMotion } from "framer-motion";
import { Icon } from "@/components/ui/icon";
import type { PortfolioItem } from "@/lib/content";
import { cn } from "@/lib/utils";

// Alternating left/right large feature cards. Replaces the basic grid for the
// home preview so the portfolio reads as editorial rather than catalog.
export function PortfolioFeature({ items }: { items: PortfolioItem[] }) {
  return (
    <div className="space-y-16 sm:space-y-24">
      {items.map((item, i) => (
        <FeatureRow key={item.slug} item={item} index={i} reverse={i % 2 === 1} />
      ))}
    </div>
  );
}

function FeatureRow({ item, index, reverse }: { item: PortfolioItem; index: number; reverse: boolean }) {
  const reduced = useReducedMotion();
  const src = item.is_raw_cover ? `/img/projects/${item.cover}` : `/media/${item.cover}`;
  // Home preview shows two features above the fold on most viewports; eager-load those.
  const eager = index < 2;

  return (
    <motion.article
      initial={reduced ? false : { opacity: 0, y: 40 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.25 }}
      transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
      className={cn(
        "grid gap-8 sm:gap-12 items-center",
        "lg:grid-cols-[1.3fr_1fr]",
        reverse && "lg:[&>div:first-child]:col-start-2 lg:[&>div:last-child]:col-start-1 lg:[&>div:last-child]:row-start-1"
      )}
    >
      {/* Image */}
      <div className="relative group overflow-hidden rounded-xl bg-ink-5">
        <Link href={`/portfolio/${item.slug}`} className="block aspect-[4/3] relative">
          <Image
            src={src}
            alt={item.title}
            fill
            sizes="(max-width: 1024px) 100vw, 60vw"
            priority={eager}
            loading={eager ? undefined : "lazy"}
            quality={90}
            className="object-cover object-center transition-transform duration-[1200ms] ease-out group-hover:scale-105 cinematic-image"
          />
          <div aria-hidden className="absolute inset-0 bg-gradient-to-tr from-ink/40 via-transparent to-transparent" />
          {/* Corner brackets */}
          <span aria-hidden className="absolute top-4 left-4 w-8 h-8 border-t-2 border-l-2 border-gold/70 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
          <span aria-hidden className="absolute bottom-4 right-4 w-8 h-8 border-b-2 border-r-2 border-gold/70 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
        </Link>
        {/* Index plate */}
        <div aria-hidden className="absolute top-4 right-4 px-3 py-1.5 bg-ink/80 backdrop-blur-sm text-gold font-mono text-[0.7rem] tracking-widest font-semibold rounded">
          {String(index + 1).padStart(2, "0")} / {item.category.toUpperCase()}
        </div>
      </div>

      {/* Copy */}
      <div className={cn("relative", reverse && "lg:text-right")}>
        <span className="block text-[0.65rem] font-bold tracking-[0.28em] uppercase text-gold mb-3">
          Project {String(index + 1).padStart(2, "0")}
        </span>
        <h3 className="font-display text-[clamp(2rem,4vw,3rem)] leading-[1.05] mb-5">
          {item.title}.
        </h3>
        <p className="text-cream-50 text-[1rem] leading-[1.7] max-w-[520px] mb-7" style={reverse ? { marginLeft: "auto" } : {}}>
          {item.blurb}
        </p>
        <Link
          href={`/portfolio/${item.slug}`}
          className="inline-flex items-center gap-2 text-white text-[0.78rem] font-bold tracking-[0.14em] uppercase border-b border-gold/40 pb-2 hover:border-gold transition-colors group"
        >
          See the build
          <Icon name="arrow-right" size={16} className="transition-transform duration-300 group-hover:translate-x-1" />
        </Link>
      </div>
    </motion.article>
  );
}
