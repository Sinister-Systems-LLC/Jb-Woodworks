// Author: RKOJ-ELENO :: 2026-05-23
"use client";
import { motion, useReducedMotion, type Variants } from "framer-motion";
import { type ReactNode } from "react";

const variants: Variants = {
  hidden: { opacity: 0, y: 28 },
  show: { opacity: 1, y: 0 }
};

type Props = {
  children: ReactNode;
  delay?: number;
  className?: string;
  amount?: number;
  as?: "div" | "article" | "section" | "li";
};

export function Reveal({ children, delay = 0, className, amount = 0.15, as = "div" }: Props) {
  const reduced = useReducedMotion();
  const MotionTag = motion[as] as typeof motion.div;
  if (reduced) {
    return <div className={className}>{children}</div>;
  }
  return (
    <MotionTag
      className={className}
      variants={variants}
      initial="hidden"
      whileInView="show"
      viewport={{ once: true, amount }}
      transition={{ duration: 0.7, delay: delay / 1000, ease: [0.16, 1, 0.3, 1] }}
    >
      {children}
    </MotionTag>
  );
}
