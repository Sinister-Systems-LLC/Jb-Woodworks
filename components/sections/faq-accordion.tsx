// Author: RKOJ-ELENO :: 2026-05-23
// FAQ presented as an editorial accordion: numbered prefix, italic question,
// answer reveals on click, gold sweep + chevron rotate, in-view stagger. Used
// on the home page and the about page.
"use client";

import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence, useInView, useReducedMotion } from "framer-motion";
import type { Faq } from "@/lib/content";

export function FaqAccordion({ items, initialOpen = -1 }: { items: Faq[]; initialOpen?: number }) {
  const [open, setOpen] = useState<number>(initialOpen);
  const reduced = useReducedMotion();
  const ref = useRef<HTMLDivElement | null>(null);
  const inView = useInView(ref, { once: true, amount: 0.15 });

  const toggle = (i: number) => setOpen((prev) => (prev === i ? -1 : i));

  // Allow keyboard arrow nav between questions.
  useEffect(() => {
    const root = ref.current;
    if (!root) return;
    const handler = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement | null;
      if (!target?.closest('[data-faq-trigger]')) return;
      const triggers = Array.from(root.querySelectorAll<HTMLElement>('[data-faq-trigger]'));
      const i = triggers.indexOf(target as HTMLElement);
      if (i < 0) return;
      if (e.key === "ArrowDown" || e.key === "ArrowRight") {
        e.preventDefault();
        triggers[(i + 1) % triggers.length]?.focus();
      } else if (e.key === "ArrowUp" || e.key === "ArrowLeft") {
        e.preventDefault();
        triggers[(i - 1 + triggers.length) % triggers.length]?.focus();
      } else if (e.key === "Home") {
        e.preventDefault();
        triggers[0]?.focus();
      } else if (e.key === "End") {
        e.preventDefault();
        triggers[triggers.length - 1]?.focus();
      }
    };
    root.addEventListener("keydown", handler);
    return () => root.removeEventListener("keydown", handler);
  }, []);

  return (
    <div ref={ref} className="relative">
      {/* Top + bottom gold rails */}
      <div aria-hidden className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-gold-dim to-transparent" />
      <div aria-hidden className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-gold-dim to-transparent" />

      <ul className="divide-y divide-line">
        {items.map((item, i) => {
          const isOpen = open === i;
          return (
            <motion.li
              key={i}
              initial={reduced ? false : { opacity: 0, y: 18 }}
              animate={inView ? { opacity: 1, y: 0 } : reduced ? false : { opacity: 0, y: 18 }}
              transition={{ duration: 0.55, delay: i * 0.06, ease: [0.16, 1, 0.3, 1] }}
              className="group relative"
            >
              {/* Gold left-rail accent — slides in on hover / open */}
              <span
                aria-hidden
                className={[
                  "absolute left-0 top-0 bottom-0 w-px bg-gold transition-all duration-500 ease-out origin-top",
                  isOpen ? "scale-y-100 opacity-100" : "scale-y-0 opacity-0 group-hover:scale-y-100 group-hover:opacity-70"
                ].join(" ")}
              />

              <button
                data-faq-trigger
                type="button"
                aria-expanded={isOpen}
                aria-controls={`faq-panel-${i}`}
                id={`faq-trigger-${i}`}
                onClick={() => toggle(i)}
                className="w-full flex items-start gap-5 sm:gap-7 py-6 sm:py-7 pl-5 sm:pl-7 pr-4 text-left transition-colors hover:bg-ink-3/40 focus-visible:bg-ink-3/40 focus-visible:outline-none"
              >
                {/* Number plate */}
                <span
                  className={[
                    "shrink-0 font-mono font-bold tabular-nums text-[0.7rem] tracking-[0.18em] pt-1.5 transition-colors duration-300",
                    isOpen ? "text-gold" : "text-cream-30 group-hover:text-gold/70"
                  ].join(" ")}
                  aria-hidden
                >
                  {String(i + 1).padStart(2, "0")}
                </span>

                {/* Question */}
                <span
                  className={[
                    "flex-1 font-display text-[clamp(1.05rem,2vw,1.4rem)] leading-[1.35] transition-colors duration-300",
                    isOpen ? "text-white" : "text-cream-80 group-hover:text-white"
                  ].join(" ")}
                >
                  {item.q}
                </span>

                {/* Chevron */}
                <span
                  aria-hidden
                  className={[
                    "shrink-0 mt-1 w-7 h-7 rounded-full border flex items-center justify-center transition-all duration-500",
                    isOpen
                      ? "border-gold bg-gold/10 rotate-180"
                      : "border-line-strong group-hover:border-gold-dim"
                  ].join(" ")}
                >
                  <svg width="11" height="11" viewBox="0 0 11 11" fill="none" aria-hidden>
                    <path d="M2 3.5L5.5 7L9 3.5" stroke={isOpen ? "#c9a84c" : "currentColor"} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </span>
              </button>

              <AnimatePresence initial={false}>
                {isOpen && (
                  <motion.div
                    key="content"
                    id={`faq-panel-${i}`}
                    role="region"
                    aria-labelledby={`faq-trigger-${i}`}
                    initial={reduced ? { height: "auto", opacity: 1 } : { height: 0, opacity: 0 }}
                    animate={reduced ? { height: "auto", opacity: 1 } : { height: "auto", opacity: 1 }}
                    exit={reduced ? { height: "auto", opacity: 0 } : { height: 0, opacity: 0 }}
                    transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
                    className="overflow-hidden"
                  >
                    <div className="pl-[3.6rem] sm:pl-[4.8rem] pr-12 pb-7 -mt-1 relative">
                      <p className="text-cream-50 text-[0.97rem] leading-[1.75] max-w-[640px]">{item.a}</p>
                      {/* Subtle gold underline under the answer */}
                      <span aria-hidden className="block mt-5 h-px w-12 bg-gold/40" />
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.li>
          );
        })}
      </ul>
    </div>
  );
}
