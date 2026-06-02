// Author: RKOJ-ELENO :: 2026-06-01
// v2: Cycling banner — FL credibility ticker (years, projects, FBC, marine fasteners, cedar/IPE).
"use client";
import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

const ITEMS = [
  { num: "2025", label: "Established in Orlando, FL" },
  { num: "150+", label: "Outdoor builds delivered along the FL coast" },
  { num: "FBC", label: "Florida Building Code-compliant framing — every job" },
  { num: "316", label: "Stainless + marine-grade fasteners on every dock" },
  { num: "IPE", label: "Cedar + IPE specialists — UV + salt resistant" },
  { num: "10yr", label: "Workmanship warranty on all custom builds" }
];

export function CyclingBanner() {
  const [i, setI] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setI((x) => (x + 1) % ITEMS.length), 3200);
    return () => clearInterval(t);
  }, []);
  const item = ITEMS[i];
  return (
    <div className="relative bg-gradient-to-r from-ink via-ink-2 to-ink border-y border-line py-7 overflow-hidden">
      <div aria-hidden className="absolute inset-y-0 left-0 w-1 bg-gradient-to-b from-transparent via-coastal to-transparent" />
      <div aria-hidden className="absolute inset-y-0 right-0 w-1 bg-gradient-to-b from-transparent via-gold to-transparent" />
      <div className="container-site relative flex items-center justify-center gap-6">
        <AnimatePresence mode="wait">
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
            className="flex flex-col sm:flex-row sm:items-baseline gap-2 sm:gap-5 text-center"
          >
            <span className="font-display text-[clamp(1.8rem,3.2vw,2.6rem)] leading-none text-gold tabular-nums">{item.num}</span>
            <span className="text-cream-80 text-[0.95rem] tracking-wide">{item.label}</span>
          </motion.div>
        </AnimatePresence>
      </div>
      {/* Tick markers */}
      <div className="absolute bottom-2 left-1/2 -translate-x-1/2 flex gap-1.5">
        {ITEMS.map((_, idx) => (
          <span
            key={idx}
            aria-hidden
            className={`h-0.5 rounded-full transition-all duration-500 ${idx === i ? "w-6 bg-coastal" : "w-2 bg-cream-30"}`}
          />
        ))}
      </div>
    </div>
  );
}
