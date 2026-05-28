// Author: RKOJ-ELENO :: 2026-05-28
"use client";
import { motion, useReducedMotion } from "framer-motion";
import { cn } from "@/lib/utils";

export function FloatingPullQuote({
  quote,
  attribution,
  align = "left",
  accent = true,
  className
}: {
  quote: string;
  attribution?: string;
  align?: "left" | "right" | "center";
  accent?: boolean;
  className?: string;
}) {
  const reduced = useReducedMotion();
  const alignClass =
    align === "right" ? "text-right ml-auto" : align === "center" ? "text-center mx-auto" : "text-left";

  return (
    <motion.figure
      initial={reduced ? false : { opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.4 }}
      transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
      className={cn(
        "relative max-w-[760px] py-12 sm:py-16",
        alignClass,
        className
      )}
    >
      {accent && (
        <span
          aria-hidden
          className={cn(
            "absolute top-0 h-[2px] w-16 bg-gradient-to-r from-gold via-gold-dim to-transparent",
            align === "right" ? "right-0" : align === "center" ? "left-1/2 -translate-x-1/2" : "left-0"
          )}
        />
      )}
      <blockquote className="font-display italic text-[clamp(1.6rem,3.4vw,2.6rem)] leading-[1.15] text-white">
        &ldquo;{quote}&rdquo;
      </blockquote>
      {attribution && (
        <figcaption className="mt-5 text-[0.78rem] tracking-[0.22em] uppercase text-gold font-bold">
          {attribution}
        </figcaption>
      )}
    </motion.figure>
  );
}
