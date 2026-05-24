// Author: RKOJ-ELENO :: 2026-05-23
"use client";
import { motion } from "framer-motion";

const ITEMS = [
  "DECKS",
  "DOCKS",
  "PERGOLAS",
  "OUTDOOR LIVING",
  "CUSTOM FURNITURE",
  "MILLWORK",
  "CABINETRY",
  "BUILT-INS",
  "TRIM CARPENTRY",
  "HARDWOOD FLOORS",
  "COMMERCIAL FABRICATION",
  "BRANDED DISPLAYS",
  "EVENT BUILDS",
  "FEATURE WALLS"
];

export function Marquee() {
  const loop = [...ITEMS, ...ITEMS, ...ITEMS];
  return (
    <div className="relative bg-ink-2 border-t border-line pt-6 pb-3 overflow-hidden">
      {/* Top hairline accent so the band reads as one with whatever sits above */}
      <div aria-hidden className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-gold-dim/60 to-transparent" />
      <div aria-hidden className="absolute inset-y-0 left-0 w-32 z-10 bg-gradient-to-r from-ink-2 to-transparent" />
      <div aria-hidden className="absolute inset-y-0 right-0 w-32 z-10 bg-gradient-to-l from-ink-2 to-transparent" />

      <motion.ul
        className="flex gap-12 list-none whitespace-nowrap"
        animate={{ x: ["0%", "-33.333%"] }}
        transition={{ duration: 40, ease: "linear", repeat: Infinity }}
        aria-hidden="true"
      >
        {loop.map((s, i) => (
          <li key={i} className="flex items-center gap-12 font-display text-[2.4rem] sm:text-[3rem] text-cream-30 italic">
            {s}
            <span className="text-gold not-italic font-sans font-black text-[1.4rem]" aria-hidden>+</span>
          </li>
        ))}
      </motion.ul>

      <span className="sr-only">
        What we build: {ITEMS.join(", ")}.
      </span>
    </div>
  );
}
