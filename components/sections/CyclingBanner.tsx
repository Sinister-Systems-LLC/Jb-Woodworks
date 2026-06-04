// Author: RKOJ-ELENO :: 2026-06-02
// D-series CyclingBanner — cycles through JBW brand trust signals between Hero and Marquee.
"use client";
import { useEffect, useState } from "react";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";

const MESSAGES = [
  { headline: "Free Estimates", detail: "Same-day response, weekdays" },
  { headline: "Custom Builds Only", detail: "No catalog pieces, ever" },
  { headline: "Est. 2025", detail: "Serving Orlando & Central FL" },
  { headline: "6 Service Lines", detail: "Docks · Decks · Furniture · More" },
  { headline: "Residential & Commercial", detail: "From pool decks to branded displays" },
  { headline: "Built In-House", detail: "No subcontracted crews, ever" },
];

const INTERVAL_MS = 3500;

export function CyclingBanner() {
  const [idx, setIdx] = useState(0);
  const reduced = useReducedMotion();

  useEffect(() => {
    if (reduced) return;
    const t = setInterval(() => setIdx((i) => (i + 1) % MESSAGES.length), INTERVAL_MS);
    return () => clearInterval(t);
  }, [reduced]);

  const msg = MESSAGES[idx];

  return (
    <div
      className="relative bg-ink border-y border-line overflow-hidden select-none"
      style={{ minHeight: 52 }}
      aria-live="polite"
      aria-atomic="true"
    >
      {/* Subtle left-edge gold accent */}
      <div aria-hidden className="absolute inset-y-0 left-0 w-[3px] bg-gradient-to-b from-transparent via-gold/50 to-transparent pointer-events-none" />

      <div className="container-site flex items-center justify-between gap-4 py-3">
        {/* Cycling message */}
        <div className="relative flex-1 overflow-hidden h-[26px] flex items-center">
          <AnimatePresence mode="wait" initial={false}>
            <motion.div
              key={idx}
              initial={{ y: reduced ? 0 : 16, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: reduced ? 0 : -16, opacity: 0 }}
              transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
              className="absolute inset-0 flex items-center gap-3"
            >
              <span className="font-mono text-[0.58rem] tracking-[0.38em] uppercase font-bold text-gold whitespace-nowrap">
                {msg.headline}
              </span>
              <span aria-hidden className="h-px w-5 bg-gold/40 shrink-0 hidden sm:block" />
              <span className="font-sans text-[0.68rem] text-cream-30 whitespace-nowrap hidden sm:block">
                {msg.detail}
              </span>
            </motion.div>
          </AnimatePresence>
        </div>

        {/* Dot nav + subtle divider */}
        <div className="flex items-center gap-3 shrink-0">
          <div aria-hidden className="h-3.5 w-px bg-line-strong hidden sm:block" />
          <div className="flex items-center gap-[5px]" role="tablist" aria-label="Trust signals">
            {MESSAGES.map((m, i) => (
              <button
                key={i}
                type="button"
                role="tab"
                aria-selected={i === idx}
                aria-label={m.headline}
                onClick={() => setIdx(i)}
                className={[
                  "rounded-full transition-all duration-300 focus-visible:outline focus-visible:outline-2 focus-visible:outline-gold",
                  i === idx
                    ? "bg-gold w-3.5 h-[3px]"
                    : "bg-cream-30/35 w-[3px] h-[3px] hover:bg-gold/60",
                ].join(" ")}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
