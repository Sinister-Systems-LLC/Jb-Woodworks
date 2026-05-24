// Author: RKOJ-ELENO :: 2026-05-24
"use client";
import { motion } from "framer-motion";
import { Icon } from "@/components/ui/icon";
import type { IconName } from "@/components/ui/icon";

type Stat = { icon: IconName; headline: string; label: string };

const STATS: Stat[] = [
  { icon: "anvil",   headline: "In-house",   label: "Designed + built by us, never subbed out" },
  { icon: "ruler",   headline: "Custom",     label: "Drawn to your space, not pulled from a catalog" },
  { icon: "leaf",    headline: "Orlando, FL", label: "Greater Orlando + Central Florida coast" },
  { icon: "compass", headline: "Est. 2025",  label: "Custom woodworking + commercial fabrication" }
];

export function NumbersBand() {
  return (
    <section className="py-20 bg-ink-2 border-y border-line">
      <div className="container-site">
        <div className="grid gap-8 sm:gap-12 sm:grid-cols-2 lg:grid-cols-4">
          {STATS.map((s, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.4 }}
              transition={{ duration: 0.6, delay: i * 0.08, ease: [0.16, 1, 0.3, 1] }}
              className="relative pl-7"
            >
              <span aria-hidden className="absolute left-0 top-1 bottom-2 w-px bg-gradient-to-b from-gold via-gold-dim to-transparent" />
              <Icon name={s.icon} size={36} className="text-gold mb-4" />
              <p className="font-display text-[clamp(1.9rem,3.4vw,2.6rem)] leading-none text-white">
                {s.headline}
              </p>
              <p className="mt-3 text-[0.85rem] text-cream-50 leading-snug max-w-[220px]">{s.label}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
