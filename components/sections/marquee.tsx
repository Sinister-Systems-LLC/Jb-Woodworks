// Author: RKOJ-ELENO :: 2026-05-23
"use client";
import { motion } from "framer-motion";

const ITEMS = [
  "DOCKS",
  "CUSTOM DECKS",
  "PERGOLAS",
  "POOL TABLES",
  "CUSTOM FURNITURE",
  "INTERIOR TRIM",
  "TREX DECKS",
  "BOAT DOCKS",
  "OUTDOOR LIVING"
];

export function Marquee() {
  const loop = [...ITEMS, ...ITEMS, ...ITEMS];
  return (
    <div className="relative bg-ink-2 border-y border-line py-7 overflow-hidden">
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
