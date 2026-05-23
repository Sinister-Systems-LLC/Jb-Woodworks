// Author: RKOJ-ELENO :: 2026-05-23
"use client";
import { motion, useReducedMotion } from "framer-motion";
import { Icon } from "@/components/ui/icon";
import type { Service } from "@/lib/content";

export function ServiceCard({ service, index }: { service: Service; index: number }) {
  const reduced = useReducedMotion();
  return (
    <motion.article
      initial={reduced ? false : { opacity: 0, y: 28 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.15 }}
      transition={{ duration: 0.65, delay: index * 0.08, ease: [0.16, 1, 0.3, 1] }}
      whileHover={reduced ? undefined : { y: -6 }}
      className="group relative bg-ink-3 border border-line p-9 pt-9 rounded-xl overflow-hidden isolate transition-colors duration-300 hover:border-transparent hover:bg-ink-4 hover:shadow-[0_18px_40px_-16px_rgba(0,0,0,0.7)]"
    >
      {/* Top gold sweep on hover */}
      <span aria-hidden className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-gold to-transparent origin-center scale-x-0 transition-transform duration-[550ms] ease-out group-hover:scale-x-100" />

      {/* Gold gradient border ring */}
      <span aria-hidden className="absolute -inset-px rounded-xl p-px opacity-0 transition-opacity duration-300 group-hover:opacity-100" style={{
        background: "linear-gradient(135deg, transparent, rgba(201,168,76,0.35), transparent)",
        WebkitMask: "linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0)",
        WebkitMaskComposite: "xor",
        maskComposite: "exclude"
      } as React.CSSProperties} />

      <motion.div
        whileHover={reduced ? undefined : { rotate: -6, scale: 1.05 }}
        transition={{ type: "spring", stiffness: 280, damping: 18 }}
        className="w-14 h-14 grid place-items-center bg-gold-dim text-gold rounded-md mb-5 transition-colors duration-300 group-hover:bg-gold group-hover:text-ink"
      >
        <Icon name={service.icon} size={26} />
      </motion.div>
      <h3 className="font-display text-[1.4rem] text-white mb-3">{service.title}</h3>
      <p className="text-cream-50 text-[0.95rem]">{service.blurb}</p>

      {/* Bottom accent that slides in on hover */}
      <span aria-hidden className="absolute bottom-0 left-0 right-0 h-0.5 bg-gold origin-left scale-x-0 transition-transform duration-[450ms] ease-out group-hover:scale-x-100" />
    </motion.article>
  );
}
