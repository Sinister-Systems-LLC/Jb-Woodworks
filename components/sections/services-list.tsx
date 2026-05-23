// Author: RKOJ-ELENO :: 2026-05-23
"use client";
import { useState } from "react";
import Link from "next/link";
import { motion, useReducedMotion, AnimatePresence } from "framer-motion";
import { Icon } from "@/components/ui/icon";
import type { Service } from "@/lib/content";

// Editorial numbered list. Big serif numerals on the left, headline + blurb on the right.
// Hover any row to peek the icon + preview accent on the right.
export function ServicesList({ services }: { services: Service[] }) {
  const [hovered, setHovered] = useState<number | null>(null);
  const reduced = useReducedMotion();

  return (
    <div className="border-t border-line">
      {services.map((s, i) => {
        const active = hovered === i;
        return (
          <motion.article
            key={s.slug}
            initial={reduced ? false : { opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.25 }}
            transition={{ duration: 0.55, delay: i * 0.06, ease: [0.16, 1, 0.3, 1] }}
            onMouseEnter={() => setHovered(i)}
            onMouseLeave={() => setHovered(null)}
            className="group relative border-b border-line"
          >
            {/* Hover spotlight bar */}
            <motion.span
              aria-hidden
              className="absolute inset-y-0 left-0 w-1 bg-gold origin-top"
              initial={{ scaleY: 0 }}
              animate={{ scaleY: active ? 1 : 0 }}
              transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
            />
            {/* Hover surface tint */}
            <motion.span
              aria-hidden
              className="absolute inset-0 bg-gradient-to-r from-gold-dim to-transparent pointer-events-none"
              initial={{ opacity: 0 }}
              animate={{ opacity: active ? 1 : 0 }}
              transition={{ duration: 0.4 }}
            />

            <Link
              href={s.exampleHref ?? `/contact?service=${s.slug}`}
              className="relative grid grid-cols-[auto_1fr_auto] items-center gap-6 sm:gap-12 py-8 sm:py-12 px-4 sm:px-8"
            >
              <span className="font-display text-[2.5rem] sm:text-[4rem] leading-none text-cream-30 group-hover:text-gold transition-colors duration-300 tabular-nums">
                {String(i + 1).padStart(2, "0")}
              </span>

              <div className="min-w-0">
                <div className="flex items-center gap-4">
                  <motion.span
                    animate={active ? { x: 0, opacity: 1 } : { x: -8, opacity: 0 }}
                    transition={{ duration: 0.3 }}
                    aria-hidden
                    className="text-gold inline-block"
                  >
                    <Icon name={s.icon} size={22} />
                  </motion.span>
                  <h3 className="font-display text-[1.6rem] sm:text-[2.4rem] m-0 leading-tight text-white">
                    {s.title}
                  </h3>
                </div>
                <p className="text-cream-50 text-[0.95rem] mt-3 max-w-[600px]">{s.blurb}</p>
              </div>

              <span className="hidden sm:flex items-center gap-2 text-gold text-[0.72rem] font-bold tracking-[0.18em] uppercase whitespace-nowrap">
                <AnimatePresence mode="wait" initial={false}>
                  {active ? (
                    <motion.span key="hover" initial={{ x: -6, opacity: 0 }} animate={{ x: 0, opacity: 1 }} exit={{ x: 6, opacity: 0 }} transition={{ duration: 0.25 }}>
                      {s.ctaLabel ?? "See examples"}
                    </motion.span>
                  ) : (
                    <motion.span key="idle" initial={{ x: -6, opacity: 0 }} animate={{ x: 0, opacity: 1 }} exit={{ x: 6, opacity: 0 }} transition={{ duration: 0.25 }} className="text-cream-30">
                      View
                    </motion.span>
                  )}
                </AnimatePresence>
                <motion.span animate={{ x: active ? 6 : 0 }} transition={{ duration: 0.3 }}>
                  <Icon name="arrow-right" size={16} />
                </motion.span>
              </span>
            </Link>
          </motion.article>
        );
      })}
    </div>
  );
}
