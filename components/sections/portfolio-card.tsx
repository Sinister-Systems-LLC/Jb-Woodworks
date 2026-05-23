// Author: RKOJ-ELENO :: 2026-05-23
"use client";
import Link from "next/link";
import Image from "next/image";
import { motion, useReducedMotion } from "framer-motion";
import { Icon } from "@/components/ui/icon";
import type { PortfolioItem } from "@/lib/content";

export function PortfolioCard({
  item,
  index,
  hidden = false
}: {
  item: PortfolioItem;
  index: number;
  hidden?: boolean;
}) {
  const reduced = useReducedMotion();
  const src = item.is_raw_cover ? `/img/projects/${item.cover}` : `/media/${item.cover}`;
  // index < 3 = visible on first paint of the listing; preload those, lazy the rest.
  const eager = index < 3;

  return (
    <motion.div
      layout
      initial={reduced ? false : { opacity: 0, y: 28 }}
      animate={
        hidden
          ? { opacity: 0, scale: 0.95, y: 20 }
          : { opacity: 1, scale: 1, y: 0 }
      }
      transition={{ duration: 0.55, delay: hidden ? 0 : index * 0.07, ease: [0.16, 1, 0.3, 1] }}
      className={hidden ? "pointer-events-none absolute" : ""}
      aria-hidden={hidden}
    >
      <Link
        href={`/portfolio/${item.slug}`}
        className="group block bg-ink-3 border border-line rounded-xl overflow-hidden transition-all duration-500 ease-out hover:border-gold hover:-translate-y-1.5 hover:shadow-[0_4px_32px_rgba(0,0,0,0.6)]"
      >
        <div className="relative aspect-[4/3] bg-ink-5 overflow-hidden">
          <Image
            src={src}
            alt={item.title}
            fill
            sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
            priority={eager}
            loading={eager ? undefined : "lazy"}
            quality={88}
            className="object-cover object-center transition-transform duration-1000 ease-out group-hover:scale-105 cinematic-image"
          />
          {/* Editorial bottom-gradient + vignette so the card title pad never fights for contrast */}
          <span aria-hidden className="absolute inset-x-0 bottom-0 h-2/3 pointer-events-none" style={{ background: "linear-gradient(180deg, transparent 0%, rgba(8,8,8,0.55) 100%)" }} />
        </div>
        <div className="px-6 pt-6 pb-7">
          <span className="block text-[0.62rem] font-bold tracking-[0.22em] uppercase text-gold mb-2">
            {item.category}
          </span>
          <h3 className="font-display text-[1.4rem] mb-2">{item.title}</h3>
          <p className="text-cream-50 text-[0.92rem] leading-[1.6] mb-3.5">{item.blurb}</p>
          <span className="inline-flex items-center gap-1.5 text-gold text-[0.72rem] font-bold tracking-[0.14em] uppercase">
            View project
            <Icon name="arrow-right" size={14} className="transition-transform duration-300 group-hover:translate-x-1" />
          </span>
        </div>
      </Link>
    </motion.div>
  );
}
